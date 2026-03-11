import hashlib
import importlib
import subprocess
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from spatial_ci.scoring import (
    ScoreArtifact,
    ScoreFailureCode,
    ScorePacket,
    ScoreStatus,
    SignatureDirection,
    score_batch,
    score_one,
)
from spatial_ci.scoring.r_bridge import InvalidScorerOutputError
from spatial_ci.signatures import GeneSignature

SINGSCORE_MODULE = importlib.import_module("spatial_ci.scoring.singscore")


def _artifact_with_single_packet(packet: ScorePacket) -> ScoreArtifact:
    return ScoreArtifact(
        target_definition_id="breast_visium_hallmarks_v1",
        scoring_contract_id="singscore_r_v1",
        signature_direction=SignatureDirection.UP_ONLY,
        bridge_contract_version="v1",
        generated_at="2026-03-10T00:00:00Z",
        run_id="run-1",
        r_version="4.4.0",
        singscore_version="1.30.0",
        renv_lock_hash="abc123",
        scoring_script_path="scripts/score_targets.R",
        scoring_script_hash="def456",
        source_expression_artifact_hash=None,
        source_manifest_id=None,
        packets=(packet,),
    )


def test_score_one_delegates_to_score_batch(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, object]] = []

    def fake_score_batch(**kwargs: object) -> ScoreArtifact:
        calls.append(kwargs)
        return _artifact_with_single_packet(
            ScorePacket(
                observation_id="obs-1",
                sample_id="sample-1",
                slide_id="slide-1",
                program_name="HALLMARK_HYPOXIA",
                status=ScoreStatus.OK,
                raw_rank_evidence=0.25,
                signature_size_declared=2,
                signature_size_matched=2,
                signature_coverage=1.0,
                dropped_by_missingness_rule=False,
                failure_code=None,
                null_calibrated_score=None,
                dropout_penalty=None,
                spatial_consistency=None,
            )
        )

    monkeypatch.setattr(SINGSCORE_MODULE, "score_batch", fake_score_batch)

    packet = score_one(
        observation_id="obs-1",
        expression_by_gene={"CA9": 5.0, "VEGFA": 4.0},
        detected_gene_ids=("CA9", "VEGFA"),
        signature=GeneSignature(name="HALLMARK_HYPOXIA", up_genes=("CA9", "VEGFA")),
        scoring_contract_id="singscore_r_v1",
        target_definition_id="breast_visium_hallmarks_v1",
        sample_id="sample-1",
        slide_id="slide-1",
    )

    assert packet.observation_id == "obs-1"
    assert len(calls) == 1
    assert calls[0]["detected_gene_ids_by_observation"] == {
        "obs-1": ("CA9", "VEGFA")
    }


def test_score_batch_maps_r_output_to_ok_packet(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        SINGSCORE_MODULE,
        "run_r_script",
        lambda paths, repo_root: subprocess.CompletedProcess(
            args=["Rscript"], returncode=0, stdout="", stderr=""
        ),
    )
    monkeypatch.setattr(
        SINGSCORE_MODULE,
        "load_score_output",
        lambda path: pa.table(
            {
                "observation_id": ["obs-1"],
                "program_name": ["HALLMARK_HYPOXIA"],
                "raw_rank_evidence": [0.25],
            }
        ),
    )
    monkeypatch.setattr(
        SINGSCORE_MODULE,
        "load_runtime_metadata",
        lambda path: {"r_version": "4.5.2", "singscore_version": "1.30.0"},
    )

    artifact = score_batch(
        expression_matrix={"obs-1": {"CA9": 5.0, "VEGFA": 4.0}},
        detected_gene_ids_by_observation={"obs-1": ("CA9", "VEGFA")},
        signatures=(GeneSignature(name="HALLMARK_HYPOXIA", up_genes=("CA9", "VEGFA")),),
        scoring_contract_id="singscore_r_v1",
        target_definition_id="breast_visium_hallmarks_v1",
        sample_ids_by_observation={"obs-1": "sample-1"},
        slide_ids_by_observation={"obs-1": "slide-1"},
    )

    assert artifact.packets[0].status is ScoreStatus.OK
    assert artifact.packets[0].failure_code is None
    assert artifact.packets[0].sample_id == "sample-1"
    assert artifact.packets[0].signature_size_declared == 2
    assert artifact.packets[0].signature_size_matched == 2
    assert artifact.r_version == "4.5.2"
    assert artifact.singscore_version == "1.30.0"


def test_score_batch_drops_empty_signature_match(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        SINGSCORE_MODULE,
        "run_r_script",
        lambda paths, repo_root: subprocess.CompletedProcess(
            args=["Rscript"], returncode=0, stdout="", stderr=""
        ),
    )
    monkeypatch.setattr(
        SINGSCORE_MODULE,
        "load_score_output",
        lambda path: pa.table(
            {
                "observation_id": ["obs-1"],
                "program_name": ["HALLMARK_HYPOXIA"],
                "raw_rank_evidence": [None],
            }
        ),
    )
    monkeypatch.setattr(
        SINGSCORE_MODULE,
        "load_runtime_metadata",
        lambda path: {"r_version": "4.5.2", "singscore_version": "1.30.0"},
    )

    artifact = score_batch(
        expression_matrix={"obs-1": {"MKI67": 5.0}},
        detected_gene_ids_by_observation={"obs-1": ("MKI67",)},
        signatures=(GeneSignature(name="HALLMARK_HYPOXIA", up_genes=("CA9", "VEGFA")),),
        scoring_contract_id="singscore_r_v1",
        target_definition_id="breast_visium_hallmarks_v1",
    )

    assert artifact.packets[0].status is ScoreStatus.DROPPED
    assert artifact.packets[0].failure_code is ScoreFailureCode.EMPTY_SIGNATURE_MATCH


def test_score_batch_fails_unsupported_directionality(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called(*args: object, **kwargs: object) -> None:
        raise AssertionError("R bridge should not run for unsupported signatures.")

    monkeypatch.setattr(SINGSCORE_MODULE, "run_r_script", fail_if_called)

    artifact = score_batch(
        expression_matrix={"obs-1": {"CA9": 5.0, "VEGFA": 4.0}},
        detected_gene_ids_by_observation={"obs-1": ("CA9", "VEGFA")},
        signatures=(
            GeneSignature(
                name="BIDIRECTIONAL",
                up_genes=("CA9",),
                down_genes=("VEGFA",),
            ),
        ),
        scoring_contract_id="singscore_r_v1",
        target_definition_id="breast_visium_hallmarks_v1",
    )

    assert artifact.packets[0].status is ScoreStatus.FAILED
    assert (
        artifact.packets[0].failure_code
        is ScoreFailureCode.UNSUPPORTED_DIRECTIONALITY
    )


def test_score_batch_writes_original_expression_mapping_without_copy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    expression_matrix = {"obs-1": {"CA9": 5, "VEGFA": 4}}

    monkeypatch.setattr(
        SINGSCORE_MODULE,
        "run_r_script",
        lambda paths, repo_root: subprocess.CompletedProcess(
            args=["Rscript"], returncode=0, stdout="", stderr=""
        ),
    )
    monkeypatch.setattr(
        SINGSCORE_MODULE,
        "load_score_output",
        lambda path: pa.table(
            {
                "observation_id": ["obs-1"],
                "program_name": ["HALLMARK_HYPOXIA"],
                "raw_rank_evidence": [0.25],
            }
        ),
    )
    monkeypatch.setattr(
        SINGSCORE_MODULE,
        "load_runtime_metadata",
        lambda path: {"r_version": "4.5.2", "singscore_version": "1.30.0"},
    )

    def capture_expression_input(
        path: Path, matrix: dict[str, dict[str, int]]
    ) -> None:
        captured["matrix"] = matrix

    monkeypatch.setattr(
        SINGSCORE_MODULE,
        "_write_expression_input",
        capture_expression_input,
    )

    score_batch(
        expression_matrix=expression_matrix,
        detected_gene_ids_by_observation={"obs-1": ("CA9", "VEGFA")},
        signatures=(GeneSignature(name="HALLMARK_HYPOXIA", up_genes=("CA9", "VEGFA")),),
        scoring_contract_id="singscore_r_v1",
        target_definition_id="breast_visium_hallmarks_v1",
    )

    assert captured["matrix"] is expression_matrix


def test_repo_root_discovers_project_root_from_markers(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    repo_root = tmp_path / "repo"
    module_path = (
        repo_root
        / "src"
        / "spatial_ci"
        / "scoring"
        / "adapters"
        / "singscore.py"
    )
    module_path.parent.mkdir(parents=True)
    module_path.write_text("# test module path\n", encoding="utf-8")
    (repo_root / "pyproject.toml").write_text(
        "[project]\nname = 'spatial-ci'\n",
        encoding="utf-8",
    )
    scripts_dir = repo_root / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "score_targets.R").write_text(
        "#!/usr/bin/env Rscript\n",
        encoding="utf-8",
    )

    monkeypatch.delenv("SPATIAL_CI_REPO_ROOT", raising=False)
    monkeypatch.setattr(SINGSCORE_MODULE, "__file__", str(module_path))

    assert SINGSCORE_MODULE._repo_root() == repo_root


def test_score_batch_rejects_duplicate_detected_gene_pairs() -> None:
    with pytest.raises(ValueError, match="duplicate detected genes"):
        score_batch(
            expression_matrix={"obs-1": {"CA9": 5.0}},
            detected_gene_ids_by_observation={"obs-1": ("CA9", "CA9")},
            signatures=(
                GeneSignature(name="HALLMARK_HYPOXIA", up_genes=("CA9", "VEGFA")),
            ),
            scoring_contract_id="singscore_r_v1",
            target_definition_id="breast_visium_hallmarks_v1",
        )


def test_score_batch_rejects_detected_gene_outside_expression_universe() -> None:
    with pytest.raises(ValueError, match="expression input universe"):
        score_batch(
            expression_matrix={"obs-1": {"CA9": 5.0}},
            detected_gene_ids_by_observation={"obs-1": ("CA9", "VEGFA")},
            signatures=(
                GeneSignature(name="HALLMARK_HYPOXIA", up_genes=("CA9", "VEGFA")),
            ),
            scoring_contract_id="singscore_r_v1",
            target_definition_id="breast_visium_hallmarks_v1",
        )


def test_score_batch_rejects_missing_observation_in_detected_membership() -> None:
    with pytest.raises(ValueError, match="detected membership"):
        score_batch(
            expression_matrix={
                "obs-1": {"CA9": 5.0},
                "obs-2": {"VEGFA": 4.0},
            },
            detected_gene_ids_by_observation={"obs-1": ("CA9",)},
            signatures=(
                GeneSignature(name="HALLMARK_HYPOXIA", up_genes=("CA9", "VEGFA")),
            ),
            scoring_contract_id="singscore_r_v1",
            target_definition_id="breast_visium_hallmarks_v1",
        )


def test_score_batch_rejects_invalid_missing_gene_threshold() -> None:
    with pytest.raises(ValueError, match="missing_gene_threshold"):
        score_batch(
            expression_matrix={"obs-1": {"CA9": 5.0}},
            detected_gene_ids_by_observation={"obs-1": ("CA9",)},
            signatures=(GeneSignature(name="HALLMARK_HYPOXIA", up_genes=("CA9",)),),
            scoring_contract_id="singscore_r_v1",
            target_definition_id="breast_visium_hallmarks_v1",
            missing_gene_threshold=1.1,
        )


def test_score_batch_rejects_incomplete_r_output_pairs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        SINGSCORE_MODULE,
        "run_r_script",
        lambda paths, repo_root: subprocess.CompletedProcess(
            args=["Rscript"], returncode=0, stdout="", stderr=""
        ),
    )
    monkeypatch.setattr(
        SINGSCORE_MODULE,
        "load_runtime_metadata",
        lambda path: {"r_version": "4.5.2", "singscore_version": "1.30.0"},
    )
    monkeypatch.setattr(
        SINGSCORE_MODULE,
        "load_score_output",
        lambda path: pa.table(
            {
                "observation_id": ["obs-1"],
                "program_name": ["HALLMARK_HYPOXIA"],
                "raw_rank_evidence": [0.25],
            }
        ),
    )

    with pytest.raises(InvalidScorerOutputError, match="missing expected score rows"):
        score_batch(
            expression_matrix={
                "obs-1": {"CA9": 5.0},
                "obs-2": {"VEGFA": 4.0},
            },
            detected_gene_ids_by_observation={
                "obs-1": ("CA9",),
                "obs-2": ("VEGFA",),
            },
            signatures=(GeneSignature(name="HALLMARK_HYPOXIA", up_genes=("CA9",)),),
            scoring_contract_id="singscore_r_v1",
            target_definition_id="breast_visium_hallmarks_v1",
        )


def test_score_one_rejects_non_singleton_batch_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_score_batch(**kwargs: object) -> ScoreArtifact:
        packet = ScorePacket(
            observation_id="obs-1",
            sample_id=None,
            slide_id=None,
            program_name="HALLMARK_HYPOXIA",
            status=ScoreStatus.OK,
            raw_rank_evidence=0.25,
            signature_size_declared=1,
            signature_size_matched=1,
            signature_coverage=1.0,
            dropped_by_missingness_rule=False,
            failure_code=None,
            null_calibrated_score=None,
            dropout_penalty=None,
            spatial_consistency=None,
        )
        return _artifact_with_single_packet(packet).model_copy(
            update={"packets": (packet, packet)}
        )

    monkeypatch.setattr(SINGSCORE_MODULE, "score_batch", fake_score_batch)

    with pytest.raises(ValueError, match="exactly one packet"):
        score_one(
            observation_id="obs-1",
            expression_by_gene={"CA9": 5.0},
            detected_gene_ids=("CA9",),
            signature=GeneSignature(name="HALLMARK_HYPOXIA", up_genes=("CA9",)),
            scoring_contract_id="singscore_r_v1",
            target_definition_id="breast_visium_hallmarks_v1",
        )


def test_hash_file_reads_in_chunks(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    payload = b"spatial-ci" * 2048
    path = tmp_path / "payload.bin"
    path.write_bytes(payload)

    def fail_read_bytes(self: Path) -> bytes:
        raise AssertionError("read_bytes() should not be used for hashing.")

    monkeypatch.setattr(Path, "read_bytes", fail_read_bytes)

    assert SINGSCORE_MODULE._hash_file(path) == hashlib.sha256(payload).hexdigest()


def test_write_detected_membership_input_uses_arrow_arrays(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    captured: dict[str, object] = {}
    real_from_arrays = pa.Table.from_arrays

    def fail_from_pylist(*args: object, **kwargs: object) -> pa.Table:
        raise AssertionError("from_pylist() should not be used.")

    def capture_from_arrays(
        arrays: list[pa.Array], *, names: list[str]
    ) -> pa.Table:
        captured["names"] = names
        captured["arrays"] = [array.to_pylist() for array in arrays]
        return real_from_arrays(arrays, names=names)

    class FakeTable:
        from_pylist = staticmethod(fail_from_pylist)
        from_arrays = staticmethod(capture_from_arrays)

    monkeypatch.setattr(SINGSCORE_MODULE.pa, "Table", FakeTable)

    output_path = tmp_path / "detected_membership.parquet"
    SINGSCORE_MODULE._write_detected_membership_input(
        output_path,
        {
            "obs-2": frozenset({"VEGFA", "CA9"}),
            "obs-1": frozenset({"CA9"}),
        },
    )

    assert captured["names"] == ["observation_id", "gene_id"]
    assert captured["arrays"] == [
        ["obs-1", "obs-2", "obs-2"],
        ["CA9", "CA9", "VEGFA"],
    ]
    assert pq.read_table(output_path).to_pylist() == [
        {"observation_id": "obs-1", "gene_id": "CA9"},
        {"observation_id": "obs-2", "gene_id": "CA9"},
        {"observation_id": "obs-2", "gene_id": "VEGFA"},
    ]


def test_validate_expression_matrix_only_checks_structure() -> None:
    class ExplosiveFloat:
        def __float__(self) -> float:
            raise AssertionError("value coercion should not happen in validation.")

    SINGSCORE_MODULE._validate_expression_matrix(
        {"obs-1": {"CA9": ExplosiveFloat()}}
    )
