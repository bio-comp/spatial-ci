# Baseline KNN Foundation Design

## Summary

This slice adds the first embedding-aware deployable baseline to Spatial-CI:

- a typed embedding artifact boundary under `src/spatial_ci/embeddings/`
- a frozen `knn_on_embeddings` baseline with contract-backed semantics
- baseline-runner and CLI support for embeddings as an optional third input

The goal is to keep baseline execution contract-first. This PR does not build an
embedding-generation pipeline, does not add `ridge_probe`, and does not emit
evaluation certificates.

## Goals

- Introduce a package-owned embedding artifact schema with Parquet read/write
  helpers.
- Consume embeddings at `observation_id` grain.
- Implement `knn_on_embeddings` with frozen v1 semantics:
  - fit split: `train`
  - metric: `cosine`
  - `k = 20`
  - no val or external-test access during fitting
- Extend the baseline runner so embeddings are optional:
  - no embeddings -> mean baselines only
  - embeddings provided -> mean baselines plus KNN
- Fail loudly on malformed embedding artifacts or broken joins.

## Non-Goals

- No `ridge_probe` in this slice.
- No embedding generation or feature extraction pipeline.
- No evaluation certificates.
- No distance-weighted or tuned KNN variants.

## Architecture

### Package shape

- `src/spatial_ci/embeddings/artifacts.py`
  - `EmbeddingArtifactRow`
  - `EmbeddingArtifact`
  - Parquet read/write helpers
- `src/spatial_ci/embeddings/__init__.py`
  - public exports
- `src/spatial_ci/baselines/knn.py`
  - frozen KNN prediction logic
- `src/spatial_ci/baselines/runner.py`
  - optional embedding-aware execution path
- `scripts/run_baselines.py`
  - optional `--embeddings` flag

### Embedding artifact boundary

Row grain:

- one row per `observation_id`

Required row fields:

- `observation_id`
- `sample_id`
- `embedding`

Artifact metadata:

- `alignment_contract_id`
- `encoder_name`
- `encoder_version`
- optional source path/hash metadata when available

This keeps embeddings explicit and typed without forcing the upstream embedding
pipeline into the same PR.

### Data flow

1. load score artifact
2. keep only `ScoreStatus.OK` rows with non-null `sample_id`
3. join manifest on `sample_id` to get `cohort_id` and `split`
4. if embeddings are present, join them on `observation_id`
5. run mean baselines as today
6. run `knn_on_embeddings` only when embeddings are available
7. emit one combined long-form baseline prediction artifact

### KNN semantics

For each `program_name`:

- build the training neighbor pool from rows where `split == train`
- use cosine distance on embedding vectors
- use fixed `k = 20`
- if fewer than 20 training rows exist, use all available train neighbors
- exclude the query observation itself when predicting train observations
- predict by the simple mean of neighbor `raw_rank_evidence`
- no distance weighting and no tuning in v1

## Failure Behavior

Hard failures in this slice:

- no eligible train rows with embeddings
- an eligible score row is missing an embedding row
- duplicate embedding `observation_id`
- inconsistent embedding dimensionality
- no usable train neighbor target for a required `program_name`
- no silent fallback from missing embeddings to mean baselines

## Testing Strategy

Required tests:

- embedding artifact roundtrip
- KNN uses train-only neighbors
- KNN excludes self-neighbor for train predictions
- KNN uses all available train neighbors when `n_train < 20`
- duplicate embedding `observation_id` fails
- missing embedding for eligible score row fails
- mixed embedding dimensionality fails
- runner emits combined long-form artifact with mean baselines plus KNN
- CLI path with and without `--embeddings`

## Follow-Up Slices

After this PR:

1. add `ridge_probe`
2. emit evaluation certificates
3. run the full baseline-only benchmark end-to-end
