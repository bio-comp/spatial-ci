"""Manifest package for pass-1 assignments and pass-2 materialization."""

from spatial_ci.manifest.artifacts import (
    LeakageReportArtifact,
    LeakageReportRow,
    MaterializedManifestArtifact,
    MaterializedManifestRow,
    RejectionLedgerArtifact,
    RejectionRow,
    ResolvedArtifact,
    SplitAssignmentArtifact,
    SplitAssignmentRow,
)
from spatial_ci.manifest.config import (
    ArtifactCandidateConfig,
    ManifestBuildConfig,
    ManifestOutputConfig,
    ManifestSourceConfig,
    ResolverConfig,
    SplitContractConfig,
    load_manifest_config,
)
from spatial_ci.manifest.leakage import build_leakage_report
from spatial_ci.manifest.pipeline import build_materialized_manifest

__all__ = [
    "ArtifactCandidateConfig",
    "LeakageReportArtifact",
    "LeakageReportRow",
    "ManifestBuildConfig",
    "ManifestOutputConfig",
    "MaterializedManifestArtifact",
    "MaterializedManifestRow",
    "ManifestSourceConfig",
    "RejectionLedgerArtifact",
    "RejectionRow",
    "ResolvedArtifact",
    "ResolverConfig",
    "SplitAssignmentArtifact",
    "SplitAssignmentRow",
    "SplitContractConfig",
    "build_materialized_manifest",
    "build_leakage_report",
    "load_manifest_config",
]
