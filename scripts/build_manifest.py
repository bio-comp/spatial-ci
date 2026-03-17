#!/usr/bin/env python3
# mypy: disable-error-code=untyped-decorator

from pathlib import Path

import click

from spatial_ci.manifest.pipeline import (
    ManifestPipelineError,
    build_materialized_manifest,
)

# build_manifest.py
# Implements the two-pass manifest builder for Spatial-CI.
# Centers on logical assignments followed by physical materialization.


@click.command()
@click.option(
    "--config", type=Path, required=True, help="Path to manifest build config"
)
@click.option(
    "--output",
    type=Path,
    required=True,
    help="Path to output materialized manifest (Parquet)",
)
@click.option(
    "--allow-missing",
    is_flag=True,
    default=False,
    help="Allow missing artifacts but emit rejections",
)
def main(config: Path, output: Path, allow_missing: bool) -> None:
    """Spatial-CI Two-Pass Manifest Builder."""

    click.secho("Starting manifest build...", fg="cyan")
    try:
        artifact = build_materialized_manifest(
            config_path=config,
            output_path=output,
            allow_missing=allow_missing,
        )
    except ManifestPipelineError as exc:
        raise click.ClickException(str(exc)) from exc
    if artifact.rejection_ledger_path is not None:
        click.secho(
            (
                "Warning: wrote rejection ledger to "
                f"{artifact.rejection_ledger_path}"
            ),
            fg="yellow",
        )
    click.secho(
        f"Final manifest written successfully to: {artifact.output_path}",
        fg="green",
    )


if __name__ == "__main__":
    main()
