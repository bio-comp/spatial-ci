import importlib.util
from pathlib import Path

import polars as pl
from click import Command
from click.testing import CliRunner


def _load_build_manifest_main() -> Command:
    module_path = Path("scripts/build_manifest.py").resolve()
    spec = importlib.util.spec_from_file_location("build_manifest_cli", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load scripts/build_manifest.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.main


def test_build_manifest_cli_writes_assignments_and_final_manifest(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "manifest.parquet"
    runner = CliRunner()
    main = _load_build_manifest_main()
    result = runner.invoke(
        main,
        [
            "--config",
            "tests/fixtures/manifest/pass2/config_materialize.yaml",
            "--output",
            str(output_path),
        ],
    )

    assignments_path = output_path.with_suffix(".assignments.parquet")
    assert result.exit_code == 0
    assert assignments_path.exists()
    assert output_path.exists()
    assert pl.read_parquet(output_path).height > 0


def test_build_manifest_cli_writes_rejections_and_fails_by_default(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "manifest.parquet"
    runner = CliRunner()
    main = _load_build_manifest_main()
    result = runner.invoke(
        main,
        [
            "--config",
            "tests/fixtures/manifest/pass2/config_materialize_missing.yaml",
            "--output",
            str(output_path),
        ],
    )

    assignments_path = output_path.with_suffix(".assignments.parquet")
    rejections_path = output_path.with_suffix(".rejections.parquet")
    assert result.exit_code != 0
    assert "rejection ledger" in result.output
    assert assignments_path.exists()
    assert rejections_path.exists()
    assert not output_path.exists()


def test_build_manifest_cli_allows_missing_with_warning(tmp_path: Path) -> None:
    output_path = tmp_path / "manifest.parquet"
    runner = CliRunner()
    main = _load_build_manifest_main()
    result = runner.invoke(
        main,
        [
            "--config",
            "tests/fixtures/manifest/pass2/config_materialize_missing.yaml",
            "--output",
            str(output_path),
            "--allow-missing",
        ],
    )

    rejections_path = output_path.with_suffix(".rejections.parquet")
    assert result.exit_code == 0
    assert "warning" in result.output.lower()
    assert output_path.exists()
    assert rejections_path.exists()
