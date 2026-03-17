from pathlib import Path

import yaml  # type: ignore[import-untyped]
from pydantic import BaseModel, Field


class ManifestSourceConfig(BaseModel):
    """One metadata source table used for pass-1 manifest building."""

    path: Path
    format: str
    field_map: dict[str, str]
    cohort_id: str | None = None


class ArtifactCandidateConfig(BaseModel):
    """Ordered candidate paths for one artifact class."""

    image: tuple[Path, ...]
    spatial_coords: tuple[Path, ...]
    scalefactors: tuple[Path, ...]
    raw_expression: tuple[Path, ...]
    derived_expression: tuple[Path, ...] = ()


class ResolverConfig(BaseModel):
    """Filesystem resolution settings for pass-2 materialization."""

    sample_roots: tuple[Path, ...] = ()
    sample_path_field: str | None = None
    artifact_candidates: ArtifactCandidateConfig


class ManifestOutputConfig(BaseModel):
    """Manifest-level settings required for pass-2 output."""

    manifest_id: str
    alignment_contract_id: str
    metadata_defaults: dict[str, str | int | float | bool | None] = Field(
        default_factory=dict
    )


class SplitContractConfig(BaseModel):
    """Split settings embedded in the manifest build config."""

    split_contract_id: str
    val_fraction: float
    external_holdout_cohorts: list[str]


class ManifestBuildConfig(BaseModel):
    """Minimal pass-1 manifest build config."""

    sources: list[ManifestSourceConfig]
    split_contract: SplitContractConfig
    resolver: ResolverConfig | None = None
    manifest: ManifestOutputConfig | None = None


def load_manifest_config(path: Path) -> ManifestBuildConfig:
    """Load the YAML manifest build config from disk."""

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return ManifestBuildConfig.model_validate(data)
