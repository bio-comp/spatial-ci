# Baseline KNN Foundation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a typed embedding artifact boundary and the frozen `knn_on_embeddings` deployable baseline on top of the existing mean-baseline runner.

**Architecture:** Add a small `spatial_ci.embeddings` package for typed Parquet artifacts, implement frozen KNN prediction logic in `spatial_ci.baselines.knn`, and extend the baseline runner/CLI so embeddings are an optional third input. Keep mean baselines unchanged when embeddings are absent, and fail loudly on malformed embedding artifacts or broken score/manifest/embedding joins.

**Tech Stack:** Python 3.13, Pydantic v2, Polars, PyArrow, pytest, Click

---

### Task 1: Add embedding artifact schemas

**Files:**
- Create: `src/spatial_ci/embeddings/artifacts.py`
- Create: `src/spatial_ci/embeddings/__init__.py`
- Test: `tests/embeddings/test_artifacts.py`

**Step 1: Write the failing tests**

Add roundtrip and validation tests for:
- valid artifact write/read
- duplicate `observation_id` rejection
- inconsistent embedding dimensionality rejection
- row `sample_id` / metadata required-field validation

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/embeddings/test_artifacts.py -q`
Expected: FAIL because the embedding artifact module does not exist yet.

**Step 3: Write minimal implementation**

Implement:
- `EmbeddingArtifactRow`
- `EmbeddingArtifact`
- `write_embedding_artifact()`
- `read_embedding_artifact()`

Use Parquet row data plus schema metadata, matching the repo’s existing artifact style.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/embeddings/test_artifacts.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add src/spatial_ci/embeddings/artifacts.py src/spatial_ci/embeddings/__init__.py tests/embeddings/test_artifacts.py
git commit -m "feat: add embedding artifact schemas"
```

### Task 2: Add frozen KNN baseline logic

**Files:**
- Create: `src/spatial_ci/baselines/knn.py`
- Test: `tests/baselines/test_knn.py`

**Step 1: Write the failing tests**

Add tests for:
- train-only neighbor pool
- self-neighbor exclusion for train predictions
- fallback to all available train neighbors when `n_train < 20`
- failure when no train rows exist for a scored program

Use small deterministic embeddings where the nearest-neighbor set is obvious.

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/baselines/test_knn.py -q`
Expected: FAIL because `knn.py` does not exist yet.

**Step 3: Write minimal implementation**

Implement a function like:
- `predict_knn_on_embeddings(frame: pl.DataFrame, *, k: int = 20) -> pl.DataFrame`

Requirements:
- require `observation_id`, `sample_id`, `cohort_id`, `split`, `program_name`, `raw_rank_evidence`, and embedding vector columns/data
- use cosine distance
- use only `split == "train"` rows as candidate neighbors
- exclude the query row from its own train prediction
- return long-form predictions with `baseline_name = "knn_on_embeddings"`

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/baselines/test_knn.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add src/spatial_ci/baselines/knn.py tests/baselines/test_knn.py
git commit -m "feat: add frozen knn baseline"
```

### Task 3: Extend baseline runner for embeddings

**Files:**
- Modify: `src/spatial_ci/baselines/runner.py`
- Modify: `src/spatial_ci/baselines/__init__.py`
- Test: `tests/baselines/test_runner.py`

**Step 1: Write the failing tests**

Add tests for:
- successful combined output with mean baselines plus KNN when embeddings are provided
- missing embedding for eligible score row fails
- duplicate embedding `observation_id` fails
- inconsistent embedding dimensionality fails
- no embeddings provided preserves mean-only behavior

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/baselines/test_runner.py -q`
Expected: FAIL because runner does not accept or validate embedding artifacts yet.

**Step 3: Write minimal implementation**

Extend the runner to:
- load optional embedding artifact
- validate one embedding row per `observation_id`
- join embeddings to eligible score rows on `observation_id`
- run KNN only when embeddings are present
- still emit mean baselines without embeddings

Thread embedding source path/hash and artifact metadata only if needed for this slice; avoid widening the baseline prediction artifact unless tests or docs require it.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/baselines/test_runner.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add src/spatial_ci/baselines/runner.py src/spatial_ci/baselines/__init__.py tests/baselines/test_runner.py
git commit -m "feat: add embedding-aware baseline runner"
```

### Task 4: Extend the CLI

**Files:**
- Modify: `scripts/run_baselines.py`
- Test: `tests/baselines/test_run_baselines_cli.py`

**Step 1: Write the failing tests**

Add CLI tests for:
- current mean-only path with no `--embeddings`
- combined mean+KNN path with `--embeddings`
- missing embedding file fails cleanly

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/baselines/test_run_baselines_cli.py -q`
Expected: FAIL because the CLI does not accept `--embeddings` yet.

**Step 3: Write minimal implementation**

Add an optional `--embeddings` argument to `scripts/run_baselines.py` and thread it to the runner.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/baselines/test_run_baselines_cli.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/run_baselines.py tests/baselines/test_run_baselines_cli.py
git commit -m "feat: add embeddings input to baseline cli"
```

### Task 5: Update docs and verify the slice

**Files:**
- Modify: `docs/ARTIFACTS.md`
- Modify: `docs/REPO_SETUP.md`
- Modify: `LOCAL_TODO.md` (local-only, do not commit)

**Step 1: Update docs**

Document:
- embedding artifact minimum shape
- `knn_on_embeddings` frozen semantics
- `scripts/run_baselines.py --embeddings` usage

Do not commit `LOCAL_TODO.md`.

**Step 2: Run targeted verification**

Run:
- `uv run pytest tests/embeddings/test_artifacts.py tests/baselines/test_knn.py tests/baselines/test_runner.py tests/baselines/test_run_baselines_cli.py -q`
- `uv run ruff check src/spatial_ci/embeddings src/spatial_ci/baselines tests/embeddings tests/baselines scripts/run_baselines.py`
- `uv run mypy src/spatial_ci/embeddings src/spatial_ci/baselines tests/embeddings tests/baselines scripts/run_baselines.py`

Expected: PASS

**Step 3: Run broader verification**

Run:
- `uv run pytest -q`

Expected: PASS

**Step 4: Commit**

```bash
git add docs/ARTIFACTS.md docs/REPO_SETUP.md
git commit -m "docs: record knn baseline foundation"
```
