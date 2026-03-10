# Spatial-CI Roadmap

This document defines the phased roadmap for Spatial-CI.

The purpose of this roadmap is to keep the project disciplined.
Spatial-CI should grow by proving one layer at a time, not by accumulating fashionable complexity.

The roadmap is organized around a simple principle:

> first make the benchmark tell the truth, then make the model more ambitious.

---

## 1. Roadmap philosophy

Spatial-CI is not a “build everything” project.

It is a staged research platform with explicit maturity levels:

1. define the contracts
2. materialize the data honestly
3. establish frozen targets
4. prove the baselines
5. run the simplest meaningful learned model
6. only then add complexity
7. only then expand scope

This order is intentional.

---

## 2. Phase 0 — project foundation

## Goal
Create the project skeleton and freeze the core documents.

## Deliverables
- `README.md`
- `docs/CONTRACTS.md`
- `docs/EVALUATION.md`
- `docs/MANIFEST_PIPELINE.md`
- `docs/TARGETS.md`
- `docs/SCORING.md`
- `docs/DESIGN_DECISIONS.md`
- `docs/ROADMAP.md`

## Success criteria
- all major scientific assumptions written down
- contract vocabulary stable enough to code against
- repo identity clear

---

## 3. Phase 1 — environment and schema freezing

## Goal
Freeze the software environment and the minimum schema layer.

## Tasks
- finalize `pyproject.toml`
- generate and commit `uv.lock`
- set up R/renv environment
- generate and commit `renv.lock` for scoring dependencies
- install singscore and required Bioconductor packages
- define the Pydantic schemas for:
  - target definition
  - alignment contract
  - split contract
  - baseline contract
  - bootstrap contract
  - sample manifest
  - evaluation certificate
- add schema tests

## Success criteria
- Python environment reproducible on supported systems
- R scoring environment locked via renv
- contracts are importable and testable
- no placeholder fields remain in core schemas

---

## 4. Phase 2 — manifest pipeline v1

## Goal
Build the two-pass manifest pipeline and prove it on real data.

## Tasks

### Pass 1
- schema discovery for raw metadata
- canonical mapping
- optional-column injection
- vocabulary normalization
- resolved patient/specimen/slide IDs
- deterministic patient-level train/val split within discovery cohorts
- external holdout designation
- fatal leakage checks
- sorted `assignments.ndjson`

### Pass 2
- path mapping or sample directory resolution
- artifact-by-artifact resolver
- pre-hash validation
- hash required artifacts
- final `SampleManifest` validation
- rejection ledger
- sorted `manifest.ndjson`

## Success criteria
- literal manifest exists
- leakage checks are real, not hypothetical
- all missing samples are explainable
- no silent attrition
- deterministic reruns produce identical manifests

---

## 5. Phase 3 — target scoring v1

## Goal
Materialize the frozen per-spot biological targets using R singscore.

## Tasks
- finalize the scoring contract (with renv.lock reference)
- implement target scoring in R:
  - scripts/score_targets.R
  - uses Bioconductor singscore
  - environment locked via renv
- score targets:
  - HALLMARK_HYPOXIA
  - HALLMARK_G2M_CHECKPOINT
  - HALLMARK_EPITHELIAL_MESENCHYMAL_TRANSITION
- apply missing-gene policy
- generate score artifacts in Parquet format with provenance
- verify score reproducibility on rerun
- generate descriptive score distribution summaries

## Success criteria
- target scores exist for all eligible spots
- dropped spots are auditable by program
- scores are reproducible under frozen R environment (renv.lock)
- target score artifacts link back to:
  - expression artifact hashes
  - scoring contract ID
  - renv.lock hash

---

## 6. Phase 4 — baseline-only benchmark

## Goal
Prove the benchmark before adding learned models.

## Tasks
- implement:
  - `global_train_mean`
  - `mean_by_train_cohort`
  - `knn_on_embeddings`
  - `ridge_probe`
- emit baseline evaluation certificates
- compute clustered bootstrap CIs
- summarize slide/patient dispersion
- document oracle analyses separately if used

## Success criteria
- baseline results are reproducible
- evaluation pipeline can emit valid certificates
- external same-assay holdout works end-to-end
- slide/patient summaries are stable and interpretable

## Why this matters
If the benchmark cannot truthfully evaluate baselines, it has no right to evaluate deep models.

---

## 7. Phase 5 — simple learned model

## Goal
Introduce the simplest meaningful learned morphology-to-expression model.

## Tasks
- choose frozen pathology feature extractor
- implement pooled embedding + linear/MLP prediction head
- train under frozen split contract
- compare against frozen baselines
- emit evaluation certificate
- document whether complexity is justified

## Success criteria
- learned model beats the strongest honest simple baseline for at least some targets
- external degradation is not catastrophic
- clustered uncertainty is credible
- results are interpretable in light of target semantics

---

## 8. Phase 6 — local spatial context

## Goal
Test whether modest spatial/context modeling adds real value.

## Tasks
- implement one context-aware extension
- declare `spatial_context` as the intervention axis
- compare only against the simpler learned model under unchanged contracts
- evaluate whether context improves external holdout behavior or just inflates internal fit

## Success criteria
- context model provides real incremental evidence
- improvement is not limited to internal discovery data
- added complexity is justified by the evaluation certificate

---

## 9. Phase 7 — first writeup

## Goal
Produce the first serious artifact that demonstrates Spatial-CI as a scientific system.

## Candidate outputs
- technical memo
- long-form design report
- benchmark-style manuscript draft
- methods preprint skeleton

## Required contents
- exact contracts used
- manifest generation procedure
- scoring policy
- baseline and simple-model results
- leakage policy
- external holdout behavior
- limitations

## Success criteria
- another person could reproduce the logic
- negative results would still be publishable internally
- the writeup is honest about scope and non-claims

---

## 10. Phase 8 — v2 scope expansion

Only after v1 is solid.

Possible expansion directions:
- exact-spot masking as an intervention
- stain normalization as a declared axis
- additional discovery/external cohorts
- alternate program targets
- derived target sets
- stronger spatial models
- uncertainty calibration work
- assay-family comparisons

Expansion should happen only after the baseline platform is trustworthy.

---

## 11. Phase 9 — isoform / splicing / APA track

This is intentionally later.

## Why deferred
Spatial-CI v1 is about getting the gene-program benchmark right.

Isoform-aware spatial biology introduces:
- different assay assumptions
- different target construction
- different truth layers
- likely different validation regimes

## Future directions
- targeted junction-aware targets
- intron-retention-aware scoring
- APA-aware targets
- long-read-informed spatial contracts
- hybrid short-read / long-read validation layers

This is a likely future branch, not a v1 obligation.

---

## 12. Phase 10 — generalized Spatial-CI platform

Once v1 and early v2 are proven, Spatial-CI may evolve from a single benchmark into a reusable framework.

Possible longer-term components:
- reusable contract package
- reusable evaluation certificate engine
- reusable manifest builder
- plug-in scoring contracts
- plug-in assay resolvers
- domain-specific extensions beyond breast Visium

This is optional.
It should be earned, not assumed.

---

## 13. Recommended order of implementation

The order below is strongly preferred:

1. docs
2. schemas
3. environment
4. manifest pipeline
5. target scoring
6. baseline evaluation
7. simple learned model
8. context model
9. writeup
10. scope expansion

If this order gets violated, the project risks turning into model theater.

---

## 14. What not to do too early

Avoid these traps in early phases:

- training a fancy model before the manifest is frozen
- changing targets while evaluating
- adding multiple assay families at once
- introducing isoform targets before program-level truth is stable
- treating external holdouts as hyperparameter playgrounds
- over-optimizing on a tiny external set
- writing big claims before baseline evaluation is honest

---

## 15. Milestone checklist

## Milestone A — documents frozen
- [ ] README
- [ ] contracts docs
- [ ] scoring doc
- [ ] roadmap doc

## Milestone B — schemas frozen
- [ ] all contract models defined
- [ ] tests pass
- [ ] uv.lock committed
- [ ] renv.lock committed

## Milestone C — manifest frozen
- [ ] assignments artifact generated
- [ ] final manifest generated
- [ ] leakage report clean
- [ ] rejection ledger understood

## Milestone D — targets frozen
- [ ] renv.lock generated and committed
- [ ] score artifacts generated via R singscore
- [ ] missing-gene handling verified
- [ ] score provenance recorded (including renv.lock hash)

## Milestone E — baseline benchmark complete
- [ ] deployable baselines run
- [ ] evaluation certificates emitted
- [ ] clustered CIs computed

## Milestone F — simple learned model complete
- [ ] model beats honest baselines where appropriate
- [ ] external holdout behavior documented

## Milestone G — first writeup complete
- [ ] methods documented
- [ ] results summarized
- [ ] limitations explicit

---

## 16. Definition of done for v1

Spatial-CI v1 is "done" only when all of the following are true:

- contracts are frozen and documented
- Python environment is locked (uv.lock)
- R scoring environment is locked (renv.lock)
- manifest is deterministic and auditable
- target scores are reproducible (via R singscore)
- baselines are implemented and evaluated honestly
- at least one simple learned model is run under frozen contracts
- evaluation certificates exist
- external same-assay holdout results exist
- the writeup is honest and complete

Anything less is a prototype, not a finished v1.

---

## 17. Strategic goal of the roadmap

The roadmap is designed to get Spatial-CI to a point where it can honestly answer:

> Is there enough trustworthy morphology-to-expression signal here to justify deeper work?

That is the first serious win.

Not SOTA.
Not hype.
Not clinical deployment.

Just a defensible scientific answer.

---

## 18. One-sentence summary

The Spatial-CI roadmap is designed to ensure that every increase in modeling ambition is earned by a benchmark stack that has already proved it can tell the truth.
