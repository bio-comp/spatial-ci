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
    load_score_output,
    run_r_script,
)


def test_bridge_paths_are_explicit_and_stable(tmp_path: Path) -> None:
    paths = build_bridge_paths(tmp_path)

    assert paths == BridgePaths(
        expression_input=tmp_path / "expression_input.csv",
        signature_input=tmp_path / "signature_input.json",
        scoring_request=tmp_path / "scoring_request.json",
        score_output=tmp_path / "score_output.parquet",
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
