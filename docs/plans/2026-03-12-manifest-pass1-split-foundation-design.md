# Manifest Pass 1 Split Foundation Design

## Summary

The first manifest PR should implement the smallest useful pass-1 slice:

- canonical metadata normalization
- resolved patient/specimen/slide identity construction
- deterministic patient-level split assignment
- a frozen split-assignment artifact

This PR must not pull in leakage auditing, rejection ledgers, artifact resolution, or final manifest materialization. The goal is to create a real package boundary and a real artifact that later manifest stages can build on.

## Scope

### In scope

- `src/spatial_ci/manifest/` package for pass-1 logic
- YAML-backed manifest build config
- canonical source-column normalization into pass-1 fields
- strict resolved identity construction
- namespaced specimen and slide IDs
- deterministic `train` / `val` / `holdout` assignment
- external cohort holdout handling from the split contract
- deterministic Parquet serialization of split assignments
- tests for normalization, identity resolution, split determinism, and failure cases

### Out of scope

- leakage reports
- rejection ledgers
- physical artifact resolution
- hashing
- final materialized sample manifest
- resolver subsystem

## Architecture

### Package shape

- `src/spatial_ci/manifest/config.py`
  - config models for metadata sources and split settings
- `src/spatial_ci/manifest/normalize.py`
  - canonical field mapping and normalization
- `src/spatial_ci/manifest/identity.py`
  - resolved ID construction and fallback provenance
- `src/spatial_ci/manifest/splits.py`
  - deterministic patient-level split assignment
- `src/spatial_ci/manifest/artifacts.py`
  - typed split-assignment row and artifact schemas
- `src/spatial_ci/manifest/pipeline.py`
  - pass-1 orchestration
- `scripts/build_manifest.py`
  - thin CLI wrapper over the package pipeline

### CLI role

`scripts/build_manifest.py` stays intentionally thin. For this PR it should:

1. load the config
2. call the pass-1 pipeline
3. write the split-assignment artifact

It should not contain embedded split or normalization logic.

## Data Model

### Row grain

The split-assignment artifact row grain is `sample_id`.

The split-decision grain is `resolved_patient_id`.

This means:

- all samples tied to the same resolved patient receive the same split
- downstream leakage auditing can reuse the frozen identity and split artifact

### Split-assignment fields

Minimum row fields for this PR:

- `sample_id`
- `cohort_id`
- `split`
- `resolved_patient_id`
- `patient_id_source`
- `resolved_specimen_id | None`
- `resolved_slide_id | None`

### Identity rules

- `resolved_patient_id` uses a strict fallback order defined in code and surfaced via `patient_id_source`
- `resolved_specimen_id` and `resolved_slide_id` must be cohort-namespaced before serialization
- namespacing happens before split logic

This avoids ambiguous cross-cohort identifiers and keeps fallback provenance explicit.

## Config Design

The first PR should use a small explicit YAML config that can run on test fixtures and later grow without redesign.

### Minimal config shape

- `sources`
  - `path`
  - `format`
  - `field_map`
  - optional constant `cohort_id`
- `split_contract`
  - `split_contract_id`
  - `val_fraction`
  - `external_holdout_cohorts`

The first PR does not need full resolver or artifact-location settings.

## Data Flow

1. load `ManifestBuildConfig`
2. read one or more metadata source tables
3. normalize source fields into canonical pass-1 columns
4. derive resolved IDs and `patient_id_source`
5. assign `holdout` for cohorts listed in `external_holdout_cohorts`
6. assign deterministic `train` or `val` once per `resolved_patient_id`
7. join patient split assignments back to sample rows
8. sort output deterministically by:
   - `split`
   - `cohort_id`
   - `sample_id`
9. write one Parquet split-assignment artifact

## Determinism

The split assignment must not use Python's built-in `hash()`.

Use a stable hash over:

- `split_contract_id`
- `resolved_patient_id`

This keeps assignments reproducible across runs and processes.

## Failure Behavior

This first PR should fail hard instead of inventing partial recovery behavior.

Hard failures for:

- missing required canonical fields
- duplicate `sample_id`
- malformed config
- invalid `val_fraction`
- inconsistent source rows that produce invalid resolved-patient assignments

Rejection ledgers belong to a later PR.

## Testing

Required tests for this PR:

- alias normalization into canonical fields
- namespaced resolved ID construction
- deterministic patient-level split assignment
- external cohort rows forced to `holdout`
- sorted output stability
- duplicate `sample_id` rejection

## Sequencing

Recommended PR sequence after this foundation:

1. add leakage audit on top of the split-assignment artifact
2. add pass-2 artifact resolution and rejection ledgers
3. add final manifest validation and serialization
