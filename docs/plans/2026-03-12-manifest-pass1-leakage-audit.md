# Manifest Pass 1 Leakage Audit Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add pass-1 leakage auditing on top of the split-assignment artifact, rename the external split to `test_external`, emit a deterministic fatal leakage report, and halt the manifest CLI on overlap.

**Architecture:** Keep leakage auditing separate from pass-2 materialization by implementing it as a pass-1 artifact consumer. Extend the manifest artifact models, add a dedicated `leakage.py` module for overlap detection, and integrate report emission plus fatal error behavior into the existing pass-1 pipeline and CLI.

**Tech Stack:** Python 3.10+, Polars, Pydantic, Click, pytest

---

### Task 1: Rename External Split To `test_external`

**Files:**
- Modify: `src/spatial_ci/manifest/splits.py`
- Modify: `tests/manifest/test_splits.py`

**Step 1: Write the failing test**

Update `tests/manifest/test_splits.py` to assert external cohorts are assigned `test_external` instead of `holdout`:

```python
def test_assign_patient_splits_marks_external_cohorts_as_test_external() -> None:
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
    assert assigned.item(0, "split") == "test_external"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/manifest/test_splits.py -q`

Expected: FAIL because the current code still emits `holdout`

**Step 3: Write minimal implementation**

Change `src/spatial_ci/manifest/splits.py` so external cohorts emit `test_external`.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/manifest/test_splits.py -q`

Expected: PASS

**Step 5: Commit**

```bash
git add src/spatial_ci/manifest/splits.py tests/manifest/test_splits.py
git commit -m "feat: rename manifest external split to test_external"
```

### Task 2: Add Leakage Report Models And Detection Logic

**Files:**
- Modify: `src/spatial_ci/manifest/artifacts.py`
- Create: `src/spatial_ci/manifest/leakage.py`
- Create: `tests/manifest/test_leakage.py`

**Step 1: Write the failing tests**

Create `tests/manifest/test_leakage.py` with coverage for clean artifacts, patient/specimen/slide overlap, null handling, namespacing safety, and deterministic sorting:

```python
import polars as pl

from spatial_ci.manifest.leakage import build_leakage_report


def test_build_leakage_report_returns_empty_for_clean_assignments() -> None:
    frame = pl.DataFrame(
        {
            "sample_id": ["s1", "s2"],
            "cohort_id": ["cohort-a", "cohort-b"],
            "split": ["train", "val"],
            "resolved_patient_id": ["cohort-a::p1", "cohort-b::p2"],
            "patient_id_source": ["patient_id", "patient_id"],
            "resolved_specimen_id": ["cohort-a::spec1", "cohort-b::spec2"],
            "resolved_slide_id": ["cohort-a::slide1", "cohort-b::slide2"],
        }
    )
    report = build_leakage_report(frame, split_contract_id="split-v1")
    assert report.n_findings == 0
    assert report.rows == []


def test_build_leakage_report_detects_patient_overlap() -> None:
    frame = pl.DataFrame(
        {
            "sample_id": ["s1", "s2"],
            "cohort_id": ["cohort-a", "cohort-a"],
            "split": ["train", "val"],
            "resolved_patient_id": ["cohort-a::p1", "cohort-a::p1"],
            "patient_id_source": ["patient_id", "patient_id"],
            "resolved_specimen_id": [None, None],
            "resolved_slide_id": [None, None],
        }
    )
    report = build_leakage_report(frame, split_contract_id="split-v1")
    assert report.n_findings == 1
    assert report.rows[0].audit_column == "resolved_patient_id"
    assert report.rows[0].overlapping_id == "cohort-a::p1"
```

Add similar tests for:

- specimen overlap
- slide overlap
- null specimen/slide IDs ignored
- `cohort-a::slide-1` vs `cohort-b::slide-1` does not collide
- rows sorted by `audit_column`, `split_left`, `split_right`, `overlapping_id`

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/manifest/test_leakage.py -q`

Expected: FAIL with missing module or models

**Step 3: Write minimal implementation**

Implement:

- `LeakageReportRow`
- `LeakageReportArtifact`
- `build_leakage_report(frame: pl.DataFrame, split_contract_id: str) -> LeakageReportArtifact`

Detection rules:

- audited columns:
  - `resolved_patient_id`
  - `resolved_specimen_id`
  - `resolved_slide_id`
- split pairs:
  - `train` vs `val`
  - `train` vs `test_external`
  - `val` vs `test_external`
- ignore null IDs
- emit one row per overlapping ID
- sort deterministically before building artifact rows

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/manifest/test_leakage.py -q`

Expected: PASS

**Step 5: Commit**

```bash
git add src/spatial_ci/manifest/artifacts.py src/spatial_ci/manifest/leakage.py tests/manifest/test_leakage.py
git commit -m "feat: add manifest leakage report detection"
```

### Task 3: Integrate Leakage Audit Into The Pass-1 Pipeline

**Files:**
- Modify: `src/spatial_ci/manifest/pipeline.py`
- Modify: `tests/manifest/test_pipeline.py`

**Step 1: Write the failing tests**

Extend `tests/manifest/test_pipeline.py` with one clean-path assertion and one fatal-path assertion:

```python
def test_build_split_assignments_does_not_write_leakage_report_when_clean(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "assignments.parquet"
    artifact = build_split_assignments(
        config_path=Path("tests/fixtures/manifest/pass1/config_basic.yaml"),
        output_path=output_path,
    )
    assert artifact.leakage_report_path is None
    assert not output_path.with_suffix(".leakage.parquet").exists()


def test_build_split_assignments_writes_fatal_leakage_report(tmp_path: Path) -> None:
    output_path = tmp_path / "assignments.parquet"
    with pytest.raises(ManifestPipelineError, match="Leakage detected"):
        build_split_assignments(
            config_path=Path("tests/fixtures/manifest/pass1/config_leakage.yaml"),
            output_path=output_path,
        )
    report_path = output_path.with_suffix(".leakage.parquet")
    report = pl.read_parquet(report_path)
    assert report.height > 0
```

Create `tests/fixtures/manifest/pass1/config_leakage.yaml` and `tests/fixtures/manifest/pass1/metadata_leakage.csv` with a patient/specimen/slide overlap across audited splits.

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/manifest/test_pipeline.py -q`

Expected: FAIL because the pipeline does not audit leakage yet

**Step 3: Write minimal implementation**

Update `build_split_assignments()` to:

- run `build_leakage_report()` after split assignment
- derive report path from output path:
  - `assignments.parquet` -> `assignments.leakage.parquet`
- write the leakage report only when findings exist
- raise `ManifestPipelineError("Leakage detected ...")` after report emission
- extend `SplitAssignmentArtifact` with `leakage_report_path: Path | None = None`

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/manifest/test_pipeline.py -q`

Expected: PASS

**Step 5: Commit**

```bash
git add src/spatial_ci/manifest/pipeline.py tests/manifest/test_pipeline.py tests/fixtures/manifest/pass1/config_leakage.yaml tests/fixtures/manifest/pass1/metadata_leakage.csv
git commit -m "feat: add fatal leakage audit to manifest pipeline"
```

### Task 4: Wire CLI Fatal Leakage Behavior

**Files:**
- Modify: `scripts/build_manifest.py`
- Modify: `tests/manifest/test_build_manifest_cli.py`

**Step 1: Write the failing test**

Add a CLI fatal-path test:

```python
def test_build_manifest_cli_writes_leakage_report_and_exits_nonzero(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "assignments.parquet"
    runner = CliRunner()
    main = _load_build_manifest_main()
    result = runner.invoke(
        main,
        [
            "--config",
            "tests/fixtures/manifest/pass1/config_leakage.yaml",
            "--output",
            str(output_path),
        ],
    )
    assert result.exit_code != 0
    assert output_path.with_suffix(".leakage.parquet").exists()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/manifest/test_build_manifest_cli.py -q`

Expected: FAIL because the CLI does not yet surface the fatal leakage path correctly

**Step 3: Write minimal implementation**

Keep `scripts/build_manifest.py` thin:

- let `build_split_assignments()` raise `ManifestPipelineError`
- map that exception to `click.ClickException`
- preserve the written leakage report artifact on failure

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/manifest/test_build_manifest_cli.py -q`

Expected: PASS

**Step 5: Commit**

```bash
git add scripts/build_manifest.py tests/manifest/test_build_manifest_cli.py
git commit -m "feat: surface fatal manifest leakage in cli"
```

### Task 5: Full Verification

**Files:**
- Modify: only files touched above if verification exposes issues

**Step 1: Run focused manifest tests**

Run: `uv run pytest tests/manifest -q`

Expected: PASS

**Step 2: Run manifest-scope type and lint checks**

Run: `uv run ruff check src/spatial_ci/manifest tests/manifest scripts/build_manifest.py`

Expected: PASS

Run: `uv run mypy src/spatial_ci/manifest tests/manifest scripts/build_manifest.py`

Expected: PASS

**Step 3: Run full repo tests**

Run: `uv run pytest -q`

Expected: PASS

**Step 4: Commit**

```bash
git add src/spatial_ci/manifest scripts/build_manifest.py tests/manifest tests/fixtures/manifest/pass1
git commit -m "test: verify manifest leakage audit slice"
```
