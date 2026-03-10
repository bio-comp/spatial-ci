# Spatial-CI Project Context

## What this project is

**Spatial-CI** is a contract-driven, leakage-resistant, decision-grade research platform for **virtual spatial transcriptomics** and **multimodal pathology AI**.

This project is a domain-specific instantiation of the broader **Circuit-CI / DomainOps** thesis:

> no claim without explicit contracts, provenance, evidence gates, and evaluation certificates.

Spatial-CI is **not** a medical device, not a clinical pathology product, and not a generic pathology-model repo. It is a **deployment-minded validation scaffold** for testing whether **morphology-to-expression** claims are biologically meaningful, reproducible, and transportable across cohorts.

---

## Core v1 scope

### Frozen scope
- **Disease:** breast cancer
- **Assay:** standard **10x Visium**
- **Task:** predict fixed per-spot biological program scores from H&E morphology
- **Image mode:** **spot-plus-context**
- **Targets:** fixed Hallmark-derived program scores
- **Validation:** pooled discovery cohorts with deterministic patient-level train/val split + same-assay external holdout

### Out of scope for v1
- Xenium
- Visium HD
- pan-cancer claims
- exact-spot-only extraction as default
- ad hoc hand-tuned gene sets
- cohort-dependent target scoring
- isoform/splicing/APA-first modeling
- clinical deployment claims
- FDA-style validation claims

---

## Current scientific question

The main v1 question is:

> Under frozen target, scoring, alignment, split, baseline, and bootstrap contracts, does H&E morphology contain enough stable signal to predict selected spatial expression programs in breast Visium data beyond honest simple baselines?

This is **not** asking whether we can build the fanciest model.  
This **is** asking whether the evidence is strong enough to justify deeper work.

---

## DomainOps / Circuit-CI framing

Spatial-CI should be treated as a **DomainOps system** with the following reusable kernel:

- explicit contracts
- first-class artifacts
- manifests and provenance
- rejection ledgers / no silent attrition
- explicit intervention axes
- evaluation certificates
- claim discipline
- baseline-before-complexity
- deterministic, auditable experiments

The spatial/pathology-specific layer is the vertical application.

---

## Core principles

1. **Explicitness over convenience**  
   If a choice materially affects interpretation, it should be explicit and versioned.

2. **Truth in advertising**  
   Targets and claims must not be described more strongly than the contracts justify.

3. **No silent attrition**  
   Missing/unresolvable samples must produce rejection artifacts, not disappear quietly.

4. **Baselines are moral objects**  
   Honest simple baselines matter more than flashy model complexity.

5. **Targets are scientific objects**  
   Target generation is part of the benchmark definition, not “just preprocessing.”

6. **Clustered uncertainty, not fake precision**  
   Visium spots are not iid.

7. **One primary intervention axis per experiment**  
   Avoid experiment soup.

8. **Complexity must be earned**  
   Do not add fancy spatial models until the benchmark and simple models prove they deserve it.

---

## Frozen v1 targets

### Target definition ID
`breast_visium_hallmarks_v1`

### Source
- **MSigDB Hallmark** gene sets
- **unmodified** for v1

### Allowed programs
- `HALLMARK_HYPOXIA`
- `HALLMARK_G2M_CHECKPOINT`
- `HALLMARK_EPITHELIAL_MESENCHYMAL_TRANSITION`

### Interpretation rules
- `HALLMARK_HYPOXIA` = hypoxia-response program
- `HALLMARK_G2M_CHECKPOINT` = G2M / proliferation-related cell-cycle signal
- `HALLMARK_EPITHELIAL_MESENCHYMAL_TRANSITION` = **EMT/mesenchymal program**
  - do **not** relabel this as pure stromal or CAF state

### Missing-gene policy
For a given spot/program:
- if more than **10%** of target genes are missing, drop that spot for that program
- otherwise score on the intersection and record the missingness

---

## Frozen scoring design

### Key decision
Use **R/Bioconductor `singscore`** as the source-of-truth implementation for target scoring.

### Why
- the Python port looked stale
- the R/Bioconductor implementation is the authoritative and maintained method
- scoring should be **single-sample** and as cohort-independent as possible

### Operational setup
- Python handles manifests, artifacts, baselines, modeling, evaluation
- R handles frozen target scoring
- R environment is frozen with **`renv.lock`**
- target score artifacts are written out and then consumed by Python

### Important scoring rules
- scoring is a first-class contract
- do not re-score targets ad hoc inside model/evaluation notebooks
- score artifacts must include provenance:
  - `target_definition_id`
  - `scoring_contract_id`
  - source expression artifact hash
  - run ID or generation timestamp
  - software / lock provenance

### Preferred artifact format
- **Parquet**, not CSV, for real score artifacts

---

## Frozen alignment design

### Alignment contract ID
`visium_context_224px_0_5mpp_v1`

### Parameters
- target mpp: `0.5`
- tile size: `224 px`
- extraction mode: `spot_plus_context`

### Interpretation
A 224 px crop at 0.5 µm/px spans ~112 µm.  
A Visium spot is ~55 µm in diameter.  
Therefore v1 is honestly a **spot-plus-context** task, not exact-spot-only.

### Required provenance for alignment
The manifest must include:
- image artifact
- spatial coordinates
- `scalefactors_json.json`

---

## Frozen split design

### Split contract philosophy
We do **not** use one whole discovery cohort as validation, because that easily turns into cohort-specific tuning.

### v1 split strategy
- pool discovery cohorts
- create **deterministic patient-level train/val split** within pooled discovery cohorts
- keep separate same-assay external holdout cohorts for stress testing

### Leakage audit requirements
Must audit overlap across:
- patient
- specimen
- slide

### Resolved identity rules
Need:
- `resolved_patient_id`
- `patient_id_source`
- `resolved_specimen_id`
- `resolved_slide_id`

### ID provenance
`patient_id_source` should distinguish:
- `true_patient_id`
- `specimen_fallback`
- `sample_fallback`

### Namespacing
Namespace resolved IDs by `cohort_id` to avoid false collisions.

---

## Manifest / provenance architecture

### Manifest philosophy
The manifest is not a convenience cache.  
It is a scientific artifact.

### Two-pass manifest builder

#### Pass 1: logical assignments
Responsibilities:
- schema discovery
- canonical field enforcement
- optional-field injection
- vocabulary normalization
- cohort filtering
- resolved ID construction
- deterministic split assignment
- leakage audit
- sorted assignment output

#### Pass 2: physical materialization
Responsibilities:
- resolve actual artifacts on disk
- pre-hash validation
- compute hashes
- validate final manifest rows
- write rejections
- write final manifest

### Required physical artifact classes
- spatial coordinates
- scalefactors metadata
- raw expression matrix
- image artifact
- optional derived expression artifact

### Important provenance rule
Do **not** conflate:
- raw assay outputs
- derived `.h5ad` or processed files

Keep them separate in the manifest.

### Failure handling
- default: halt on missing required artifacts
- if `--allow-missing` is used, still emit rejection ledger and warning

---

## Baseline philosophy

The model must earn its complexity.

### Required deployable baselines
- `global_train_mean`
- `mean_by_train_cohort`
- `knn_on_embeddings`
- `ridge_probe`

### Rules
- baselines must be frozen by contract
- oracle analyses may exist, but must be clearly separated
- do not present oracle analyses as fair deployable baselines

### Example frozen semantics
- `knn_on_embeddings`: fit on train only, cosine distance, fixed `k`
- `ridge_probe`: fit on train, tune on val, no external-test peeking

---

## Evaluation philosophy

Spatial-CI evaluates **evidence states**, not just metrics.

### Primary metric
- **Spearman correlation** per target program

### Required uncertainty
- **clustered bootstrap CI**
- cluster by patient if available, else slide

### Required grouped summaries
Per target, include:
- median slide-level Spearman
- IQR slide-level Spearman
- worst-decile slide performance

### External holdout language
External same-assay holdouts are:
- transportability stress tests
- not broad deployment guarantees
- not proof of universal generalization

### Evaluation artifact
Main output is an **EvaluationCertificate** containing:
- run identity
- contract stack
- primary intervention axis
- metrics by target
- uncertainty
- baseline comparisons
- leakage status
- notes

---

## Experiment philosophy

### Rule
Every experiment must declare **exactly one primary intervention axis**.

### Typical v1 axes
- `baseline`
- `encoder`
- `spatial_context`
- `normalization`
- `target_definition`

### Compound runs
Allowed, but must be labeled as compound and interpreted more weakly.

### Baseline-first progression
Recommended order:
1. manifest sanity
2. score generation sanity
3. baseline experiments
4. simple learned model
5. modest context extension
6. more complex models only if justified

---

## Artifact graph

The main artifact flow is:

```text
raw metadata + raw files
    ↓
split assignment artifact
    ↓
sample manifest
    ↓
R singscore target score artifact
    ↓
embedding artifact
    ↓
run config
    ↓
prediction artifact
    ↓
evaluation certificate
```

### Core artifact types
- split assignments
- manifest
- score artifacts
- embeddings
- run configs
- predictions
- evaluation certificates
- rejection ledgers
- leakage reports

---

## Current environment strategy

We are using a mixed Python + Conda + R setup.

### Files
- `pyproject.toml`: Python package metadata + tooling config
- `environment.yml`: mixed runtime environment
- `renv.lock`: frozen R environment for scoring

### Why
- **Python** handles package structure, manifests, baselines, models, evaluation
- **R** handles singscore
- **Conda/mamba** style env is pragmatic for compiled scientific deps, Torch, OpenSlide, and future PyMC

### Environment notes
- keep base environment CPU-safe where possible
- Linux/GPU-specific extras can be split later if needed
- do not treat pure Python tooling as the full environment truth for this project

---

## Current repo structure

### Current major docs include:
- `README.md`
- `docs/CONTRACTS.md`
- `docs/MANIFEST_PIPELINE.md`
- `docs/EVALUATION.md`
- `docs/ROADMAP.md`

### Plus supporting docs:
- targets
- scoring
- design decisions
- artifacts
- experiments
- assumptions
- failure modes
- claims
- principles
- etc.

The repo is doc-heavy right now by design; next priority is turning the core contract stack into code.

---

## Coding guidance for OpenCode

When working in this repo:

### Prefer
- small, explicit modules
- Pydantic schemas for contracts/artifacts
- Polars for table-oriented manifest logic
- deterministic sorting before serialization
- Parquet for serious tabular artifacts
- explicit input/output paths in scripts
- failure-loud behavior on contract violations

### Avoid
- notebook-only logic
- hidden defaults for scientific choices
- silent regeneration of target scores
- mixing raw and derived artifacts
- changing target semantics without versioning
- writing code that assumes one filesystem layout unless explicitly frozen

---

## Architectural priority

The first code should implement:
- contract schemas
- manifest pipeline
- scoring interface boundary
- baseline pipeline
- evaluation certificate generation

Do not start with fancy models.

---

## Immediate implementation priorities

### Create Python schemas for:
- `TargetDefinition`
- `ScoringContract`
- `AlignmentContract`
- `SplitContract`
- `BaselineContract`
- `BootstrapContract`
- `SampleManifest`
- `EvaluationCertificate`

### Implement `scripts/build_manifest.py`:
- pass 1
- pass 2
- rejection ledger
- leakage audit

### Implement R scoring boundary:
- `scripts/bootstrap_renv.R`
- `scripts/score_targets.R`
- score artifact schema

### Implement baseline pipeline:
- global mean
- train-cohort mean
- kNN on embeddings
- ridge probe

### Implement evaluation certificate generation

---

## What success looks like

Spatial-CI succeeds if it can honestly answer:
- what signal is present
- what signal is absent
- which targets are learnable enough from morphology
- which models add value beyond honest baselines
- how much signal survives external holdout stress
- what caveats or failures remain

The project is not trying to always look good.  
It is trying to make weak claims hard to produce and strong claims easier to recognize.

---

## Non-goals

Spatial-CI is not:
- a clinical product
- an FDA-readiness project
- a pan-pathology benchmark zoo
- an isoform/splicing platform in v1
- a substitute for wet-lab spatial transcriptomics
- a credential or pathology certification
- a model-hype machine

---

## Short summary for coding agents

Spatial-CI is a contract-first benchmark system for virtual spatial transcriptomics in breast Visium.
The system centers on:
- frozen contracts
- explicit provenance
- leakage-resistant manifests
- R-based single-sample target scoring via singscore
- strong baselines
- clustered uncertainty
- evaluation certificates
- narrow, disciplined claims

When in doubt:
- preserve contract clarity
- preserve provenance
- preserve determinism
- preserve auditability
- weaken claims rather than strengthen them

---

## Assumptions
- You want a single context file for coding agents, not another giant spec document.
- You want it optimized for repo implementation decisions, not marketing copy.
- You want it aligned with the latest decision: **R `singscore` + mixed Python/Conda/R environment**.

## How we test/validate
- The file is good if an agent can use it to scaffold the first code pass without asking what the project is, what the v1 scope is, what contracts exist, or where scoring happens.
- The first concrete validation is whether it produces the correct initial modules:
    - contract schemas
    - manifest builder
    - R scoring boundary
    - baseline runner
    - evaluation certificate logic

## Next 3 actions
1. Save that as `project-context.md` at the repo root.
2. Generate `pyproject.toml`, `environment.yml`, and `scripts/bootstrap_renv.R` / `scripts/score_targets.R` to match it exactly.
3. Start coding `src/spatial_ci/contracts/` before anything model-related.
