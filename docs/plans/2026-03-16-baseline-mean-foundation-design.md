# Baseline Mean Foundation Design

## Summary

This slice introduces the first honest baseline execution path for Spatial-CI:

- a typed baseline prediction artifact
- a package-owned baseline runner
- the two nonparametric deployable baselines:
  - `global_train_mean`
  - `mean_by_train_cohort`
- a thin `scripts/run_baselines.py` CLI

The goal is to create a real baseline boundary without pretending the full
baseline benchmark is complete. Embedding baselines and evaluation
certificates remain follow-up slices.

## Goals

- Create a stable baseline package under `src/spatial_ci/baselines/`.
- Consume frozen score artifacts plus the materialized manifest.
- Fit baseline statistics on `train` only.
- Emit deterministic, long-form prediction artifacts.
- Fail loudly on malformed joins, missing contract IDs, or unusable score rows.

## Non-Goals

- No `knn_on_embeddings` implementation yet.
- No `ridge_probe` implementation yet.
- No evaluation certificate generation yet.
- No oracle baselines in this slice.

## PR Scope

This first PR lands:

- baseline prediction schemas
- mean-baseline fit/predict logic
- baseline runner + CLI
- tests for train-only semantics and cohort fallback behavior

This PR explicitly defers:

- embedding inputs and embedding-aware baselines
- bootstrap uncertainty
- certificate emission

## Architecture

### Package shape

- `src/spatial_ci/baselines/artifacts.py`
  - `BaselineName`
  - `BaselinePredictionRow`
  - `BaselinePredictionArtifact`
  - Parquet read/write helpers
- `src/spatial_ci/baselines/mean.py`
  - train-only fit helpers for global mean and cohort mean
- `src/spatial_ci/baselines/runner.py`
  - score-artifact loading
  - manifest join/validation
  - baseline execution orchestration
- `src/spatial_ci/baselines/__init__.py`
  - public exports
- `scripts/run_baselines.py`
  - thin CLI

### Input boundary

This slice consumes:

- a score artifact parquet
- a materialized manifest parquet
- explicit run metadata via CLI flags:
  - `run_id`
  - `baseline_contract_id`
  - `split_contract_id`
  - optional `manifest_id`

The score artifact already owns:

- `target_definition_id`
- `scoring_contract_id`

The manifest parquet currently does not carry artifact-level metadata, so the
split and optional manifest identifiers remain explicit CLI inputs for now.

### Join semantics

Join score rows to manifest rows on `sample_id`.

Requirements:

- only `ScoreStatus.OK` rows are eligible baseline targets
- every eligible score row must carry non-null `sample_id`
- every joined `sample_id` must exist exactly once in the manifest
- manifest rows must provide:
  - `sample_id`
  - `cohort_id`
  - `split`

### Baseline semantics

#### 1. `global_train_mean`

For each `program_name`, compute:

- mean of `raw_rank_evidence` over `split == train`

Predict that mean for every eligible row.

#### 2. `mean_by_train_cohort`

For each `program_name` and `cohort_id`, compute:

- mean of `raw_rank_evidence` over `split == train`

Prediction rule:

- use matching train-cohort mean when available
- otherwise fall back to the program-level global train mean

This matches the repo’s glossary and contract text that allow fallback to the
global train mean when cohort-specific training support is absent.

### Output artifact

Prediction output is long-form, one row per:

- `observation_id x program_name x baseline_name`

Row fields:

- `observation_id`
- `sample_id`
- `cohort_id`
- `split`
- `program_name`
- `baseline_name`
- `predicted_score`

Artifact fields:

- `run_id`
- `baseline_contract_id`
- `split_contract_id`
- `target_definition_id`
- `scoring_contract_id`
- optional `manifest_id`
- `source_score_artifact_path`
- `source_score_artifact_hash`
- `source_manifest_path`
- `source_manifest_hash`
- `rows`

This artifact intentionally stores predictions only, not duplicated observed
targets. Later evaluation can join back to the score artifact by
`observation_id x program_name`.

## Failure Behavior

Hard failure conditions for this slice:

- no eligible `ScoreStatus.OK` rows
- missing `sample_id` on eligible score rows
- duplicate manifest `sample_id`
- score rows missing from manifest
- no train rows for a required `program_name`
- unsupported requested baseline name

## Testing Strategy

Required tests:

- artifact schema roundtrip
- `global_train_mean` uses train-only rows
- `mean_by_train_cohort` uses matching train cohort when present
- `mean_by_train_cohort` falls back to global mean when needed
- dropped/failed score rows are excluded
- runner join validation on missing or duplicate `sample_id`
- CLI writes deterministic Parquet output

## Follow-Up Slices

After this PR:

1. add `knn_on_embeddings` and `ridge_probe`
2. add evaluation certificate generation
3. then benchmark the full baseline stack end-to-end
