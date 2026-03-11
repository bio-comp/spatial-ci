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
from spatial_ci.scoring.singscore import (
    MissingGenePolicy,
    ScoreResult,
    TiePolicy,
    score_batch,
    score_one,
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
    "score_batch",
    "score_one",
    "singscore",
]
