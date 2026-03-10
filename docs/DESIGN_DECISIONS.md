# Spatial-CI Design Decisions

This document records the major design decisions that shaped Spatial-CI and explains why they were made.

The goal is not to preserve every conversational path.
The goal is to preserve the reasoning behind the system as it exists.

This file is intentionally opinionated.

---

## 1. Why Spatial-CI exists

Spatial-CI exists because the default way many pathology-AI and spatial-omics projects are built is too weak.

Typical weak pattern:

- broad, fuzzy task framing
- unclear biological targets
- hidden preprocessing
- leaky splits
- architecture-first thinking
- shallow baselines
- one-number reporting
- overclaiming from small external sets

Spatial-CI was designed to be the opposite:
- narrower
- more explicit
- more auditable
- less flattering
- more scientifically serious

---

## 2. Why this is a Circuit-CI descendant

Spatial-CI is not an unrelated project.
It is a domain-specific expression of the broader **Circuit-CI** worldview.

The key inherited ideas are:

- no claim without contracts
- no silent intervention surface
- no trust without provenance
- no evaluation without evidence gates
- no broad claim from weak artifacts

Circuit-CI is the general thesis.
Spatial-CI is one sharp biomedical implementation.

---

## 3. Why the project is narrow

We deliberately froze v1 to:

- breast cancer
- standard Visium
- spot-plus-context extraction
- a few Hallmark program targets
- same-assay external holdout

Why:
because a benchmark can fail by trying to do everything at once.

The narrower design improves:
- interpretability
- debugging
- biological clarity
- split integrity
- evaluation honesty

Spatial-CI is designed to answer one hard question well before it tries to answer many.

---

## 4. Why we rejected “predict the whole transcriptome” for v1

Predicting every gene sounds ambitious, but it creates several problems:

- too much biological heterogeneity
- weak interpretability
- harder debugging
- higher chance of leaderboard-style metric theater
- easier to hide failure under aggregate statistics

Program-level targets are a better first step because they are:
- more interpretable
- more robust
- easier to defend scientifically
- better aligned with visible pathology structure

---

## 5. Why we rejected hand-tuned gene lists

Hand-built gene lists are seductive because they feel understandable.

They are also dangerous because they make it easy to smuggle in:
- intuition-driven bias
- cohort-specific cleanup
- performance tuning disguised as biology
- hidden target drift

That is why Spatial-CI v1 uses unmodified Hallmark source sets instead of custom mini-signatures.

---

## 6. Why the target names became stricter

We explicitly corrected earlier semantic drift.

Examples:
- “stromal program” was too broad and misleading for `HALLMARK_EPITHELIAL_MESENCHYMAL_TRANSITION`
- “proliferation” was too broad if we were only freezing `HALLMARK_G2M_CHECKPOINT`

Spatial-CI requires **truth in advertising**:
target names must match what the contract actually defines.

This protects the project from accidentally claiming more biological specificity than the target supports.

---

## 7. Why we rejected cohort-dependent target scoring

A major turning point was realizing that some common scoring methods are too dependent on the rest of the dataset.

That is fine for exploratory analysis.
It is bad for a frozen target contract.

We wanted a target score for a single spot to depend only on that spot’s expression vector.

That led to the shift toward **single-sample, rank-based scoring**.

The deeper reason:
if the target depends on the cohort, the benchmark target can drift when the cohort changes.

That is unacceptable for Spatial-CI.

---

## 8. Why exact-spot extraction is not the default

We initially flirted with exact-spot semantics, but the geometry forced an honest correction.

At `0.5 µm/px`, a `224 px` tile spans `112 µm`.
A Visium spot is roughly `55 µm` in diameter.

That means the chosen crop inherently includes context.

Rather than pretend otherwise, Spatial-CI made the correct move:
- call the mode `spot_plus_context`
- defer exact-spot masking to a later intervention axis

This is a core Spatial-CI habit:
when the math contradicts the rhetoric, fix the rhetoric.

---

## 9. Why one whole cohort is not a good validation set

A major scientific correction was realizing that using one whole discovery cohort as validation can quietly become cohort-specific tuning.

If you tune heavily on one cohort, you are not validating generalization.
You are learning that cohort’s style.

That is why Spatial-CI moved to:
- pooled discovery cohorts
- deterministic patient-level train/val split within discovery cohorts
- separate external same-assay holdout cohorts

This is a stronger and more honest generalization design.

---

## 10. Why deterministic patient-level splitting matters

Splitting at the patient level is essential because morphology and biology are not independent across samples from the same patient.

If related samples leak across splits, the model can appear to generalize by memorizing patient-specific structure.

Deterministic hashing was chosen because it gives:
- reproducibility
- stability across reruns
- easy reconstitution from identifiers

The split assignment itself becomes an artifact, not a hidden side effect.

---

## 11. Why fallback provenance became first-class

One of the sharpest data-engineering insights was this:

If patient IDs are missing, naïvely falling back to `sample_id` can create **false separation** and silently permit leakage.

That led to two critical design choices:

1. derive `resolved_patient_id` using a strict fallback order
2. persist `patient_id_source` into the final manifest

This turns uncertain identity resolution into an auditable property of the dataset, not an invisible guess.

---

## 12. Why namespacing IDs matters

Generic specimen or slide IDs can collide across cohorts.

Without namespacing, you can create:
- fake leakage alarms
- fake uniqueness
- ambiguous audit reports

That is why Spatial-CI namespaces:
- patient
- specimen
- slide

using `cohort_id`.

This is subtle, but critical for cross-cohort benchmarking.

---

## 13. Why the manifest builder is two-pass

A single monolithic pipeline that both:
- experiments with metadata logic
- and hashes gigabyte-scale pathology artifacts

is a bad engineering loop.

The two-pass design separates:

### Pass 1
logical inclusion/exclusion, splits, audit

### Pass 2
physical provenance and hashing

This improves:
- speed
- debugging
- resumability
- audit clarity

It also cleanly separates “which samples belong?” from “what exact files back those samples?”

---

## 14. Why the resolver became artifact-by-artifact

Assuming one filesystem layout is brittle.

Different cohorts and tool versions can vary in:
- file names
- directory depth
- Space Ranger version
- project-specific derived artifacts

That is why Spatial-CI resolves each required artifact independently rather than assuming one global root structure.

This was one of the most important robustness upgrades in the pipeline.

---

## 15. Why scalefactors became required

Coordinates alone are not enough to reconstruct alignment.

The alignment contract is only physically meaningful if the scaling relationship between:
- array geometry
- spatial coordinates
- downsampled image
- original image

is preserved.

That is why `scalefactors_json.json` became a required artifact in the manifest.

Without it, the spot-to-pixel contract is incomplete.

---

## 16. Why raw and derived expression files are separated

A derived `.h5ad` is not the same scientific artifact as the raw 10x matrix.

Conflating them destroys provenance.

Separating:
- raw expression artifact
- derived expression artifact

was therefore mandatory.

This matters because a model result should be traceable to the true assay artifact, not just to a convenient derived file.

---

## 17. Why we added a rejection ledger

A benchmark can rot if missing or hard-to-resolve samples disappear silently.

That kind of quiet attrition can systematically bias:
- the external test set
- the apparent transportability
- the stability of conclusions

That is why Spatial-CI requires:
- a rejection ledger
- halt-by-default behavior
- explicit `--allow-missing` escape hatch if necessary

This is one of the strongest anti-self-deception features in the project.

---

## 18. Why we separated deployable baselines from oracle analyses

A big evaluation correction was noticing that some baseline ideas were actually oracles in disguise.

Example:
- `mean_by_slide` on test data is not a deployable baseline if it uses test-label information

That led to the explicit split:

### Deployable baselines
- fair, usable without test labels

### Oracle analyses
- useful as upper-bound context
- never to be presented as honest baseline competitors

This distinction is essential for evaluation integrity.

---

## 19. Why the model must earn complexity

Spatial-CI rejects architecture theater.

A complex spatial model is only justified if it clearly beats:
- trivial baselines
- simple embedding-space baselines
- linear probes

The default progression is:

1. simple statistics
2. kNN / ridge on frozen embeddings
3. simple learned head
4. more complex spatial context
5. only then deeper complexity

This keeps the project focused on scientific signal, not neural-network aesthetics.

---

## 20. Why the bootstrap must be clustered

Visium spots are not iid.

Treating them as iid yields overconfident uncertainty estimates.

Spatial-CI therefore requires clustered bootstrap by:
- patient when available
- otherwise slide

This was one of the key moments where the project stopped being “good ML hygiene” and became genuinely decision-grade.

---

## 21. Why the project is not called deployable

We explicitly corrected earlier language that implied the system was close to deployment.

It is not.

Spatial-CI is a:
- deployment-minded validation scaffold
- decision-grade research platform
- rigorous research system

It is **not**:
- a clinical product
- a diagnostic system
- an FDA-ready package

This linguistic correction matters because overclaiming is part of what Spatial-CI exists to prevent.

---

## 22. Why spatial transcriptomics is central but not magical

Spatial transcriptomics matters because pathology is fundamentally spatial.

But standard spatial assays have limitations:
- resolution constraints
- assay chemistry constraints
- often gene-level rather than isoform-level readouts
- cost and complexity barriers

That is why Spatial-CI v1 focuses on:
- gene-program-level signals
- same-assay validation
- morphology-to-expression contracts

rather than pretending the whole future is already solved.

---

## 23. Why isoform / splicing / APA were deferred

Given the user’s background, it was tempting to push into:

- exon skipping
- alt 5′ / alt 3′
- intron retention
- APA

But these sit more naturally in:
- long-read spatial methods
- targeted isoform-aware assays
- later-stage, more advanced contract design

They were deferred because v1 should first establish trustworthy gene-program benchmarking.

This was a discipline decision, not a rejection of that biology.

---

## 24. Why the project name is Spatial-CI

The name works because it:
- preserves lineage with Circuit-CI
- signals spatial biology/pathology
- is short, memorable, and extensible
- leaves room for future growth beyond one assay or task

Spatial-CI is broad enough to grow into:
- spatial gene-program validation
- isoform-aware spatial work
- multimodal pathology contracts
- future domain-specific subpackages

---

## 25. Why this project matters

Spatial-CI is designed to be more than a portfolio piece.

It is intended to embody a specific point of view:

> pathology AI should be judged by explicit contracts, frozen targets, leakage-resistant data engineering, honest baselines, and transportability-aware evaluation.

That is the real product.

The code exists to express that thesis concretely.

---

## 26. What would count as failure of the design

The design would have failed if it allowed:

- drifting biological targets
- cohort-specific validation theater
- silent sample attrition
- baseline cheating
- fake uncertainty
- filesystem-assumption brittleness
- provenance collapse
- semantic overclaiming

Every major decision in Spatial-CI was made to push against one of those failure modes.

---

## 27. What would count as success of the design

The design succeeds if it makes the following possible:

- honest negative results
- reproducible positive results
- auditable data inclusion/exclusion
- interpretable comparisons across runs
- robust external stress testing
- scientific trust in the benchmark itself

That is a stronger success criterion than “high metric.”

---

## 28. Final design thesis

Spatial-CI is built on one core belief:

> The most valuable thing in high-stakes computational biology is not another model. It is a system that makes weak claims hard to produce and strong claims easier to recognize.

That is the design center of the entire project.
