from pathlib import Path

import pytest

from spatial_ci.manifest.config import ResolverConfig, load_manifest_config
from spatial_ci.manifest.resolver import (
    ArtifactResolutionError,
    ResolvedSampleArtifacts,
    resolve_sample_artifacts,
    resolve_sample_root,
)


def _resolver_config() -> ResolverConfig:
    config = load_manifest_config(
        Path("tests/fixtures/manifest/pass2/config_materialize.yaml")
    )
    assert config.resolver is not None
    return config.resolver


def test_resolve_sample_root_prefers_explicit_sample_path_field() -> None:
    resolver = _resolver_config()

    sample_root = resolve_sample_root(
        {
            "sample_id": "spot-1",
            "sample_path": "tests/fixtures/manifest/pass2/sample-root/spot-1",
        },
        resolver_config=resolver,
    )

    assert sample_root == Path("tests/fixtures/manifest/pass2/sample-root/spot-1")


def test_resolve_sample_root_falls_back_to_sample_root_search() -> None:
    resolver = _resolver_config().model_copy(update={"sample_path_field": None})

    sample_root = resolve_sample_root(
        {"sample_id": "spot-2"},
        resolver_config=resolver,
    )

    assert sample_root == Path("tests/fixtures/manifest/pass2/sample-root/spot-2")


def test_resolve_sample_artifacts_uses_ordered_candidates() -> None:
    resolver = _resolver_config()

    resolved = resolve_sample_artifacts(
        {
            "sample_id": "spot-1",
            "sample_path": "tests/fixtures/manifest/pass2/sample-root/spot-1",
        },
        resolver_config=resolver,
    )

    assert isinstance(resolved, ResolvedSampleArtifacts)
    assert resolved.image.path.name == "image.tiff"
    assert resolved.spatial_coords.path.name == "tissue_positions_list.csv"
    assert resolved.derived_expression is not None
    assert resolved.derived_expression.path.name == "expression.h5ad"


def test_resolve_sample_artifacts_allows_missing_optional_derived_expression() -> None:
    resolver = _resolver_config()

    resolved = resolve_sample_artifacts(
        {
            "sample_id": "spot-2",
            "sample_path": "tests/fixtures/manifest/pass2/sample-root/spot-2",
        },
        resolver_config=resolver,
    )

    assert resolved.derived_expression is None
    assert resolved.raw_expression.path.name == "filtered_feature_bc_matrix.h5"


def test_resolve_sample_artifacts_raises_on_missing_required_artifact() -> None:
    resolver = _resolver_config()

    with pytest.raises(ArtifactResolutionError, match="image"):
        resolve_sample_artifacts(
            {
                "sample_id": "spot-missing",
                "sample_path": "tests/fixtures/manifest/pass2/sample-root/spot-missing",
            },
            resolver_config=resolver,
        )
