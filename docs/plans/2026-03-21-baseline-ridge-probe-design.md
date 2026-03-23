# Baseline Ridge Probe Design

## Summary

This slice adds the last required deployable baseline in the frozen v1 stack:
`ridge_probe`.

The goal is to keep the baseline runner contract-first and boring:

- standardized embedding features, using train-only statistics
- per-program ridge regression
- alpha grid fixed to `{0.1, 1.0, 10.0}`
- fit on `train`
- tune on `val`
- predict on all splits without external-test peeking

This PR does not emit evaluation certificates yet.

## Goals

- Implement `ridge_probe` as a frozen embedding-space deployable baseline.
- Record the chosen alpha in the baseline prediction artifact at artifact level.
- Fail loudly when the split structure is insufficient for honest tuning.
- Reuse the existing score + manifest + embedding join path from the KNN slice.
- Keep long-form prediction rows unchanged.

## Non-Goals

- No evaluation certificate generation.
- No alpha search beyond `{0.1, 1.0, 10.0}`.
- No multi-target shared model fitting.
- No oracle variants or external-test-informed tuning.

## Architecture

### Package shape

- `src/spatial_ci/baselines/ridge.py`
  - frozen per-program ridge fitting and prediction
- `src/spatial_ci/baselines/artifacts.py`
  - artifact-level `ridge_probe_selected_alpha_by_program`
- `src/spatial_ci/baselines/runner.py`
  - extend baseline execution to include ridge when embeddings are present
- `scripts/run_baselines.py`
  - no new flag required; embeddings still gate embedding-aware baselines

### Data flow

1. load score artifact and keep only `ScoreStatus.OK` rows
2. join manifest on `sample_id`
3. if embeddings are present, join them on `observation_id`
4. emit mean baselines
5. emit `knn_on_embeddings`
6. emit `ridge_probe`
7. write one combined long-form baseline prediction artifact

### Ridge semantics

For each `program_name`:

- take rows with `split == train` as the fit pool
- take rows with `split == val` as the tuning pool
- standardize embedding dimensions using train-only mean and scale
- fit one ridge model per alpha in `{0.1, 1.0, 10.0}`
- choose the alpha with lowest validation MSE
- break ties by smaller alpha for determinism
- refit is not needed because all candidate models are already fit on full train
- predict for every available row using the chosen alpha

Artifact-level metadata:

- `ridge_probe_selected_alpha_by_program: dict[str, float] | None`

Rules:

- if any `ridge_probe` rows are present, the mapping must exist and cover every
  predicted ridge program exactly
- if no `ridge_probe` rows are present, the mapping must be `None`

## Failure Behavior

Hard failures in this slice:

- embeddings missing for an eligible score row
- a program has fewer than 2 train rows
- a program has no val rows
- non-finite or inconsistent embedding features
- artifact metadata and ridge rows disagree on selected alphas

## Testing Strategy

Required tests:

- ridge predictor chooses the correct alpha on deterministic fixtures
- standardization uses train-only statistics
- ridge fails when a program has fewer than 2 train rows
- ridge fails when a program has no val rows
- artifact roundtrip preserves `ridge_probe_selected_alpha_by_program`
- runner emits mean + KNN + ridge when embeddings are present
- runner records alpha metadata when ridge rows are present
- CLI path with embeddings emits ridge predictions and alpha metadata

## Follow-Up Slice

After this PR:

1. emit evaluation certificates
2. run the full baseline-only benchmark end-to-end
