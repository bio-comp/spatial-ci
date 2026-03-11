"""Small public API surface for extraction-friendly scoring code."""

from spatial_ci.scoring.artifacts import (
    ScoreArtifact,
    ScoreFailureCode,
    ScorePacket,
    ScorePacketAdapter,
    ScoreStatus,
    SignatureDirection,
)
from spatial_ci.scoring.calibration import (
    CalibrationStatus,
    ReferencePopulation,
    ReferencePopulationKind,
    RobustCalibrationResult,
    robust_calibrate_scores,
)
from spatial_ci.scoring.singscore import score_batch, score_one

__all__ = [
    "CalibrationStatus",
    "ReferencePopulation",
    "ReferencePopulationKind",
    "RobustCalibrationResult",
    "ScoreArtifact",
    "ScoreFailureCode",
    "ScorePacket",
    "ScorePacketAdapter",
    "ScoreStatus",
    "SignatureDirection",
    "robust_calibrate_scores",
    "score_batch",
    "score_one",
]
