import polars as pl

PASS1_CANONICAL_COLUMNS = [
    "sample_id",
    "patient_id",
    "specimen_id",
    "slide_id",
    "cohort_id",
]


def normalize_manifest_source(
    frame: pl.DataFrame,
    *,
    field_map: dict[str, str],
    cohort_id: str | None,
) -> pl.DataFrame:
    """Map source aliases into pass-1 canonical manifest fields."""

    rename_map = {
        source_name: canonical_name
        for source_name, canonical_name in field_map.items()
        if source_name in frame.columns
    }
    normalized = frame.rename(rename_map)

    if cohort_id is not None:
        normalized = normalized.with_columns(pl.lit(cohort_id).alias("cohort_id"))

    required_columns = {"sample_id", "cohort_id"}
    missing_columns = sorted(required_columns - set(normalized.columns))
    if missing_columns:
        missing_display = ", ".join(missing_columns)
        raise ValueError(f"Missing required canonical fields: {missing_display}")

    ordered_columns = [
        column_name
        for column_name in PASS1_CANONICAL_COLUMNS
        if column_name in normalized.columns
    ]
    return normalized.select(ordered_columns)
