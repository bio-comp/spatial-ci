import polars as pl

from spatial_ci.manifest.normalize import normalize_manifest_source


def test_normalize_manifest_source_maps_aliases_to_canonical_fields() -> None:
    frame = pl.DataFrame(
        {
            "sample": ["spot-1"],
            "patient": ["patient-1"],
            "slide": ["slide-1"],
        }
    )
    normalized = normalize_manifest_source(
        frame,
        field_map={
            "sample": "sample_id",
            "patient": "patient_id",
            "slide": "slide_id",
        },
        cohort_id="cohort-a",
    )
    assert normalized.columns == ["sample_id", "patient_id", "slide_id", "cohort_id"]
    assert normalized.item(0, "cohort_id") == "cohort-a"
