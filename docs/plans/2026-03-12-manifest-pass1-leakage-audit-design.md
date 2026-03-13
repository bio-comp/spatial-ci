# Manifest Pass 1 Leakage Audit Design

## Summary

The second manifest PR should add leakage auditing on top of the frozen split-assignment artifact produced by pass 1.

This PR must:

- rename the external split label from `holdout` to `test_external`
- audit overlap across patient, specimen, and slide identities
- emit a dedicated leakage report artifact
- halt the CLI when leakage is detected

This PR must not pull in pass-2 artifact resolution, hashing, rejection ledgers, or final manifest materialization.

## Scope

### In scope

- rename the manifest split label from `holdout` to `test_external`
- overlap detection over the split-assignment artifact
- patient/specimen/slide leakage checks
- fatal leakage-report artifact emission
- deterministic leakage-report serialization
- CLI failure behavior when overlap exists
- tests for clean runs, overlap cases, null handling, and deterministic output

### Out of scope

- pass-2 artifact resolution
- rejection ledgers
- final manifest serialization
- leakage remediation
- resolver configuration

## Architecture

### Package shape

- `src/spatial_ci/manifest/splits.py`
  - rename external split output from `holdout` to `test_external`
- `src/spatial_ci/manifest/leakage.py`
  - overlap detection and deterministic leakage-report construction
- `src/spatial_ci/manifest/artifacts.py`
  - add leakage-report row and artifact models
- `src/spatial_ci/manifest/pipeline.py`
  - run leakage audit after building split assignments
  - write report on failure
  - raise `ManifestPipelineError`
- `scripts/build_manifest.py`
  - surface fatal leakage as a nonzero CLI outcome

### Boundary

The leakage audit must consume the pass-1 split-assignment table as its input.

It must not depend on pass-2 physical artifact resolution. The goal of this PR is to freeze split-integrity checking as a separate, auditable pass-1 concern.

## Data Model

### Split label correction

The external split label must be renamed now:

- old: `holdout`
- new: `test_external`

This keeps the manifest output aligned with the documented split-pair contract before leakage reporting is introduced.

### Leakage-report row fields

Minimum row fields:

- `split_left`
- `split_right`
- `audit_column`
- `overlapping_id`

### Leakage-report artifact fields

Minimum artifact metadata:

- `split_contract_id`
- `report_path`
- `n_findings`

## Audit Rules

### Audited columns

The pipeline must audit overlap across:

- `resolved_patient_id`
- `resolved_specimen_id`
- `resolved_slide_id`

### Audited split pairs

v1 split pairs:

- `train` vs `val`
- `train` vs `test_external`
- `val` vs `test_external`

### Null handling

Null specimen and slide IDs must remain null and must not be treated as overlapping values.

The audit must only consider real non-null IDs.

### Namespacing expectation

Namespaced IDs produced in pass 1 must remain the overlap keys.

This prevents false overlap from generic specimen or slide identifiers reused across cohorts.

## Behavior

### No leakage

If no overlap exists:

- do not write a leakage report artifact
- return the split-assignment artifact normally

### Leakage found

If any overlap exists:

- write a leakage report artifact
- include every overlapping ID as a separate row
- sort findings deterministically by:
  - `audit_column`
  - `split_left`
  - `split_right`
  - `overlapping_id`
- halt immediately by raising `ManifestPipelineError`

There is no warnings-only mode.

## Output Paths

The leakage-report path should be derived from the requested split-assignment output path.

Example:

- split assignments: `assignments.parquet`
- leakage report: `assignments.leakage.parquet`

This avoids widening the config surface for this PR.

## Testing

Required tests for this PR:

- external cohorts now emit `test_external`
- clean split-assignment artifact yields zero leakage findings
- patient leakage is detected
- specimen leakage is detected
- slide leakage is detected
- null specimen/slide IDs do not create fake overlap
- namespaced IDs with the same raw suffix do not collide
- leakage report rows are deterministic and sorted
- CLI writes split assignments, writes leakage report, and exits nonzero on overlap

## Sequencing

Recommended next PR after this one:

1. pass-2 artifact resolution
2. rejection ledger output
3. final manifest validation and serialization
