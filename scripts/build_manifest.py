#!/usr/bin/env python3
# mypy: disable-error-code=untyped-decorator

from pathlib import Path

import click

from spatial_ci.manifest.pipeline import build_split_assignments

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

    if allow_missing:
        raise click.ClickException(
            "--allow-missing is not implemented in the pass-1 split-foundation slice."
        )

    click.secho("Starting Pass 1: Logical Assignments...", fg="cyan")
    artifact = build_split_assignments(
        config_path=config,
        output_path=output,
    )
    click.secho(
        (
            "Split assignments written successfully to: "
            f"{artifact.output_path}"
        ),
        fg="green",
    )


if __name__ == "__main__":
    main()
