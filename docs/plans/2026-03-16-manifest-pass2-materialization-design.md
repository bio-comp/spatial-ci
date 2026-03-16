# Manifest Pass-2 Materialization Design

## Summary

Spatial-CI pass 2 turns pass-1 split assignments into a deterministic, hashed,
validated final manifest with explicit rejection accounting.

This slice lands the whole pass-2 path in one PR:
- resolver config and artifact probing
- pre-hash validation
- SHA256 provenance hashing
- rejection ledger output
- final manifest materialization
- CLI wiring through `scripts/build_manifest.py`

The design keeps the CLI thin and puts the materialization logic under
`src/spatial_ci/manifest/`.

## Goals

- Materialize a final manifest from pass-1 split assignments plus physical files.
- Probe required artifacts independently instead of assuming one fixed layout.
- Record every failed sample in a rejection ledger.
- Halt by default on any rejection, with `--allow-missing` as an explicit escape
  hatch.
- Serialize deterministic Parquet outputs for assignments, rejections, and the
  final manifest.

## Non-Goals

- No new cohort filtering or vocabulary normalization work in pass 2.
- No baseline or evaluation work.
- No notebook helpers or one-off conversion tools.
- No schema redesign beyond what pass-2 materialization requires.

## Architecture

Pass 2 is built in the same order the contract requires:

1. resolver configuration and artifact-by-artifact probing
2. pre-hash validation and SHA256 hashing
3. rejection ledger and final manifest emission

This all lands in one PR, but the implementation is still layered so each seam
is testable and the runtime behavior stays explicit.

### Modules

- `src/spatial_ci/manifest/config.py`
  - extend config models for pass-2 resolver/materialization settings
- `src/spatial_ci/manifest/artifacts.py`
  - add resolved-artifact, rejection-ledger, and materialized-manifest models
- `src/spatial_ci/manifest/resolver.py`
  - sample-root resolution and independent artifact probing
- `src/spatial_ci/manifest/validation.py`
  - pre-hash validation and final row validation helpers
- `src/spatial_ci/manifest/hashing.py`
  - chunked SHA256 helpers and provenance construction
- `src/spatial_ci/manifest/materialize.py`
  - pass-2 orchestration from assignments to outputs
- `src/spatial_ci/manifest/pipeline.py`
  - composition point for pass 1 + pass 2
- `scripts/build_manifest.py`
  - thin orchestration over both passes

## Config Design

Pass 2 extends the existing manifest build config rather than introducing a
second file.

### Resolver config

- `sample_roots: list[Path]`
  - declared base directories to search for sample roots
- `sample_path_field: str | None`
  - optional metadata column carrying an explicit sample directory or sample root
- `artifact_candidates`
  - ordered candidate paths for:
    - `image`
    - `spatial_coords`
    - `scalefactors`
    - `raw_expression`
    - optional `derived_expression`

### Manifest config

- `manifest_id: str`
- `alignment_contract_id: str`
- optional static metadata defaults attached to every final manifest row

The existing split config remains unchanged.

## Pass-2 Inputs

Pass 2 consumes:

- the pass-1 split-assignment artifact
- the normalized/resolved staging frame used to build assignments
- resolver/materialization config

This is necessary because pass 2 may need extra metadata columns for sample-root
resolution even though the pass-1 artifact itself stays intentionally small.

## Resolver Behavior

### Sample root resolution

Resolve a sample root using one of:

1. explicit per-row path field, if configured
2. otherwise search declared `sample_roots` for a directory named by `sample_id`

This assumption is frozen in config instead of being hidden in code.

### Artifact probing

Probe each artifact independently using ordered candidate paths from config.

Required artifacts:
- image
- spatial coordinates
- scalefactors
- raw expression

Optional artifact:
- derived expression

Do not infer one artifact path from another.

## Validation and Hashing

### Pre-hash validation

Before hashing, each candidate row must confirm:

- required IDs are present
- resolved sample root exists
- each required artifact exists
- raw and derived expression are distinct
- image / coords / scalefactors / raw expression are distinct paths
- split/cohort/sample values remain coherent with pass-1 assignments

### Hashing

- use SHA256
- hash required artifacts always
- hash derived expression only if present
- build provenance objects after hashing succeeds

## Rejection Policy

Any failure in:

- sample-root resolution
- required artifact resolution
- pre-hash validation
- final manifest row schema validation

becomes one rejection-ledger row.

The pipeline continues through all assigned samples so the rejection ledger is
complete.

### Default behavior

- write rejection ledger if any rows were rejected
- halt after writing it

### `--allow-missing`

- still write rejection ledger
- still warn visibly in the CLI
- write final manifest with accepted rows only

No empty rejection ledger is written when there are no rejections.

## Output Shapes

All outputs remain Parquet.

Given `--output manifest.parquet`, the pipeline writes:

- `manifest.assignments.parquet`
- `manifest.assignments.leakage.parquet` on pass-1 overlap only
- `manifest.rejections.parquet` when any pass-2 rejection exists
- `manifest.parquet` for accepted final rows

### Final manifest row grain

`sample_id`

### Final row fields

- `sample_id`
- `cohort_id`
- `split`
- `resolved_patient_id`
- `patient_id_source`
- optional `resolved_specimen_id`
- optional `resolved_slide_id`
- artifact provenance for:
  - image
  - spatial coords
  - scalefactors
  - raw expression
  - optional derived expression
- explicit metadata block

### Rejection ledger row fields

- `sample_id`
- `cohort_id`
- `split`
- `reason`
- optional `details`

## CLI Contract

`scripts/build_manifest.py` stays the only entry point for this slice.

Flags remain:
- `--config`
- `--output`
- `--allow-missing`

Behavior:

1. run pass 1 and write assignments
2. halt immediately on leakage after writing the leakage report
3. otherwise run pass 2
4. write rejection ledger when needed
5. write final manifest only when allowed by the rejection policy

## Testing Strategy

Required test areas:

- resolver candidate fallback behavior
- sample-root resolution from explicit path field and from root search
- pre-hash validation failure paths
- raw vs derived artifact distinction
- chunked SHA256 hashing
- rejection ledger writing and default fatal behavior
- `--allow-missing` escape hatch
- final manifest row/schema validation
- deterministic output sorting and path naming

## Acceptance Criteria

- clean fixtures produce assignments + final manifest with no rejection ledger
- missing required artifacts produce a rejection ledger and fatal exit by default
- `--allow-missing` produces a warning, a rejection ledger, and a partial final
  manifest
- final manifest rows contain distinct provenance for image, spatial coords,
  scalefactors, raw expression, and optional derived expression
- outputs are sorted and deterministic

## Risks and Controls

### Risk: hidden layout assumptions
Control:
- keep sample-root resolution and artifact candidates explicit in config

### Risk: expensive work before obvious failures
Control:
- pre-hash validation runs before hashing

### Risk: silent attrition
Control:
- rejection ledger is mandatory whenever rejections occur

### Risk: provenance ambiguity
Control:
- raw and derived expression remain separate artifact fields

## Recommended PR Scope

One PR, one integrated pass-2 slice:

- config expansion
- resolver/probing
- hashing
- rejection ledger
- final manifest materialization
- CLI wiring
- fixtures/tests/docs updates
