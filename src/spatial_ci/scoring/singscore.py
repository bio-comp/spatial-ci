"""Internal-first singscore boundary for Spatial-CI.

The scorer stays inside Spatial-CI until R parity, contract behavior, and
reuse demand justify extraction into a standalone package.
"""

import csv
import hashlib
import json
import os
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from spatial_ci.scoring.artifacts import (
    ScoreArtifact,
    ScoreFailureCode,
    ScorePacket,
    ScoreStatus,
    SignatureDirection,
)
from spatial_ci.scoring.r_bridge import (
    InvalidScorerOutputError,
    build_bridge_paths,
    load_runtime_metadata,
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
    override = os.environ.get("SPATIAL_CI_REPO_ROOT")
    if override:
        return Path(override).resolve()

    for candidate in Path(__file__).resolve().parents:
        if (
            (candidate / "pyproject.toml").exists()
            and (candidate / "scripts" / "score_targets.R").exists()
        ):
            return candidate

    raise FileNotFoundError(
        "Could not resolve Spatial-CI repo root from module path. Set "
        "SPATIAL_CI_REPO_ROOT to override discovery."
    )


def _hash_file(path: Path) -> str:
    if not path.exists():
        return "missing"

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4096), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_expression_matrix(
    expression_matrix: Mapping[str, Mapping[str, float]],
) -> None:
    if not expression_matrix:
        raise ValueError(
            f"{ScoreFailureCode.INVALID_EXPRESSION_INPUT.value}: expression_matrix "
            "must not be empty."
        )

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

        for gene, value in expression_by_gene.items():
            if not gene:
                raise ValueError(
                    f"{ScoreFailureCode.INVALID_EXPRESSION_INPUT.value}: gene "
                    f"must be non-empty for {observation_id}."
                )


def _validate_signatures(signatures: Sequence[GeneSignature]) -> None:
    if not signatures:
        raise ValueError("signatures must not be empty.")

    signature_names = [signature.name for signature in signatures]
    duplicates = sorted(
        {
            signature_name
            for signature_name in signature_names
            if signature_names.count(signature_name) > 1
        }
    )
    if duplicates:
        duplicate_summary = ", ".join(duplicates)
        raise ValueError(f"signature names must be unique: {duplicate_summary}.")


def _validate_missing_gene_threshold(missing_gene_threshold: float) -> None:
    if not 0.0 <= missing_gene_threshold <= 1.0:
        raise ValueError("missing_gene_threshold must be within [0.0, 1.0].")


def _expression_gene_universe(
    expression_matrix: Mapping[str, Mapping[str, float]],
) -> frozenset[str]:
    return frozenset(
        gene
        for expression_by_gene in expression_matrix.values()
        for gene in expression_by_gene
    )


def _normalize_detected_gene_ids_by_observation(
    *,
    detected_gene_ids_by_observation: Mapping[str, Sequence[str]],
    observation_ids: Sequence[str],
    expression_gene_universe: frozenset[str],
) -> dict[str, frozenset[str]]:
    expected_observation_ids = set(observation_ids)
    observed_observation_ids = set(detected_gene_ids_by_observation)

    missing_observations = sorted(expected_observation_ids - observed_observation_ids)
    if missing_observations:
        missing_summary = ", ".join(missing_observations)
        raise ValueError(
            "detected membership is missing observations from the expression input: "
            f"{missing_summary}."
        )

    unexpected_observations = sorted(
        observed_observation_ids - expected_observation_ids
    )
    if unexpected_observations:
        unexpected_summary = ", ".join(unexpected_observations)
        raise ValueError(
            "detected membership contains unexpected observations: "
            f"{unexpected_summary}."
        )

    normalized: dict[str, frozenset[str]] = {}
    for observation_id in observation_ids:
        raw_gene_ids = detected_gene_ids_by_observation[observation_id]
        if isinstance(raw_gene_ids, str):
            raise ValueError(
                "detected membership gene ids must be provided as a sequence of "
                f"strings for {observation_id}, not a single string."
            )

        normalized_gene_ids = tuple(str(gene_id).strip() for gene_id in raw_gene_ids)
        if any(not gene_id for gene_id in normalized_gene_ids):
            raise ValueError(
                "detected membership gene ids must be non-empty strings for "
                f"{observation_id}."
            )

        unique_gene_ids = frozenset(normalized_gene_ids)
        if len(unique_gene_ids) != len(normalized_gene_ids):
            raise ValueError(
                "detected membership contains duplicate detected genes for "
                f"{observation_id}."
            )

        unknown_gene_ids = sorted(unique_gene_ids - expression_gene_universe)
        if unknown_gene_ids:
            unknown_summary = ", ".join(unknown_gene_ids)
            raise ValueError(
                "detected membership references genes outside the expression input "
                f"universe for {observation_id}: {unknown_summary}."
            )

        normalized[observation_id] = unique_gene_ids

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
                        if gene not in expression_matrix[observation_id]
                        else float(expression_matrix[observation_id][gene])
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


def _write_detected_membership_input(
    path: Path, detected_gene_ids_by_observation: Mapping[str, frozenset[str]]
) -> None:
    observation_ids: list[str] = []
    gene_ids: list[str] = []
    for observation_id in sorted(detected_gene_ids_by_observation):
        for gene_id in sorted(detected_gene_ids_by_observation[observation_id]):
            observation_ids.append(observation_id)
            gene_ids.append(gene_id)

    table = pa.Table.from_arrays(
        [
            pa.array(observation_ids, type=pa.string()),
            pa.array(gene_ids, type=pa.string()),
        ],
        names=["observation_id", "gene_id"],
    )
    pq.write_table(table, path)


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
    runtime_metadata: Mapping[str, str],
    packets: Sequence[ScorePacket],
    run_id: str | None,
    source_expression_artifact_hash: str | None,
    source_manifest_id: str | None,
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
        run_id=run_id or "scoring-boundary-r-bridge",
        r_version=runtime_metadata["r_version"],
        singscore_version=runtime_metadata["singscore_version"],
        renv_lock_hash=_hash_file(repo_root / "renv.lock"),
        scoring_script_path="scripts/score_targets.R",
        scoring_script_hash=_hash_file(scoring_script),
        source_expression_artifact_hash=source_expression_artifact_hash,
        source_manifest_id=source_manifest_id,
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
    detected_gene_ids_by_observation: Mapping[str, frozenset[str]],
    sample_ids_by_observation: Mapping[str, str] | None,
    slide_ids_by_observation: Mapping[str, str] | None,
    missing_gene_threshold: float,
    debug_mode: bool,
) -> list[ScorePacket]:
    packets: list[ScorePacket] = []
    minimum_coverage = 1.0 - missing_gene_threshold

    for row in rows:
        observation_id = str(row["observation_id"])
        program_name = str(row["program_name"])
        signature = signatures_by_name[program_name]
        raw_value = row["raw_rank_evidence"]

        if raw_value is not None and not isinstance(raw_value, int | float | str):
            raise TypeError(
                "raw_rank_evidence must be numeric or null in scorer output."
            )

        declared_size = len(signature.up_genes)
        if declared_size <= 0:
            raise ValueError("Signatures must declare at least one up gene.")
        matched_gene_ids = tuple(
            sorted(
                detected_gene_ids_by_observation[observation_id]
                & frozenset(signature.up_genes)
            )
        )
        matched_size = len(matched_gene_ids)
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
                matched_gene_ids=matched_gene_ids if debug_mode else None,
            )
        )

    return packets


def _validate_output_rows(
    *,
    rows: Sequence[dict[str, object]],
    observation_ids: Sequence[str],
    signatures_by_name: Mapping[str, GeneSignature],
) -> None:
    expected_observation_ids = set(observation_ids)
    expected_program_names = set(signatures_by_name)
    expected_pairs = {
        (observation_id, program_name)
        for observation_id in observation_ids
        for program_name in signatures_by_name
    }

    seen_pairs: set[tuple[str, str]] = set()
    for row in rows:
        observation_id = str(row["observation_id"])
        program_name = str(row["program_name"])
        pair = (observation_id, program_name)

        if observation_id not in expected_observation_ids:
            raise InvalidScorerOutputError(
                "Score output references unexpected observation_id: "
                f"{observation_id}."
            )
        if program_name not in expected_program_names:
            raise InvalidScorerOutputError(
                f"Score output references unexpected program_name: {program_name}."
            )
        if pair in seen_pairs:
            raise InvalidScorerOutputError(
                "Score output contains duplicate observation_id x program_name rows."
            )
        seen_pairs.add(pair)

    missing_pairs = sorted(expected_pairs - seen_pairs)
    if missing_pairs:
        raise InvalidScorerOutputError("Score output is missing expected score rows.")


def score_batch(
    *,
    expression_matrix: Mapping[str, Mapping[str, float]],
    detected_gene_ids_by_observation: Mapping[str, Sequence[str]],
    signatures: Sequence[GeneSignature],
    scoring_contract_id: str,
    target_definition_id: str,
    sample_ids_by_observation: Mapping[str, str] | None = None,
    slide_ids_by_observation: Mapping[str, str] | None = None,
    missing_gene_threshold: float = 0.1,
    debug_mode: bool = False,
    run_id: str | None = None,
    source_expression_artifact_hash: str | None = None,
    source_manifest_id: str | None = None,
) -> ScoreArtifact:
    """Score one batch of observations against one or more signatures."""

    _validate_expression_matrix(expression_matrix)
    _validate_signatures(signatures)
    _validate_missing_gene_threshold(missing_gene_threshold)
    observation_ids = sorted(expression_matrix)
    normalized_detected_gene_ids_by_observation = (
        _normalize_detected_gene_ids_by_observation(
            detected_gene_ids_by_observation=detected_gene_ids_by_observation,
            observation_ids=observation_ids,
            expression_gene_universe=_expression_gene_universe(expression_matrix),
        )
    )
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
            _write_expression_input(paths.expression_input, expression_matrix)
            _write_signature_input(paths.signature_input, supported_signatures)
            _write_detected_membership_input(
                paths.detected_membership, normalized_detected_gene_ids_by_observation
            )
            _write_scoring_request(
                paths.scoring_request,
                target_definition_id=target_definition_id,
                scoring_contract_id=scoring_contract_id,
                debug_mode=debug_mode,
            )
            run_r_script(paths, repo_root=_repo_root())
            table = load_score_output(paths.score_output)
            runtime_metadata = load_runtime_metadata(paths.runtime_metadata)
            rows = table.to_pylist()
            signatures_by_name = {
                signature.name: signature for signature in supported_signatures
            }
            _validate_output_rows(
                rows=rows,
                observation_ids=observation_ids,
                signatures_by_name=signatures_by_name,
            )
            packets.extend(
                _packets_from_output(
                    rows=rows,
                    signatures_by_name=signatures_by_name,
                    detected_gene_ids_by_observation=(
                        normalized_detected_gene_ids_by_observation
                    ),
                    sample_ids_by_observation=sample_ids_by_observation,
                    slide_ids_by_observation=slide_ids_by_observation,
                    missing_gene_threshold=missing_gene_threshold,
                    debug_mode=debug_mode,
                )
            )
    else:
        runtime_metadata = {"r_version": "unknown", "singscore_version": "unknown"}

    return _make_artifact(
        target_definition_id=target_definition_id,
        scoring_contract_id=scoring_contract_id,
        signature_direction=_signature_direction(signatures),
        runtime_metadata=runtime_metadata,
        packets=packets,
        run_id=run_id,
        source_expression_artifact_hash=source_expression_artifact_hash,
        source_manifest_id=source_manifest_id,
    )


def score_one(
    *,
    observation_id: str,
    expression_by_gene: Mapping[str, float],
    detected_gene_ids: Sequence[str],
    signature: GeneSignature,
    scoring_contract_id: str,
    target_definition_id: str,
    sample_id: str | None = None,
    slide_id: str | None = None,
    missing_gene_threshold: float = 0.1,
    debug_mode: bool = False,
    run_id: str | None = None,
    source_expression_artifact_hash: str | None = None,
    source_manifest_id: str | None = None,
) -> ScorePacket:
    """Convenience wrapper over batch scoring for one observation."""

    artifact = score_batch(
        expression_matrix={observation_id: dict(expression_by_gene)},
        detected_gene_ids_by_observation={observation_id: tuple(detected_gene_ids)},
        signatures=(signature,),
        scoring_contract_id=scoring_contract_id,
        target_definition_id=target_definition_id,
        sample_ids_by_observation=(
            {observation_id: sample_id} if sample_id is not None else None
        ),
        slide_ids_by_observation=(
            {observation_id: slide_id} if slide_id is not None else None
        ),
        missing_gene_threshold=missing_gene_threshold,
        debug_mode=debug_mode,
        run_id=run_id,
        source_expression_artifact_hash=source_expression_artifact_hash,
        source_manifest_id=source_manifest_id,
    )
    if len(artifact.packets) != 1:
        raise ValueError("score_one() expected exactly one packet from score_batch().")
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
