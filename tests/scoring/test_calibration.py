import pytest

from spatial_ci.scoring import (
    CalibrationStatus,
    ReferencePopulation,
    ReferencePopulationKind,
    RobustCalibrationResult,
    robust_calibrate_scores,
)


def test_robust_calibration_uses_median_and_mad_for_heavy_tails() -> None:
    raw_scores = {
        "spot_1": 0.10,
        "spot_2": 0.11,
        "spot_3": 0.09,
        "spot_4": 0.12,
        "spot_5": 0.50,
    }
    reference_population = ReferencePopulation(
        label="discovery_train",
        kind=ReferencePopulationKind.TRAINING,
        sample_ids=("spot_1", "spot_2", "spot_3", "spot_4", "spot_5"),
    )

    calibrated = robust_calibrate_scores(
        raw_scores,
        reference_population=reference_population,
    )

    assert calibrated["spot_5"].status is CalibrationStatus.OK
    assert calibrated["spot_5"].reference_median == pytest.approx(0.11)
    assert calibrated["spot_5"].reference_mad == pytest.approx(0.01)
    assert calibrated["spot_5"].robust_z_score == pytest.approx(
        (0.50 - 0.11) / (1.4826 * 0.01)
    )


def test_robust_calibration_flags_extreme_outliers_without_moving_center() -> None:
    raw_scores = {
        "spot_1": 0.10,
        "spot_2": 0.11,
        "spot_3": 0.12,
        "spot_4": 0.13,
        "spot_5": 1.50,
    }
    reference_population = ReferencePopulation(
        label="holdout_controls",
        kind=ReferencePopulationKind.CONTROL,
        sample_ids=("spot_1", "spot_2", "spot_3", "spot_4"),
    )

    calibrated = robust_calibrate_scores(
        raw_scores,
        reference_population=reference_population,
    )

    assert calibrated["spot_5"].reference_median == pytest.approx(0.115)
    assert calibrated["spot_5"].reference_mad == pytest.approx(0.01)
    assert calibrated["spot_5"].robust_z_score is not None
    assert calibrated["spot_5"].robust_z_score > 90.0


def test_robust_calibration_reports_degenerate_reference_distribution_for_zero_mad(
) -> None:
    raw_scores = {
        "spot_1": 0.42,
        "spot_2": 0.42,
        "spot_3": 0.42,
        "spot_4": 0.50,
    }
    reference_population = ReferencePopulation(
        label="flat_reference",
        kind=ReferencePopulationKind.COHORT,
        sample_ids=("spot_1", "spot_2", "spot_3"),
    )

    calibrated = robust_calibrate_scores(
        raw_scores,
        reference_population=reference_population,
    )

    assert (
        calibrated["spot_4"].status
        is CalibrationStatus.DEGENERATE_REFERENCE_DISTRIBUTION
    )
    assert calibrated["spot_4"].reference_median == pytest.approx(0.42)
    assert calibrated["spot_4"].reference_mad == pytest.approx(0.0)
    assert calibrated["spot_4"].robust_z_score is None


def test_robust_calibration_reports_tiny_reference_population() -> None:
    raw_scores = {
        "spot_1": 0.10,
        "spot_2": 0.11,
        "spot_3": 0.12,
    }
    reference_population = ReferencePopulation(
        label="tiny_reference",
        kind=ReferencePopulationKind.CUSTOM,
        sample_ids=("spot_1", "spot_2"),
    )

    calibrated = robust_calibrate_scores(
        raw_scores,
        reference_population=reference_population,
    )

    assert calibrated["spot_3"].status is CalibrationStatus.REFERENCE_TOO_SMALL
    assert calibrated["spot_3"].reference_size == 2
    assert calibrated["spot_3"].robust_z_score is None


def test_robust_calibration_requires_reference_ids_to_exist() -> None:
    raw_scores = {
        "spot_1": 0.10,
        "spot_2": 0.11,
        "spot_3": 0.12,
    }
    reference_population = ReferencePopulation(
        label="missing_reference",
        kind=ReferencePopulationKind.TRAINING,
        sample_ids=("spot_1", "spot_4"),
    )

    calibrated = robust_calibrate_scores(
        raw_scores,
        reference_population=reference_population,
    )

    assert calibrated["spot_2"].status is CalibrationStatus.MISSING_DATA
    assert calibrated["spot_2"].missing_reference_ids == ("spot_4",)
    assert calibrated["spot_2"].robust_z_score is None


def test_robust_calibration_result_rejects_ok_status_with_missing_values() -> None:
    with pytest.raises(ValueError, match="status ok"):
        RobustCalibrationResult(
            raw_score=0.1,
            reference_label="train",
            reference_kind=ReferencePopulationKind.TRAINING,
            reference_size=3,
            reference_median=None,
            reference_mad=0.01,
            scaled_reference_mad=0.014826,
            robust_z_score=1.0,
            status=CalibrationStatus.OK,
        )


def test_robust_calibration_result_rejects_non_ok_status_with_robust_z_score(
) -> None:
    with pytest.raises(ValueError, match="robust_z_score"):
        RobustCalibrationResult(
            raw_score=0.1,
            reference_label="train",
            reference_kind=ReferencePopulationKind.TRAINING,
            reference_size=3,
            reference_median=0.1,
            reference_mad=0.0,
            scaled_reference_mad=0.0,
            robust_z_score=1.0,
            status=CalibrationStatus.DEGENERATE_REFERENCE_DISTRIBUTION,
        )
