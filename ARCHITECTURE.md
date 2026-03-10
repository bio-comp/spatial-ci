# Architecture

## Scoring Boundary

Spatial-CI treats scoring as an internal-first subsystem.

- The authoritative reference implementation is R/Bioconductor `singscore`.
- Python scoring code belongs under `src/spatial_ci/scoring/`.
- Signature definitions belong under `src/spatial_ci/signatures/`.
- Extraction into a standalone repo is deferred until parity and benchmark
  gates are met.

Current policy:

> singscore core is internal-first, extraction candidate after parity and
> benchmark completion.
