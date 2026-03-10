# Spatial-CI Glossary

This glossary defines the core vocabulary used throughout Spatial-CI.

Its purpose is not to be encyclopedic.
Its purpose is to make the project’s terms precise enough that:

- experiments are interpretable
- contracts are comparable
- docs stay consistent
- claims do not drift in meaning over time

Spatial-CI is built on the idea that unclear words create unclear science.

---

## A

### Alignment Contract
A versioned artifact that defines how molecular spatial units are linked to visual inputs.

In Spatial-CI v1, this includes:
- target microns-per-pixel
- crop size
- extraction mode
- any declared stain normalization behavior

The alignment contract exists because the image crop seen by a model is a scientific choice, not an inevitability.

### Artifact
A concrete, versionable object produced or consumed by the Spatial-CI pipeline.

Examples:
- split assignments
- manifests
- target score tables
- embeddings
- evaluation certificates
- rejection ledgers

An artifact is more than a file. It is a file with scientific meaning.

### Assay
The experimental measurement platform that generates the data.

Examples:
- 10x Visium
- Visium HD
- Xenium
- future long-read spatial workflows

Spatial-CI v1 is restricted to standard Visium.

---

## B

### Baseline
A simpler predictive strategy used to judge whether a more complex model has actually earned its complexity.

Examples in Spatial-CI:
- global train mean
- mean by train cohort
- kNN on embeddings
- ridge probe

### Baseline Contract
A versioned artifact that freezes the exact semantics of the baseline family.

It specifies:
- which baselines are allowed
- what training data they can see
- how fallback logic works
- which hyperparameters are fixed
- which split may be used for tuning

### Benchmark
A structured evaluation setting used to test a defined scientific question.

Spatial-CI is not just a benchmark in the casual sense.
It is a contract-driven benchmark designed to make weak claims harder to produce.

### Bootstrap Contract
A versioned artifact that defines how uncertainty intervals are computed.

In v1, this includes:
- clustering unit
- number of bootstrap replicates
- deterministic seed

It exists to prevent fake certainty from invalid iid resampling.

---

## C

### Certificate
Short for **Evaluation Certificate** unless otherwise specified.

A formal artifact that records whether a given run deserves belief under a frozen set of contracts.

### Claim
A specific scientific statement that a run is implicitly or explicitly making.

Examples:
- morphology predicts hypoxia-related spatial signal in breast Visium
- adding spatial context improves transportability
- a learned model outperforms honest simple baselines

Spatial-CI exists to formalize and discipline claims.

### Cohort
A dataset grouping that typically shares acquisition, study, or institutional characteristics.

Cohorts matter because:
- they can encode batch effects
- they can create leakage risk
- they are central to transportability claims

### Compound Experiment
An experiment in which multiple major factors change at once.

Compound experiments may be useful for exploration, but they are not clean one-factor comparisons.

### Contract
A versioned specification that makes an important assumption explicit and auditable.

Examples:
- target definition contract
- scoring contract
- alignment contract
- split contract
- baseline contract
- bootstrap contract

Contracts are the core abstraction of Spatial-CI.

### Contract Drift
A silent change to the meaning of a contract without a version change.

Examples:
- changing the scorer but keeping the same scoring ID
- changing split logic without minting a new split contract
- renaming an EMT target as stromal without changing target semantics

Spatial-CI treats contract drift as a serious failure mode.

### Circuit-CI
The broader conceptual ancestor of Spatial-CI.

Circuit-CI is the general thesis that claims should be judged through explicit contracts, evidence gates, provenance, and certificates.
Spatial-CI is a domain-specific instantiation of that philosophy.

---

## D

### Decision-Grade
A descriptive term used in Spatial-CI to mean:
- explicit
- auditable
- contract-aware
- resistant to obvious self-deception
- strong enough to support serious internal judgment

It does **not** mean clinically validated or regulator-approved.

### Deployment-Minded
Built with the rigor and failure-awareness needed for serious downstream use, while still remaining a research platform rather than a product.

### Derived Artifact
An artifact produced from other artifacts rather than directly from raw source data.

Examples:
- score artifacts
- embeddings
- predictions
- evaluation certificates

### Derived Target
A target that is built from one or more source targets or scoring rules rather than copied directly from a source set.

Example:
- a future combined proliferation target built from multiple Hallmark sets

Derived targets are allowed only if explicitly versioned.

### Discovery Cohorts
The pooled internal cohorts used to create train/validation splits.

These are distinct from external holdout cohorts.

---

## E

### Embedding
A vector representation of an image crop, usually produced by a pretrained model or encoder.

In Spatial-CI, embeddings are treated as artifacts and must be tied to:
- the encoder
- the alignment contract
- the source image/provenance chain

### Embedding Artifact
A stored representation of extracted image features with explicit provenance and contract linkage.

### EMT / Mesenchymal Program
In Spatial-CI v1, this refers specifically to the meaning of:
- `HALLMARK_EPITHELIAL_MESENCHYMAL_TRANSITION`

It must not be casually relabeled as a pure stromal or CAF program.

### Evaluation
The process of determining whether a run deserves belief under the frozen contract stack.

### Evaluation Certificate
A formal artifact that summarizes:
- what was evaluated
- under what contracts
- with what metrics
- with what uncertainty
- against what baselines
- with what leakage status

This is the most important decision artifact in Spatial-CI.

### Experiment
A declared intervention under frozen contracts.

An experiment is not merely “a run.”
It is a run whose scientific context is explicitly named.

### Experiment Soup
A bad experimental state where many things change at once and no one can tell what caused the result.

Spatial-CI was largely designed to prevent this.

### External Holdout
A held-out cohort or set of cohorts not used for training or tuning.

In v1, external holdouts are same-assay transportability stress tests.

---

## F

### Fallback ID
A resolved identifier used when a more direct identifier is missing.

Examples:
- specimen used as a patient proxy
- sample used as a patient proxy

Fallbacks must always be auditable.

### Frozen
A term meaning:
- explicitly defined
- no longer vague
- stable enough to code or evaluate against
- not to be silently mutated in place

A frozen object may later be superseded, but not quietly redefined.

---

## G

### Generalization
Performance beyond the exact data used for fitting.

Spatial-CI uses the term carefully and prefers to distinguish:
- internal validation behavior
- same-assay external transportability
- broader claims, which are usually not justified in v1

### G2M Checkpoint
One of the fixed v1 target programs:
- `HALLMARK_G2M_CHECKPOINT`

Used as a proliferation-related but specifically named cell-cycle target.

### Global Train Mean
A simple deployable baseline that predicts the global mean target score computed from training data only.

### Ground Truth
In Spatial-CI, usually the frozen per-spot biological target score generated under the target definition and scoring contracts.

This is not “ultimate truth” in a philosophical sense.
It is the declared target object for the benchmark.

---

## H

### Hallmark Program
A target program derived from the MSigDB Hallmark gene sets.

Spatial-CI v1 uses three:
- hypoxia
- G2M checkpoint
- epithelial mesenchymal transition

### Hash
A deterministic content fingerprint used for provenance.

Usually SHA256 in Spatial-CI manifests and artifact tracking.

### Holdout
Data intentionally excluded from fitting and tuning so performance can be evaluated on unseen data.

### Hypoxia Program
In v1, this refers to:
- `HALLMARK_HYPOXIA`

Used as a plausible morphology-linked tumor microenvironment program.

---

## I

### ID Namespacing
The practice of prefixing identifiers with cohort or context information to avoid accidental collisions.

Examples:
- `cohort_id:patient_id`
- `cohort_id:slide_id`

### Immutable Biology
A Spatial-CI design goal in which the biological target definition is kept stable and not quietly tuned to the data.

### Input Artifact
Any artifact consumed by a run.

Examples:
- manifest
- target score table
- embeddings
- run config

### Intervention Axis
The primary dimension a run is meant to vary.

Examples:
- baseline
- encoder
- spatial context
- normalization
- target definition

Each experiment must declare one primary intervention axis.

### IQR
Interquartile range.

Used in Spatial-CI for dispersion summaries such as slide-level metric spread.

---

## K

### kNN on Embeddings
A deployable baseline that predicts target values using nearest neighbors in frozen embedding space.

In v1, this baseline is governed by the baseline contract.

---

## L

### Leakage
Any overlap or information pathway that allows training/tuning to benefit unfairly from held-out data.

Spatial-CI specifically audits leakage across:
- patient
- specimen
- slide

### Leakage Ledger / Leakage Report
An artifact recording detected overlap or leakage failures.

Leakage is treated as a fatal benchmark event unless explicitly investigated before rerunning.

### Linear Probe
A simple predictive model using fixed embeddings and a linear readout.

In Spatial-CI, ridge is the preferred “honest simple model” version of this idea.

---

## M

### Manifest
Short for **Sample Manifest** unless otherwise specified.

A provenance artifact that records:
- which samples are included
- which split they belong to
- how IDs were resolved
- which physical files back the sample
- which hashes verify those files

### Mean by Train Cohort
A deployable baseline that predicts target values using the mean score of the matching training cohort, with fallback to the global train mean when needed.

### Metadata Normalization
The process of converting heterogeneous source metadata into a canonical staging schema.

Spatial-CI treats this as a scientific operation, not just housekeeping.

### Model Theater
A failure mode in which the codebase focuses on architecture novelty while neglecting baseline quality, target stability, leakage, or provenance.

Spatial-CI is explicitly anti–model theater.

---

## N

### Namespaced ID
An identifier that includes contextual information, usually cohort, to avoid false collisions.

### Non-Goal
Something the project explicitly refuses to optimize for in the current version.

Spatial-CI documents non-goals to prevent scope creep and hype drift.

---

## O

### Oracle Baseline
A “baseline” that secretly uses information unavailable at real inference time.

Example:
- slide mean computed from true labels of the test slide

Oracle analyses may be useful for context, but they must never be presented as honest deployable baselines.

### Out of Scope
A feature, task, assay, or claim intentionally excluded from the current project version.

---

## P

### Patient-Level Split
A split in which all samples tied to the same resolved patient are assigned to the same split.

This is essential for avoiding patient leakage.

### Patient ID Source
A field recording whether patient identity came from:
- true patient ID
- specimen fallback
- sample fallback

This is crucial for auditability.

### Path Mapping
A mapping from logical sample identity to actual filesystem locations.

Spatial-CI does not assume that `sample_id == directory name` unless that convention is explicitly frozen and tested.

### Pre-Hash Validation
A lightweight validation step performed before expensive file hashing.

It catches obvious structural problems early.

### Prediction Artifact
An artifact storing model predictions explicitly rather than recomputing them during evaluation.

### Provenance
The traceable history of where an artifact came from and what source objects support it.

Spatial-CI is extremely provenance-sensitive.

### singscore

The R/Bioconductor package used for v1 single-sample rank-based target scoring.

Spatial-CI v1 uses singscore (not PySingscore) for target scoring, with the R environment frozen via `renv.lock`.

---

## Q

### QC
Quality control.

In Spatial-CI, QC may refer to:
- source sample filtering
- score eligibility filtering
- artifact resolution checks
- validation failures

QC decisions must be made explicit, not buried.

---

## R

### Rank-Based Scoring
A family of scoring approaches that use within-sample expression ranks rather than cohort-wide relative distributions.

Preferred in Spatial-CI v1 because they support sample independence more naturally.

### Rejection Ledger
An artifact that records samples rejected during manifest generation or validation.

Used to prevent silent attrition.

### Reproducibility
The ability to reconstruct a result from:
- frozen contracts
- input artifacts
- environment
- code revision
- run config

Spatial-CI is optimized for reproducibility, not just rerunnability in a vague sense.

### Resolved Patient ID
A canonical patient-like identifier created through a defined fallback hierarchy and namespacing strategy.

### Ridge Probe
A deployable baseline using standardized embeddings with ridge regression under frozen tuning rules.

### Roadmap
A staged plan for how the project grows while preserving discipline.

---

## S

### Same-Assay External Holdout
An external dataset using the same assay family as the discovery data.

Used in v1 as the main transportability stress test.

### Sample Manifest
The core provenance artifact for included samples.

### Scoring Contract
A contract that freezes how target program scores are computed from expression data.

### Silent Attrition
When samples disappear from the benchmark without an explicit rejection record.

Spatial-CI treats this as a serious benchmark corruption risk.

### Source-Faithful Target
A target that stays faithful to its declared source definition rather than being locally hand-tuned.

### Spatial-CI
A contract-driven, leakage-resistant, decision-grade research platform for virtual spatial transcriptomics and multimodal pathology AI.

### Spatial Context
Any modeling choice that explicitly incorporates neighboring spatial information beyond a simple per-crop representation.

### Spot
The standard molecular spatial unit in Visium.

In v1, targets are scored per spot, while image crops are spot-plus-context.

### Spot-Plus-Context
The frozen v1 extraction mode in which the image crop spans more than the Visium spot itself.

### Split Assignment Artifact
An artifact that records which samples belong to which split under the frozen split contract.

### Split Contract
A contract that defines discovery/external cohort logic and split membership rules.

### Staging Table
An intermediate table used during manifest construction before final nested artifact serialization.

---

## T

### Target
The biological quantity the model is being asked to predict.

In v1, targets are per-spot Hallmark-derived program scores.

### Target Definition
A contract that freezes:
- which programs are allowed
- where they come from
- whether modification is allowed
- how they should be interpreted

### Target Drift
A change in what the target means without a new versioned definition.

### Transportability
How well a result survives movement across cohorts or settings.

In v1, this is tested primarily through same-assay external holdout behavior.

### Truth in Advertising
A design principle requiring target names and interpretation language to match what the contracts actually define.

Example:
- do not call EMT “stromal” unless explicitly qualified

---

## U

### Uncertainty
The quantified instability or variability of performance estimates.

In Spatial-CI v1, uncertainty is primarily represented through clustered bootstrap confidence intervals.

### Unique Patient Table
A staging object used to assign train/validation split membership once per patient before joining assignments back into the main table.

### uv
The project’s package and environment manager.

`uv.lock` is the actual frozen environment artifact.

---

## V

### Validation
The internal held-out evaluation within the pooled discovery cohorts.

Distinct from:
- training
- external holdout testing

### Versioned
Explicitly assigned an identity that should change when meaning changes.

Contracts, manifests, score artifacts, and certificates should all be versioned or traceable to versioned inputs.

### Virtual Spatial Transcriptomics
The task of predicting molecular spatial signals from morphology and related inputs rather than directly measuring them with a wet-lab spatial assay.

Spatial-CI is a validation platform for this class of claims.

### Visium
The standard 10x spatial transcriptomics platform used in v1.

---

## W

### Weak Claim
A claim that appears stronger than the evidence supporting it.

Spatial-CI is built to make weak claims harder to produce.

### Worst-Decile Performance
A summary statistic capturing poor-tail behavior across slides or other grouped units.

Used in Spatial-CI to prevent strong means from hiding catastrophic subsets.

### Workflow
A sequence of pipeline steps.

Spatial-CI distinguishes between:
- logical workflows
- physical artifact workflows
- evaluation workflows

---

## 2. One-sentence summary

The Spatial-CI glossary exists to keep the project’s language sharp enough that scientific meaning does not drift while the codebase grows.

