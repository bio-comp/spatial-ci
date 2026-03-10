# Spatial-CI Evaluation

This document defines how Spatial-CI evaluates morphology-to-expression models.

The purpose of this evaluation framework is **not** to maximize pretty metrics.
It is to determine whether a result is:

- biologically meaningful
- reproducible
- leakage-resistant
- transportable across cohorts
- honest about uncertainty
- worth deeper investment

---

## 1. Evaluation philosophy

Spatial-CI does **not** treat evaluation as a scoreboard.

It treats evaluation as an **evidence gate**.

A model result is only interesting if it survives:

- frozen target definitions
- frozen split logic
- frozen baseline semantics
- leakage audits
- honest clustered uncertainty
- external holdout stress testing

The central question is:

> Under fixed contracts, does morphology contain transportable signal for the target program?

---

## 2. What counts as success

A run is considered promising only if it can show all of the following:

1. meaningful performance on the intended target program
2. clear improvement over deployable baselines
3. acceptable behavior across slides/patients, not just in aggregate
4. no leakage
5. acceptable degradation on external same-assay holdout
6. reproducible artifact lineage

If those conditions are not met, the result is exploratory at best.

---

## 3. Primary evaluation task in v1

For each fixed target program, predict a per-spot biological score from H&E morphology.

### Frozen v1 target programs

- `HALLMARK_HYPOXIA`
- `HALLMARK_G2M_CHECKPOINT`
- `HALLMARK_EPITHELIAL_MESENCHYMAL_TRANSITION`

### Prediction unit

- standard Visium **spot**

### Visual input

- `spot_plus_context` crop under the frozen alignment contract

### Ground truth

- single-sample, rank-based per-spot program score from the frozen scoring contract

---

## 4. Evaluation units

Spatial-CI must track multiple units of analysis.

### Molecular unit
- spatial spot

### Image unit
- extracted image crop

### Tissue unit
- slide

### Biological unit
- patient

### Dataset unit
- cohort

These units are not interchangeable.

Spot-level metrics alone are insufficient.

---

## 5. Metrics

## 5.1 Primary metric

### Spearman correlation

For each target program, the primary metric is:

- **overall Spearman correlation** between predicted and ground-truth per-spot scores

Why:
- robust to monotonic but nonlinear relationships
- less fragile than raw linear correlation under skewed expression-derived scores
- more honest for rank-like biological program structure

---

## 5.2 Required uncertainty metric

### Clustered bootstrap CI

Report:

- `clustered_bootstrap_ci_95`

Bootstrap must respect the dependence structure:

- cluster by `patient` if patient information is available
- otherwise cluster by `slide`

### Why

Spot-level iid bootstrap is invalid for Visium because:
- spots on the same slide are correlated
- slides from the same patient are biologically related
- technical artifacts are shared within tissue sections

---

## 5.3 Required dispersion summaries

Per target program, report at minimum:

- median slide-level Spearman
- IQR of slide-level Spearman
- worst-decile slide performance

These summaries are required because:

- a strong aggregate metric can hide catastrophic failure on subsets
- the project cares about transportability and robustness, not just mean behavior

---

## 5.4 Optional secondary metrics

These are useful but secondary in v1:

- Pearson correlation
- MAE
- R²
- calibration-oriented summaries
- rank-based error summaries
- thresholded performance for exploratory analyses

These must never replace the primary required metric family.

---

## 6. Baseline evaluation

## 6.1 Philosophy

A learned model must earn its complexity.

If a simple baseline explains as much signal as a more complex model, the complex model has not justified itself.

## 6.2 Required deployable baselines

Every target program must be evaluated against:

- `global_train_mean`
- `mean_by_train_cohort`
- `knn_on_embeddings`
- `ridge_probe`

## 6.3 Analysis-only oracle checks

Oracle analyses may be reported separately for context, such as:

- `oracle_slide_mean`

These are not deployable baselines.
They exist only to show rough upper-bound intuition.

They must be segregated in reporting.

---

## 7. Split-aware evaluation

## 7.1 Discovery setting

Discovery cohorts are pooled.
Patients are deterministically assigned to:

- `train`
- `val`

within the pooled discovery set.

## 7.2 External holdout setting

External same-assay cohorts are assigned to:

- `test_external`

These cohorts are never used for tuning.

## 7.3 Interpretation rules

### Train
Used for fitting.

### Val
Used for tuning and model selection.

### Test external
Used for transportability stress testing.

No decisions may be tuned against the external set.

---

## 8. What must be evaluated per run

For each run, evaluation must be reported:

- per program
- per split
- against frozen baselines
- with clustered uncertainty
- with leakage status
- with contract identifiers attached

No anonymous metric dumps are allowed.

---

## 9. Evaluation certificate

## 9.1 Purpose

The `EvaluationCertificate` is the core output artifact of Spatial-CI evaluation.

It exists to answer:

- what was evaluated
- under which contracts
- with what uncertainty
- against what baselines
- on which data regime
- with what leakage status

## 9.2 Required run-level fields

At minimum:

- `run_id`
- `target_definition_id`
- `alignment_contract_id`
- `split_contract_id`
- `baseline_contract_id`
- `bootstrap_contract_id`
- `intervention_axis`

## 9.3 Required per-program fields

At minimum:

- `overall_spearman`
- `clustered_bootstrap_ci_95`
- `slide_summaries`
- `deployable_baselines`
- optional `oracle_analysis`

---

## 10. Intervention-aware evaluation

## 10.1 Rule

Every run must declare exactly one primary intervention axis.

Examples:
- `baseline`
- `encoder`
- `spatial_context`
- `normalization`
- `target_definition`

## 10.2 Why

If many dimensions change at once, the run is not cleanly interpretable.

Spatial-CI therefore distinguishes:

- **clean one-axis runs**
- **compound runs**

Compound runs may still be useful, but they should not be interpreted as evidence for one specific change.

---

## 11. What should trigger skepticism

A result should be treated skeptically if:

- it only beats trivial baselines by a tiny margin
- external performance collapses
- slide-level worst-decile behavior is terrible
- uncertainty intervals are wide enough to overlap baseline performance
- missing samples were allowed and rejections were large
- patient/specimen/slide fallback IDs dominate the manifest
- performance looks too good relative to weak baselines and tiny data
- the target interpretation is broader than the target contract supports

---

## 12. What should trigger failure

A run fails evaluation if any of the following occur:

- leakage detected
- required artifacts missing from certificate
- baselines omitted
- bootstrap performed iid at spot level
- target definition drifted
- external set used in tuning
- contract identifiers are missing or mismatched
- rejection handling was silent

---

## 13. Reporting style

Spatial-CI reports should emphasize:

- target program name
- contract IDs
- split regime
- baseline comparisons
- clustered uncertainty
- slide/patient summaries
- external holdout behavior
- known weaknesses

Avoid:
- “state-of-the-art” language
- inflated transportability claims
- vague references to “generalization”
- one-number summaries with no dispersion context

---

## 14. Recommended evaluation table layout

For each target program, a standard summary table should include:

- run ID
- intervention axis
- split contract ID
- overall Spearman
- 95% clustered CI
- median slide Spearman
- IQR slide Spearman
- worst-decile slide Spearman
- baseline scores:
  - global mean
  - train-cohort mean
  - kNN
  - ridge
- external holdout score
- leakage status

---

## 15. Minimum interpretation standard

A run is not considered meaningful just because Spearman is positive.

A run becomes interesting when:

- it is better than the strongest simple baseline
- the CI is credible
- slide-level behavior is not disastrous
- external degradation is tolerable
- the target semantics are honest
- the result survives the full contract stack

---

## 16. v1 evaluation goal

The goal of v1 is not to prove “virtual spatial transcriptomics is solved.”

The goal of v1 is to produce an honest answer to:

> For fixed breast Visium Hallmark programs under frozen contracts, does morphology carry enough stable signal to justify deeper work?

That is the right level of ambition.

---

## 17. Future evaluation extensions

Deferred to later versions:

- calibration contracts
- abstention/defer policies
- assay-family comparison
- isoform-aware target evaluation
- uncertainty decomposition
- subgroup fairness analyses
- region-level or neighborhood-level outcome evaluation

These may become first-class later, but are not part of the minimum v1 gate.

---

## 18. One-sentence summary

Spatial-CI evaluation exists to determine whether a morphology-to-expression claim deserves belief, not just whether a model produced an attractive number.
