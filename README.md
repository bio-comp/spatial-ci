# Spatial-CI

**Spatial-CI** is a contract-driven, leakage-resistant, decision-grade research platform for **virtual spatial transcriptomics** and **multimodal pathology AI**.

It is a domain-specific instantiation of the broader **Circuit-CI** thesis:

> no claim without explicit contracts, provenance, evidence gates, and evaluation certificates.

Spatial-CI is not a medical device, not a clinical diagnostic system, and not a generic “train a cool pathology model” repo. It is a **deployment-minded validation scaffold** for testing whether **morphology-to-expression** claims are biologically meaningful, reproducible, and transportable across cohorts.

---

## Why this exists

Computational pathology and virtual spatial transcriptomics are vulnerable to a familiar pattern of failure:

- weakly defined biological targets
- unclear alignment between image and molecular signals
- leaky train/validation/test splits
- hidden preprocessing assumptions
- architecture theater
- cherry-picked baselines
- untrustworthy uncertainty estimates
- silent sample attrition
- overclaiming on small external holdouts

Spatial-CI exists to make those failures harder.

The core question for v1 is:

> Can H&E morphology from standard breast Visium data predict fixed, predeclared spatial expression programs across cohorts without leakage, hidden target drift, or misleading evaluation?

---

## What Spatial-CI is

Spatial-CI is a **decision-grade research platform** with:

- immutable target definitions
- explicit alignment contracts
- explicit split contracts
- explicit baseline contracts
- explicit bootstrap contracts
- manifest/provenance artifacts
- deterministic data engineering
- rejection ledgers instead of silent dropping
- per-program evaluation certificates

This is a **platform for deciding whether a morphology-to-expression result should be trusted**, not just a codebase for training models.

---

## Relationship to Circuit-CI

- **Circuit-CI** = the general thesis and contract/certification philosophy
- **Spatial-CI** = the spatial pathology instantiation of that philosophy

Spatial-CI should remain a separate repo, but explicitly inherit the Circuit-CI worldview:

- claims must be formalized
- artifacts must be versioned
- interventions must be named
- evaluation must be auditably reproducible
- transportability matters
- uncertainty matters
- evidence gates matter

---

## v1 scope

### Frozen scientific scope

- **Disease:** breast cancer
- **Assay:** standard **10x Visium**
- **Task:** morphology-to-expression program prediction
- **Image extraction mode:** **spot-plus-context**
- **Target outputs:** fixed Hallmark-derived program scores
- **Evaluation:** internal discovery split + external same-assay holdout

### Out of scope for v1

- Xenium
- Visium HD
- multi-cancer pooled claims
- exact-spot masking as default mode
- custom hand-tuned gene signatures
- cohort-dependent target scoring
- isoform/splicing/APA-first modeling
- clinical deployment claims
- broad production workflows

---

## Core design principles

1. **Truth in advertising**
   - target names must match what they actually measure
   - no “CAF score” if the target is really EMT-like signal
   - no “proliferation” if the target is actually only G2M

2. **Immutable biology**
   - do not tune signatures to the cohort
   - do not drop genes because they “look noisy”
   - do not let target construction drift under the model

3. **Single-sample target scoring**
   - a target score for one spot should depend only on that spot’s expression
   - avoid cohort-dependent background scoring for frozen targets

4. **No oracle baselines**
   - no baselines that use test-label information under the hood

5. **No silent attrition**
   - missing/unresolvable samples must be recorded in a rejection ledger
   - default behavior is to halt unless missing samples are explicitly allowed

6. **No hidden intervention surface**
   - alignment, target definition, split logic, baseline logic, and bootstrap policy are all first-class contracts

7. **No fake uncertainty**
   - Visium spots are not iid
   - bootstrap must respect patient/slide clustering

---

## Scientific framing

Spatial-CI is not asking:

> “Can a deep net beat another deep net?”

It is asking:

> “Under a fixed biological target definition, fixed alignment policy, fixed split policy, and fixed evaluation rules, is there evidence that morphology contains transportable signal for these spatial programs?”

That is a much stronger and more scientific question.

---

## Biological targets in v1

### Frozen target set

`target_definition_id = "breast_visium_hallmarks_v1"`

Programs:

- `HALLMARK_HYPOXIA`
- `HALLMARK_G2M_CHECKPOINT`
- `HALLMARK_EPITHELIAL_MESENCHYMAL_TRANSITION`

### Interpretation rules

- `HALLMARK_HYPOXIA` → hypoxia-response program
- `HALLMARK_G2M_CHECKPOINT` → G2M/cell-cycle progression signal
- `HALLMARK_EPITHELIAL_MESENCHYMAL_TRANSITION` → **EMT/mesenchymal program**, **not** a pure stromal or CAF state

---

## Alignment philosophy

A molecular “spot” is not self-defining from the image side.

The molecular target lives at the Visium spot, but the visual model sees a crop. The crop definition is a scientific choice and must be versioned.

### Frozen v1 alignment

`alignment_id = "visium_context_224px_0_5mpp_v1"`

- target mpp: `0.5`
- tile size: `224 px`
- extraction mode: `spot_plus_context`

At `0.5 µm/px`, a `224 px` crop spans `112 µm`. Standard Visium spots are roughly `55 µm` in diameter, so v1 is explicitly a **spot-plus-context** task.

---

## Split philosophy

The split must answer a real generalization question.

Using one whole discovery cohort as “validation” is not enough if it becomes a tuning target for batch artifacts.

### Frozen v1 split strategy

- pool **discovery cohorts**
- perform deterministic **patient-level train/val splitting within discovery cohorts**
- reserve separate **external same-assay cohorts** as true held-out transportability tests

This prevents:
- treating one whole cohort as a hyperparameter target
- calling “memorized cohort style” generalization
- conflating validation with external testing

---

## Baseline philosophy

A baseline without frozen semantics is a p-hack waiting to happen.

The model must **earn** its complexity by beating simple, deployable baselines.

### Deployable baselines

- `global_train_mean`
- `mean_by_train_cohort`
- `knn_on_embeddings`
- `ridge_probe`

### Analysis-only oracle checks

Examples:
- `oracle_slide_mean`

These must never be mixed with deployable baselines.

---

## Evaluation philosophy

A single scalar metric is not enough.

An evaluation artifact must encode:

- what was evaluated
- under what contracts
- on how many biological units
- with what uncertainty
- relative to which baselines
- with what leakage status

Per program, v1 should report at minimum:

- `overall_spearman`
- `clustered_bootstrap_ci_95`
- slide/patient-level summaries
- deployable baseline results
- optional oracle analysis block

---

## Data engineering philosophy

Spatial-CI uses a **two-pass manifest builder**.

### Pass 1: fast logical assignment
- schema discovery
- schema normalization
- canonical field enforcement
- vocabulary normalization
- cohort filtering
- patient/specimen/slide resolution
- deterministic split assignment
- leakage audit
- writing split assignments

### Pass 2: slow provenance materialization
- artifact resolution
- pre-hash validation
- file hashing
- final manifest validation
- rejection ledger writing
- final deterministic manifest output

### Why two passes

Hashing large pathology artifacts during metadata experimentation is a great way to destroy iteration speed.

Two-pass design gives:
- faster iteration
- idempotence
- resumability
- cleaner failure handling

---

## What Spatial-CI is not claiming

Spatial-CI v1 is **not** claiming:

- clinical deployment
- FDA readiness
- pathology sign-out utility
- pan-cancer generalization
- isoform/splicing mastery
- causal identification of biology from morphology
- replacement of wet-lab spatial transcriptomics

It is a rigorous **research platform** for evaluating whether morphology-to-expression claims are worth believing.

---

## Repository identity

- **Repo name:** `spatial-ci`
- **Python package:** `spatial_ci`

Suggested subtitle:

> Contract-driven validation for virtual spatial transcriptomics and multimodal pathology AI

---

## Repository structure

```
spatial-ci/
├── README.md
├── LICENSE
├── pyproject.toml
├── uv.lock
├── renv.lock
├── .Rprofile
├── environment.yml
├── docs/
│   ├── CONTRACTS.md
│   ├── EVALUATION.md
│   ├── MANIFEST_PIPELINE.md
│   ├── TARGETS.md
│   └── DESIGN_DECISIONS.md
├── contracts/
│   ├── artifacts/
│   ├── schemas/
│   └── examples/
├── src/
│   └── spatial_ci/
│       ├── manifest/
│       ├── contracts/
│       ├── scoring/
│       ├── baselines/
│       ├── models/
│       ├── evaluation/
│       └── utils/
├── scripts/
│   ├── build_manifest.py
│   ├── score_targets.R
│   ├── bootstrap_renv.R
│   ├── run_baselines.py
│   └── evaluate_run.py
└── tests/
