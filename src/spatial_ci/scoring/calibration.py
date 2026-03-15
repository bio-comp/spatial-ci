"""Robust calibration helpers layered on top of raw signature scores."""

import math
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from statistics import median

MAD_SCALE_FACTOR = 1.4826


class ReferencePopulationKind(str, Enum):
    """Typed reference-population categories for robust calibration."""

    TRAINING = "training"
    CONTROL = "control"
    COHORT = "cohort"
    CUSTOM = "custom"


class CalibrationStatus(str, Enum):
    """Outcome state for robust score calibration."""

    OK = "ok"
    MISSING_DATA = "missing_data"
    REFERENCE_TOO_SMALL = "reference_too_small"
    DEGENERATE_REFERENCE_DISTRIBUTION = "degenerate_reference_distribution"


@dataclass(frozen=True)
class ReferencePopulation:
    """Explicit, typed reference set for cohort-aware calibration."""

    label: str
    kind: ReferencePopulationKind
    sample_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.label.strip():
            raise ValueError("label must be non-empty.")
        if not self.sample_ids:
            raise ValueError("sample_ids must contain at least one sample.")
        if len(set(self.sample_ids)) != len(self.sample_ids):
            raise ValueError("sample_ids must not contain duplicates.")


@dataclass(frozen=True)
class RobustCalibrationResult:
    """Calibrated view of one raw score against a typed reference set."""

    raw_score: float | None
    reference_label: str
    reference_kind: ReferencePopulationKind
    reference_size: int
    reference_median: float | None
    reference_mad: float | None
    scaled_reference_mad: float | None
    robust_z_score: float | None
    status: CalibrationStatus
    missing_reference_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.reference_size < 1:
            raise ValueError("reference_size must be at least 1.")

        if self.status is CalibrationStatus.OK:
            required_fields = {
                "raw_score": self.raw_score,
                "reference_median": self.reference_median,
                "reference_mad": self.reference_mad,
                "scaled_reference_mad": self.scaled_reference_mad,
                "robust_z_score": self.robust_z_score,
            }
            missing_fields = sorted(
                field_name
                for field_name, value in required_fields.items()
                if value is None
            )
            if missing_fields:
                missing_display = ", ".join(missing_fields)
                raise ValueError(
                    "status ok requires non-None values for: "
                    f"{missing_display}."
                )
            if self.missing_reference_ids:
                raise ValueError(
                    "status ok must not carry missing_reference_ids."
                )

        if self.status is CalibrationStatus.DEGENERATE_REFERENCE_DISTRIBUTION:
            required_fields = {
                "reference_median": self.reference_median,
                "reference_mad": self.reference_mad,
                "scaled_reference_mad": self.scaled_reference_mad,
            }
            missing_fields = sorted(
                field_name
                for field_name, value in required_fields.items()
                if value is None
            )
            if missing_fields:
                missing_display = ", ".join(missing_fields)
                raise ValueError(
                    "degenerate reference results require non-None values for: "
                    f"{missing_display}."
                )

        if self.status is CalibrationStatus.REFERENCE_TOO_SMALL:
            if any(
                value is not None
                for value in (
                    self.reference_median,
                    self.reference_mad,
                    self.scaled_reference_mad,
                    self.robust_z_score,
                )
            ):
                raise ValueError(
                    "reference_too_small results must not populate calibration "
                    "summary fields."
                )

        if self.robust_z_score is not None and self.status is not CalibrationStatus.OK:
            raise ValueError("robust_z_score is only valid when status is ok.")

        if (
            self.missing_reference_ids
            and self.status is not CalibrationStatus.MISSING_DATA
        ):
            raise ValueError(
                "missing_reference_ids are only valid for missing_data results."
            )


def _is_finite_number(value: float) -> bool:
    return math.isfinite(value)


def _median_absolute_deviation(values: tuple[float, ...], *, center: float) -> float:
    deviations = tuple(abs(value - center) for value in values)
    return float(median(deviations))


def _build_result(
    *,
    raw_score: float | None,
    reference_population: ReferencePopulation,
    reference_size: int,
    reference_median: float | None,
    reference_mad: float | None,
    scaled_reference_mad: float | None,
    robust_z_score: float | None,
    status: CalibrationStatus,
    missing_reference_ids: tuple[str, ...] = (),
) -> RobustCalibrationResult:
    return RobustCalibrationResult(
        raw_score=raw_score,
        reference_label=reference_population.label,
        reference_kind=reference_population.kind,
        reference_size=reference_size,
        reference_median=reference_median,
        reference_mad=reference_mad,
        scaled_reference_mad=scaled_reference_mad,
        robust_z_score=robust_z_score,
        status=status,
        missing_reference_ids=missing_reference_ids,
    )


def robust_calibrate_scores(
    raw_scores: Mapping[str, float],
    *,
    reference_population: ReferencePopulation,
    min_reference_size: int = 3,
    mad_scale_factor: float = MAD_SCALE_FACTOR,
    min_mad: float = 1e-12,
) -> dict[str, RobustCalibrationResult]:
    """Compute MAD-based robust z-scores over a declared reference population.

    This function calibrates already-computed raw scores. It does not replace
    the single-sample rank-based scoring kernel.
    """

    missing_reference_ids = tuple(
        sorted(
            sample_id
            for sample_id in reference_population.sample_ids
            if sample_id not in raw_scores
        )
    )
    if missing_reference_ids:
        return {
            sample_id: _build_result(
                raw_score=raw_scores[sample_id]
                if _is_finite_number(raw_scores[sample_id])
                else None,
                reference_population=reference_population,
                reference_size=len(reference_population.sample_ids),
                reference_median=None,
                reference_mad=None,
                scaled_reference_mad=None,
                robust_z_score=None,
                status=CalibrationStatus.MISSING_DATA,
                missing_reference_ids=missing_reference_ids,
            )
            for sample_id in raw_scores
        }

    reference_scores = tuple(
        raw_scores[sample_id] for sample_id in reference_population.sample_ids
    )
    if len(reference_scores) < min_reference_size:
        return {
            sample_id: _build_result(
                raw_score=raw_scores[sample_id]
                if _is_finite_number(raw_scores[sample_id])
                else None,
                reference_population=reference_population,
                reference_size=len(reference_scores),
                reference_median=None,
                reference_mad=None,
                scaled_reference_mad=None,
                robust_z_score=None,
                status=CalibrationStatus.REFERENCE_TOO_SMALL,
            )
            for sample_id in raw_scores
        }

    if not all(_is_finite_number(score) for score in reference_scores):
        return {
            sample_id: _build_result(
                raw_score=raw_scores[sample_id]
                if _is_finite_number(raw_scores[sample_id])
                else None,
                reference_population=reference_population,
                reference_size=len(reference_scores),
                reference_median=None,
                reference_mad=None,
                scaled_reference_mad=None,
                robust_z_score=None,
                status=CalibrationStatus.MISSING_DATA,
            )
            for sample_id in raw_scores
        }

    reference_median = float(median(reference_scores))
    reference_mad = _median_absolute_deviation(
        reference_scores,
        center=reference_median,
    )
    scaled_reference_mad = mad_scale_factor * reference_mad

    if reference_mad <= min_mad:
        return {
            sample_id: _build_result(
                raw_score=raw_scores[sample_id]
                if _is_finite_number(raw_scores[sample_id])
                else None,
                reference_population=reference_population,
                reference_size=len(reference_scores),
                reference_median=reference_median,
                reference_mad=reference_mad,
                scaled_reference_mad=scaled_reference_mad,
                robust_z_score=None,
                status=CalibrationStatus.DEGENERATE_REFERENCE_DISTRIBUTION,
            )
            for sample_id in raw_scores
        }

    calibrated: dict[str, RobustCalibrationResult] = {}
    for sample_id, raw_score in raw_scores.items():
        if not _is_finite_number(raw_score):
            calibrated[sample_id] = _build_result(
                raw_score=None,
                reference_population=reference_population,
                reference_size=len(reference_scores),
                reference_median=reference_median,
                reference_mad=reference_mad,
                scaled_reference_mad=scaled_reference_mad,
                robust_z_score=None,
                status=CalibrationStatus.MISSING_DATA,
            )
            continue

        calibrated[sample_id] = _build_result(
            raw_score=raw_score,
            reference_population=reference_population,
            reference_size=len(reference_scores),
            reference_median=reference_median,
            reference_mad=reference_mad,
            scaled_reference_mad=scaled_reference_mad,
            robust_z_score=(raw_score - reference_median) / scaled_reference_mad,
            status=CalibrationStatus.OK,
        )

    return calibrated
