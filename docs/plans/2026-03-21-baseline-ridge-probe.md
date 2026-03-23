# Baseline Ridge Probe Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add the frozen `ridge_probe` deployable baseline on top of the existing score + manifest + embedding baseline runner, and record the selected alpha per program in the baseline prediction artifact.

**Architecture:** Implement per-program ridge regression in `spatial_ci.baselines.ridge`, extend baseline prediction artifacts with artifact-level `ridge_probe_selected_alpha_by_program`, and extend the runner/CLI so embedding-aware runs emit mean baselines, KNN, and ridge together under frozen tuning rules.

**Tech Stack:** Python 3.13, Pydantic v2, Polars, NumPy, pytest, Click

---

### Task 1: Extend baseline prediction artifacts for ridge metadata

**Files:**
- Modify: `src/spatial_ci/baselines/artifacts.py`
- Test: `tests/baselines/test_baseline_artifacts.py`

**Step 1: Write the failing tests**

Add tests for:
- artifact roundtrip with `ridge_probe_selected_alpha_by_program`
- artifact rejects ridge rows without matching alpha metadata
- artifact rejects alpha metadata when no ridge rows are present

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/baselines/test_baseline_artifacts.py -q`
Expected: FAIL because the artifact does not yet model ridge alpha provenance.

**Step 3: Write minimal implementation**

Extend `BaselinePredictionArtifact` with:
- `ridge_probe_selected_alpha_by_program: dict[str, float] | None = None`

Add validation so:
- ridge rows require non-null metadata covering every ridge program
- non-ridge artifacts keep the field as `None`

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/baselines/test_baseline_artifacts.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add src/spatial_ci/baselines/artifacts.py tests/baselines/test_baseline_artifacts.py
git commit -m "feat: add ridge alpha metadata to baseline artifacts"
```

### Task 2: Add frozen ridge prediction logic

**Files:**
- Create: `src/spatial_ci/baselines/ridge.py`
- Test: `tests/baselines/test_ridge.py`

**Step 1: Write the failing tests**

Add tests for:
- alpha selection from `{0.1, 1.0, 10.0}`
- train-only standardization
- failure when a program has fewer than 2 train rows
- failure when a program has no val rows
- deterministic tie-breaking toward smaller alpha

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/baselines/test_ridge.py -q`
Expected: FAIL because `ridge.py` does not exist yet.

**Step 3: Write minimal implementation**

Implement:
- `predict_ridge_probe(frame: pl.DataFrame, *, alphas: tuple[float, ...] = (0.1, 1.0, 10.0)) -> tuple[pl.DataFrame, dict[str, float]]`

Requirements:
- require `observation_id`, `sample_id`, `cohort_id`, `split`, `program_name`,
  `raw_rank_evidence`, and `embedding`
- fit candidates on `train`
- select alpha by validation MSE on `val`
- predict long-form rows with `baseline_name = "ridge_probe"`

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/baselines/test_ridge.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add src/spatial_ci/baselines/ridge.py tests/baselines/test_ridge.py
git commit -m "feat: add frozen ridge baseline"
```

### Task 3: Extend baseline runner for ridge

**Files:**
- Modify: `src/spatial_ci/baselines/runner.py`
- Modify: `src/spatial_ci/baselines/__init__.py`
- Test: `tests/baselines/test_runner.py`

**Step 1: Write the failing tests**

Add tests for:
- successful combined output with mean baselines, KNN, and ridge when embeddings are provided
- alpha metadata is populated for ridge runs
- failure when a required program has no val rows
- failure when a required program has too few train rows

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/baselines/test_runner.py -q`
Expected: FAIL because the runner does not emit ridge or record alpha metadata.

**Step 3: Write minimal implementation**

Extend the runner to:
- call `predict_ridge_probe()` whenever embeddings are present
- merge its predictions with the existing prediction frames
- store `ridge_probe_selected_alpha_by_program` on the artifact
- preserve the existing mean-only behavior when embeddings are absent

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/baselines/test_runner.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add src/spatial_ci/baselines/runner.py src/spatial_ci/baselines/__init__.py tests/baselines/test_runner.py
git commit -m "feat: add ridge baseline runner integration"
```

### Task 4: Extend the CLI and docs

**Files:**
- Modify: `scripts/run_baselines.py`
- Modify: `docs/ARTIFACTS.md`
- Modify: `docs/REPO_SETUP.md`
- Test: `tests/baselines/test_run_baselines_cli.py`
- Modify: `LOCAL_TODO.md` (local-only, do not commit)

**Step 1: Write the failing tests**

Add CLI coverage for:
- embeddings path now emitting mean + KNN + ridge
- ridge alpha metadata present in the written artifact

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/baselines/test_run_baselines_cli.py -q`
Expected: FAIL because the CLI output contract does not yet include ridge metadata.

**Step 3: Write minimal implementation**

Keep the current `--embeddings` flag and update CLI messaging/docs to reflect
all embedding-aware baselines.

**Step 4: Run targeted verification**

Run:
- `uv run pytest tests/baselines/test_baseline_artifacts.py tests/baselines/test_ridge.py tests/baselines/test_runner.py tests/baselines/test_run_baselines_cli.py -q`
- `uv run ruff check src/spatial_ci/baselines tests/baselines scripts/run_baselines.py`
- `uv run mypy src/spatial_ci/baselines tests/baselines scripts/run_baselines.py`

Expected: PASS

**Step 5: Run broader verification**

Run:
- `uv run pytest -q`

Expected: PASS

**Step 6: Commit**

```bash
git add scripts/run_baselines.py docs/ARTIFACTS.md docs/REPO_SETUP.md tests/baselines/test_run_baselines_cli.py
git commit -m "docs: record ridge baseline foundation"
```
