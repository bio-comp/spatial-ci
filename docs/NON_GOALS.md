# Spatial-CI Non-Goals

This document defines what Spatial-CI is **not** trying to do.

The purpose of a non-goals document is to prevent scope creep, false expectations, and accidental overclaiming.

A project becomes stronger not only by knowing what it is, but by knowing what it refuses to be.

---

## 1. Why non-goals matter

Spatial-CI lives near many seductive areas:

- pathology AI hype
- spatial transcriptomics hype
- multimodal foundation-model hype
- translational medicine hype
- “future of diagnostics” hype

Without explicit non-goals, it would be easy for the project to quietly slide from:
- honest benchmark design

into:
- broad unsupported claims

This document exists to prevent that.

---

## 2. Spatial-CI is not a medical device

Spatial-CI is **not**:

- a regulated clinical product
- a pathology decision-support device
- a diagnostic workflow intended for patient care
- a validated clinical assay replacement

It is a **research platform**.

Even if a model performs well inside Spatial-CI, that does not mean it is clinically deployable.

---

## 3. Spatial-CI is not an FDA-readiness project

Spatial-CI is not trying, in v1, to produce:

- FDA submission packages
- regulatory-grade analytical validation
- production-grade device documentation
- product lifecycle controls for medical deployment

The project is **deployment-minded**, but not **deployment-ready**.

That distinction is essential.

---

## 4. Spatial-CI is not trying to replace wet-lab spatial transcriptomics

The project does **not** claim that morphology-based prediction replaces:

- spatial transcriptomics assays
- molecular pathology assays
- targeted validation workflows
- direct biological measurement

The purpose of Spatial-CI is to evaluate whether morphology carries enough signal to justify deeper work, not to declare wet-lab assays obsolete.

---

## 5. Spatial-CI is not a generic pathology benchmark zoo

Spatial-CI v1 is intentionally narrow.

It is not trying to be:

- every pathology task in one repo
- every spatial assay in one repo
- a giant pan-cancer benchmark suite
- a universal digital pathology framework

Narrowness is a strength here, not a weakness.

---

## 6. Spatial-CI is not a whole-transcriptome vanity project

v1 does **not** try to:

- predict every gene equally
- maximize transcriptome-wide coverage
- optimize for the largest possible label space
- win on leaderboard breadth

It deliberately chooses a smaller set of interpretable program-level targets.

The project values clarity over breadth.

---

## 7. Spatial-CI is not trying to discover new biology in v1

v1 is not a new-biology discovery engine.

It is not trying to:
- infer novel cell states
- discover new signatures
- generate new target definitions on the fly
- invent custom biomarker panels from benchmark behavior

The target biology is frozen on purpose.

Discovery may come later, but it is not a v1 goal.

---

## 8. Spatial-CI is not a “deep learning first” project

The project does **not** exist to showcase the most advanced model.

It is not primarily about:
- GNN novelty
- transformer novelty
- giant pathology foundation-model branding
- architecture complexity for its own sake

The model is downstream of the contracts.

If a ridge probe wins honestly, that is a valid and important result.

---

## 9. Spatial-CI is not trying to maximize headline metrics

It is not a goal to produce:
- the highest possible internal score
- the most flattering external result
- the cleanest-looking figure at all costs

The benchmark is designed to tell the truth, even if the truth is disappointing.

A negative result is acceptable.
A dishonest positive result is not.

---

## 10. Spatial-CI is not a notebook-centric research project

The source of truth should not live in notebooks.

Spatial-CI is not trying to be:
- a collection of exploratory notebooks that slowly became a pipeline
- an undocumented Jupyter ecosystem
- a benchmark that only one person can rerun interactively

Notebooks may be useful for exploration, but frozen logic must live in code and contracts.

---

## 11. Spatial-CI is not a certificate or credential substitute

Spatial-CI may become a serious public artifact and signal of mastery.

But it is **not** trying to be:
- a formal pathology credential
- a medical qualification
- a lab-director credential
- a substitute for board certification
- a shortcut to diagnostic authority

It is a research and methods platform, not a professional license.

---

## 12. Spatial-CI is not full pathology training

Working on Spatial-CI does **not** mean:
- mastering all of pathology
- replacing pathology residency/fellowship
- understanding every disease process at diagnostic depth
- becoming a signer of pathology reports

The project needs enough pathology grounding to reason honestly about morphology and assay design.
It does not claim to replace the full discipline.

---

## 13. Spatial-CI is not an isoform/splicing platform in v1

Given the broader interest in:
- intron retention
- exon skipping
- alt 5′ / alt 3′
- APA

it would be easy to force those into v1.

Spatial-CI explicitly does **not** do that in v1.

v1 is about:
- gene-program-level spatial targets
- not isoform-aware target construction
- not long-read spatial contract design
- not splicing-specific ground truth

Those are future directions, not current obligations.

---

## 14. Spatial-CI is not trying to solve transportability in one step

The project does not claim to establish:

- universal morphology-to-expression generalization
- cross-assay invariance
- cross-institution robustness for all settings
- pan-platform transportability

The external same-assay holdout in v1 is a **stress test**, not a universal guarantee.

---

## 15. Spatial-CI is not trying to make every choice optimal in theory

Some choices in v1 are pragmatic and disciplined rather than theoretically perfect.

Examples:
- focusing on Hallmark targets
- using a narrow assay scope
- preferring a stable simple stack over maximal flexibility
- privileging clear contracts over all possible modeling sophistication

The project is trying to be:
- honest
- reproducible
- useful

not metaphysically perfect.

---

## 16. Spatial-CI is not anti-model

Rejecting architecture theater does **not** mean the project is anti-modeling.

It simply means:
- model complexity must be earned
- baselines matter
- evaluation comes first
- complexity without trustworthy benchmarking is noise

The project welcomes sophisticated models once the benchmark stack has earned them.

---

## 17. Spatial-CI is not a promise that morphology is enough

A core non-goal is to avoid claiming that morphology alone is sufficient to recover the full biological truth.

Even a successful result in Spatial-CI does **not** imply:
- morphology contains all relevant information
- molecular assays are redundant
- the predicted score is a substitute for direct measurement

The whole point of the benchmark is to measure how much signal is present, not to assume total sufficiency.

---

## 18. Spatial-CI is not an excuse to ignore data engineering

A surprisingly common failure mode in research projects is treating data engineering as boring overhead.

Spatial-CI explicitly rejects that.

It is not a goal to:
- hand-wave provenance
- tolerate fuzzy manifests
- accept silent sample loss
- skip leakage audits because the model is cool

The manifest layer is part of the science.

---

## 19. Spatial-CI is not intended to hide negative results

The project is designed so that:
- failed baselines
- weak transportability
- target mismatch
- poor external generalization
- rejected samples

can all be made explicit.

This is not a project whose success depends on always looking good.

---

## 20. Spatial-CI is not meant to become a monolithic mega-framework by default

Although Spatial-CI may grow into something reusable, v1 is not trying to become:

- a giant monorepo
- a universal omics benchmarking engine
- a plug-in platform for every biomedical modality
- a grand unified pathology operating system

That kind of expansion, if it happens, should be earned after the core benchmark proves itself.

---

## 21. Spatial-CI is not a substitute for external judgment

Even if Spatial-CI is built carefully, it is still a system designed by people with assumptions.

It is not a goal to claim:
- complete objectivity
- perfect neutrality
- universal correctness of its contract choices

Instead, the goal is to make the assumptions explicit enough that others can critique them properly.

That is much more valuable.

---

## 22. Spatial-CI is not trying to be impressive at the cost of being true

This is the deepest non-goal.

Spatial-CI is not here to be:
- maximally flashy
- maximally trendy
- maximally publishable in the shallowest sense
- maximally reassuring

It is here to be:
- explicit
- falsifiable
- auditable
- scientifically honest

If that makes it less glamorous, that is acceptable.

---

## 23. One-sentence summary

Spatial-CI is not trying to be a clinical product, a credential, a pan-pathology mega-benchmark, or a model-hype machine; it is trying to be a truthful research system for evaluating morphology-to-expression claims under explicit contracts.
