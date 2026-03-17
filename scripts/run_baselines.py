#!/usr/bin/env python3
# mypy: disable-error-code=untyped-decorator

from pathlib import Path

import click

from spatial_ci.baselines.runner import run_mean_baselines


@click.command()
@click.option("--scores", type=Path, required=True, help="Path to score artifact")
@click.option("--manifest", type=Path, required=True, help="Path to manifest parquet")
@click.option(
    "--output",
    type=Path,
    required=True,
    help="Path to output baseline prediction artifact",
)
@click.option("--run-id", type=str, required=True, help="Baseline run identifier")
@click.option(
    "--baseline-contract-id",
    type=str,
    required=True,
    help="Versioned baseline contract identifier",
)
@click.option(
    "--split-contract-id",
    type=str,
    required=True,
    help="Versioned split contract identifier",
)
@click.option(
    "--manifest-id",
    type=str,
    required=False,
    help="Optional manifest identifier for artifact provenance",
)
def main(
    scores: Path,
    manifest: Path,
    output: Path,
    run_id: str,
    baseline_contract_id: str,
    split_contract_id: str,
    manifest_id: str | None,
) -> None:
    """Run the mean-baseline foundation against frozen score and manifest inputs."""

    artifact = run_mean_baselines(
        score_artifact_path=scores,
        manifest_path=manifest,
        output_path=output,
        run_id=run_id,
        baseline_contract_id=baseline_contract_id,
        split_contract_id=split_contract_id,
        manifest_id=manifest_id,
    )
    click.secho(
        (
            "Baseline predictions written successfully using manifest: "
            f"{artifact.source_manifest_path}"
        ),
        fg="green",
    )
    click.secho(
        f"Output artifact: {artifact.n_rows} rows at {output}",
        fg="green",
    )


if __name__ == "__main__":
    main()
