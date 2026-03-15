import polars as pl

from spatial_ci.manifest.splits import assign_patient_splits


def test_assign_patient_splits_is_deterministic() -> None:
    frame = pl.DataFrame(
        {
            "sample_id": ["s1", "s2"],
            "cohort_id": ["cohort-a", "cohort-a"],
            "resolved_patient_id": ["cohort-a::p1", "cohort-a::p2"],
        }
    )
    first = assign_patient_splits(
        frame,
        split_contract_id="split-v1",
        val_fraction=0.5,
        external_holdout_cohorts=[],
    )
    second = assign_patient_splits(
        frame,
        split_contract_id="split-v1",
        val_fraction=0.5,
        external_holdout_cohorts=[],
    )
    assert first.equals(second)


def test_assign_patient_splits_marks_external_cohorts_as_test_external() -> None:
    frame = pl.DataFrame(
        {
            "sample_id": ["s1"],
            "cohort_id": ["external-a"],
            "resolved_patient_id": ["external-a::p1"],
        }
    )
    assigned = assign_patient_splits(
        frame,
        split_contract_id="split-v1",
        val_fraction=0.2,
        external_holdout_cohorts=["external-a"],
    )
    assert assigned.item(0, "split") == "test_external"
