"""Public scoring API for internal-first Spatial-CI scoring work."""

from spatial_ci.scoring.api import (
    CalibrationStatus,
    MissingGenePolicy,
    ReferencePopulation,
    ReferencePopulationKind,
    RobustCalibrationResult,
    ScoreArtifact,
    ScoreFailureCode,
    ScorePacket,
    ScorePacketAdapter,
    ScoreResult,
    ScoreStatus,
    SignatureDirection,
    TiePolicy,
    robust_calibrate_scores,
    singscore,
)

__all__ = [
    "CalibrationStatus",
    "MissingGenePolicy",
    "ReferencePopulation",
    "ReferencePopulationKind",
    "RobustCalibrationResult",
    "ScoreArtifact",
    "ScoreResult",
    "ScoreFailureCode",
    "ScorePacket",
    "ScorePacketAdapter",
    "ScoreStatus",
    "SignatureDirection",
    "TiePolicy",
    "robust_calibrate_scores",
    "singscore",
]
