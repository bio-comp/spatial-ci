import pytest

from spatial_ci.scoring import (
    CalibrationStatus,
    ReferencePopulation,
    ReferencePopulationKind,
    robust_calibrate_scores,
)


def test_golden_heavy_tailed_reference_distribution() -> None:
    calibrated = robust_calibrate_scores(
        {
            "spot_1": 0.10,
            "spot_2": 0.11,
            "spot_3": 0.09,
            "spot_4": 0.12,
            "spot_5": 0.50,
        },
        reference_population=ReferencePopulation(
            label="golden_heavy_tail",
            kind=ReferencePopulationKind.COHORT,
            sample_ids=("spot_1", "spot_2", "spot_3", "spot_4", "spot_5"),
        ),
    )

    assert calibrated["spot_5"].status is CalibrationStatus.OK
    assert calibrated["spot_5"].reference_median == pytest.approx(0.11)
    assert calibrated["spot_5"].reference_mad == pytest.approx(0.01)
    assert calibrated["spot_5"].scaled_reference_mad == pytest.approx(0.014826)
    assert calibrated["spot_5"].robust_z_score == pytest.approx(26.305139619587226)


def test_golden_extreme_outlier_against_control_reference() -> None:
    calibrated = robust_calibrate_scores(
        {
            "spot_1": 0.10,
            "spot_2": 0.11,
            "spot_3": 0.12,
            "spot_4": 0.13,
            "spot_5": 1.50,
        },
        reference_population=ReferencePopulation(
            label="golden_controls",
            kind=ReferencePopulationKind.CONTROL,
            sample_ids=("spot_1", "spot_2", "spot_3", "spot_4"),
        ),
    )

    assert calibrated["spot_5"].status is CalibrationStatus.OK
    assert calibrated["spot_5"].reference_median == pytest.approx(0.115)
    assert calibrated["spot_5"].reference_mad == pytest.approx(0.01)
    assert calibrated["spot_5"].robust_z_score == pytest.approx(93.41697018750848)


def test_golden_zero_mad_reference_distribution() -> None:
    calibrated = robust_calibrate_scores(
        {
            "spot_1": 0.42,
            "spot_2": 0.42,
            "spot_3": 0.42,
            "spot_4": 0.50,
        },
        reference_population=ReferencePopulation(
            label="golden_flat",
            kind=ReferencePopulationKind.COHORT,
            sample_ids=("spot_1", "spot_2", "spot_3"),
        ),
    )

    assert (
        calibrated["spot_4"].status
        is CalibrationStatus.DEGENERATE_REFERENCE_DISTRIBUTION
    )
    assert calibrated["spot_4"].reference_median == pytest.approx(0.42)
    assert calibrated["spot_4"].reference_mad == pytest.approx(0.0)
    assert calibrated["spot_4"].robust_z_score is None


def test_golden_tiny_reference_population() -> None:
    calibrated = robust_calibrate_scores(
        {
            "spot_1": 0.10,
            "spot_2": 0.11,
            "spot_3": 0.12,
        },
        reference_population=ReferencePopulation(
            label="golden_tiny",
            kind=ReferencePopulationKind.CUSTOM,
            sample_ids=("spot_1", "spot_2"),
        ),
    )

    assert calibrated["spot_3"].status is CalibrationStatus.REFERENCE_TOO_SMALL
    assert calibrated["spot_3"].reference_size == 2
    assert calibrated["spot_3"].robust_z_score is None
