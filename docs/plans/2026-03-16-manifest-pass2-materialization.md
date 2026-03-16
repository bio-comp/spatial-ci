# Manifest Pass-2 Materialization Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the full pass-2 manifest materialization path: resolver config, artifact probing, SHA256 hashing, rejection ledger output, and final manifest serialization behind the existing `build_manifest.py` CLI.

**Architecture:** Extend the pass-1 manifest pipeline with a package-owned pass-2 orchestration layer. Implement resolver logic, validation, hashing, rejection accounting, and final row materialization as separate small modules, then compose them in `pipeline.py` and keep the CLI thin.

**Tech Stack:** Python 3.13, Pydantic, Polars, Click, pytest, Ruff, mypy

---

### Task 1: Extend Manifest Config for Pass 2

**Files:**
- Modify: `src/spatial_ci/manifest/config.py`
- Test: `tests/manifest/test_config.py`
- Fixture: `tests/fixtures/manifest/pass2/config_materialize.yaml`

**Step 1: Write the failing test**

Add a test that loads a pass-2 config fixture and asserts:
- resolver sample roots are parsed
- optional sample path field is parsed
- artifact candidate lists are parsed
- manifest ID and alignment contract ID are parsed

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/manifest/test_config.py -q`
Expected: FAIL because pass-2 config fields are not defined yet.

**Step 3: Write minimal implementation**

Add config models for:
- resolver settings
- artifact candidate settings
- manifest output settings

Keep the existing pass-1 config shape intact.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/manifest/test_config.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add src/spatial_ci/manifest/config.py tests/manifest/test_config.py tests/fixtures/manifest/pass2/config_materialize.yaml
git commit -m "feat: add manifest pass-2 config models"
```

### Task 2: Add Pass-2 Artifact and Rejection Models

**Files:**
- Modify: `src/spatial_ci/manifest/artifacts.py`
- Test: `tests/manifest/test_artifacts.py`

**Step 1: Write the failing test**

Add tests for:
- resolved artifact model validation
- rejection row / rejection ledger models
- materialized manifest row model validation

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/manifest/test_artifacts.py -q`
Expected: FAIL because the new models do not exist yet.

**Step 3: Write minimal implementation**

Add models for:
- `ResolvedArtifact`
- `RejectionRow`
- `RejectionLedgerArtifact`
- `MaterializedManifestRow`
- `MaterializedManifestArtifact`

Keep field names aligned with the docs and existing provenance schemas.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/manifest/test_artifacts.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add src/spatial_ci/manifest/artifacts.py tests/manifest/test_artifacts.py
git commit -m "feat: add manifest pass-2 artifact models"
```

### Task 3: Implement Sample-Root Resolution and Artifact Probing

**Files:**
- Create: `src/spatial_ci/manifest/resolver.py`
- Test: `tests/manifest/test_resolver.py`
- Fixtures:
  - `tests/fixtures/manifest/pass2/sample-tree/**`
  - `tests/fixtures/manifest/pass2/config_materialize.yaml`

**Step 1: Write the failing test**

Add tests for:
- explicit per-row sample path field resolution
- fallback root search by `sample_id`
- ordered candidate probing for required artifacts
- optional derived-expression resolution
- rejection-ready failure when a required artifact cannot be resolved

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/manifest/test_resolver.py -q`
Expected: FAIL because resolver logic does not exist yet.

**Step 3: Write minimal implementation**

Implement:
- sample-root resolution
- ordered candidate probing per artifact class
- required vs optional artifact handling

Return explicit resolved-artifact records instead of raw strings.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/manifest/test_resolver.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add src/spatial_ci/manifest/resolver.py tests/manifest/test_resolver.py tests/fixtures/manifest/pass2
git commit -m "feat: add manifest artifact resolver"
```

### Task 4: Add Pre-Hash Validation and SHA256 Hashing

**Files:**
- Create: `src/spatial_ci/manifest/validation.py`
- Create: `src/spatial_ci/manifest/hashing.py`
- Test:
  - `tests/manifest/test_validation.py`
  - `tests/manifest/test_hashing.py`

**Step 1: Write the failing tests**

Add tests for:
- rejecting raw/derived path conflation
- rejecting duplicate required artifact paths
- rejecting missing required IDs before hashing
- chunked SHA256 hashing returning stable values for fixture files

**Step 2: Run tests to verify they fail**

Run:
- `uv run pytest tests/manifest/test_validation.py -q`
- `uv run pytest tests/manifest/test_hashing.py -q`
Expected: FAIL because validation/hashing helpers do not exist yet.

**Step 3: Write minimal implementation**

Implement:
- pre-hash validation helpers
- chunked SHA256 helper
- provenance object construction from resolved artifacts

**Step 4: Run tests to verify they pass**

Run:
- `uv run pytest tests/manifest/test_validation.py -q`
- `uv run pytest tests/manifest/test_hashing.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add src/spatial_ci/manifest/validation.py src/spatial_ci/manifest/hashing.py tests/manifest/test_validation.py tests/manifest/test_hashing.py
git commit -m "feat: add manifest validation and hashing helpers"
```

### Task 5: Materialize Final Manifest and Rejection Ledger

**Files:**
- Create: `src/spatial_ci/manifest/materialize.py`
- Modify: `src/spatial_ci/manifest/pipeline.py`
- Test: `tests/manifest/test_materialize.py`
- Fixtures:
  - `tests/fixtures/manifest/pass2/metadata_materialize.csv`
  - `tests/fixtures/manifest/pass2/config_materialize.yaml`

**Step 1: Write the failing test**

Add tests for:
- clean materialization writes final manifest only
- missing required artifact writes rejection ledger and raises by default
- `allow_missing=True` writes rejection ledger and a partial final manifest
- final manifest is sorted by `split`, `cohort_id`, `sample_id`

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/manifest/test_materialize.py -q`
Expected: FAIL because pass-2 materialization does not exist yet.

**Step 3: Write minimal implementation**

Implement:
- pass-2 orchestration over pass-1 rows
- complete rejection collection before policy decision
- deterministic Parquet writes for manifest and rejection ledger
- `materialize_manifest(...)` entry point

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/manifest/test_materialize.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add src/spatial_ci/manifest/materialize.py src/spatial_ci/manifest/pipeline.py tests/manifest/test_materialize.py tests/fixtures/manifest/pass2/metadata_materialize.csv tests/fixtures/manifest/pass2/config_materialize.yaml
git commit -m "feat: add manifest pass-2 materialization"
```

### Task 6: Wire the CLI Through Both Passes

**Files:**
- Modify: `scripts/build_manifest.py`
- Test: `tests/manifest/test_build_manifest_cli.py`

**Step 1: Write the failing test**

Add CLI tests for:
- clean end-to-end run writes `manifest.assignments.parquet` and final manifest
- pass-2 rejection writes `manifest.rejections.parquet` and exits nonzero
- `--allow-missing` writes final manifest plus rejection ledger and exits zero with warning text

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/manifest/test_build_manifest_cli.py -q`
Expected: FAIL because the CLI still only drives pass 1.

**Step 3: Write minimal implementation**

Update the CLI to:
- write assignments to `output.with_suffix(".assignments.parquet")`
- run pass 2 on the pass-1 result
- keep leakage fatal
- surface pass-2 rejection behavior as Click errors/warnings

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/manifest/test_build_manifest_cli.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/build_manifest.py tests/manifest/test_build_manifest_cli.py
git commit -m "feat: wire manifest cli through pass-2 materialization"
```

### Task 7: Update Docs and Package Exports

**Files:**
- Modify: `src/spatial_ci/manifest/__init__.py`
- Modify: `docs/MANIFEST_PIPELINE.md`
- Modify: `docs/CONTRACTS.md`

**Step 1: Write the failing test or assertion**

For docs-heavy work, use a targeted grep/assertion step:
- verify `docs/MANIFEST_PIPELINE.md` and `docs/CONTRACTS.md` mention:
  - pass-2 rejection ledger
  - `test_external`
  - Parquet output names

**Step 2: Run check to verify it fails or is stale**

Run:
- `rg -n "rejection ledger|manifest.rejections.parquet|test_external" docs/MANIFEST_PIPELINE.md docs/CONTRACTS.md`
Expected: missing or stale wording before edits.

**Step 3: Write minimal implementation**

Update docs to match the landed pass-2 behavior and export any new manifest types/functions from `__init__.py`.

**Step 4: Run check to verify it passes**

Run:
- `rg -n "rejection ledger|manifest.rejections.parquet|test_external" docs/MANIFEST_PIPELINE.md docs/CONTRACTS.md`
Expected: the expected phrases are present and aligned.

**Step 5: Commit**

```bash
git add src/spatial_ci/manifest/__init__.py docs/MANIFEST_PIPELINE.md docs/CONTRACTS.md
git commit -m "docs: align manifest docs with pass-2 materialization"
```

### Task 8: Final Verification

**Files:**
- Modify only if needed to fix breakage found in verification

**Step 1: Run targeted manifest/scoring checks**

Run:
- `uv run pytest tests/manifest -q`
- `uv run pytest tests/golden/test_singscore_parity.py tests/scoring/test_r_bridge.py -q`
- `uv run ruff check src/spatial_ci/manifest tests/manifest scripts/build_manifest.py`
- `uv run mypy src/spatial_ci/manifest tests/manifest scripts/build_manifest.py`

Expected: PASS

**Step 2: Run full repo verification**

Run:
- `uv run ruff check .`
- `uv run pytest -q`

Expected: PASS

**Step 3: Note known repo-wide mypy baseline**

Run:
- `uv run mypy src tests scripts/build_manifest.py`

Expected: still fails only on the pre-existing unrelated Hypothesis decorator issue in `tests/contracts/test_definitions.py` unless separately fixed.

**Step 4: Commit any final fixes**

If verification required fixes:

```bash
git add <fixed files>
git commit -m "fix: close manifest pass-2 verification gaps"
```

If no fixes were needed, do not create an empty commit.
