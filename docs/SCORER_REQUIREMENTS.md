# Scorer Requirements

Spatial-CI should not start by inventing a brand-new transcriptomics score.
It should start by defining the scorer contract that makes failure modes
explicit.

## Contract Properties

Every scorer integrated into Spatial-CI should satisfy or explicitly report on
these properties:

1. **Sample-local invariance**
   - Adding unrelated cells or spots must not change a spot's raw score.
2. **Sparse-awareness**
   - Zeros, ties, and dropout must not be silently treated as strong evidence.
3. **Signature-size calibration**
   - Small and large signatures must not be compared as though their scales are
     naturally equivalent.
4. **Missing-gene accounting**
   - Coverage must be reported explicitly rather than hidden.
5. **Directionality support**
   - Up-only and up/down signatures must be handled explicitly.
6. **Spatial separation**
   - Raw expression evidence and neighborhood-aware smoothing must remain
     separate outputs.
7. **Audit packet output**
   - A scorer must emit an inspection-ready packet, not just a naked scalar.

## ScorePacket v0

Spatial-CI's first scorer contract is a packet, not a single number.

Minimum packet fields:
- `raw_rank_evidence`
- `signature_coverage`
- `dropout_penalty`
- `null_calibrated_score`
- `spatial_consistency`
- `uncertainty_flag`
- `failure_codes`

The packet should support `MISSING_DATA` and other explicit failure states
rather than fabricating values.

## Baseline Methods

Before any new formula work, benchmark stable baselines and adapters:
- `singscore`
- `UCell`
- `AUCell`
- `ssGSEA`
- optionally `scPS` if it is reproducible in this stack

The goal is not to declare one universal winner. The goal is to compare methods
and packet outputs under realistic failure slices.

## Benchmark Slices

Evaluate methods and packets separately across:
- null signatures
- dropout and tie inflation
- signature-size variation
- unrelated-sample invariance
- spatial neighborhood perturbation
- reviewability and false-positive rate

## Current Direction

- Keep raw `singscore` as a simple deterministic baseline.
- Use packet fields to make missingness, calibration, smoothing, and uncertainty
  explicit.
- Prefer falsifiable contract improvements over a claim that a new scalar is
  universally better.
