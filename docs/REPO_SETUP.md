# Spatial-CI Repo Setup

This document describes how to set up the Spatial-CI repository for development and reproducible research.

The goal is not merely to “get the code running.”
The goal is to make sure the environment, contracts, and filesystem conventions support the scientific guarantees Spatial-CI depends on.

---

## 1. Setup philosophy

Spatial-CI setup must support:

- deterministic environments
- explicit contract schemas
- auditable manifests
- stable experiment outputs
- cross-platform development where practical
- optional GPU/Linux acceleration where useful

The repository should be usable in at least two realistic modes:

1. **CPU-safe development mode**
   - docs
   - schemas
   - manifest building
   - target scoring
   - baseline evaluation
   - light testing

2. **GPU/Linux experiment mode**
   - large image processing
   - embedding extraction
   - model training
   - faster spatial pipelines

These two modes should share the same conceptual contracts even if the dependency stacks differ slightly.

---

## 2. Repository layout

Recommended repo structure:

```
spatial-ci/
├── README.md
├── LICENSE
├── pyproject.toml
├── uv.lock
├── .gitignore
├── docs/
│   ├── CONTRACTS.md
│   ├── DESIGN_DECISIONS.md
│   ├── EVALUATION.md
│   ├── EXPERIMENTS.md
│   ├── MANIFEST_PIPELINE.md
│   ├── REPO_SETUP.md
│   ├── ROADMAP.md
│   ├── SCORING.md
│   └── TARGETS.md
├── contracts/
│   ├── artifacts/
│   ├── schemas/
│   └── examples/
├── configs/
│   ├── targets/
│   ├── splits/
│   ├── baselines/
│   ├── bootstrap/
│   └── experiments/
├── data/
│   ├── raw/
│   ├── interim/
│   ├── processed/
│   └── external/
├── scripts/
│   ├── build_manifest.py
│   ├── score_targets.py
│   ├── run_baselines.py
│   ├── extract_embeddings.py
│   ├── train_model.py
│   └── evaluate_run.py
├── src/
│   └── spatial_ci/
│       ├── __init__.py
│       ├── baselines/
│       ├── contracts/
│       ├── evaluation/
│       ├── experiments/
│       ├── manifest/
│       ├── models/
│       ├── scoring/
│       ├── transforms/
│       └── utils/
└── tests/
    ├── test_contracts.py
    ├── test_manifest_pipeline.py
    ├── test_scoring.py
    ├── test_baselines.py
    └── fixtures/
```

## 3. Python version policy

Recommended Python version range:

>=3.11,<3.12 for maximum boring stability in the current stack

Why:

- stable scientific Python support
- fewer surprises with pathology/image dependencies
- fewer compatibility issues with Linux/GPU extras

If a future stack reliably supports 3.12+, that should be introduced deliberately and documented.

## 4. Package manager and lock policy

Spatial-CI uses a **bimodal environment** approach:

**Python side:**

- `uv` for Python package management (developer workflow)
- `environment.yml` for Conda/micromamba runtime definitions
- `pyproject.toml` defines Python dependency intent
- `uv.lock` is the frozen Python environment artifact
- `uv.lock` must be committed to version control

**R side:**

- `renv` for R package management  
- `renv.lock` is the frozen R environment artifact
- `.Rprofile` activates renv on project load
- `renv.lock` must be committed to version control

**Note:** pyproject.toml is NOT the whole environment truth anymore. The R scoring stack is a separate locked environment. Use `environment.yml` for explicit runtime definitions with micromamba/mamba.

## 5. Environment modes

### 5.1 Base environment

The base environment should support:

- contracts
- docs
- manifest pipeline
- score consumption (Python side)
- baseline evaluation
- CPU-safe tests

Typical Python dependencies:

- polars
- pydantic
- scanpy
- anndata
- torch
- torchvision
- openslide-python
- openslide-bin
- pytest
- ruff

Typical R dependencies (via renv):

- singscore (Bioconductor)
- SingleCellExperiment
- scRNAseq annotation packages

### 5.2 Optional GPU/Linux extras

GPU- and Linux-specific packages should live in optional extras or separate environment groups.

Examples:

- cucim
- CUDA-specific torch wheels if needed
- large-scale WSI acceleration packages

Do not force Linux/GPU-only packages into the base cross-platform environment unless absolutely necessary.

## 6. R/renv setup for scoring

Spatial-CI uses R for target scoring via Bioconductor's singscore package.

**Required setup:**

1. Initialize renv in the project:
   ```r
   renv::init()
   ```

2. Install required R packages:
   ```r
   install.packages("singscore")
   ```

3. Snapshot the environment:
   ```r
   renv::snapshot()
   ```

4. Commit both `renv.lock` and `.Rprofile` to version control.

**Bootstrapping renv on a new machine:**

```r
source("renv/activate.R")
renv::restore()
```

**Key rules:**

- Always use `renv::snapshot()` after installing new R packages
- Never modify packages outside of renv
- The `renv.lock` file is the source of truth for R dependencies

## ## 7. OpenSlide dependency policy

openslide-python alone is not enough.
The OpenSlide runtime/library must also be available.

**Recommended base approach:**

- include openslide-bin in Python dependencies where appropriate
- document OS-specific installation notes if needed

The repo should clearly distinguish:

- Python package dependency
- runtime/system dependency

## 8. Dependency management with unidep

Spatial-CI uses [unidep](https://github.com/mwibutwa/unidep) to unify Conda and pip dependencies in a single source of truth.

The project uses:

- `pyproject.toml` with `[tool.unidep]` for dependency definitions
- `environment.yml` for explicit Conda/micromamba runtime definitions
- `uv.lock` for Python-only development workflows

**Key principles:**

- Prefer Conda packages for compiled scientific/system dependencies
- Keep pip editable install in the dependencies
- Keep GPU-only extras out of the base set
- Use `[tool.unidep]` as the single source of truth
- Set `project_dependency_handling = "ignore"` to avoid duplication

See `pyproject.toml` for the full configuration.

## 9. Initial setup workflow

Typical first-time setup:

- clone the repo
- install uv
- create/sync the environment
- verify the lockfile
- run tests
- run a lightweight smoke check

### Option A: uv (Python-only development)

```
git clone <repo-url>
cd spatial-ci
uv sync
uv run pytest
```

If there are optional extras:

```
uv sync --extra gpu-linux
```

### Option B: micromamba/Conda (full runtime including R)

```
git clone <repo-url>
cd spatial-ci
micromamba env create -f environment.yml
micromamba activate spatial-ci
pytest
```

**Note:** R dependencies are managed separately via `renv.lock`.
## 10. Data directory policy

The repo must clearly separate code from data.

Recommended directories:

- data/raw/
- data/interim/
- data/processed/
- data/external/

**Rules**

- do not commit large raw datasets to git
- manifests and tiny examples may live under contracts/artifacts/ or tests/fixtures/
- generated large artifacts should be ignored unless intentionally versioned

## 11. Path mapping policy

Do not hardcode the assumption that:

> sample_id == directory name

Use one of:

- explicit path mapping file
- metadata-provided path column
- documented filesystem convention enforced by tests

This must be treated as part of the data-engineering contract, not as an informal convenience.

## 12. Config layout

Spatial-CI should separate code from experiment/config state.

Recommended config folders:

- configs/targets/
- configs/splits/
- configs/baselines/
- configs/bootstrap/
- configs/experiments/

These files should hold:

- frozen target references
- split definitions
- baseline settings
- bootstrap settings
- run-level experiment metadata

No important configuration should live only inside notebooks.

## 13. Contract schemas vs artifact instances

Spatial-CI distinguishes between:

**Schemas**

The definitions of valid artifacts:

- Pydantic models
- enums
- validation rules

**Artifact instances**

Concrete frozen files:

- split assignment outputs
- manifests
- evaluation certificates
- score artifacts

**Recommended separation:**

- `src/spatial_ci/contracts/` for schema code
- `contracts/artifacts/` for materialized artifact files
- `contracts/examples/` for small example JSON/NDJSON snippets

## 14. Testing policy

**Minimum required test classes**

### Contract tests

Validate:

- required fields
- enums
- serialization/deserialization
- rejection of invalid states

### Manifest tests

Validate:

- schema normalization
- optional-column injection
- namespaced ID resolution
- leakage detection
- resolver behavior
- rejection ledger behavior

### Scoring tests

Validate:

- scorer reproducibility
- missing-gene behavior
- score provenance fields

### Baseline tests

Validate:

- honest split usage
- fallback rules
- tuning boundaries

## 15. Linting and formatting

Recommended tooling:

- ruff for linting
- optional formatter of choice if desired, but keep it boring and deterministic

The point is not stylistic purity.
The point is reducing accidental ambiguity in a codebase built around explicit contracts.

## 16. Notebook policy

Notebooks may be useful for exploration, but they are not a source of truth.

**Rules:**

- no frozen logic should live only in notebooks
- no scoring or split policy should be notebook-only
- notebooks may inspect artifacts, but artifacts must be generated by scripts/modules

Spatial-CI is contract-driven, not notebook-driven.

## 17. Script policy

Each major workflow should have an explicit script or command entry point.

**Python scripts:**

- build_manifest.py
- run_baselines.py
- extract_embeddings.py
- train_model.py
- evaluate_run.py

**R scripts:**

- score_targets.R - computes frozen target scores using singscore
- bootstrap_renv.R - bootstraps renv environment

Each should:

- accept explicit input/output paths
- log contract identifiers
- fail loudly on contract mismatch
- avoid hidden defaults for scientific choices

Current baseline note:

- `run_baselines.py` currently covers the mean-baseline foundation
  (`global_train_mean` and `mean_by_train_cohort`)
- it consumes an explicit score artifact plus manifest parquet
- `--embeddings <path>` enables the frozen `knn_on_embeddings` baseline on the
  same joined score rows; omit it to run mean baselines only
- the embeddings artifact must carry `observation_id`, `sample_id`, and
  finite embedding vectors at a single consistent dimensionality
- embedding baselines and evaluation certificates are follow-up slices

## 18. Logging policy

Every major run should log:

- run ID
- target definition ID
- scoring contract ID
- split contract ID
- baseline contract ID
- bootstrap contract ID
- alignment contract ID
- software environment identity
- input artifact hashes where applicable

This makes debugging and audit much easier later.

## 19. Output artifact policy

All serious outputs should be explicit files, not ephemeral printouts.

Important artifact types include:

- split assignments
- manifests
- score artifacts
- baseline outputs
- evaluation certificates
- rejection ledgers
- leakage reports

Recommended formats:

- JSON
- NDJSON
- parquet where tabular scale demands it

## 20. Git hygiene

**Recommended .gitignore categories:**

- raw data
- processed data
- model checkpoints
- large intermediate artifacts
- OS/editor junk
- temporary experiment outputs not intended for version control

**Do commit:**

- docs
- schemas
- small example artifacts
- tests
- lockfile
- small configs

## 21. Suggested first boot sequence

A sensible sequence for bringing the repo to life:

1. create repo skeleton
2. add docs
3. add pyproject.toml
4. generate uv.lock
5. implement contract schemas
6. write contract tests
7. implement manifest Pass 1
8. implement manifest Pass 2
9. generate first frozen manifest
10. implement scoring
11. implement baselines
12. implement simple model

Do not start by writing the fanciest model first.

22. Minimal “repo is healthy” checklist

The repo is minimally healthy when:

uv sync works

tests pass

contract schemas import cleanly

manifest scripts run on fixtures

one example artifact can be validated end-to-end

That is the point where the repository has become an engineering system, not just an idea dump.

## 23. One-sentence summary

Spatial-CI repo setup exists to make the scientific contract stack reproducible in code, not just persuasive in prose.
