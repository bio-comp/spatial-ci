# Spatial-CI Scoring

This document defines how Spatial-CI converts expression measurements into frozen biological target scores.

The purpose of this document is to prevent one of the most dangerous forms of benchmark drift:

> changing the target score definition while pretending the biological task stayed the same.

In Spatial-CI, scoring is not a convenience function.
It is part of the target contract.

---

## 1. Scoring philosophy

Spatial-CI requires target scores to be:

- biologically interpretable
- deterministic
- auditable
- stable across reruns
- independent of the model
- as independent as possible from cohort-level composition

The core principle is:

> a target score for one spatial spot should depend only on that spot’s expression vector, not on the surrounding cohort.

That is why Spatial-CI v1 moved away from cohort-dependent score construction for its frozen targets.

---

## 2. Why scoring matters so much

In many projects, target scoring is treated like a harmless preprocessing choice.

It is not.

Changing the scorer can change:
- the effective label distribution
- the relative rank of spots
- the difficulty of the prediction task
- cross-cohort comparability
- the apparent success of a model

So in Spatial-CI, scoring is part of the scientific definition of the target.

---

## 3. What v1 is scoring

Spatial-CI v1 scores **per-spot biological programs** derived from fixed Hallmark targets.

The frozen source targets are:

- `HALLMARK_HYPOXIA`
- `HALLMARK_G2M_CHECKPOINT`
- `HALLMARK_EPITHELIAL_MESENCHYMAL_TRANSITION`

The output of scoring is:

- one scalar score per spot
- per target program
- under a frozen scoring contract

---

## 4. Why we rejected cohort-dependent scoring

A major design correction in Spatial-CI was rejecting cohort-dependent scoring for the main frozen target definition.

Examples of why that matters:

- if the score depends on the global distribution of the dataset, the target changes when the dataset changes
- if the score depends on control-gene pools chosen relative to the cohort, the target is not truly fixed
- if the score is recomputed differently across cohorts, external evaluation becomes muddled

That kind of target drift is unacceptable for Spatial-CI.

---

## 5. Why single-sample scoring is preferred

Single-sample scoring gives a cleaner target contract because each spot is scored from its own expression vector.

This has several advantages:

- less sensitivity to cohort composition
- easier comparison across datasets
- better alignment with external validation
- easier to reason about as a frozen per-sample target

This is not a claim that single-sample scoring is universally superior in all biological contexts.
It is a claim that it is the better fit for **Spatial-CI’s frozen benchmarking philosophy**.

---

## 6. Frozen v1 scoring direction

Spatial-CI v1 uses **R/Bioconductor singscore** as the source-of-truth implementation.

### Execution boundary

**Python does not generate frozen target scores directly.**

The scoring architecture is:

1. **Python** builds the manifest and prepares expression artifacts
2. **R** computes frozen target scores using singscore
3. **Python** resumes downstream evaluation by consuming the emitted score artifacts

This cross-language boundary is explicit: **Python → R → Python**.

### Entry point

The scoring entry point is:

```
scripts/score_targets.R
```

This script:
- Takes expression artifacts and target definitions as input
- Applies the frozen scoring contract via singscore
- Emits score artifacts in Parquet format

### Environment freezing

The R scorer environment is frozen via `renv.lock`:

- All R package dependencies are locked
- The `renv.lock` hash is recorded in the scoring contract
- Recomputing scores requires the same `renv.lock`

This ensures reproducibility independent of the Python environment.

---

## 7. Scoring contract requirements

Any valid scoring contract in Spatial-CI must specify:

- scoring method name
- implementation source (Bioconductor singscore)
- environment lockfile reference (renv.lock with hash)
- score variant
- tie-breaking policy
- missing-gene policy
- any normalization assumptions
- deterministic seed if applicable

If any of these are unspecified, the scoring contract is incomplete.

---

## 8. v1 scoring contract sketch

Example conceptual fields:

- `scoring_contract_id`
- `method_name`
- `implementation_source`
- `environment_lockfile` (renv.lock hash)
- `variant`
- `tie_policy`
- `missing_gene_policy`
- `score_orientation`
- `normalization_method`

Example v1 values:

- `method_name = "singscore"`
- `implementation_source = "Bioconductor"`
- `environment_lockfile = "renv.lock @ <hash>"`
- `variant = "uncentered_rank_based_single_sample"`
- `tie_policy = "average_rank"`
- `missing_gene_policy = "drop_if_missing_gt_10pct_else_intersect"`

The exact field names may evolve, but the semantics must remain explicit.

---

## 9. Normalization policy

Spatial-CI distinguishes between:

- expression normalization used to prepare the matrix
- target scoring used to produce the program value

These are related, but not identical.

The scoring contract must explicitly state the normalization assumptions required by the scoring implementation.

It is not acceptable to hide normalization inside a notebook without versioning it.

---

## 10. Tie handling

If the scoring method depends on rank assignments, tie handling must be frozen.

Recommended v1 behavior:
- average rank for ties

Why this matters:
- different tie strategies can slightly shift scores
- score drift from tie handling is subtle and easy to ignore
- subtle drift still counts as target drift

---

## 11. Missing-gene policy

Spatial-CI requires missing-gene handling to be frozen and auditable.

### Frozen v1 rule

For a given spot and target program:

- if more than **10%** of the target genes are missing from the detected transcript pool, drop that spot for that program
- if **10% or fewer** are missing, score on the intersection and record the condition

This rule exists to avoid:
- scoring nearly absent targets as if they were fully observed
- silently changing the effective biology under sparse detection

---

## 12. What “missing” means

A gene should be treated as missing according to the scoring pipeline’s declared input matrix semantics.

This must be documented clearly.

Examples of ambiguity to avoid:
- confusing true zero counts with filtered-out genes
- confusing undetected genes with genes absent from the matrix itself
- using different missingness interpretations across cohorts

Spatial-CI requires one declared interpretation.

---

## 13. What counts as scoring drift

Scoring drift occurs when target scores change meaningfully without a new scoring contract version.

Examples of scoring drift:

- changing from one scoring package to another (e.g., PySingscore → singscore)
- changing the R environment (different renv.lock)
- changing tie handling
- changing missing-gene threshold
- changing rank variant
- changing normalization without versioning it
- swapping from single-sample rank scoring to cohort-dependent score construction

Any of these require a new scoring contract version.

---

## 14. Source-faithful vs derived scoring

Spatial-CI distinguishes between:

### Source-faithful scoring
Applying the declared scoring method directly to the frozen source gene set.

### Derived scoring
Combining source targets, rescaling them, or otherwise building a new target score.

Derived scoring is allowed, but only if it gets:
- a new target/scoring contract
- explicit documentation
- explicit rationale

v1 defaults to source-faithful scoring.

---

## 15. Why we did not freeze on scanpy_score_genes for v1

This was a deliberate decision.

Reasons:
- it can depend on cohort-wide properties
- it introduces dataset-relative control-gene behavior
- it is less aligned with the “one spot, one score” philosophy of Spatial-CI

This does **not** mean it is a bad method generally.
It means it is not the preferred fit for frozen v1 targets.

---

## 16. Score direction and interpretation

A scoring contract must make it explicit what higher or lower scores mean.

For example:

- higher hypoxia score = stronger hypoxia-like program expression
- higher G2M score = stronger G2M-like cell-cycle activity
- higher EMT score = stronger EMT/mesenchymal-like program expression

This sounds obvious, but it prevents sign inversions and hidden transformations from creeping into the evaluation pipeline.

---

## 17. Score comparability across cohorts

Spatial-CI does not assume that scores are perfectly comparable across all biological contexts simply because the same formula was applied.

What the scoring contract guarantees is:

- the **definition** is stable
- the **implementation** is stable
- the **target meaning** is stable

Cross-cohort differences in score distribution may still occur for real biological or technical reasons.

That is what evaluation is supposed to interrogate.

---

## 18. Score caching and provenance

If scores are materialized and cached, the score artifact must retain provenance linking back to:

- target definition ID
- scoring contract ID
- input expression artifact hash
- **renv.lock hash** (R environment provenance)
- generation timestamp or run ID

Otherwise score files become orphaned labels with unclear meaning.

---

## 19. Recommended score artifact fields

**Format:** Parquet (preferred for real artifacts; CSV acceptable for small test cases)

A per-sample or per-spot score artifact should include at minimum:

- `sample_id`
- `spot_id` or spatial unit identifier
- `target_definition_id`
- `scoring_contract_id`
- `program_name`
- `score_value`
- `n_target_genes_total`
- `n_target_genes_observed`
- `missing_fraction`
- `dropped_by_missingness_rule`
- `renv_lock_hash` (for reproducibility)

This makes score generation auditable.

---

## 20. Scoring and evaluation are separate

A crucial Spatial-CI distinction:

- **Scoring** defines the target
- **Evaluation** measures how well the model predicts that target

These must not be blurred together.

Bad pattern:
- tweak the scorer until evaluation looks good

Spatial-CI forbids that kind of hidden coupling.

---

## 21. What a scoring contract is designed to prevent

The scoring layer is designed to prevent:

- target mutation under the model
- cohort-relative label drift
- unclear missing-gene behavior
- implementation ambiguity
- undocumented score transformations
- post hoc target redefinition to rescue weak models

---

## 22. What success looks like

A good scoring system in Spatial-CI is one where:

- another person can recompute the same scores (via renv.lock)
- another cohort can be scored under the same definition
- missing genes are handled transparently
- the target meaning does not change when the dataset changes
- the R environment is reproducibly frozen
- evaluation is testing a stable object rather than a moving label

---

## 23. Future scoring extensions

Later versions may add:

- derived target scoring contracts
- multi-program composite scoring
- isoform-aware scoring
- junction-aware scoring
- APA-aware scoring
- region/neighborhood-level target scoring

But each of those must become a new scoring contract, not a silent modification of v1.

---

## 24. One-sentence summary

Spatial-CI scoring exists to make target biology stable enough that model evaluation tests a real scientific object rather than a drifting label construction procedure.
