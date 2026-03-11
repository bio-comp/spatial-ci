# Scoring Boundary R Bridge Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a batch-first, R-authoritative `singscore` boundary that emits typed long-form score artifacts with explicit status, failure, and provenance semantics.

**Architecture:** Python remains the contract-facing layer and owns validation, policy interpretation, packet assembly, and provenance. R/Bioconductor `singscore` remains the numeric source of truth, invoked through a deterministic file-based bridge that returns one long-form Parquet artifact.

**Tech Stack:** Python 3.13, Pydantic v2, `subprocess`, `pyarrow`, R `singscore`, R `jsonlite`, R `arrow`, `pytest`, `uv`

---

### Task 1: Freeze artifact schemas

**Files:**
- Create: `src/spatial_ci/scoring/artifacts.py`
- Modify: `src/spatial_ci/scoring/api.py`
- Modify: `src/spatial_ci/scoring/__init__.py`
- Modify: `tests/scoring/test_packet.py`
- Create: `tests/scoring/test_artifacts.py`

**Step 1: Write the failing test**

```python
from spatial_ci.scoring.artifacts import (
    ScoreArtifact,
    ScoreFailureCode,
    ScorePacket,
    ScoreStatus,
)


def test_score_packet_requires_observation_grain() -> None:
    packet = ScorePacket(
        observation_id="obs-1",
        sample_id="sample-1",
        slide_id="slide-1",
        program_name="HALLMARK_HYPOXIA",
        status=ScoreStatus.OK,
        raw_rank_evidence=0.25,
        signature_size_declared=4,
        signature_size_matched=4,
        signature_coverage=1.0,
        dropped_by_missingness_rule=False,
        failure_code=None,
        null_calibrated_score=None,
        dropout_penalty=None,
        spatial_consistency=None,
    )
    assert packet.observation_id == "obs-1"


def test_score_artifact_keeps_provenance_off_rows() -> None:
    artifact = ScoreArtifact(
        target_definition_id="breast_visium_hallmarks_v1",
        scoring_contract_id="singscore_r_v1",
        signature_direction="up_only",
        bridge_contract_version="v1",
        generated_at="2026-03-10T00:00:00Z",
        run_id="run-1",
        r_version="4.4.0",
        singscore_version="1.30.0",
        renv_lock_hash="abc123",
        scoring_script_path="scripts/score_targets.R",
        scoring_script_hash="def456",
        source_expression_artifact_hash=None,
        source_manifest_id=None,
        packets=(),
    )
    assert artifact.bridge_contract_version == "v1"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/scoring/test_artifacts.py tests/scoring/test_packet.py -q`
Expected: FAIL with `ModuleNotFoundError` for `spatial_ci.scoring.artifacts` or schema mismatches against the old packet model.

**Step 3: Write minimal implementation**

```python
class ScoreStatus(str, Enum):
    OK = "ok"
    DROPPED = "dropped"
    FAILED = "failed"


class ScoreFailureCode(str, Enum):
    LOW_SIGNATURE_COVERAGE = "low_signature_coverage"
    EMPTY_SIGNATURE_MATCH = "empty_signature_match"
    UNSUPPORTED_DIRECTIONALITY = "unsupported_directionality"
    R_SUBPROCESS_ERROR = "r_subprocess_error"
    INVALID_SCORER_OUTPUT = "invalid_scorer_output"
    INVALID_EXPRESSION_INPUT = "invalid_expression_input"


class ScorePacket(BaseModel):
    observation_id: str
    sample_id: str | None = None
    slide_id: str | None = None
    program_name: str
    status: ScoreStatus
    raw_rank_evidence: float | None = None
    signature_size_declared: int
    signature_size_matched: int
    signature_coverage: float
    dropped_by_missingness_rule: bool
    failure_code: ScoreFailureCode | None = None
    null_calibrated_score: float | None = None
    dropout_penalty: float | None = None
    spatial_consistency: float | None = None
    matched_gene_ids: tuple[str, ...] | None = None


class ScoreArtifact(BaseModel):
    target_definition_id: str
    scoring_contract_id: str
    signature_direction: str
    bridge_contract_version: str
    generated_at: str
    run_id: str
    r_version: str
    singscore_version: str
    renv_lock_hash: str
    scoring_script_path: str
    scoring_script_hash: str
    source_expression_artifact_hash: str | None = None
    source_manifest_id: str | None = None
    packets: tuple[ScorePacket, ...]
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/scoring/test_artifacts.py tests/scoring/test_packet.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/scoring/test_artifacts.py tests/scoring/test_packet.py src/spatial_ci/scoring/artifacts.py src/spatial_ci/scoring/api.py src/spatial_ci/scoring/__init__.py
git commit -m "feat: add scoring artifact schemas"
```

### Task 2: Freeze the R bridge contract

**Files:**
- Create: `src/spatial_ci/scoring/r_bridge.py`
- Create: `tests/scoring/test_r_bridge.py`
- Modify: `scripts/score_targets.R`

**Step 1: Write the failing test**

```python
from pathlib import Path

from spatial_ci.scoring.r_bridge import BridgePaths, build_bridge_paths


def test_bridge_paths_are_explicit_and_stable(tmp_path: Path) -> None:
    paths = build_bridge_paths(tmp_path)
    assert paths.expression_input.name == "expression_input.csv"
    assert paths.signature_input.name == "signature_input.json"
    assert paths.scoring_request.name == "scoring_request.json"
    assert paths.score_output.name == "score_output.parquet"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/scoring/test_r_bridge.py::test_bridge_paths_are_explicit_and_stable -q`
Expected: FAIL with `ModuleNotFoundError` for `spatial_ci.scoring.r_bridge`.

**Step 3: Write minimal implementation**

```python
@dataclass(frozen=True)
class BridgePaths:
    expression_input: Path
    signature_input: Path
    scoring_request: Path
    score_output: Path


def build_bridge_paths(workdir: Path) -> BridgePaths:
    return BridgePaths(
        expression_input=workdir / "expression_input.csv",
        signature_input=workdir / "signature_input.json",
        scoring_request=workdir / "scoring_request.json",
        score_output=workdir / "score_output.parquet",
    )
```

**Step 4: Expand tests for bridge failures**

```python
def test_nonzero_r_exit_maps_to_subprocess_error(...) -> None:
    ...


def test_missing_required_output_column_maps_to_invalid_output(...) -> None:
    ...
```

Run: `uv run pytest tests/scoring/test_r_bridge.py -q`
Expected: FAIL until subprocess and output validation logic exist.

**Step 5: Implement bridge execution and validation**

```python
completed = subprocess.run(
    ["Rscript", "scripts/score_targets.R", str(paths.expression_input), str(paths.signature_input), str(paths.scoring_request), str(paths.score_output)],
    cwd=repo_root,
    capture_output=True,
    text=True,
    check=False,
)

if completed.returncode != 0:
    raise RSubprocessError(completed.stderr)

table = pq.read_table(paths.score_output)
required = {"observation_id", "program_name", "raw_rank_evidence", "signature_size_matched"}
if not required.issubset(table.schema.names):
    raise InvalidScorerOutputError(required - set(table.schema.names))
```

**Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/scoring/test_r_bridge.py -q`
Expected: PASS

**Step 7: Commit**

```bash
git add tests/scoring/test_r_bridge.py src/spatial_ci/scoring/r_bridge.py scripts/score_targets.R
git commit -m "feat: add explicit singscore bridge contract"
```

### Task 3: Implement batch-first scoring API

**Files:**
- Modify: `src/spatial_ci/scoring/singscore.py`
- Modify: `src/spatial_ci/scoring/api.py`
- Modify: `src/spatial_ci/scoring/__init__.py`
- Create: `tests/scoring/test_singscore_adapter.py`
- Modify: `tests/scoring/test_public_api.py`

**Step 1: Write the failing test**

```python
from spatial_ci.scoring import score_batch, score_one
from spatial_ci.signatures import GeneSignature


def test_score_one_delegates_to_score_batch(monkeypatch) -> None:
    calls = []

    def fake_score_batch(**kwargs):
        calls.append(kwargs)
        return fake_artifact_with_single_packet()

    monkeypatch.setattr("spatial_ci.scoring.singscore.score_batch", fake_score_batch)

    packet = score_one(
        observation_id="obs-1",
        expression_by_gene={"CA9": 5.0, "VEGFA": 4.0},
        signature=GeneSignature(name="HALLMARK_HYPOXIA", up_genes=("CA9", "VEGFA")),
        scoring_contract_id="singscore_r_v1",
        target_definition_id="breast_visium_hallmarks_v1",
    )

    assert packet.observation_id == "obs-1"
    assert len(calls) == 1
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/scoring/test_singscore_adapter.py::test_score_one_delegates_to_score_batch -q`
Expected: FAIL because `score_batch` does not exist.

**Step 3: Write minimal implementation**

```python
def score_batch(
    *,
    expression_matrix: Mapping[str, Mapping[str, float]],
    signatures: Sequence[GeneSignature],
    scoring_contract_id: str,
    target_definition_id: str,
    ...
) -> ScoreArtifact:
    validate_expression_matrix(expression_matrix)
    validate_signatures(signatures)
    bridge_output = run_r_scorer(...)
    packets = assemble_packets(...)
    return ScoreArtifact(..., packets=tuple(packets))


def score_one(... ) -> ScorePacket:
    artifact = score_batch(
        expression_matrix={observation_id: expression_by_gene},
        signatures=(signature,),
        scoring_contract_id=scoring_contract_id,
        target_definition_id=target_definition_id,
        ...
    )
    return artifact.packets[0]
```

**Step 4: Add failing tests for status mapping**

```python
def test_empty_signature_match_becomes_dropped_packet() -> None:
    ...


def test_duplicate_observation_ids_raise_invalid_expression_input() -> None:
    ...


def test_down_genes_become_unsupported_directionality_failures() -> None:
    ...
```

Run: `uv run pytest tests/scoring/test_singscore_adapter.py tests/scoring/test_public_api.py -q`
Expected: FAIL until packet assembly and validation are implemented.

**Step 5: Implement packet assembly and policy logic**

```python
if signature.down_genes:
    return failed_packets_for_program(..., failure_code=ScoreFailureCode.UNSUPPORTED_DIRECTIONALITY)

coverage = matched / declared
if matched == 0:
    status = ScoreStatus.DROPPED
    failure = ScoreFailureCode.EMPTY_SIGNATURE_MATCH
elif coverage < (1 - missing_gene_threshold):
    status = ScoreStatus.DROPPED
    failure = ScoreFailureCode.LOW_SIGNATURE_COVERAGE
else:
    status = ScoreStatus.OK
    failure = None
```

**Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/scoring/test_singscore_adapter.py tests/scoring/test_public_api.py -q`
Expected: PASS

**Step 7: Commit**

```bash
git add tests/scoring/test_singscore_adapter.py tests/scoring/test_public_api.py src/spatial_ci/scoring/singscore.py src/spatial_ci/scoring/api.py src/spatial_ci/scoring/__init__.py
git commit -m "feat: add batch-first singscore adapter"
```

### Task 4: Convert the R scorer to long-form artifact output

**Files:**
- Modify: `scripts/score_targets.R`
- Create: `tests/golden/fixtures/singscore/expression_input.csv`
- Create: `tests/golden/fixtures/singscore/signature_input.json`
- Create: `tests/golden/fixtures/singscore/scoring_request.json`

**Step 1: Write the failing golden test**

```python
from pathlib import Path

from spatial_ci.scoring.r_bridge import run_r_bridge


def test_r_bridge_reads_long_form_parquet_fixture(tmp_path: Path) -> None:
    artifact = run_r_bridge(
        expression_input=Path("tests/golden/fixtures/singscore/expression_input.csv"),
        signature_input=Path("tests/golden/fixtures/singscore/signature_input.json"),
        scoring_request=Path("tests/golden/fixtures/singscore/scoring_request.json"),
    )
    assert {packet.program_name for packet in artifact.packets} == {"HALLMARK_HYPOXIA"}
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/golden/test_singscore_parity.py -q`
Expected: FAIL because the R script still writes a wide CSV and the fixture set does not exist.

**Step 3: Update the R script**

```r
args <- commandArgs(trailingOnly = TRUE)
expression_input <- args[[1]]
signature_input <- args[[2]]
scoring_request <- args[[3]]
score_output <- args[[4]]

expr <- read.csv(expression_input, row.names = 1, check.names = FALSE)
signatures <- jsonlite::fromJSON(signature_input, simplifyVector = TRUE)
request <- jsonlite::fromJSON(scoring_request, simplifyVector = TRUE)

rows <- list()
for (program_name in names(signatures)) {
  genes <- signatures[[program_name]][["up_genes"]]
  present <- intersect(genes, rownames(expr))
  scores <- singscore::simpleScore(expr[present, , drop = FALSE], upSet = present, centerScore = FALSE)$TotalScore
  rows[[length(rows) + 1]] <- data.frame(
    observation_id = colnames(expr),
    program_name = program_name,
    raw_rank_evidence = scores,
    signature_size_matched = length(present)
  )
}

out <- do.call(rbind, rows)
arrow::write_parquet(out, score_output)
```

**Step 4: Run the golden test**

Run: `uv run pytest tests/golden/test_singscore_parity.py -q`
Expected: PASS once the fixtures and long-form output line up.

**Step 5: Commit**

```bash
git add scripts/score_targets.R tests/golden/fixtures/singscore/expression_input.csv tests/golden/fixtures/singscore/signature_input.json tests/golden/fixtures/singscore/scoring_request.json tests/golden/test_singscore_parity.py
git commit -m "feat: emit long-form singscore parquet artifacts"
```

### Task 5: Prove parity and round-trip artifact behavior

**Files:**
- Modify: `tests/golden/test_singscore_parity.py`
- Create: `tests/golden/test_score_artifact_roundtrip.py`
- Modify: `docs/scoring.md`

**Step 1: Write the failing parity and round-trip tests**

```python
def test_python_bridge_matches_frozen_r_fixture() -> None:
    artifact = score_batch(...)
    packet = only_packet(artifact)
    assert packet.raw_rank_evidence == pytest.approx(0.25, abs=1e-12)


def test_score_artifact_roundtrip_preserves_status_and_provenance(tmp_path: Path) -> None:
    artifact = score_batch(...)
    write_score_artifact(artifact, tmp_path / "score_output.parquet")
    reloaded = read_score_artifact(tmp_path / "score_output.parquet")
    assert reloaded.packets == artifact.packets
    assert reloaded.bridge_contract_version == artifact.bridge_contract_version
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/golden/test_singscore_parity.py tests/golden/test_score_artifact_roundtrip.py -q`
Expected: FAIL until fixture expectations and artifact read/write helpers exist.

**Step 3: Implement fixture assertions and artifact IO helpers**

```python
def write_score_artifact(artifact: ScoreArtifact, path: Path) -> None:
    table = pa.Table.from_pylist([...])
    pq.write_table(table, path)


def read_score_artifact(path: Path) -> ScoreArtifact:
    table = pq.read_table(path)
    ...
```

**Step 4: Run focused then full verification**

Run: `uv run pytest tests/golden/test_singscore_parity.py tests/golden/test_score_artifact_roundtrip.py -q`
Expected: PASS

Run: `uv run ruff check .`
Expected: PASS

Run: `uv run mypy src tests scripts/build_manifest.py`
Expected: PASS

Run: `uv run pytest -q`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/golden/test_singscore_parity.py tests/golden/test_score_artifact_roundtrip.py docs/scoring.md src/spatial_ci/scoring/artifacts.py src/spatial_ci/scoring/r_bridge.py src/spatial_ci/scoring/singscore.py
git commit -m "test: prove singscore bridge parity"
```
