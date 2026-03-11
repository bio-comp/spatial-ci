"""File-based bridge between Python policy code and the R scorer."""

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq


@dataclass(frozen=True)
class BridgePaths:
    """Explicit bridge file contract for the R scorer."""

    expression_input: Path
    signature_input: Path
    scoring_request: Path
    detected_membership: Path
    score_output: Path
    runtime_metadata: Path


class RSubprocessError(RuntimeError):
    """Raised when the R scorer process exits unsuccessfully."""


class InvalidScorerOutputError(RuntimeError):
    """Raised when the R scorer output artifact is malformed."""


def build_bridge_paths(workdir: Path) -> BridgePaths:
    """Build the deterministic bridge file layout inside a workdir."""

    return BridgePaths(
        expression_input=workdir / "expression_input.csv",
        signature_input=workdir / "signature_input.json",
        scoring_request=workdir / "scoring_request.json",
        detected_membership=workdir / "detected_membership.parquet",
        score_output=workdir / "score_output.parquet",
        runtime_metadata=workdir / "runtime_metadata.json",
    )


def run_r_script(
    paths: BridgePaths, *, repo_root: Path
) -> subprocess.CompletedProcess[str]:
    """Invoke the canonical R scorer with the explicit bridge inputs."""

    completed = subprocess.run(
        [
            "Rscript",
            "scripts/score_targets.R",
            str(paths.expression_input),
            str(paths.signature_input),
            str(paths.scoring_request),
            str(paths.detected_membership),
            str(paths.score_output),
            str(paths.runtime_metadata),
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )

    if completed.returncode != 0:
        raise RSubprocessError(completed.stderr.strip() or "R scorer failed.")

    return completed


def load_score_output(score_output: Path) -> pa.Table:
    """Load and validate the R scorer output artifact."""

    table = pq.read_table(score_output)
    required_columns = {
        "observation_id",
        "program_name",
        "raw_rank_evidence",
    }
    missing_columns = sorted(required_columns - set(table.schema.names))
    if missing_columns:
        missing_summary = ", ".join(missing_columns)
        raise InvalidScorerOutputError(
            f"Score output is missing required columns: {missing_summary}."
        )

    return table


def load_runtime_metadata(runtime_metadata: Path) -> dict[str, str]:
    """Load and validate the runtime metadata emitted by the R scorer."""

    payload = json.loads(runtime_metadata.read_text(encoding="utf-8"))
    required_fields = {"r_version", "singscore_version"}
    missing_fields = sorted(required_fields - set(payload))
    if missing_fields:
        missing_summary = ", ".join(missing_fields)
        raise InvalidScorerOutputError(
            f"Runtime metadata is missing required fields: {missing_summary}."
        )

    r_version = payload["r_version"]
    singscore_version = payload["singscore_version"]
    if not isinstance(r_version, str) or not r_version:
        raise InvalidScorerOutputError(
            "Runtime metadata r_version must be a non-empty string."
        )
    if not isinstance(singscore_version, str) or not singscore_version:
        raise InvalidScorerOutputError(
            "Runtime metadata singscore_version must be a non-empty string."
        )

    return {
        "r_version": r_version,
        "singscore_version": singscore_version,
    }


__all__ = [
    "BridgePaths",
    "InvalidScorerOutputError",
    "RSubprocessError",
    "build_bridge_paths",
    "load_runtime_metadata",
    "load_score_output",
    "run_r_script",
]
