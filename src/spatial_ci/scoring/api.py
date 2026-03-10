"""Small public API surface for extraction-friendly scoring code."""

from spatial_ci.scoring.calibration import (
    CalibrationStatus,
    ReferencePopulation,
    ReferencePopulationKind,
    RobustCalibrationResult,
    robust_calibrate_scores,
)
from spatial_ci.scoring.packet import (
    ScoreFailureCode,
    ScorePacket,
    ScorePacketAdapter,
    SignatureCoverage,
    SignatureDirectionality,
    UncertaintyFlag,
)
from spatial_ci.scoring.singscore import (
    MissingGenePolicy,
    ScoreResult,
    TiePolicy,
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
