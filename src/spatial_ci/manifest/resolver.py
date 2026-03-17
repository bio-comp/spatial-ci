from collections.abc import Mapping
from pathlib import Path

from pydantic import BaseModel

from spatial_ci.manifest.artifacts import ResolvedArtifact
from spatial_ci.manifest.config import ResolverConfig


class ArtifactResolutionError(RuntimeError):
    """Raised when pass-2 artifact resolution fails for a sample."""


class ResolvedSampleArtifacts(BaseModel):
    """All resolved pass-2 artifact paths for one sample."""

    sample_id: str
    sample_root: Path
    image: ResolvedArtifact
    spatial_coords: ResolvedArtifact
    scalefactors: ResolvedArtifact
    raw_expression: ResolvedArtifact
    derived_expression: ResolvedArtifact | None = None


def _normalize_string(value: object) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    if normalized == "":
        return None
    return normalized


def _resolve_candidate_path(sample_root: Path, candidate: Path) -> Path:
    if candidate.is_absolute():
        return candidate
    return sample_root / candidate


def resolve_sample_root(
    row: Mapping[str, object],
    *,
    resolver_config: ResolverConfig,
) -> Path:
    """Resolve the sample root for one row using explicit path or root search."""

    sample_id = _normalize_string(row.get("sample_id"))
    if sample_id is None:
        raise ArtifactResolutionError(
            "sample_id is required for sample-root resolution"
        )

    if resolver_config.sample_path_field is not None:
        sample_path_value = _normalize_string(
            row.get(resolver_config.sample_path_field)
        )
        if sample_path_value is not None:
            sample_root = Path(sample_path_value)
            if sample_root.exists():
                return sample_root
            raise ArtifactResolutionError(
                f"sample root does not exist for {sample_id}: {sample_root}"
            )

    for root in resolver_config.sample_roots:
        candidate = root / sample_id
        if candidate.exists():
            return candidate

    raise ArtifactResolutionError(
        f"could not resolve sample root for {sample_id}"
    )


def _resolve_required_artifact(
    sample_root: Path,
    *,
    artifact_type: str,
    candidates: tuple[Path, ...],
) -> ResolvedArtifact:
    for candidate in candidates:
        resolved_path = _resolve_candidate_path(sample_root, candidate)
        if resolved_path.exists():
            return ResolvedArtifact(artifact_type=artifact_type, path=resolved_path)
    raise ArtifactResolutionError(
        f"could not resolve required {artifact_type} artifact under {sample_root}"
    )


def _resolve_optional_artifact(
    sample_root: Path,
    *,
    artifact_type: str,
    candidates: tuple[Path, ...],
) -> ResolvedArtifact | None:
    for candidate in candidates:
        resolved_path = _resolve_candidate_path(sample_root, candidate)
        if resolved_path.exists():
            return ResolvedArtifact(artifact_type=artifact_type, path=resolved_path)
    return None


def resolve_sample_artifacts(
    row: Mapping[str, object],
    *,
    resolver_config: ResolverConfig,
) -> ResolvedSampleArtifacts:
    """Resolve all configured pass-2 artifacts for one sample."""

    sample_id = _normalize_string(row.get("sample_id"))
    if sample_id is None:
        raise ArtifactResolutionError("sample_id is required for artifact resolution")

    sample_root = resolve_sample_root(row, resolver_config=resolver_config)
    candidates = resolver_config.artifact_candidates
    return ResolvedSampleArtifacts(
        sample_id=sample_id,
        sample_root=sample_root,
        image=_resolve_required_artifact(
            sample_root,
            artifact_type="image",
            candidates=candidates.image,
        ),
        spatial_coords=_resolve_required_artifact(
            sample_root,
            artifact_type="spatial_coords",
            candidates=candidates.spatial_coords,
        ),
        scalefactors=_resolve_required_artifact(
            sample_root,
            artifact_type="scalefactors",
            candidates=candidates.scalefactors,
        ),
        raw_expression=_resolve_required_artifact(
            sample_root,
            artifact_type="raw_expression",
            candidates=candidates.raw_expression,
        ),
        derived_expression=_resolve_optional_artifact(
            sample_root,
            artifact_type="derived_expression",
            candidates=candidates.derived_expression,
        ),
    )
