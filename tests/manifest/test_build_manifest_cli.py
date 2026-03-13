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


def test_build_manifest_cli_writes_split_assignment_artifact(tmp_path: Path) -> None:
    output_path = tmp_path / "assignments.parquet"
    runner = CliRunner()
    main = _load_build_manifest_main()
    result = runner.invoke(
        main,
        [
            "--config",
            "tests/fixtures/manifest/pass1/config_basic.yaml",
            "--output",
            str(output_path),
        ],
    )
    assert result.exit_code == 0
    assert output_path.exists()
    assert pl.read_parquet(output_path).height > 0
