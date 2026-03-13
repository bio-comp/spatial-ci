import polars as pl

PATIENT_FALLBACK_ORDER = [
    "patient_id",
    "specimen_id",
    "slide_id",
    "sample_id",
]


def _normalize_string(value: object) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    if normalized == "":
        return None
    return normalized


def _namespace_identity(cohort_id: str, raw_id: str | None) -> str | None:
    if raw_id is None:
        return None
    return f"{cohort_id}::{raw_id}"


def derive_resolved_identity(frame: pl.DataFrame) -> pl.DataFrame:
    """Add resolved pass-1 identity fields and patient-source provenance."""

    rows: list[dict[str, object]] = []
    for row in frame.to_dicts():
        cohort_id = _normalize_string(row.get("cohort_id"))
        sample_id = _normalize_string(row.get("sample_id"))
        if cohort_id is None or sample_id is None:
            raise ValueError(
                "sample_id and cohort_id are required for identity resolution"
            )

        patient_source = "sample_id"
        patient_value = sample_id
        for source_name in PATIENT_FALLBACK_ORDER:
            candidate = _normalize_string(row.get(source_name))
            if candidate is not None:
                patient_source = source_name
                patient_value = candidate
                break

        specimen_id = _normalize_string(row.get("specimen_id"))
        slide_id = _normalize_string(row.get("slide_id"))

        rows.append(
            {
                **row,
                "resolved_patient_id": _namespace_identity(cohort_id, patient_value),
                "patient_id_source": patient_source,
                "resolved_specimen_id": _namespace_identity(cohort_id, specimen_id),
                "resolved_slide_id": _namespace_identity(cohort_id, slide_id),
            }
        )

    return pl.DataFrame(rows)
