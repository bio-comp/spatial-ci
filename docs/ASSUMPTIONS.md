# Spatial-CI Assumptions

This document records the major assumptions Spatial-CI makes in its current design.

The purpose of this file is not to pretend the project is assumption-free.
The purpose is to make the assumptions explicit enough that they can be:

- inspected
- challenged
- revised
- versioned
- audited

A hidden assumption is a quiet source of benchmark corruption.
An explicit assumption is a design choice.

---

## 1. Why an assumptions document exists

Every serious research system is built on assumptions.

In Spatial-CI, those assumptions affect:

- target meaning
- split validity
- provenance trust
- model interpretation
- evaluation credibility
- claim strength

The worst assumptions are not the controversial ones.
The worst assumptions are the ones nobody notices because they were never written down.

This document exists to reduce that category.

---

## 2. Meta-assumption: explicitness is better than false objectivity

Spatial-CI assumes that it is better to make assumptions explicit than to pretend the benchmark is neutral or assumption-free.

This means:
- design choices should be named
- defaults should be justified
- frozen versions should exist
- critique is expected

Spatial-CI is not built on the fantasy of perfect objectivity.
It is built on the discipline of explicit objectivity constraints.

---

## 3. Scientific scope assumptions

## 3.1 Breast cancer is a reasonable first disease domain
Spatial-CI assumes breast cancer is a defensible first domain for v1 because:

- it is biologically rich
- it has public spatial datasets
- it offers plausible morphology-linked programs
- it is narrow enough to keep the benchmark interpretable

This does **not** imply that breast cancer is representative of all pathology domains.

## 3.2 Standard Visium is a reasonable first assay
Spatial-CI assumes standard Visium is a reasonable first assay family because:

- it is widely used
- public paired image + spatial datasets exist
- spot-level geometry is interpretable enough to formalize
- it is a practical first target for a contract system

This does **not** imply that Visium is the best or final assay for all future Spatial-CI work.

## 3.3 Same-assay external holdouts are a meaningful first transportability test
Spatial-CI assumes that same-assay external cohorts are a useful first stress test for transportability.

This is a weaker claim than “broad generalization,” but stronger than internal validation alone.

---

## 4. Biological target assumptions

## 4.1 Program-level targets are appropriate for v1
Spatial-CI assumes that program-level biological targets are more appropriate for a first benchmark than:
- full transcriptome prediction
- raw count prediction
- isoform-aware targets
- de novo biology discovery tasks

The assumption is that interpretability and robustness matter more than maximal label breadth in v1.

## 4.2 Hallmark sets are an acceptable source of target biology
Spatial-CI assumes that unmodified Hallmark gene sets are a defensible starting source for target definitions because they are:
- standardized
- public
- broadly interpretable
- easier to defend than ad hoc signatures

This does **not** imply they are the perfect biological ontology.

## 4.3 The chosen v1 targets are plausible morphology-linked programs
Spatial-CI assumes that the following are plausible first morphology-to-expression targets:

- `HALLMARK_HYPOXIA`
- `HALLMARK_G2M_CHECKPOINT`
- `HALLMARK_EPITHELIAL_MESENCHYMAL_TRANSITION`

This does **not** imply:
- all are equally learnable
- all have clean single-process semantics
- morphology must contain strong signal for all of them

## 4.4 EMT/mesenchymal signal is not equivalent to a pure stromal state
Spatial-CI explicitly assumes that:
- `HALLMARK_EPITHELIAL_MESENCHYMAL_TRANSITION` is best interpreted as an EMT/mesenchymal-like program
- not a pure CAF or stromal state

This is a semantic assumption designed to prevent overclaiming.

---

## 5. Scoring assumptions

## 5.1 Single-sample scoring is preferable for frozen benchmark targets
Spatial-CI assumes that a score depending only on the current spot’s expression vector is better suited to frozen benchmarking than a score that depends materially on cohort-wide composition.

This assumption drives the preference for single-sample rank-based scoring in v1.

## 5.2 Ranking-based program scoring is sufficiently stable for v1
Spatial-CI assumes that rank-based scoring is an acceptable compromise between:
- biological interpretability
- robustness
- sample independence
- implementation practicality

This does **not** imply it is the best possible scoring method in all settings.

## 5.3 A 10% missing-gene threshold is a reasonable v1 policy
Spatial-CI assumes that:
- dropping a spot for a program when more than 10% of program genes are missing
- and scoring on the intersection otherwise

is a reasonable operational rule for v1.

This is a policy assumption, not a law of nature.

---

## 6. Alignment assumptions

## 6.1 Spot-plus-context is the correct honesty-preserving default
Spatial-CI assumes that with a 224 px crop at 0.5 µm/px, the image task is honestly described as **spot-plus-context**, not exact-spot-only.

This is a geometric assumption grounded in the crop/spot size relationship.

## 6.2 Context is biologically relevant
Spatial-CI assumes that the local tissue neighborhood likely contains biologically meaningful information for spatial program prediction.

This is why spot-plus-context is not treated as contamination by default.

## 6.3 Scalefactors are required for reconstructable alignment
Spatial-CI assumes that coordinates alone are insufficient for fully reconstructable alignment and that scalefactor metadata is part of the minimum valid alignment provenance chain.

---

## 7. Split and leakage assumptions

## 7.1 Patient-level split is the correct default exclusion unit
Spatial-CI assumes that the patient is the correct default biological exclusion unit for v1.

Why:
- related samples from the same patient may share morphology and biology
- splitting them across train and val/test can produce misleadingly good performance

This does **not** imply patient is always the only correct unit in every future assay or task.

## 7.2 Specimen and slide leakage are still meaningful risks
Spatial-CI assumes that even if patient-level exclusion is enforced, specimen-level and slide-level overlap still matter enough to audit explicitly.

## 7.3 Fallback identity resolution is weaker than true patient identity
Spatial-CI assumes that:
- specimen-as-patient
- sample-as-patient

are weaker identity proxies than true patient IDs.

That is why fallback provenance must be preserved in the manifest.

## 7.4 Deterministic hash-based split assignment is acceptable
Spatial-CI assumes deterministic hash-based assignment is a reasonable way to stabilize patient-level train/val splits for a benchmark.

This is a reproducibility assumption, not a claim that hash-based splitting is universally optimal.

---

## 8. Provenance assumptions

## 8.1 File hashes are a meaningful provenance anchor
Spatial-CI assumes that content hashes (for example, SHA256) are a valid and useful way to detect whether the same artifact is being reused.

## 8.2 Raw and derived expression artifacts are scientifically distinct
Spatial-CI assumes that:
- raw assay outputs
- derived analysis files such as `.h5ad`

must be treated as different objects.

This is both a provenance assumption and a scientific one.

## 8.3 Rejection ledgers improve honesty
Spatial-CI assumes that recording rejected samples explicitly is better than silently continuing with a smaller benchmark.

This assumption underlies the halt-by-default rejection policy.

---

## 9. Baseline assumptions

## 9.1 Simple baselines are meaningful comparators
Spatial-CI assumes that the following baselines are meaningful reference points:

- global mean
- train-cohort mean
- kNN on embeddings
- ridge on embeddings

This assumption is central to the “earn the network” philosophy.

## 9.2 Oracle analyses are useful only when clearly segregated
Spatial-CI assumes that oracle-style upper bounds may be informative, but only if they are clearly separated from honest deployable baselines.

## 9.3 Beating weak baselines is not enough
Spatial-CI assumes that model success should be judged against the strongest honest simple baseline, not merely the easiest baseline to beat.

---

## 10. Evaluation assumptions

## 10.1 Spearman is a reasonable primary metric for v1
Spatial-CI assumes Spearman correlation is a defensible primary metric because:
- target scores are program-like and often rank-interpretable
- monotonic structure matters
- it is less brittle than pure linear assumptions

This does **not** imply Spearman is sufficient on its own.

## 10.2 Spot-level iid bootstrap is invalid
Spatial-CI assumes that iid spot bootstrap is misleading for Visium because:
- spots are spatially correlated
- slides share technical context
- patients can contribute higher-level structure

## 10.3 Clustered bootstrap is good enough for v1
Spatial-CI assumes clustered bootstrap by patient, or slide when patient is unavailable, is an acceptable uncertainty approach for v1.

This is a practical methodology assumption, not a universal endpoint for future uncertainty work.

## 10.4 Slide-level summaries are necessary
Spatial-CI assumes that mean-only reporting is too weak and that grouped summaries like:
- median
- IQR
- worst decile

are necessary to understand robustness.

---

## 11. Experiment assumptions

## 11.1 One primary intervention axis improves interpretability
Spatial-CI assumes that requiring each run to name one primary intervention axis improves clarity and reduces experiment soup.

## 11.2 Compound experiments are real but weaker for interpretation
Spatial-CI assumes that experiments with multiple moving parts may still be useful, but support weaker claims.

## 11.3 A run config should be enough to reconstruct intent
Spatial-CI assumes that if contracts, configs, manifests, and outputs are preserved, another person should be able to reconstruct what the run was supposed to test.

---

## 12. Modeling assumptions

## 12.1 A pretrained encoder is the right starting point
Spatial-CI assumes that v1 should not train a pathology backbone from scratch.

The assumption is that:
- representation reuse is practical
- benchmark integrity matters more than backbone novelty
- modeling novelty is not the primary contribution of the system

## 12.2 Complexity should be earned
Spatial-CI assumes that complex spatial/context models should not be introduced until:
- baselines are working
- simple learned heads are established
- the benchmark can already tell the truth

## 12.3 A negative modeling result is scientifically valuable
Spatial-CI assumes that a result such as “ridge is as good as the MLP” is a valid and important scientific output, not a project failure.

---

## 13. Claim assumptions

## 13.1 Claims are conditional
Spatial-CI assumes every serious claim is conditional on:
- contracts
- artifacts
- evaluation logic
- uncertainty
- external holdout scope

This is why claim statements should be narrow and structured.

## 13.2 External holdout results are stress tests, not universal guarantees
Spatial-CI assumes that v1 external holdout behavior supports limited transportability claims, not broad universality claims.

## 13.3 Negative claims are legitimate
Spatial-CI assumes that statements like:
- “insufficient evidence for morphology-linked signal”
- “complex model adds nothing beyond ridge”
- “external signal is weak”

are acceptable and valuable outputs.

---

## 14. Infrastructure assumptions

## 14.1 uv + lockfile is sufficient for environment freezing
Spatial-CI assumes that:
- `pyproject.toml`
- `uv.lock`

are sufficient to freeze the environment for practical reproducibility, assuming platform-specific caveats are handled honestly.

## 14.2 Base environment and GPU extras should be separated
Spatial-CI assumes it is better to keep:
- base CPU-safe dependencies
- optional Linux/GPU-specific extras

separate, rather than forcing one bloated environment on all users.

## 14.3 Scripts are the source of truth, not notebooks
Spatial-CI assumes frozen logic should live in:
- scripts
- modules
- contracts
- configs

and not only in notebooks.

---

## 15. Assumptions that are intentionally weak

Some assumptions in Spatial-CI are deliberately held weakly and may change in future versions.

Examples:
- the exact scoring implementation choice
- the best external holdout cohort mix
- the best spatial context architecture
- the eventual best target family
- the optimal bootstrap design

These are treated as versionable design assumptions, not eternal truths.

---

## 16. Assumptions that should be hardest to change

Some assumptions are more foundational and should not be changed casually:

- no silent attrition
- explicit contracts
- patient-aware leakage discipline
- truth in advertising for targets
- explicit provenance
- no oracle baselines disguised as fair ones
- clustered rather than iid uncertainty for Visium

Changing any of these would alter the identity of Spatial-CI itself.

---

## 17. What this document is trying to prevent

This assumptions document is specifically meant to prevent:

- accidental dogmatism
- hidden benchmark ideology
- silent contract drift
- vague future rewrites of what the project “always meant”

If the project changes, the assumptions should change explicitly with it.

---

## 18. One-sentence summary

Spatial-CI assumes many things, but it treats those assumptions as auditable design choices rather than invisible truths.
