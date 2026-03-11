"""Internal-first singscore boundary for Spatial-CI.

The scorer stays inside Spatial-CI until R parity, contract behavior, and
reuse demand justify extraction into a standalone package.
"""

import csv
import hashlib
import json
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from spatial_ci.scoring.artifacts import (
    ScoreArtifact,
    ScoreFailureCode,
    ScorePacket,
    ScoreStatus,
    SignatureDirection,
)
from spatial_ci.scoring.r_bridge import (
    build_bridge_paths,
    load_score_output,
    run_r_script,
)
from spatial_ci.signatures import GeneSignature


class MissingGenePolicy(str, Enum):
    """How the scorer should behave when signature genes are absent."""

    INTERSECT = "intersect"
    ERROR = "error"
    DROP_SAMPLE = "drop_sample"


class TiePolicy(str, Enum):
    """Explicit tie-handling controls for future Python scoring parity work."""

    AVERAGE = "average"
    MIN = "min"
    MAX = "max"
    DENSE = "dense"


@dataclass(frozen=True)
class ScoreResult:
    """Minimal score artifact returned by the legacy placeholder scorer."""

    score: float | None
    n_genes_total: int
    n_genes_matched: int
    missing_genes: tuple[str, ...]
    tie_policy: TiePolicy
    missing_gene_policy: MissingGenePolicy


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _hash_file(path: Path) -> str:
    if not path.exists():
        return "missing"

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _normalize_expression_matrix(
    expression_matrix: Mapping[str, Mapping[str, float]],
) -> dict[str, dict[str, float]]:
    if not expression_matrix:
        raise ValueError(
            f"{ScoreFailureCode.INVALID_EXPRESSION_INPUT.value}: expression_matrix "
            "must not be empty."
        )

    normalized: dict[str, dict[str, float]] = {}
    for observation_id, expression_by_gene in expression_matrix.items():
        if not observation_id:
            raise ValueError(
                f"{ScoreFailureCode.INVALID_EXPRESSION_INPUT.value}: observation_id "
                "must be non-empty."
            )

        if not expression_by_gene:
            raise ValueError(
                f"{ScoreFailureCode.INVALID_EXPRESSION_INPUT.value}: "
                f"expression_by_gene must not be empty for {observation_id}."
            )

        normalized[observation_id] = {
            gene: float(value) for gene, value in expression_by_gene.items()
        }

    return normalized


def _signature_direction(signatures: Sequence[GeneSignature]) -> SignatureDirection:
    return (
        SignatureDirection.UP_DOWN
        if any(signature.down_genes for signature in signatures)
        else SignatureDirection.UP_ONLY
    )


def _write_expression_input(
    path: Path, expression_matrix: Mapping[str, Mapping[str, float]]
) -> None:
    genes = sorted(
        {
            gene
            for expression_by_gene in expression_matrix.values()
            for gene in expression_by_gene
        }
    )
    observation_ids = sorted(expression_matrix)

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["gene", *observation_ids])
        for gene in genes:
            writer.writerow(
                [
                    gene,
                    *[
                        expression_matrix[observation_id].get(gene, 0.0)
                        for observation_id in observation_ids
                    ],
                ]
            )


def _write_signature_input(path: Path, signatures: Sequence[GeneSignature]) -> None:
    payload = {
        signature.name: {"up_genes": list(signature.up_genes)}
        for signature in signatures
        if not signature.down_genes
    }
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def _write_scoring_request(
    path: Path,
    *,
    target_definition_id: str,
    scoring_contract_id: str,
    debug_mode: bool,
) -> None:
    payload = {
        "bridge_contract_version": "v1",
        "debug_mode": debug_mode,
        "scoring_contract_id": scoring_contract_id,
        "target_definition_id": target_definition_id,
    }
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def _make_artifact(
    *,
    target_definition_id: str,
    scoring_contract_id: str,
    signature_direction: SignatureDirection,
    packets: Sequence[ScorePacket],
) -> ScoreArtifact:
    repo_root = _repo_root()
    scoring_script = repo_root / "scripts" / "score_targets.R"
    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    return ScoreArtifact(
        target_definition_id=target_definition_id,
        scoring_contract_id=scoring_contract_id,
        signature_direction=signature_direction,
        bridge_contract_version="v1",
        generated_at=generated_at,
        run_id="scoring-boundary-r-bridge",
        r_version="unknown",
        singscore_version="unknown",
        renv_lock_hash=_hash_file(repo_root / "renv.lock"),
        scoring_script_path="scripts/score_targets.R",
        scoring_script_hash=_hash_file(scoring_script),
        source_expression_artifact_hash=None,
        source_manifest_id=None,
        packets=tuple(
            sorted(
                packets,
                key=lambda packet: (packet.observation_id, packet.program_name),
            )
        ),
    )


def _unsupported_packets(
    *,
    observation_ids: Sequence[str],
    signature: GeneSignature,
    sample_ids_by_observation: Mapping[str, str] | None,
    slide_ids_by_observation: Mapping[str, str] | None,
) -> list[ScorePacket]:
    return [
        ScorePacket(
            observation_id=observation_id,
            sample_id=(
                sample_ids_by_observation.get(observation_id)
                if sample_ids_by_observation
                else None
            ),
            slide_id=(
                slide_ids_by_observation.get(observation_id)
                if slide_ids_by_observation
                else None
            ),
            program_name=signature.name,
            status=ScoreStatus.FAILED,
            raw_rank_evidence=None,
            signature_size_declared=len(signature.up_genes),
            signature_size_matched=0,
            signature_coverage=0.0,
            dropped_by_missingness_rule=False,
            failure_code=ScoreFailureCode.UNSUPPORTED_DIRECTIONALITY,
            null_calibrated_score=None,
            dropout_penalty=None,
            spatial_consistency=None,
        )
        for observation_id in observation_ids
    ]


def _packets_from_output(
    *,
    rows: Sequence[dict[str, object]],
    signatures_by_name: Mapping[str, GeneSignature],
    sample_ids_by_observation: Mapping[str, str] | None,
    slide_ids_by_observation: Mapping[str, str] | None,
    missing_gene_threshold: float,
) -> list[ScorePacket]:
    packets: list[ScorePacket] = []
    minimum_coverage = 1.0 - missing_gene_threshold

    for row in rows:
        observation_id = str(row["observation_id"])
        program_name = str(row["program_name"])
        signature = signatures_by_name[program_name]
        declared_size = len(signature.up_genes)
        matched_value = row["signature_size_matched"]
        raw_value = row["raw_rank_evidence"]

        if not isinstance(matched_value, int | float | str):
            raise TypeError(
                "signature_size_matched must be an int-like value in scorer output."
            )
        if raw_value is not None and not isinstance(raw_value, int | float | str):
            raise TypeError(
                "raw_rank_evidence must be numeric or null in scorer output."
            )

        matched_size = int(matched_value)
        raw_rank_evidence = None if raw_value is None else float(raw_value)
        coverage = matched_size / declared_size

        if matched_size == 0:
            status = ScoreStatus.DROPPED
            failure_code = ScoreFailureCode.EMPTY_SIGNATURE_MATCH
            dropped = True
        elif coverage < minimum_coverage:
            status = ScoreStatus.DROPPED
            failure_code = ScoreFailureCode.LOW_SIGNATURE_COVERAGE
            dropped = True
        else:
            status = ScoreStatus.OK
            failure_code = None
            dropped = False

        packets.append(
            ScorePacket(
                observation_id=observation_id,
                sample_id=(
                    sample_ids_by_observation.get(observation_id)
                    if sample_ids_by_observation
                    else None
                ),
                slide_id=(
                    slide_ids_by_observation.get(observation_id)
                    if slide_ids_by_observation
                    else None
                ),
                program_name=program_name,
                status=status,
                raw_rank_evidence=raw_rank_evidence,
                signature_size_declared=declared_size,
                signature_size_matched=matched_size,
                signature_coverage=coverage,
                dropped_by_missingness_rule=dropped,
                failure_code=failure_code,
                null_calibrated_score=None,
                dropout_penalty=None,
                spatial_consistency=None,
            )
        )

    return packets


def score_batch(
    *,
    expression_matrix: Mapping[str, Mapping[str, float]],
    signatures: Sequence[GeneSignature],
    scoring_contract_id: str,
    target_definition_id: str,
    sample_ids_by_observation: Mapping[str, str] | None = None,
    slide_ids_by_observation: Mapping[str, str] | None = None,
    missing_gene_threshold: float = 0.1,
    debug_mode: bool = False,
) -> ScoreArtifact:
    """Score one batch of observations against one or more signatures."""

    normalized_expression_matrix = _normalize_expression_matrix(expression_matrix)
    observation_ids = sorted(normalized_expression_matrix)
    supported_signatures = tuple(
        signature for signature in signatures if not signature.down_genes
    )
    unsupported_signatures = tuple(
        signature for signature in signatures if signature.down_genes
    )

    packets: list[ScorePacket] = []
    for signature in unsupported_signatures:
        packets.extend(
            _unsupported_packets(
                observation_ids=observation_ids,
                signature=signature,
                sample_ids_by_observation=sample_ids_by_observation,
                slide_ids_by_observation=slide_ids_by_observation,
            )
        )

    if supported_signatures:
        with tempfile.TemporaryDirectory(prefix="spatial-ci-singscore-") as tmpdir:
            workdir = Path(tmpdir)
            paths = build_bridge_paths(workdir)
            _write_expression_input(
                paths.expression_input, normalized_expression_matrix
            )
            _write_signature_input(paths.signature_input, supported_signatures)
            _write_scoring_request(
                paths.scoring_request,
                target_definition_id=target_definition_id,
                scoring_contract_id=scoring_contract_id,
                debug_mode=debug_mode,
            )
            run_r_script(paths, repo_root=_repo_root())
            table = load_score_output(paths.score_output)
            packets.extend(
                _packets_from_output(
                    rows=table.to_pylist(),
                    signatures_by_name={
                        signature.name: signature for signature in supported_signatures
                    },
                    sample_ids_by_observation=sample_ids_by_observation,
                    slide_ids_by_observation=slide_ids_by_observation,
                    missing_gene_threshold=missing_gene_threshold,
                )
            )

    return _make_artifact(
        target_definition_id=target_definition_id,
        scoring_contract_id=scoring_contract_id,
        signature_direction=_signature_direction(signatures),
        packets=packets,
    )


def score_one(
    *,
    observation_id: str,
    expression_by_gene: Mapping[str, float],
    signature: GeneSignature,
    scoring_contract_id: str,
    target_definition_id: str,
    sample_id: str | None = None,
    slide_id: str | None = None,
    missing_gene_threshold: float = 0.1,
    debug_mode: bool = False,
) -> ScorePacket:
    """Convenience wrapper over batch scoring for one observation."""

    artifact = score_batch(
        expression_matrix={observation_id: dict(expression_by_gene)},
        signatures=(signature,),
        scoring_contract_id=scoring_contract_id,
        target_definition_id=target_definition_id,
        sample_ids_by_observation=(
            {observation_id: sample_id} if sample_id is not None else None
        ),
        slide_ids_by_observation={observation_id: slide_id} if slide_id else None,
        missing_gene_threshold=missing_gene_threshold,
        debug_mode=debug_mode,
    )
    return artifact.packets[0]


def singscore(
    expression_by_gene: Mapping[str, float],
    signature: GeneSignature,
    *,
    tie_policy: TiePolicy = TiePolicy.AVERAGE,
    missing_gene_policy: MissingGenePolicy = MissingGenePolicy.INTERSECT,
) -> ScoreResult:
    """Legacy placeholder for a native Python numerical scorer."""

    raise NotImplementedError(
        "Python singscore remains internal-first until Bioconductor parity and "
        "contract behavior are implemented and verified."
    )


__all__ = [
    "MissingGenePolicy",
    "ScoreResult",
    "TiePolicy",
    "score_batch",
    "score_one",
    "singscore",
]
