"""Artifact schemas for baseline prediction outputs."""

import json
from enum import Enum
from math import isfinite
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from pydantic import BaseModel, ConfigDict, Field, model_validator


class BaselineName(str, Enum):
    """Supported deployable baseline names."""

    GLOBAL_TRAIN_MEAN = "global_train_mean"
    MEAN_BY_TRAIN_COHORT = "mean_by_train_cohort"
    KNN_ON_EMBEDDINGS = "knn_on_embeddings"
    RIDGE_PROBE = "ridge_probe"


class BaselinePredictionRow(BaseModel):
    """One baseline prediction row at observation x program x baseline grain."""

    model_config = ConfigDict(frozen=True)

    observation_id: str = Field(min_length=1)
    sample_id: str = Field(min_length=1)
    cohort_id: str = Field(min_length=1)
    split: str = Field(min_length=1)
    program_name: str = Field(min_length=1)
    baseline_name: BaselineName
    predicted_score: float


class BaselinePredictionArtifact(BaseModel):
    """Artifact-level metadata plus prediction rows."""

    model_config = ConfigDict(frozen=True)

    run_id: str = Field(min_length=1)
    baseline_contract_id: str = Field(min_length=1)
    split_contract_id: str = Field(min_length=1)
    target_definition_id: str = Field(min_length=1)
    scoring_contract_id: str = Field(min_length=1)
    manifest_id: str | None = None
    source_score_artifact_path: str = Field(min_length=1)
    source_score_artifact_hash: str = Field(min_length=1)
    source_manifest_path: str = Field(min_length=1)
    source_manifest_hash: str = Field(min_length=1)
    ridge_probe_selected_alpha_by_program: dict[str, float] | None = None
    n_rows: int = Field(ge=0)
    rows: tuple[BaselinePredictionRow, ...]

    @model_validator(mode="after")
    def validate_row_count(self) -> "BaselinePredictionArtifact":
        if self.n_rows != len(self.rows):
            raise ValueError("n_rows must match len(rows)")
        ridge_programs = {
            row.program_name
            for row in self.rows
            if row.baseline_name is BaselineName.RIDGE_PROBE
        }
        if not ridge_programs:
            if self.ridge_probe_selected_alpha_by_program is not None:
                raise ValueError(
                    "ridge_probe_selected_alpha_by_program must be None when no "
                    "ridge_probe rows are present"
                )
            return self

        selected_alpha_by_program = self.ridge_probe_selected_alpha_by_program
        if selected_alpha_by_program is None:
            raise ValueError(
                "ridge_probe_selected_alpha_by_program is required when ridge_probe "
                "rows are present"
            )
        if set(selected_alpha_by_program) != ridge_programs:
            raise ValueError(
                "ridge_probe_selected_alpha_by_program must match the predicted "
                "ridge_probe program set"
            )
        invalid_programs = sorted(
            program_name
            for program_name, alpha in selected_alpha_by_program.items()
            if not isfinite(alpha) or alpha <= 0.0
        )
        if invalid_programs:
            invalid_display = ", ".join(invalid_programs)
            raise ValueError(
                "ridge_probe_selected_alpha_by_program must contain positive finite "
                f"alpha values; invalid programs: {invalid_display}"
            )
        return self


def write_baseline_prediction_artifact(
    artifact: BaselinePredictionArtifact, path: Path
) -> None:
    """Write a baseline prediction artifact to Parquet."""

    row_table = pa.Table.from_pylist(
        [row.model_dump(mode="json") for row in artifact.rows]
    )
    artifact_metadata = artifact.model_dump(mode="json")
    artifact_metadata.pop("rows")
    schema_metadata = {
        **(row_table.schema.metadata or {}),
        b"spatial_ci_baseline_prediction_artifact": json.dumps(
            artifact_metadata, sort_keys=True
        ).encode("utf-8"),
    }
    pq.write_table(row_table.replace_schema_metadata(schema_metadata), path)


def read_baseline_prediction_artifact(path: Path) -> BaselinePredictionArtifact:
    """Read a baseline prediction artifact from Parquet."""

    table = pq.read_table(path)
    schema_metadata = table.schema.metadata or {}
    encoded_metadata = schema_metadata.get(
        b"spatial_ci_baseline_prediction_artifact"
    )
    if encoded_metadata is None:
        raise ValueError(
            "Parquet artifact is missing spatial_ci_baseline_prediction_artifact "
            "metadata."
        )

    artifact_metadata = json.loads(encoded_metadata.decode("utf-8"))
    rows = tuple(BaselinePredictionRow.model_validate(row) for row in table.to_pylist())
    return BaselinePredictionArtifact.model_validate(
        {**artifact_metadata, "rows": rows}
    )


__all__ = [
    "BaselineName",
    "BaselinePredictionArtifact",
    "BaselinePredictionRow",
    "read_baseline_prediction_artifact",
    "write_baseline_prediction_artifact",
]
