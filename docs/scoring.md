# Scoring Strategy

## Direction

Spatial-CI keeps Python singscore work **inside this repo** for now.

The current source-of-truth scoring boundary remains:
- R/Bioconductor `singscore`
- frozen through repo-level environment provenance
- consumed by Spatial-CI as a deterministic score artifact

For v1, the bridge contract is intentionally thin and explicit:
- Python writes `expression_input.csv`, `signature_input.json`,
  `scoring_request.json`, and `detected_membership.parquet`
- R writes `score_output.parquet` and `runtime_metadata.json`
- R owns only raw `singscore` numeric output
- Python owns detected-membership coverage, drop policy, packet assembly, and
  output invariants

The near-term goal is not to launch a new standalone scoring package. The goal
is to make Spatial-CI's scoring layer deterministic, benchmarkable, auditable,
and parity-tested against the maintained R reference.

## Why Internal First

Splitting too early would optimize for packaging theater instead of the actual
moat:
- explicit contracts
- R parity tests
- sparse/spatial failure handling
- benchmark harness
- publishable evaluation artifacts

The scorer math alone is not the differentiator. The differentiator is the
audit-grade harness around it.

## Intended Internal Layout

```text
src/spatial_ci/
  scoring/
    singscore.py
    api.py
    validators.py
    packet.py
  signatures/
tests/
  golden/
  scoring/
docs/
  scoring.md
  SCORER_REQUIREMENTS.md
```

Design rules for the internal scorer:
- no Spatial-CI-specific assumptions inside the core scoring function
- tiny public API
- clean dependency boundaries
- extraction-friendly module names and signatures
- scorer adapters should emit packet-shaped outputs instead of naked scalars

## Extraction Gate

Keep the scorer embedded until at least one of these becomes true:
- the scorer is useful outside Spatial-CI
- the API stabilizes
- parity with the R reference is proven
- PyPI distribution or external adoption becomes a real need

If those gates are met, extraction can be reconsidered under a name such as
`singscorepy`.

## Validation Gates

Use these gates before extraction:
- Parity gate: Python matches Bioconductor `singscore` on golden cases
- Contract gate: explicit behavior for missing genes, duplicates, ties, and
  directed or undirected signatures
- Sparse gate: score stability and diagnostics on sparse spatial or
  single-cell-style inputs
- Reuse gate: at least two internal consumers beyond one notebook or script
- Packaging gate: API stability is high enough that breaking changes are
  unlikely

## Robust Calibration Layer

MAD belongs **after** the raw score, not in place of it.

Recommended pattern:
- compute the raw single-sample rank-based signature score first
- declare a typed reference population explicitly
- summarize the reference distribution with median and MAD
- compute an optional robust z-score for diagnostics or anomaly interpretation

Reference formula:

```text
robust_z = (raw_score - median(reference_scores)) / (1.4826 * MAD(reference_scores))
```

This layer is intended for:
- post-score calibration against a declared reference set
- QC and anomaly detection
- robust dispersion reporting across regions, patients, or cohorts

This layer is not intended to replace the primary singscore contract. The raw
score remains the decision primitive because it preserves the single-sample,
rank-based interpretation that should not drift when unrelated samples are
added.

Failure rules:
- if the reference population is missing, emit `MISSING_DATA`
- if the reference set is too small, emit `REFERENCE_TOO_SMALL`
- if MAD is zero or effectively zero, emit `DEGENERATE_REFERENCE_DISTRIBUTION`
- do not fabricate a numeric robust z-score in those cases

## ScorePacket Contract

Spatial-CI should treat the review object as a packet, not as one scalar.

Current packet shape:
- `raw_rank_evidence`
- `signature_coverage`
- `dropout_penalty`
- `null_calibrated_score`
- `spatial_consistency`
- `uncertainty_flag`
- `failure_codes`

This keeps the deterministic scorer, calibration, coverage accounting, and
spatial agreement separate. A scorer adapter can emit `MISSING_DATA` for packet
fields it cannot populate yet, but it must still honor the packet shape.

Coverage is not inferred from `expression > 0`. It is computed from an explicit
observation-level detected-membership artifact so zero-filling or matrix
densification cannot silently redefine the missingness contract.

## Near-Term Work

1. Keep the scorer internal to `spatial_ci.scoring`.
2. Add golden-case parity tests against the R reference.
3. Add packet-shaped scorer output contracts and adapters.
4. Add optional robust calibration over declared reference populations.
5. Add Spatial-specific extensions only after parity is proven:
   - sparse-aware diagnostics
   - AnnData adapter
   - missing-gene contract behavior
   - tie-policy controls
