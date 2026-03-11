import shutil
from pathlib import Path

from spatial_ci.scoring.r_bridge import (
    build_bridge_paths,
    load_runtime_metadata,
    load_score_output,
    run_r_script,
)

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "singscore"


def test_r_bridge_emits_long_form_parquet_fixture(tmp_path: Path) -> None:
    paths = build_bridge_paths(tmp_path)
    shutil.copyfile(FIXTURE_DIR / "expression_input.csv", paths.expression_input)
    shutil.copyfile(FIXTURE_DIR / "signature_input.json", paths.signature_input)
    shutil.copyfile(FIXTURE_DIR / "scoring_request.json", paths.scoring_request)
    shutil.copyfile(
        FIXTURE_DIR / "detected_membership.parquet", paths.detected_membership
    )

    run_r_script(paths, repo_root=Path(__file__).resolve().parents[2])
    table = load_score_output(paths.score_output)
    runtime_metadata = load_runtime_metadata(paths.runtime_metadata)
    rows = sorted(table.to_pylist(), key=lambda row: row["observation_id"])

    assert table.column_names == [
        "observation_id",
        "program_name",
        "raw_rank_evidence",
    ]
    assert runtime_metadata == {"r_version": "4.5.2", "singscore_version": "1.30.0"}
    assert rows == [
        {
            "observation_id": "obs-1",
            "program_name": "HALLMARK_HYPOXIA",
            "raw_rank_evidence": 1.0,
        },
        {
            "observation_id": "obs-2",
            "program_name": "HALLMARK_HYPOXIA",
            "raw_rank_evidence": 0.0,
        },
    ]
