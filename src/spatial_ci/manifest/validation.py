from collections.abc import Mapping
from pathlib import Path

from spatial_ci.manifest.resolver import ResolvedSampleArtifacts

REQUIRED_ROW_FIELDS = (
    "sample_id",
    "cohort_id",
    "split",
    "resolved_patient_id",
    "patient_id_source",
)


class PreHashValidationError(RuntimeError):
    """Raised when a resolved pass-2 row fails lightweight validation."""


def _normalize_string(value: object) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    if normalized == "":
        return None
    return normalized


def _validate_required_row_fields(row: Mapping[str, object]) -> None:
    for field_name in REQUIRED_ROW_FIELDS:
        if _normalize_string(row.get(field_name)) is None:
            raise PreHashValidationError(
                f"missing required field before hashing: {field_name}"
            )


def _validate_path_exists(path: Path, *, label: str) -> None:
    if not path.exists():
        raise PreHashValidationError(f"{label} does not exist: {path}")


def validate_pre_hash_sample(
    row: Mapping[str, object],
    *,
    resolved_artifacts: ResolvedSampleArtifacts,
) -> None:
    """Validate one resolved sample before expensive hashing begins."""

    _validate_required_row_fields(row)
    _validate_path_exists(resolved_artifacts.sample_root, label="sample root")

    required_paths = {
        "image": resolved_artifacts.image.path,
        "spatial_coords": resolved_artifacts.spatial_coords.path,
        "scalefactors": resolved_artifacts.scalefactors.path,
        "raw_expression": resolved_artifacts.raw_expression.path,
    }
    for label, path in required_paths.items():
        _validate_path_exists(path, label=label)

    unique_required_paths = {path.resolve() for path in required_paths.values()}
    if len(unique_required_paths) != len(required_paths):
        raise PreHashValidationError(
            "required artifact paths must remain distinct before hashing"
        )

    derived_expression = resolved_artifacts.derived_expression
    if derived_expression is not None:
        _validate_path_exists(derived_expression.path, label="derived_expression")
        if (
            derived_expression.path.resolve()
            == resolved_artifacts.raw_expression.path.resolve()
        ):
            raise PreHashValidationError(
                "raw and derived expression artifacts must remain distinct"
            )
