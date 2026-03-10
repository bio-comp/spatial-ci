# Spatial-CI Architecture

This document describes the logical architecture of Spatial-CI.

The goal is not to describe every implementation detail.
The goal is to explain how the major parts of the system fit together, why they are separated, and where the main scientific control points live.

Spatial-CI is not architected as “a model with some preprocessing.”
It is architected as a **contract-driven research system** whose purpose is to make morphology-to-expression claims explicit, auditable, and difficult to fake.

---

## 1. Architectural philosophy

The architecture is built around one central rule:

> every scientifically meaningful transformation should correspond to an explicit artifact boundary or contract boundary.

This means the system is intentionally broken into layers rather than hidden in one end-to-end script.

The major architectural goals are:

- explicit contracts
- deterministic artifact flow
- auditable provenance
- leakage-resistant splits
- frozen target generation
- reproducible baseline and model evaluation
- claim discipline through certificates

---

## 2. High-level system view

At a high level, Spatial-CI has six major layers:

1. **Contract layer**
2. **Manifest and provenance layer**
3. **Target scoring layer**
4. **Feature / embedding layer**
5. **Experiment execution layer**
6. **Evaluation and certificate layer**

These layers are deliberately separated so that:
- data issues do not hide inside model code
- target drift does not hide inside evaluation notebooks
- split logic does not hide inside training scripts
- claims can be traced back to artifacts

---

## 3. High-level dataflow

The conceptual dataflow for v1 is:

```
raw metadata + raw sample files
    ↓
schema normalization + split assignment
    ↓
sample manifest
    ↓
target score artifacts
    ↓
image extraction / embedding artifacts
    ↓
experiment config + model/baseline execution
    ↓
prediction artifacts
    ↓
evaluation certificate
```

Each step should emit an explicit artifact rather than silently mutating state in memory and moving on.

## 4. Contract layer

**Purpose**

The contract layer defines the frozen assumptions under which a run is valid.

**Main contracts**

Spatial-CI v1 uses these major contracts:

- TargetDefinition
- ScoringContract
- AlignmentContract
- SplitContract
- BaselineContract
- BootstrapContract

**Why this layer exists**

Without this layer, the benchmark would be vulnerable to:

- hidden task drift
- silent preprocessing changes
- unclear experimental comparability
- target mutation under the model

The contract layer is the architectural "constitution" of Spatial-CI.

## 5. Manifest and provenance layer

**Purpose**

The manifest layer turns messy metadata and filesystem artifacts into a frozen, auditable benchmark universe.

**Major responsibilities**

- schema discovery
- schema normalization
- canonical field enforcement
- optional-field injection
- vocabulary normalization
- resolved ID construction
- deterministic split assignment
- leakage auditing
- artifact resolution
- file hashing
- rejection tracking

**Main artifacts**

- split assignment artifact
- sample manifest
- rejection ledger
- leakage report

**Why this layer exists**

This is where many benchmarks quietly fail.
If this layer is weak, the rest of the stack becomes decorative.

## 6. Two-pass manifest architecture

The manifest layer is split into two passes.

### Pass 1: logical assignment

This pass is fast and metadata-centered.

**Responsibilities:**

- normalize source metadata
- enforce canonical fields
- derive resolved patient/specimen/slide IDs
- assign train/val/test membership
- detect leakage
- write deterministic assignments

### Pass 2: physical materialization

This pass is slower and provenance-centered.

**Responsibilities:**

- resolve actual files on disk
- validate candidate sample records
- compute hashes
- validate final manifest rows
- write rejection ledger
- emit final manifest

**Why two passes exist**

Because mixing:
- fast split logic
with
- expensive artifact hashing
creates a bad engineering loop and makes debugging miserable.

## 7. Resolver subsystem

**Purpose**

The resolver is responsible for locating required physical artifacts for each sample.

**Key principle**

The resolver operates artifact-by-artifact, not by assuming one global file layout.

**Required v1 artifact classes**

- spatial coordinates
- scalefactors metadata
- raw expression matrix
- image artifact

**Optional:**

- derived expression matrix

**Why it is separate**

File-layout assumptions are one of the easiest ways to accidentally bias a benchmark.
The resolver should therefore be treated as its own subsystem, not an ad hoc helper.

## 8. Target scoring layer

**Purpose**

The target scoring layer converts expression data into frozen per-spot program scores.

**Inputs**

- raw or declared expression artifact
- target definition
- scoring contract

**Outputs**

- target score artifact (Parquet format)

**Implementation**

Spatial-CI v1 uses **R/Bioconductor singscore** for target scoring:

- Python builds the manifest and prepares expression artifacts
- R computes frozen target score artifacts using singscore
- Score artifacts are emitted as Parquet files
- Python resumes downstream evaluation by consuming these artifacts

This cross-language boundary is explicit: **Python → R → Python**.

**Responsibilities**

- enforce source-faithful target semantics
- apply the scoring contract (via R singscore)
- enforce missing-gene policy
- record score provenance (including renv.lock hash)

**Why it is separate**

Targets are not just labels.
They are scientific objects.

If target generation is hidden inside experiment code, the whole benchmark becomes vulnerable to silent drift.

The R/Python split makes the scoring boundary auditable and reproducible.

## 9. Feature / embedding layer

**Purpose**

The feature layer transforms image inputs into reusable representations for baseline and model families.

**Inputs**

- image artifacts from the manifest
- alignment contract
- encoder identity

**Outputs**

- embedding artifacts

**Responsibilities**

- apply the frozen alignment contract
- extract image-level or spot-level features
- record encoder provenance
- preserve linkage to source image artifacts

**Why it is separate**

Spatial-CI treats embeddings as explicit intermediate artifacts rather than ephemeral tensors.

This improves:

- reuse
- auditability
- baseline fairness
- model comparison clarity

## 10. Experiment execution layer

**Purpose**

The experiment layer binds frozen artifacts and contracts into a declared run.

**Inputs**

- manifest
- score artifacts
- embedding artifacts
- run config
- contract identifiers

**Outputs**

- predictions
- run metadata
- diagnostics
- logs

**Responsibilities**

- enforce one primary intervention axis
- run baseline or learned models
- avoid hidden regeneration of upstream artifacts
- produce explicit prediction artifacts

**Why it is separate**

A run should be reconstructable from:

- its config
- its inputs
- its contract stack
- its outputs

That is only possible if experiment execution is an explicit architectural layer.

## 11. Evaluation layer

**Purpose**

The evaluation layer determines whether the outputs of a run deserve belief.

**Inputs**

- prediction artifacts
- target score artifacts
- baseline contract
- bootstrap contract
- split contract
- run metadata

**Outputs**

- evaluation certificate
- optional diagnostics
- optional error summaries

**Responsibilities**

- compute frozen metrics
- compare against deployable baselines
- compute clustered uncertainty
- summarize grouped behavior
- record leakage status and notes

**Why it is separate**

Evaluation should not be entangled with training.
It is a distinct scientific judgment layer.

This separation reduces:

- metric hacking
- accidental data leakage
- run/evaluation confusion

## 12. Certificate layer

Strictly speaking, the certificate is part of evaluation, but conceptually it deserves its own emphasis.

**Purpose**

The EvaluationCertificate is the artifact that says:

> given these contracts and these artifacts, this is the current evidence state of the run.

It is the architectural endpoint of a run, not just a report.

**Why it matters**

The certificate is what turns:

- files
- scores
- baselines
- predictions
- uncertainty

into a structured scientific statement.

## 13. Main artifact graph

The architecture is easiest to understand as an artifact graph.

```
Contract artifacts
    ├── TargetDefinition
    ├── ScoringContract
    ├── AlignmentContract
    ├── SplitContract
    ├── BaselineContract
    └── BootstrapContract

Raw metadata + source files
    ↓
Split assignment artifact
    ↓
Sample manifest
    ↓
Target score artifact
    ↓
Embedding artifact
    ↓
Run config
    ↓
Prediction artifact
    ↓
Evaluation certificate
```

Failures at any point should produce:

- rejection artifacts
- leakage artifacts
- validation errors

rather than silent continuation.

## 14. Separation of concerns

Spatial-CI architecture is intentionally strict about separation of concerns.

- **Contracts**: Define meaning.
- **Manifest**: Defines what data exist and are allowed into the benchmark.
- **Scoring**: Defines the target.
- **Embeddings**: Define reusable image representations.
- **Experiment execution**: Defines a declared intervention.
- **Evaluation**: Defines whether the result deserves belief.
- **Certificates**: Define the formal evidence state.

This separation is what keeps the benchmark from collapsing into one giant opaque pipeline.

## 15. Where the main scientific control points are

The architecture has a few especially important control points:

1. **TargetDefinition** - If target semantics drift, the task drifts.
2. **ScoringContract** - If scoring drifts, the labels drift.
3. **SplitContract** - If split logic drifts, generalization claims drift.
4. **SampleManifest** - If provenance drifts, the benchmark universe drifts.
5. **BaselineContract** - If baseline semantics drift, model-comparison claims drift.
6. **BootstrapContract** - If uncertainty logic drifts, confidence claims drift.

These are the parts of the architecture that most strongly govern truthfulness.

## 16. Failure containment

One role of architecture is to contain failure.

Spatial-CI tries to ensure that if one layer fails, it fails visibly.

**Examples:**

- manifest resolution fails → rejection ledger or hard halt
- leakage detected → fatal leakage report
- scoring contract mismatch → target artifact invalid
- missing artifact lineage → run invalid
- evaluation missing contract IDs → certificate invalid

The architecture should make it difficult for failures to remain flattering.

## 17. Determinism boundaries

Several layers are expected to be deterministic under fixed inputs:

- split assignment
- manifest generation
- target scoring
- artifact hashing
- baseline behavior
- certificate generation

If randomness exists, it should be:

- explicit
- seeded
- logged
- versioned where necessary

Determinism is not a universal law, but it is a major architectural goal.

## 18. What the architecture deliberately does not centralize

Spatial-CI does not try to centralize everything into:

- one god-object pipeline
- one huge config file
- one mega-class
- one notebook
- one monolithic training script

This is intentional.

Monoliths are seductive, but they hide assumptions and make drift easier.

## 19. Interface boundaries that should remain stable

Even if implementation evolves, these interfaces should remain conceptually stable:

- manifest format
- score artifact format
- embedding artifact format
- run config structure
- evaluation certificate structure
- contract identifiers and versioning rules

These interface boundaries are what allow the system to evolve without losing identity.

## 20. How the architecture supports the project thesis

Spatial-CI’s thesis is not “better models.”
It is:

explicit contracts, explicit provenance, honest baselines, and transportability-aware evaluation are more valuable than model complexity on a weak benchmark.

The architecture embodies that thesis by putting:

- contracts
- manifests
- scores
- baselines
- certificates

at the center of the system.

The model is one component, not the king of the project.

## 21. What a healthy architecture looks like in practice

A healthy Spatial-CI implementation should make it easy to answer:

- Which manifest produced these results?
- Which scoring contract generated these labels?
- Which exact image crop policy was used?
- Which split contract governed this run?
- Which baseline family is the real comparator?
- Was uncertainty computed properly?
- What was rejected?
- What is the exact claim supported by the certificate?

If the architecture cannot answer those questions, it is not healthy enough.

## 22. One-sentence summary

Spatial-CI architecture is a layered contract-and-artifact system designed to make morphology-to-expression benchmarking explicit, auditable, and hard to accidentally flatter.
