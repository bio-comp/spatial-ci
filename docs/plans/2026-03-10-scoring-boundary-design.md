# Scoring Boundary Design

## Goal

Make the Spatial-CI scoring layer contract-safe and batch-oriented without
inventing a second numeric implementation. R/Bioconductor `singscore` remains
the canonical scoring engine; Python owns API stability, policy enforcement,
packet assembly, and artifact provenance.

## Scope

This design covers the next scoring-boundary slice only:

- stable Python scoring API
- batch-first R-backed bridge
- typed score artifact schema
- explicit failure and drop semantics
- long-form score artifact output
- golden parity fixtures against frozen R output

This design does not include:

- a native Python singscore implementation
- bidirectional signatures in v1
- null calibration, dropout penalties, or spatial smoothing beyond placeholder
  fields
- baseline or evaluation pipelines

## Core Decision

The scoring layer is part of the benchmark contract, not a place to be clever.
The main risks are numeric drift, semantic drift, and fake parity. The safe
boundary is:

- R/Bioconductor `singscore` is the numeric source of truth
- Python is the stable scoring API and policy layer
- parity is proven against frozen R fixtures
- no competing Python math path is added in this slice

## Public Boundary

Primary public API:

- `score_batch(expression_matrix, signatures, scoring_contract, target_definition_id) -> ScoreArtifact`

Secondary convenience wrapper:

- `score_one(...) -> ScorePacket`

The production interface is batch-first because:

- the R bridge amortizes better over matrices than per-observation calls
- parity fixtures are naturally matrix-oriented
- downstream scoring artifacts are produced in batches

`score_one()` must delegate to `score_batch()` and must not introduce a second
bridge path.

## Row Grain

The canonical score row is:

- `observation_id x program_name`

`sample_id` is optional parent metadata, not the primary grain. This avoids
confusing spot-level outputs with whole-sample outputs in Visium-style data.

## Component Layout

- `src/spatial_ci/scoring/singscore.py`
  - public batch-first API
  - stable Python boundary
  - no canonical math implementation
- `src/spatial_ci/scoring/artifacts.py`
  - `ScoreStatus`
  - `ScoreFailureCode`
  - `ScorePacket`
  - `ScoreArtifact`
  - provenance helpers
- `src/spatial_ci/scoring/r_bridge.py`
  - deterministic temp-workdir handoff
  - writes bridge input artifacts
  - invokes `Rscript`
  - reads long-form score output
  - maps bridge failures into Python-visible failures
- `scripts/score_targets.R`
  - canonical numeric scorer
  - consumes explicit bridge inputs
  - computes raw singscore values and matched-gene counts
  - emits one long-form score file

## Schema Design

### ScorePacket

`ScorePacket` is row-like and intentionally boring.

Required fields:

- `observation_id`
- `sample_id: str | None`
- `slide_id: str | None`
- `program_name`
- `status`
- `raw_rank_evidence`
- `signature_size_declared`
- `signature_size_matched`
- `signature_coverage`
- `dropped_by_missingness_rule`
- `failure_code`
- `null_calibrated_score`
- `dropout_penalty`
- `spatial_consistency`

Notes:

- `status` is first-class: `OK`, `DROPPED`, `FAILED`
- `failure_code` is meaningful only when `status != OK`
- `null_calibrated_score`, `dropout_penalty`, and `spatial_consistency` stay
  `None` in v1
- `matched_gene_ids` may be emitted only in debug mode for parity/debug work,
  not in canonical production artifacts

### ScoreArtifact

`ScoreArtifact` carries collection-level metadata and provenance, not repeated
row payload.

Required fields:

- `target_definition_id`
- `scoring_contract_id`
- `signature_direction`
- `bridge_contract_version`
- `generated_at`
- `run_id`
- `r_version`
- `singscore_version`
- `renv_lock_hash`
- `scoring_script_path`
- `scoring_script_hash`
- `source_expression_artifact_hash: str | None`
- `source_manifest_id: str | None`
- `packets`

Artifact-level metadata stays here even if downstream exports later denormalize
some fields into Parquet columns.

## Ownership Boundary

R owns:

- raw `singscore` numeric output
- matched-gene counting per `observation_id x program_name`
- rank and tie semantics

Python owns:

- signature parsing and validation
- directionality support policy
- missingness policy interpretation
- status and failure-code assignment
- packet assembly
- artifact serialization
- provenance attachment

This is the stable split:

- numeric truth in R
- benchmark-policy truth in Python

## Directionality Policy

Spatial-CI v1 supports up-only signatures only.

Rules:

- if a signature has `down_genes`, Python treats it as unsupported for v1
- internal logic records a request-level unsupported-direction failure
- exported artifacts may materialize row-level failed packets for rectangular
  completeness if needed
- `signature_direction` is explicit in the artifact even when all signatures are
  up-only

## Bridge Contract

Python writes exactly three bridge inputs:

- `expression_input.csv`
- `signature_input.json`
- `scoring_request.json`

R writes exactly one bridge output:

- `score_output.parquet`

`scoring_request.json` must include at least:

- `bridge_contract_version`
- `target_definition_id`
- `scoring_contract_id`
- `debug_mode`

The bridge workdir should be deterministic in structure and fully inspectable.

## Missingness Policy

R reports numeric score output and matched-gene counts.

Python interprets policy:

- compute `signature_coverage`
- compare matched genes to declared signature size
- mark rows `DROPPED` when the missingness rule is violated
- distinguish zero-match from low-coverage cases

Recommended failure/drop semantics:

- `DROPPED + EMPTY_SIGNATURE_MATCH`
- `DROPPED + LOW_SIGNATURE_COVERAGE`
- `FAILED + UNSUPPORTED_DIRECTIONALITY`
- `FAILED + INVALID_EXPRESSION_INPUT`
- `FAILED + R_SUBPROCESS_ERROR`
- `FAILED + INVALID_SCORER_OUTPUT`

## Error Semantics

### Python-side input errors

- empty expression matrix
- duplicate `observation_id`
- nonnumeric expression values

These should be rejected before invoking R and surfaced as
`INVALID_EXPRESSION_INPUT`.

### Bridge failures

- `R_SUBPROCESS_ERROR`
  - `Rscript` crashes, exits nonzero, or cannot be invoked
- `INVALID_SCORER_OUTPUT`
  - R runs but output is missing required columns, malformed, or inconsistent

Separating these failure modes matters for debugging the boundary cleanly.

## Canonical Artifact Format

Canonical production output is long-form Parquet with one row per
`observation_id x program_name`.

The typed Python `ScoreArtifact` is the in-memory representation. Downstream
evaluation should consume score artifacts, not re-run scoring logic.

## Test Strategy

The first implementation slice must include:

1. Golden parity fixture test against frozen R output artifact
2. Long-form row-schema test at `observation_id x program_name`
3. Missingness and status-mapping test
4. Subprocess-failure mapping test
5. `score_one()` delegation test
6. Duplicate `observation_id` rejection test

Success means:

- the same frozen inputs always produce the same score artifact
- Python policy decisions are reproducible and visible
- bridge failures and malformed scorer output are distinguishable
- downstream consumers never need to know how R was invoked

## Implementation Order

1. Freeze schemas and exported scoring API
2. Freeze bridge contract files
3. Implement failing tests for artifacts and bridge errors
4. Update the R scorer to emit long-form Parquet
5. Implement Python bridge and batch API
6. Add golden parity fixtures and debug-mode coverage

## Open Constraints

- `score_output.parquet` assumes R-side Parquet support via `arrow`
- canonical artifacts stay lean; debug-only matched-gene IDs are optional
- no native Python scorer should be introduced until the R-backed parity layer
  is stable and benchmarked
