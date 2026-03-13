import polars as pl

from spatial_ci.manifest.leakage import build_leakage_report


def test_build_leakage_report_returns_empty_for_clean_assignments() -> None:
    frame = pl.DataFrame(
        {
            "sample_id": ["s1", "s2"],
            "cohort_id": ["cohort-a", "cohort-b"],
            "split": ["train", "val"],
            "resolved_patient_id": ["cohort-a::p1", "cohort-b::p2"],
            "patient_id_source": ["patient_id", "patient_id"],
            "resolved_specimen_id": ["cohort-a::spec1", "cohort-b::spec2"],
            "resolved_slide_id": ["cohort-a::slide1", "cohort-b::slide2"],
        }
    )
    report = build_leakage_report(frame, split_contract_id="split-v1")
    assert report.n_findings == 0
    assert report.rows == []


def test_build_leakage_report_detects_patient_overlap() -> None:
    frame = pl.DataFrame(
        {
            "sample_id": ["s1", "s2"],
            "cohort_id": ["cohort-a", "cohort-a"],
            "split": ["train", "val"],
            "resolved_patient_id": ["cohort-a::p1", "cohort-a::p1"],
            "patient_id_source": ["patient_id", "patient_id"],
            "resolved_specimen_id": [None, None],
            "resolved_slide_id": [None, None],
        }
    )
    report = build_leakage_report(frame, split_contract_id="split-v1")
    assert report.n_findings == 1
    assert report.rows[0].audit_column == "resolved_patient_id"
    assert report.rows[0].overlapping_id == "cohort-a::p1"


def test_build_leakage_report_detects_specimen_and_slide_overlap() -> None:
    frame = pl.DataFrame(
        {
            "sample_id": ["s1", "s2", "s3", "s4"],
            "cohort_id": ["cohort-a", "cohort-a", "cohort-a", "cohort-a"],
            "split": ["train", "val", "train", "test_external"],
            "resolved_patient_id": [
                "cohort-a::p1",
                "cohort-a::p2",
                "cohort-a::p3",
                "cohort-a::p4",
            ],
            "patient_id_source": ["patient_id"] * 4,
            "resolved_specimen_id": [
                "cohort-a::spec1",
                "cohort-a::spec1",
                None,
                None,
            ],
            "resolved_slide_id": [
                None,
                None,
                "cohort-a::slide1",
                "cohort-a::slide1",
            ],
        }
    )
    report = build_leakage_report(frame, split_contract_id="split-v1")
    findings = [(row.audit_column, row.overlapping_id) for row in report.rows]
    assert ("resolved_specimen_id", "cohort-a::spec1") in findings
    assert ("resolved_slide_id", "cohort-a::slide1") in findings


def test_build_leakage_report_ignores_null_optional_ids() -> None:
    frame = pl.DataFrame(
        {
            "sample_id": ["s1", "s2"],
            "cohort_id": ["cohort-a", "cohort-a"],
            "split": ["train", "test_external"],
            "resolved_patient_id": ["cohort-a::p1", "cohort-a::p2"],
            "patient_id_source": ["patient_id", "patient_id"],
            "resolved_specimen_id": [None, None],
            "resolved_slide_id": [None, None],
        }
    )
    report = build_leakage_report(frame, split_contract_id="split-v1")
    assert report.n_findings == 0


def test_build_leakage_report_respects_namespacing() -> None:
    frame = pl.DataFrame(
        {
            "sample_id": ["s1", "s2"],
            "cohort_id": ["cohort-a", "cohort-b"],
            "split": ["train", "test_external"],
            "resolved_patient_id": ["cohort-a::p1", "cohort-b::p2"],
            "patient_id_source": ["patient_id", "patient_id"],
            "resolved_specimen_id": ["cohort-a::slide-1", "cohort-b::slide-1"],
            "resolved_slide_id": [None, None],
        }
    )
    report = build_leakage_report(frame, split_contract_id="split-v1")
    assert report.n_findings == 0


def test_build_leakage_report_sorts_findings_deterministically() -> None:
    frame = pl.DataFrame(
        {
            "sample_id": ["s1", "s2", "s3", "s4"],
            "cohort_id": ["cohort-a"] * 4,
            "split": ["test_external", "train", "val", "train"],
            "resolved_patient_id": [
                "cohort-a::p2",
                "cohort-a::p2",
                "cohort-a::p1",
                "cohort-a::p3",
            ],
            "patient_id_source": ["patient_id"] * 4,
            "resolved_specimen_id": [
                "cohort-a::spec2",
                "cohort-a::spec2",
                None,
                None,
            ],
            "resolved_slide_id": [
                None,
                None,
                "cohort-a::slide1",
                "cohort-a::slide1",
            ],
        }
    )
    report = build_leakage_report(frame, split_contract_id="split-v1")
    rows = [
        (row.audit_column, row.split_left, row.split_right, row.overlapping_id)
        for row in report.rows
    ]
    assert rows == sorted(rows)
