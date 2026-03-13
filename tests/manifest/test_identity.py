import polars as pl

from spatial_ci.manifest.identity import derive_resolved_identity


def test_derive_resolved_identity_namespaces_slide_and_specimen_ids() -> None:
    frame = pl.DataFrame(
        {
            "sample_id": ["spot-1"],
            "cohort_id": ["cohort-a"],
            "patient_id": ["patient-1"],
            "specimen_id": ["specimen-1"],
            "slide_id": ["slide-1"],
        }
    )
    resolved = derive_resolved_identity(frame)
    assert resolved.item(0, "resolved_patient_id") == "cohort-a::patient-1"
    assert resolved.item(0, "resolved_specimen_id") == "cohort-a::specimen-1"
    assert resolved.item(0, "resolved_slide_id") == "cohort-a::slide-1"
    assert resolved.item(0, "patient_id_source") == "patient_id"


def test_derive_resolved_identity_falls_back_to_sample_id_when_patient_missing(
) -> None:
    frame = pl.DataFrame({"sample_id": ["spot-1"], "cohort_id": ["cohort-a"]})
    resolved = derive_resolved_identity(frame)
    assert resolved.item(0, "resolved_patient_id") == "cohort-a::spot-1"
    assert resolved.item(0, "patient_id_source") == "sample_id"
