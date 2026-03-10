"""Public scoring API for internal-first Spatial-CI scoring work."""

from spatial_ci.scoring.api import (
    CalibrationStatus,
    MissingGenePolicy,
    ReferencePopulation,
    ReferencePopulationKind,
    RobustCalibrationResult,
    ScoreFailureCode,
    ScorePacket,
    ScorePacketAdapter,
    ScoreResult,
    SignatureCoverage,
    SignatureDirectionality,
    TiePolicy,
    UncertaintyFlag,
    robust_calibrate_scores,
    singscore,
)

__all__ = [
    "CalibrationStatus",
    "MissingGenePolicy",
    "ReferencePopulation",
    "ReferencePopulationKind",
    "RobustCalibrationResult",
    "ScoreResult",
    "ScoreFailureCode",
    "ScorePacket",
    "ScorePacketAdapter",
    "SignatureCoverage",
    "SignatureDirectionality",
    "TiePolicy",
    "UncertaintyFlag",
    "robust_calibrate_scores",
    "singscore",
]
