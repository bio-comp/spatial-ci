# Baseline Mean Foundation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add the first baseline execution boundary to Spatial-CI with a typed prediction artifact, a baseline runner, and the two mean-based deployable baselines: `global_train_mean` and `mean_by_train_cohort`.

**Architecture:** Create a new `spatial_ci.baselines` package with artifact schemas, train-only mean-baseline logic, and a runner that joins score artifacts to the materialized manifest. Keep `scripts/run_baselines.py` thin and explicit.

**Tech Stack:** Python 3.13, Pydantic, Polars, Click, pytest, Ruff, mypy

---

### Task 1: Add Baseline Artifact Schemas

**Files:**
- Create: `src/spatial_ci/baselines/artifacts.py`
- Create: `src/spatial_ci/baselines/__init__.py`
- Test: `tests/baselines/test_artifacts.py`

**Step 1: Write the failing test**

Add tests for:
- `BaselinePredictionRow` validation
- `BaselinePredictionArtifact` count consistency
- Parquet write/read roundtrip

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/baselines/test_artifacts.py -q`
Expected: FAIL because baseline artifact code does not exist yet.

**Step 3: Write minimal implementation**

Add:
- `BaselineName`
- `BaselinePredictionRow`
- `BaselinePredictionArtifact`
- read/write helpers

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/baselines/test_artifacts.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add src/spatial_ci/baselines/artifacts.py src/spatial_ci/baselines/__init__.py tests/baselines/test_artifacts.py
git commit -m "feat: add baseline prediction artifacts"
```

### Task 2: Implement Mean Baseline Logic

**Files:**
- Create: `src/spatial_ci/baselines/mean.py`
- Test: `tests/baselines/test_mean.py`

**Step 1: Write the failing test**

Add tests for:
- `global_train_mean` uses train rows only
- `mean_by_train_cohort` uses cohort-specific train means
- `mean_by_train_cohort` falls back to global when cohort mean is absent
- dropped/failed score rows are excluded from fitting

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/baselines/test_mean.py -q`
Expected: FAIL because mean baseline logic does not exist yet.

**Step 3: Write minimal implementation**

Implement train-only fit helpers and row-wise prediction builders for:
- `global_train_mean`
- `mean_by_train_cohort`

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/baselines/test_mean.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add src/spatial_ci/baselines/mean.py tests/baselines/test_mean.py
git commit -m "feat: add mean baseline predictors"
```

### Task 3: Add Baseline Runner

**Files:**
- Create: `src/spatial_ci/baselines/runner.py`
- Test: `tests/baselines/test_runner.py`

**Step 1: Write the failing test**

Add tests for:
- joining score artifact rows to manifest by `sample_id`
- rejecting missing `sample_id` on eligible score rows
- rejecting duplicate manifest `sample_id`
- rejecting score rows missing from the manifest
- producing long-form prediction rows for both mean baselines

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/baselines/test_runner.py -q`
Expected: FAIL because the runner does not exist yet.

**Step 3: Write minimal implementation**

Implement runner logic that:
- reads the score artifact
- filters to `ScoreStatus.OK`
- validates joinability against the manifest parquet
- executes requested mean baselines
- writes the prediction artifact

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/baselines/test_runner.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add src/spatial_ci/baselines/runner.py tests/baselines/test_runner.py
git commit -m "feat: add baseline runner"
```

### Task 4: Wire the CLI

**Files:**
- Create: `scripts/run_baselines.py`
- Test: `tests/baselines/test_run_baselines_cli.py`

**Step 1: Write the failing test**

Add CLI tests for:
- successful run writing a baseline prediction artifact
- explicit argument validation
- deterministic output row count and baseline-name coverage

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/baselines/test_run_baselines_cli.py -q`
Expected: FAIL because the CLI does not exist yet.

**Step 3: Write minimal implementation**

Implement a thin CLI with explicit flags:
- `--scores`
- `--manifest`
- `--output`
- `--run-id`
- `--baseline-contract-id`
- `--split-contract-id`
- `--manifest-id`

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/baselines/test_run_baselines_cli.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/run_baselines.py tests/baselines/test_run_baselines_cli.py
git commit -m "feat: add baseline runner cli"
```

### Task 5: Update Docs and Run Full Verification

**Files:**
- Update: `docs/REPO_SETUP.md`
- Update: any other touched baseline docs if needed

**Step 1: Update docs**

Document:
- the new `run_baselines.py` entry point
- the prediction artifact shape
- that this slice covers mean baselines only, with embedding baselines deferred

**Step 2: Run targeted verification**

Run:
- `uv run pytest tests/baselines -q`
- `uv run ruff check src/spatial_ci/baselines tests/baselines scripts/run_baselines.py`
- `uv run mypy src/spatial_ci/baselines tests/baselines scripts/run_baselines.py`

**Step 3: Run full repo verification**

Run:
- `uv run ruff check .`
- `uv run mypy src tests scripts/build_manifest.py scripts/run_baselines.py`
- `uv run pytest -q`

**Step 4: Commit**

```bash
git add docs/REPO_SETUP.md src/spatial_ci/baselines tests/baselines scripts/run_baselines.py
git commit -m "docs: record baseline mean foundation"
```
