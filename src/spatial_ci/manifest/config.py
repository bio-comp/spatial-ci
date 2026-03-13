from pathlib import Path

import yaml  # type: ignore[import-untyped]
from pydantic import BaseModel


class ManifestSourceConfig(BaseModel):
    """One metadata source table used for pass-1 manifest building."""

    path: Path
    format: str
    field_map: dict[str, str]
    cohort_id: str | None = None


class SplitContractConfig(BaseModel):
    """Split settings embedded in the manifest build config."""

    split_contract_id: str
    val_fraction: float
    external_holdout_cohorts: list[str]


class ManifestBuildConfig(BaseModel):
    """Minimal pass-1 manifest build config."""

    sources: list[ManifestSourceConfig]
    split_contract: SplitContractConfig


def load_manifest_config(path: Path) -> ManifestBuildConfig:
    """Load the YAML manifest build config from disk."""

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return ManifestBuildConfig.model_validate(data)
