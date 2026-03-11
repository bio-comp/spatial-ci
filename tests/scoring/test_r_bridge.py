import json
import subprocess
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from spatial_ci.scoring.r_bridge import (
    BridgePaths,
    InvalidScorerOutputError,
    RSubprocessError,
    build_bridge_paths,
    load_runtime_metadata,
    load_score_output,
    run_r_script,
)


def test_bridge_paths_are_explicit_and_stable(tmp_path: Path) -> None:
    paths = build_bridge_paths(tmp_path)

    assert paths == BridgePaths(
        expression_input=tmp_path / "expression_input.csv",
        signature_input=tmp_path / "signature_input.json",
        scoring_request=tmp_path / "scoring_request.json",
        detected_membership=tmp_path / "detected_membership.parquet",
        score_output=tmp_path / "score_output.parquet",
        runtime_metadata=tmp_path / "runtime_metadata.json",
    )


def test_nonzero_r_exit_maps_to_subprocess_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=["Rscript"],
            returncode=2,
            stdout="",
            stderr="scorer blew up",
        )

    monkeypatch.setattr("spatial_ci.scoring.r_bridge.subprocess.run", fake_run)

    with pytest.raises(RSubprocessError, match="scorer blew up"):
        run_r_script(build_bridge_paths(tmp_path), repo_root=tmp_path)


def test_missing_required_output_column_maps_to_invalid_output(tmp_path: Path) -> None:
    output_path = tmp_path / "score_output.parquet"
    pq.write_table(
        pa.table(
            {
                "observation_id": ["obs-1"],
                "program_name": ["HALLMARK_HYPOXIA"],
            }
        ),
        output_path,
    )

    with pytest.raises(InvalidScorerOutputError, match="raw_rank_evidence"):
        load_score_output(output_path)


def test_runtime_metadata_requires_versions(tmp_path: Path) -> None:
    metadata_path = tmp_path / "runtime_metadata.json"
    metadata_path.write_text(json.dumps({"r_version": "4.5.2"}), encoding="utf-8")

    with pytest.raises(InvalidScorerOutputError, match="singscore_version"):
        load_runtime_metadata(metadata_path)


@pytest.mark.parametrize(  # type: ignore[untyped-decorator]
    ("missing_field", "expected_message"),
    [
        ("expression_input", "expression_input.csv"),
        ("signature_input", "signature_input.json"),
        ("scoring_request", "scoring_request.json"),
        ("detected_membership", "detected_membership.parquet"),
    ],
)
def test_missing_bridge_input_maps_to_clear_r_error(
    tmp_path: Path, missing_field: str, expected_message: str
) -> None:
    paths = build_bridge_paths(tmp_path)
    paths.expression_input.write_text(
        "gene,obs-1\nCA9,1\n",
        encoding="utf-8",
    )
    paths.signature_input.write_text(
        json.dumps({"HALLMARK_HYPOXIA": {"up_genes": ["CA9"]}}),
        encoding="utf-8",
    )
    paths.scoring_request.write_text(
        json.dumps(
            {
                "bridge_contract_version": "v1",
                "debug_mode": False,
                "scoring_contract_id": "singscore_r_v1",
                "target_definition_id": "breast_visium_hallmarks_v1",
            }
        ),
        encoding="utf-8",
    )
    pq.write_table(
        pa.table(
            {
                "observation_id": ["obs-1"],
                "gene_id": ["CA9"],
            }
        ),
        paths.detected_membership,
    )

    getattr(paths, missing_field).unlink()

    with pytest.raises(RSubprocessError, match=expected_message):
        run_r_script(paths, repo_root=Path(__file__).resolve().parents[2])
