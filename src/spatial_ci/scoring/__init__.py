"""Public scoring API for internal-first Spatial-CI scoring work."""

from spatial_ci.scoring.api import (
    CalibrationStatus,
    ReferencePopulation,
    ReferencePopulationKind,
    RobustCalibrationResult,
    ScoreArtifact,
    ScoreFailureCode,
    ScorePacket,
    ScorePacketAdapter,
    ScoreStatus,
    SignatureDirection,
    robust_calibrate_scores,
    score_batch,
    score_one,
)

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
