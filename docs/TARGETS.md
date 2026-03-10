# Spatial-CI Targets

This document defines the biological target philosophy for Spatial-CI and freezes the target scope for v1.

The purpose of this document is to prevent one of the most common failure modes in computational biology and pathology AI:

> changing the biological meaning of the target while pretending the task stayed the same.

Spatial-CI treats target biology as a first-class scientific artifact.

---

## 1. Target philosophy

Spatial-CI does **not** allow vague or drifting biological targets.

A valid target definition must be:

- explicit
- versioned
- interpretable
- reproducible
- independent of the model being tested

A target is not just “what the label file contains.”
A target is a scientific claim about what signal we are trying to predict.

---

## 2. What we are predicting in v1

Spatial-CI v1 predicts **per-spot biological program scores** from H&E morphology.

This is **not** the same as:

- predicting raw counts directly
- predicting every gene equally
- predicting full transcript structure
- discovering novel target biology on the fly

Instead, v1 predicts a small number of fixed, predeclared **program-level signals**.

---

## 3. Why program-level targets

We chose program-level targets because they are a better fit for a first serious Spatial-CI build than transcriptome-wide direct prediction.

Reasons:

- more biologically interpretable
- more robust than individual genes
- easier to compare across cohorts
- less vulnerable to noise in single genes
- better aligned with morphological plausibility
- easier to evaluate honestly

This does **not** mean gene-level prediction is unimportant.
It means v1 should optimize for scientific clarity rather than maximal scope.

---

## 4. Why not custom signatures

Spatial-CI v1 does **not** use custom hand-built signatures.

We explicitly reject:
- ad hoc mini-gene lists
- targets assembled by intuition alone
- dropping genes because they “look noisy”
- modifying signatures based on behavior in the training data
- “breast-specific cleanup” unless versioned as a derived target

Why:
because hand-tuned targets are one of the easiest ways to leak prior beliefs and overfit without admitting it.

---

## 5. Source of truth for v1 targets

The source of truth for v1 target biology is:

- **MSigDB Hallmark gene sets**

These are used because they are:
- public
- standardized
- widely recognized
- interpretable at the program level
- easier to defend than custom lists

---

## 6. Frozen v1 target definition

### Identifier
`target_definition_id = "breast_visium_hallmarks_v1"`

### Source database
`msigdb_hallmark_v2023.1`

### Tissue modification
`is_tissue_modified = false`

### Allowed programs
- `HALLMARK_HYPOXIA`
- `HALLMARK_G2M_CHECKPOINT`
- `HALLMARK_EPITHELIAL_MESENCHYMAL_TRANSITION`

This target set is frozen for v1.

---

## 7. Interpretation rules

Spatial-CI requires **truth in advertising** when naming and interpreting targets.

### 7.1 HALLMARK_HYPOXIA
Interpretation:
- hypoxia-response program
- oxygen-deprivation-associated transcriptional response

What it is **not**:
- direct HIF1A abundance
- a perfect readout of hypoxic state under all conditions
- a pure microenvironment-only variable

### 7.2 HALLMARK_G2M_CHECKPOINT
Interpretation:
- G2M/cell-cycle program
- proliferation-related cell-cycle activity

What it is **not**:
- a generic “all proliferation everywhere” claim unless explicitly described that way in a derived target
- a direct measure of mitotic rate at single-cell precision

### 7.3 HALLMARK_EPITHELIAL_MESENCHYMAL_TRANSITION
Interpretation:
- EMT/mesenchymal program

What it is **not**:
- a pure stromal program
- a pure CAF-state target
- a clean fibroblast-only signal

Spatial-CI explicitly forbids relabeling this as “stromal program” without qualification.

---

## 8. Why these targets were chosen

These programs were selected because they are plausible first targets for morphology-to-expression prediction.

### 8.1 Hypoxia
Why useful:
- biologically important in tumors
- connected to tumor architecture, necrosis, vascular limitation, and microenvironmental gradients
- plausible to carry morphological correlates

### 8.2 G2M checkpoint
Why useful:
- strongest morphology-linked target in the set
- tied to proliferative activity
- easier to defend as visually learnable than many other programs

### 8.3 EMT / mesenchymal program
Why useful:
- captures a major tissue-state program
- likely tied to morphology and tissue organization
- valuable as a harder, more ambiguous target

Why dangerous:
- can be confounded by stromal composition
- must not be oversold as a pure fibroblast or CAF label

---

## 9. What was explicitly deferred

The following targets or target families were explicitly deferred out of v1:

- T-cell exhaustion programs
- custom stromal/CAF subtype programs
- immune-state subtype signatures
- isoform-aware targets
- intron retention targets
- alternative 5′/3′ splice targets
- APA targets
- whole-transcriptome direct objectives

These are not rejected forever.
They are deferred because v1 needs a narrower and more defensible scope.

---

## 10. Target scoring philosophy

A target program is not fully defined until its scoring rule is frozen.

Spatial-CI requires the target score for a spot to be:
- single-sample
- sample-independent
- deterministic under a frozen implementation
- auditable with respect to missing genes

This is why v1 moved away from dataset-dependent scoring methods as the primary target definition.

---

## 11. Frozen scoring direction

Spatial-CI v1 uses **R/Bioconductor singscore** for target scoring.

The scorer is run as an R script (`scripts/score_targets.R`), and the R environment is frozen via `renv.lock`.

The critical requirement is not the brand name of the scorer.
The critical requirement is that the score for one spot depends only on that spot's expression vector, and that the scoring environment is reproducible.

Score artifacts are produced by R and consumed by Python for downstream evaluation.

---

## 12. Missing-gene policy

Target scoring must handle incomplete detection honestly.

### Frozen v1 rule
For a given spot and target program:

- if more than **10%** of the program genes are missing from the detected transcript pool, drop that spot for that program
- if **10% or fewer** are missing, score on the intersection and record the condition

This is a scientific policy, not just an implementation detail.

---

## 13. What counts as target drift

Target drift occurs when the biological meaning of the target changes without a version change.

Examples of forbidden target drift:

- removing genes because they hurt performance
- adding genes because they improve cross-cohort robustness
- swapping scoring methods without minting a new target/scoring contract
- renaming EMT to stromal
- combining Hallmark sets while still calling them by the original set name
- filtering genes differently per cohort

Any of those require a **new contract version**.

---

## 14. Derived targets

Spatial-CI allows derived targets, but only if they are explicitly versioned.

Example of acceptable derived target:
- `proliferation_union_v2 = union(HALLMARK_E2F_TARGETS, HALLMARK_G2M_CHECKPOINT)`

Rules for derived targets:
- must have a new identifier
- must document the source sets
- must document the derivation rule
- must not masquerade as an unmodified Hallmark target

v1 does **not** use derived targets by default.

---

## 15. Target plausibility vs target truth

Spatial-CI distinguishes between:

### Biological target truth
What the molecular program score actually means.

### Morphological plausibility
Whether that target is likely to leave a visible footprint in tissue architecture.

A target can be biologically valid but visually implausible.
That does not make the target bad.
It makes it a risky first benchmark target.

v1 therefore privileges targets that are:
- biologically meaningful
- but also plausibly morphology-linked

---

## 16. What Spatial-CI is not doing with targets

Spatial-CI v1 is **not**:

- claiming the targets are perfect representations of ground truth biology
- claiming the program score is clinically sufficient
- claiming morphology alone can fully reconstruct the program
- claiming all target errors are equally important
- claiming all Hallmark sets are equally learnable from morphology

It is testing whether these fixed target definitions are learnable enough to justify deeper work.

---

## 17. Target documentation requirements

Every target definition in Spatial-CI must document:

- identifier
- source database/version
- exact allowed programs
- interpretation rules
- scoring implementation
- missing-gene policy
- whether tissue modification is allowed
- whether the target is source-faithful or derived

If any of these are missing, the target definition is incomplete.

---

## 18. v1 target summary

Spatial-CI v1 uses three fixed Hallmark-derived program targets:

- `HALLMARK_HYPOXIA`
- `HALLMARK_G2M_CHECKPOINT`
- `HALLMARK_EPITHELIAL_MESENCHYMAL_TRANSITION`

These are chosen because they are:
- standardized
- interpretable
- plausibly morphology-linked
- narrow enough for a serious first benchmark

They are scored with a single-sample ranking-based method under a frozen contract.

---

## 19. Future target expansions

Likely future directions include:

- derived proliferation programs
- carefully defined immune-state programs
- targeted isoform/junction-aware targets
- intron-retention-aware targets
- APA-aware targets
- long-read-informed spatial targets
- region/neighborhood-level composite targets

But none of these belong in frozen v1 unless explicitly versioned.

---

## 20. One-sentence summary

Spatial-CI targets are fixed, versioned biological programs designed to make morphology-to-expression claims scientifically interpretable rather than cosmetically impressive.
