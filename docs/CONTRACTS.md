
## `docs/CONTRACTS.md`

```markdown
# Spatial-CI Contracts

This document defines the first-class contracts that govern Spatial-CI.

The purpose of these contracts is to make every important scientific and engineering assumption **explicit, versioned, and auditable**.

Spatial-CI treats the following as first-class contracts:

- target biology
- target scoring
- image–molecule alignment
- split logic
- baseline semantics
- bootstrap semantics
- sample/provenance manifest
- evaluation certificate
- intervention axis declaration

---

## 1. Contract philosophy

Spatial-CI follows a simple rule:

> If a choice could materially affect interpretation, it must be named and versioned.

This prevents:
- hidden preprocessing drift
- leaky comparisons
- target mutation under the model
- benchmark theater
- irreproducible evaluation

---

## 2. TargetDefinition

## Purpose

Defines the biological targets the model is allowed to predict.

This contract must freeze:
- source database/version
- allowed programs
- whether tissue-specific modification is permitted
- scoring method and its implementation
- missing-gene policy

## v1 requirements

### Identifier
- `target_definition_id = "breast_visium_hallmarks_v1"`

### Source
- unmodified **MSigDB Hallmark** programs

### Allowed programs
- `HALLMARK_HYPOXIA`
- `HALLMARK_G2M_CHECKPOINT`
- `HALLMARK_EPITHELIAL_MESENCHYMAL_TRANSITION`

### Semantics
- `HALLMARK_EPITHELIAL_MESENCHYMAL_TRANSITION` must be described as an **EMT/mesenchymal program**
- it must **not** be relabeled as a pure stromal or CAF state

### Tissue modification
- `is_tissue_modified = false`

No “breast-specific cleanup” is allowed in v1.

### Missing-gene policy
- if more than **10%** of genes in the target set are missing for a spot, drop that spot for that program
- if **10% or fewer** are missing, score on the intersection and record the condition

---

## 3. ScoringContract

## Purpose

Defines how per-spot program scores are computed from expression data.

## Philosophy

To claim immutable biology, the score for one spot must depend only on that spot’s expression vector.

Cohort-dependent scoring is not allowed in the main frozen target definition.

## v1 requirements

### Scoring family
- **single-sample, rank-based scoring**

### Preferred implementation direction
- **R/Bioconductor `singscore`**

### The contract must freeze
- package name and source
- package version / Bioconductor release
- environment lock provenance (for example `renv.lock`)
- scoring variant
- tie-breaking behavior
- missing-gene behavior
- output artifact format and provenance fields

### v1 rationale
We explicitly moved away from cohort-dependent methods such as
`scanpy_score_genes` for the primary frozen target definition. The current v1
direction is to treat R/Bioconductor `singscore` as the authoritative scoring
implementation and to freeze that boundary through lockfile-backed provenance
rather than a Python package commit pin.

---

## 4. AlignmentContract

## Purpose

Defines how image crops are linked to molecular spatial units.

## Philosophy

The visual input seen by the model is not identical to the molecular spot. That mapping is a scientific choice and must be versioned.

## v1 requirements

### Identifier
- `alignment_id = "visium_context_224px_0_5mpp_v1"`

### Frozen parameters
- target mpp: `0.5`
- tile size: `224 px`
- extraction mode: `spot_plus_context`

### Interpretation
At `0.5 µm/px`, a `224 px` crop spans `112 µm`. Standard Visium spots are roughly `55 µm` in diameter, so this is explicitly a **spot-plus-context** contract.

### Deferred choices
The following are not part of default v1 and must be treated as later intervention axes:
- exact-spot circular masking
- alternative context window sizes
- stain normalization as a default preprocessing step

---

## 5. SplitContract

## Purpose

Defines the discovery/external holdout logic.

## Philosophy

Validation should not become a disguised cohort-specific tuning target.

## v1 requirements

### Discovery cohorts
A pooled set of discovery cohorts is used for training/validation.

### Validation logic
- deterministic **patient-level** split **within** discovery cohorts

### External cohorts
- separate **same-assay external holdout cohorts**

### Assignment rules
- patient-based
- deterministic
- hash-stable

### Prohibited design
Do not use one whole discovery cohort purely as validation if it becomes the main tuning target.

### Why
That setup risks memorizing cohort-specific batch artifacts while calling the result “generalization.”

---

## 6. LeakageContract

## Purpose

Defines how leakage is detected and what constitutes fatal overlap.

## v1 requirements

Leakage must be audited across:
- patient
- specimen
- slide

### Auditable fallback IDs
The pipeline must derive:
- `resolved_patient_id`
- `patient_id_source`

Possible `patient_id_source` values:
- `true_patient_id`
- `specimen_fallback`
- `sample_fallback`

### Namespacing rules
To avoid collisions across cohorts:
- `resolved_patient_id`
- `resolved_specimen_id`
- `resolved_slide_id`

must be namespaced using `cohort_id`.

### Null handling
Null specimen/slide IDs must remain null.
Do **not** stringify them into fake values like `cohort:null`.

### Failure behavior
If overlap is detected between any split pair, the pipeline must:
- write a fatal leakage report
- halt

---

## 7. BaselineContract

## Purpose

Defines the exact semantics of simple baseline models.

## Philosophy

Baselines must be frozen tightly enough that they cannot be quietly p-hacked.

## v1 deployable baselines

### 1. `global_train_mean`
Global mean score computed from training data only.

### 2. `mean_by_train_cohort`
Mean score for the matching training cohort.

If evaluated on an unseen external cohort with no matching training cohort, it must fall back to `global_train_mean`.

### 3. `knn_on_embeddings`
Frozen semantics:
- fit split: `train`
- `k = 20`
- metric: `cosine`
- no access to val or external test during fitting

### 4. `ridge_probe`
Frozen semantics:
- standardized features
- alpha grid: `{0.1, 1.0, 10.0}`
- fit on `train`
- tune on `val`
- evaluate on held-out split
- no access to external test during tuning

## Oracle analysis block

Analysis-only upper bounds are allowed but must be segregated.

Examples:
- `oracle_slide_mean`

They must never appear in the same category as deployable baselines.

---

## 8. BootstrapContract

## Purpose

Defines uncertainty estimation for evaluation metrics.

## Philosophy

Spot-level iid resampling is invalid for Visium because spots are correlated within slides and patients.

## v1 requirements

### Cluster unit
- cluster by `patient` when available
- otherwise fallback to `slide`

### Frozen parameters
- `n_replicates = 1000`
- deterministic seed

### Prohibited behavior
- iid spot bootstrap
- unlabeled resampling rules
- changing cluster unit between runs without declaring a new contract

---

## 9. ManifestContract

## Purpose

Defines what a valid sample/provenance record must contain.

## Philosophy

The manifest is a scientific artifact, not a convenience cache.

It must capture enough information to:
- reconstruct provenance
- audit data inclusion/exclusion
- reproduce alignment inputs
- distinguish raw from derived molecular data

## Required conceptual fields

### Identity and split
- `sample_id`
- `split`
- `cohort_id`

### Auditability
- `resolved_patient_id`
- `patient_id_source`
- optional `resolved_specimen_id`
- optional `resolved_slide_id`

### Metadata
Nested metadata block including at least:
- cohort
- assay/platform
- tissue type
- patient identifier or resolved equivalent

### Image/molecule alignment artifacts
- image URI + hash
- spatial coordinates URI + hash
- scalefactors URI + hash

### Expression artifacts
- raw expression URI + hash
- optional derived expression URI + hash

## Raw vs derived rule

A derived `.h5ad` must never masquerade as the raw assay object.

Keep raw and derived artifacts in separate fields.

---

## 10. ResolverContract

## Purpose

Defines how physical sample artifacts are discovered on disk.

## Philosophy

Do not assume one file layout.

Probe each artifact independently.

## v1 artifact classes

### Spatial coordinates
Probe candidates such as:
- `outs/spatial/tissue_positions.csv`
- `outs/spatial/tissue_positions_list.csv`
- root-level spatial fallbacks

### Scalefactors
Probe candidates such as:
- `outs/spatial/scalefactors_json.json`
- root-level fallback

### Raw expression
Probe candidates such as:
- `outs/filtered_feature_bc_matrix.h5`
- root-level fallback

### Image artifact
Priority order:
1. manifest-provided TIFF if explicitly available
2. `outs/spatial/tissue_hires_image.png`
3. project-defined root-level fallback

## Failure behavior
If an assigned sample cannot resolve required artifacts:
- record a rejection
- halt by default

---

## 11. RejectionContract

## Purpose

Defines how failed samples are handled.

## Philosophy

No silent attrition.

## v1 rules

If a sample fails resolution or validation:
- write it to a rejection ledger
- include `sample_id`
- include explicit reason

### Default behavior
- halt

### Explicit escape hatch
- `--allow-missing` may allow completion
- rejection ledger must still be written
- a visible warning must be emitted

---

## 12. EvaluationCertificate

## Purpose

Defines the minimum information required for an interpretable evaluation artifact.

## Philosophy

A single number is not enough.

## Required run-level fields

- `run_id`
- `target_definition_id`
- `alignment_contract_id`
- `split_contract_id`
- `baseline_contract_id`
- `bootstrap_contract_id`
- `intervention_axis`

## Required program-level fields

- `overall_spearman`
- `clustered_bootstrap_ci_95`
- slide/patient-level summary statistics
- deployable baseline results
- optional oracle analysis block

## Recommended summary fields
- median Spearman across slides
- IQR across slides
- worst-decile slide performance

## Multi-program handling
The certificate must make it explicit whether:
- one certificate contains `metrics_by_program`, or
- one certificate is emitted per program

---

## 13. InterventionContract

## Purpose

Defines how experimental changes are classified.

## Philosophy

A run should not pretend to support clean causal interpretation if multiple major dimensions changed at once.

## v1 allowed primary axes

- `baseline`
- `encoder`
- `spatial_context`
- `normalization`
- `target_definition`

## Rule
Every run must declare **exactly one primary intervention axis**.

Compound runs are allowed, but they must be labeled as compound and not interpreted as clean one-factor comparisons.

---

## 14. Manifest pipeline contract

## Pass 1: logical assignments
Responsibilities:
- schema discovery
- canonical field enforcement
- optional field injection
- vocabulary normalization
- cohort filtering
- deterministic split assignment
- leakage audit
- sorted assignment output

## Pass 2: physical materialization
Responsibilities:
- artifact resolution
- pre-hash validation
- hashing
- final manifest validation
- rejection ledger output
- deterministic final manifest serialization

## Determinism rule
Sort the flattened staging table before serialization, e.g.:
- `split`
- `cohort_id`
- `sample_id`

---

## 15. Contract evolution rules

Any material change to the following requires a **new contract version**:

- biological target set
- scoring implementation
- image crop definition
- split logic
- leakage resolution logic
- baseline semantics
- bootstrap unit or replicate count
- manifest schema
- evaluation certificate schema

Do not silently mutate a contract in place.

---

## 16. Summary

Spatial-CI uses contracts to force scientific honesty.

The point is not just to run models.
The point is to make it difficult to produce a believable-looking result that does not deserve belief.
