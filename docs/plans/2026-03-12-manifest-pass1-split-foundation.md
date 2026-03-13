# Manifest Pass 1 Split Foundation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the first useful manifest slice: canonical metadata normalization, resolved patient/specimen/slide IDs, deterministic patient-level split assignment, and a sorted Parquet split-assignment artifact.

**Architecture:** Keep `scripts/build_manifest.py` thin and move all pass-1 logic into `src/spatial_ci/manifest/`. Use YAML config + Polars tables + Pydantic models, with deterministic split assignment based on a stable SHA256-derived fraction over `split_contract_id` and `resolved_patient_id`.

**Tech Stack:** Python 3.10+, Polars, Pydantic, PyYAML, Click, pytest

---

### Task 1: Scaffold Manifest Package And Config Models

**Files:**
- Modify: `pyproject.toml`
- Create: `src/spatial_ci/manifest/__init__.py`
- Create: `src/spatial_ci/manifest/config.py`
- Create: `src/spatial_ci/manifest/artifacts.py`
- Create: `tests/manifest/test_config.py`

**Step 1: Write the failing tests**

```python
from pathlib import Path

from spatial_ci.manifest.config import ManifestBuildConfig, load_manifest_config


def test_load_manifest_config_reads_yaml_fixture() -> None:
    config = load_manifest_config(
        Path("tests/fixtures/manifest/pass1/config_basic.yaml")
    )
    assert config.split_contract.split_contract_id == "breast_visium_split_v1"
    assert config.sources[0].field_map["sample"] == "sample_id"


def test_split_assignment_artifact_model_requires_expected_fields() -> None:
    from spatial_ci.manifest.artifacts import SplitAssignmentRow

    row = SplitAssignmentRow(
        sample_id="spot-1",
        cohort_id="cohort-a",
        split="train",
        resolved_patient_id="cohort-a::patient-1",
        patient_id_source="patient_id",
        resolved_specimen_id=None,
        resolved_slide_id=None,
    )
    assert row.sample_id == "spot-1"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/manifest/test_config.py -q`

Expected: FAIL with `ModuleNotFoundError` or missing `load_manifest_config`

**Step 3: Write minimal implementation**

Implement:

- `pyproject.toml`
  - add `pyyaml>=6.0`
- `src/spatial_ci/manifest/config.py`
  - `ManifestSourceConfig`
  - `SplitContractConfig`
  - `ManifestBuildConfig`
  - `load_manifest_config(path: Path) -> ManifestBuildConfig`
- `src/spatial_ci/manifest/artifacts.py`
  - `SplitAssignmentRow`
  - `SplitAssignmentArtifact`
- `src/spatial_ci/manifest/__init__.py`
  - re-export config loader and artifact models

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/manifest/test_config.py -q`

Expected: PASS

**Step 5: Commit**

```bash
git add pyproject.toml src/spatial_ci/manifest/__init__.py src/spatial_ci/manifest/config.py src/spatial_ci/manifest/artifacts.py tests/manifest/test_config.py
git commit -m "feat: add manifest config and artifact models"
```

### Task 2: Implement Canonical Field Normalization

**Files:**
- Create: `src/spatial_ci/manifest/normalize.py`
- Create: `tests/manifest/test_normalize.py`
- Create: `tests/fixtures/manifest/pass1/metadata_aliases.csv`
- Create: `tests/fixtures/manifest/pass1/config_aliases.yaml`

**Step 1: Write the failing test**

```python
import polars as pl

from spatial_ci.manifest.normalize import normalize_manifest_source


def test_normalize_manifest_source_maps_aliases_to_canonical_fields() -> None:
    frame = pl.DataFrame(
        {
            "sample": ["spot-1"],
            "patient": ["patient-1"],
            "slide": ["slide-1"],
        }
    )
    normalized = normalize_manifest_source(
        frame,
        field_map={
            "sample": "sample_id",
            "patient": "patient_id",
            "slide": "slide_id",
        },
        cohort_id="cohort-a",
    )
    assert normalized.columns == ["sample_id", "patient_id", "slide_id", "cohort_id"]
    assert normalized.item(0, "cohort_id") == "cohort-a"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/manifest/test_normalize.py -q`

Expected: FAIL with missing module/function

**Step 3: Write minimal implementation**

Implement `normalize_manifest_source()` using Polars:

- rename columns according to `field_map`
- inject constant `cohort_id` if configured
- require canonical `sample_id` and `cohort_id`
- preserve optional patient/specimen/slide fields when present
- return only canonical pass-1 columns

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/manifest/test_normalize.py -q`

Expected: PASS

**Step 5: Commit**

```bash
git add src/spatial_ci/manifest/normalize.py tests/manifest/test_normalize.py tests/fixtures/manifest/pass1/metadata_aliases.csv tests/fixtures/manifest/pass1/config_aliases.yaml
git commit -m "feat: add manifest source normalization"
```

### Task 3: Implement Resolved Identity Construction

**Files:**
- Create: `src/spatial_ci/manifest/identity.py`
- Create: `tests/manifest/test_identity.py`

**Step 1: Write the failing tests**

```python
import polars as pl

from spatial_ci.manifest.identity import derive_resolved_identity


def test_derive_resolved_identity_namespaces_slide_and_specimen_ids() -> None:
    frame = pl.DataFrame(
        {
            "sample_id": ["spot-1"],
            "cohort_id": ["cohort-a"],
            "patient_id": ["patient-1"],
            "specimen_id": ["specimen-1"],
            "slide_id": ["slide-1"],
        }
    )
    resolved = derive_resolved_identity(frame)
    assert resolved.item(0, "resolved_patient_id") == "cohort-a::patient-1"
    assert resolved.item(0, "resolved_specimen_id") == "cohort-a::specimen-1"
    assert resolved.item(0, "resolved_slide_id") == "cohort-a::slide-1"
    assert resolved.item(0, "patient_id_source") == "patient_id"


def test_derive_resolved_identity_falls_back_to_sample_id_when_patient_missing() -> None:
    frame = pl.DataFrame({"sample_id": ["spot-1"], "cohort_id": ["cohort-a"]})
    resolved = derive_resolved_identity(frame)
    assert resolved.item(0, "resolved_patient_id") == "cohort-a::spot-1"
    assert resolved.item(0, "patient_id_source") == "sample_id"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/manifest/test_identity.py -q`

Expected: FAIL with missing module/function

**Step 3: Write minimal implementation**

Implement:

- strict fallback order for patient resolution
- `patient_id_source`
- namespaced specimen/slide IDs
- stable string normalization for empty/null values

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/manifest/test_identity.py -q`

Expected: PASS

**Step 5: Commit**

```bash
git add src/spatial_ci/manifest/identity.py tests/manifest/test_identity.py
git commit -m "feat: add manifest identity resolution"
```

### Task 4: Implement Deterministic Patient-Level Split Assignment

**Files:**
- Create: `src/spatial_ci/manifest/splits.py`
- Create: `tests/manifest/test_splits.py`

**Step 1: Write the failing tests**

```python
import polars as pl

from spatial_ci.manifest.splits import assign_patient_splits


def test_assign_patient_splits_is_deterministic() -> None:
    frame = pl.DataFrame(
        {
            "sample_id": ["s1", "s2"],
            "cohort_id": ["cohort-a", "cohort-a"],
            "resolved_patient_id": ["cohort-a::p1", "cohort-a::p2"],
        }
    )
    first = assign_patient_splits(
        frame,
        split_contract_id="split-v1",
        val_fraction=0.5,
        external_holdout_cohorts=[],
    )
    second = assign_patient_splits(
        frame,
        split_contract_id="split-v1",
        val_fraction=0.5,
        external_holdout_cohorts=[],
    )
    assert first.equals(second)


def test_assign_patient_splits_marks_external_cohorts_as_holdout() -> None:
    frame = pl.DataFrame(
        {
            "sample_id": ["s1"],
            "cohort_id": ["external-a"],
            "resolved_patient_id": ["external-a::p1"],
        }
    )
    assigned = assign_patient_splits(
        frame,
        split_contract_id="split-v1",
        val_fraction=0.2,
        external_holdout_cohorts=["external-a"],
    )
    assert assigned.item(0, "split") == "holdout"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/manifest/test_splits.py -q`

Expected: FAIL with missing module/function

**Step 3: Write minimal implementation**

Implement:

- stable SHA256-based fraction over `split_contract_id` + `resolved_patient_id`
- `train` / `val` assignment from `val_fraction`
- `holdout` override for `external_holdout_cohorts`
- validation for `0.0 < val_fraction < 1.0`

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/manifest/test_splits.py -q`

Expected: PASS

**Step 5: Commit**

```bash
git add src/spatial_ci/manifest/splits.py tests/manifest/test_splits.py
git commit -m "feat: add deterministic manifest split assignment"
```

### Task 5: Implement Pass-1 Pipeline And Sorted Parquet Output

**Files:**
- Create: `src/spatial_ci/manifest/pipeline.py`
- Create: `tests/manifest/test_pipeline.py`
- Create: `tests/fixtures/manifest/pass1/config_basic.yaml`
- Create: `tests/fixtures/manifest/pass1/config_duplicate.yaml`
- Create: `tests/fixtures/manifest/pass1/metadata_basic.csv`

**Step 1: Write the failing tests**

```python
from pathlib import Path

import polars as pl

from spatial_ci.manifest.pipeline import build_split_assignments


def test_build_split_assignments_writes_sorted_parquet(tmp_path: Path) -> None:
    output_path = tmp_path / "assignments.parquet"
    artifact = build_split_assignments(
        config_path=Path("tests/fixtures/manifest/pass1/config_basic.yaml"),
        output_path=output_path,
    )
    table = pl.read_parquet(output_path)
    assert output_path.exists()
    assert table.columns == [
        "sample_id",
        "cohort_id",
        "split",
        "resolved_patient_id",
        "patient_id_source",
        "resolved_specimen_id",
        "resolved_slide_id",
    ]
    assert table.select(["split", "cohort_id", "sample_id"]).rows() == sorted(
        table.select(["split", "cohort_id", "sample_id"]).rows()
    )
    assert artifact.split_contract_id == "breast_visium_split_v1"


def test_build_split_assignments_rejects_duplicate_sample_id(tmp_path: Path) -> None:
    from spatial_ci.manifest.pipeline import ManifestPipelineError

    with pytest.raises(ManifestPipelineError, match="duplicate sample_id"):
        build_split_assignments(
            config_path=Path("tests/fixtures/manifest/pass1/config_duplicate.yaml"),
            output_path=tmp_path / "assignments.parquet",
        )
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/manifest/test_pipeline.py -q`

Expected: FAIL with missing module/function

**Step 3: Write minimal implementation**

Implement `build_split_assignments()`:

- load config
- read source tables with Polars
- normalize fields
- derive resolved identity
- assign deterministic splits
- validate duplicate `sample_id`
- sort by `split`, `cohort_id`, `sample_id`
- write Parquet
- return typed artifact metadata

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/manifest/test_pipeline.py -q`

Expected: PASS

**Step 5: Commit**

```bash
git add src/spatial_ci/manifest/pipeline.py tests/manifest/test_pipeline.py tests/fixtures/manifest/pass1/config_basic.yaml tests/fixtures/manifest/pass1/config_duplicate.yaml tests/fixtures/manifest/pass1/metadata_basic.csv
git commit -m "feat: add manifest pass-1 split pipeline"
```

### Task 6: Thin CLI Integration

**Files:**
- Modify: `scripts/build_manifest.py`
- Create: `tests/manifest/test_build_manifest_cli.py`

**Step 1: Write the failing test**

```python
from pathlib import Path

import polars as pl
from click.testing import CliRunner

from scripts.build_manifest import main


def test_build_manifest_cli_writes_split_assignment_artifact(tmp_path: Path) -> None:
    output_path = tmp_path / "assignments.parquet"
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--config",
            "tests/fixtures/manifest/pass1/config_basic.yaml",
            "--output",
            str(output_path),
        ],
    )
    assert result.exit_code == 0
    assert output_path.exists()
    assert pl.read_parquet(output_path).height > 0
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/manifest/test_build_manifest_cli.py -q`

Expected: FAIL because the CLI is still placeholder-only

**Step 3: Write minimal implementation**

Replace the placeholder body in `scripts/build_manifest.py` with:

- config loading
- call into `build_split_assignments()`
- concise success output
- ignore `--allow-missing` for now except for a clear “not implemented in pass-1” guard if necessary

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/manifest/test_build_manifest_cli.py -q`

Expected: PASS

**Step 5: Commit**

```bash
git add scripts/build_manifest.py tests/manifest/test_build_manifest_cli.py
git commit -m "feat: wire manifest cli to pass-1 pipeline"
```

### Task 7: Full Verification And Cleanup

**Files:**
- Modify: `src/spatial_ci/manifest/__init__.py`
- Modify: any files touched above only if required by lint/type/test failures

**Step 1: Run focused manifest tests**

Run: `uv run pytest tests/manifest -q`

Expected: PASS

**Step 2: Run repo verification**

Run: `uv run ruff check .`

Expected: PASS

Run: `uv run mypy src tests scripts/build_manifest.py`

Expected: PASS, or only previously known unrelated failures if they still exist on untouched files

Run: `uv run pytest -q`

Expected: PASS

**Step 3: Make minimal cleanup changes if verification exposes issues**

Only touch files in this PR’s scope unless an unrelated pre-existing failure blocks the PR.

**Step 4: Commit**

```bash
git add pyproject.toml scripts/build_manifest.py src/spatial_ci/manifest tests/manifest tests/fixtures/manifest/pass1
git commit -m "test: verify manifest split foundation slice"
```
