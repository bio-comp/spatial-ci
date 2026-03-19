# Spatial-CI Artifacts

This document defines the major artifact types used in Spatial-CI.

Artifacts are the physical embodiment of the contract system.
They are how Spatial-CI turns abstract scientific intent into auditable, reproducible objects.

The purpose of this document is to answer:

- what artifacts exist
- why they exist
- what each one must contain
- how they relate to each other
- which ones are source-of-truth versus derived outputs

---

## 1. Artifact philosophy

Spatial-CI treats artifacts as first-class objects.

An artifact is not just “a file the pipeline happened to write.”
An artifact is a versioned scientific object that should make one of the following explicit:

- provenance
- target meaning
- split membership
- alignment semantics
- baseline semantics
- evaluation evidence
- failure/rejection state

If a result cannot be connected back to explicit artifacts, it is not trustworthy under the Spatial-CI standard.

---

## 2. Artifact categories

Spatial-CI artifacts fall into six broad categories:

1. **Contract artifacts**
2. **Source/provenance artifacts**
3. **Intermediate derived artifacts**
4. **Run artifacts**
5. **Evaluation artifacts**
6. **Failure/audit artifacts**

Each category serves a different purpose.

---

## 3. Contract artifacts

## 3.1 Purpose

Contract artifacts define the frozen scientific and engineering assumptions under which a run is valid.

Examples:
- target definition
- scoring contract
- alignment contract
- split contract
- baseline contract
- bootstrap contract

## 3.2 Role

These are the reference objects that make experiments comparable.

If two runs use different contract artifacts, they are not automatically comparable.

## 3.3 Expected storage

Examples:
- `configs/targets/*.yaml`
- `configs/splits/*.yaml`
- `configs/baselines/*.yaml`
- `configs/bootstrap/*.yaml`
- JSON snapshots under `contracts/artifacts/` if needed

---

## 4. Source/provenance artifacts

## 4.1 Purpose

These artifacts identify the physical data objects that entered the benchmark.

They provide:
- identity
- paths/URIs
- hashes
- inclusion/exclusion traceability

## 4.2 Main provenance artifact

### SampleManifest

The `SampleManifest` is the core provenance artifact in Spatial-CI.

It records:
- what sample exists
- which split it belongs to
- which physical files back it
- how identity was resolved
- whether raw and derived molecular files are distinct
- which alignment-supporting files exist

## 4.3 Why it matters

Without a strong provenance artifact, it is impossible to tell whether:
- a sample truly belongs in the benchmark
- a result was computed from the intended files
- a later rerun used the same underlying data

---

## 5. Intermediate derived artifacts

## 5.1 Purpose

These are data products derived from source/provenance artifacts but still upstream of final evaluation.

Examples:
- score artifacts
- embedding artifacts
- normalized expression artifacts
- extracted image tile indices
- patient split assignment tables

These artifacts should be explicit and versioned because they materially affect interpretation.

---

## 6. Run artifacts

## 6.1 Purpose

Run artifacts are the outputs of a specific experiment execution.

Examples:
- run config snapshot
- model predictions
- training summaries
- logs
- diagnostics
- run metadata

Run artifacts are not the final scientific verdict.
They are the trace of a particular experiment execution.

---

## 7. Evaluation artifacts

## 7.1 Purpose

Evaluation artifacts record whether the result deserves belief.

The most important evaluation artifact is the:

### EvaluationCertificate

This artifact ties together:
- run identity
- contract stack
- metrics
- uncertainty
- baseline comparisons
- leakage status

It is the core “decision-grade” object in Spatial-CI.

---

## 8. Failure and audit artifacts

## 8.1 Purpose

These artifacts preserve negative or suspicious states rather than letting them disappear.

Examples:
- leakage reports
- rejection ledgers
- missing-artifact reports
- validation failure traces
- score-drop summaries due to missing-gene policy

These are essential because silent failure is one of the easiest ways to corrupt a benchmark.

---

## 9. Artifact lineage

Spatial-CI artifacts should form a lineage graph.

A typical lineage chain looks like:

1. raw metadata + raw files
2. split assignments
3. sample manifest
4. target score artifacts
5. embedding artifacts
6. experiment config
7. model predictions
8. evaluation certificate

The more of this chain is explicit, the more trustworthy the project becomes.

---

## 10. Core artifact set for v1

The minimum serious artifact set for v1 is:

- split assignment artifact
- sample manifest
- target score artifact
- embedding artifact
- run config
- prediction artifact
- evaluation certificate
- rejection ledger
- leakage report if applicable

This is the minimum stack required to make Spatial-CI more than just a code exercise.

---

## 11. Split assignment artifact

## Purpose

Records which samples/patients belong to which split under the frozen split contract.

## Why it exists

The split is too important to be left implicit inside code.

## Minimum contents

- `sample_id`
- `cohort_id`
- `split`
- `resolved_patient_id`
- `patient_id_source`
- optional `resolved_specimen_id`
- optional `resolved_slide_id`

## Typical format

- `assignments.ndjson`
- or parquet if scale justifies it

---

## 12. Sample manifest

## Purpose

Defines the physically realized sample universe for the benchmark.

## Minimum contents

### Identity
- `sample_id`
- `split`
- `cohort_id`

### Auditability
- `resolved_patient_id`
- `patient_id_source`
- optional resolved specimen/slide IDs

### Metadata
- tissue type
- assay/platform
- other needed cohort metadata

### Image/molecule alignment
- image URI/hash
- spatial coordinates URI/hash
- scalefactors URI/hash

### Molecular artifacts
- raw expression URI/hash
- optional derived expression URI/hash

## Why it exists

This is the artifact that makes the benchmark traceable to actual files, not just assumptions.

---

## 13. Target score artifact

## Purpose

Stores the per-spot biological program scores used as prediction targets.

**Generated by:** R/Bioconductor singscore (via `scripts/score_targets.R`)

**Environment:** R environment is locked via `renv.lock`

## Minimum contents

- `sample_id`
- `spot_id`
- `target_definition_id`
- `scoring_contract_id`
- `program_name`
- `score_value`
- `n_target_genes_total`
- `n_target_genes_observed`
- `missing_fraction`
- `dropped_by_missingness_rule`
- `renv_lock_hash` (for provenance)

## Why it exists

This keeps target generation explicit and auditable, instead of recomputing labels in hidden notebook cells.

The R/Python split makes the scoring boundary reproducible.

---

## 14. Embedding artifact

## Purpose

Stores precomputed image features for downstream baselines and simple learned models.

## Minimum contents

- `sample_id`
- spatial unit identifier
- encoder name
- encoder version
- alignment contract ID
- feature dimensionality
- embedding storage path/hash

The on-disk embedding table should also expose a stable observation grain:

- `observation_id`
- `sample_id`
- `embedding` as a non-empty finite vector with one consistent dimensionality across rows

## Why it exists

Embeddings should be reproducible and explicitly tied to:
- the encoder
- the alignment contract
- the image artifact source

Otherwise “same embeddings” becomes ambiguous.

---

## 15. Run config artifact

## Purpose

Defines one specific experiment execution.

## Minimum contents

- `run_id`
- task name
- variant name
- contract IDs
- model family
- relevant hyperparameters
- input artifact references
- output locations
- primary intervention axis
- seed(s)

## Why it exists

A run config makes it possible to reconstruct not just “what code was run,” but “what scientific configuration was intended.”

---

## 16. Prediction artifact

## Purpose

Stores the raw predictions emitted by a run.

## Minimum contents

- `run_id`
- `observation_id`
- `sample_id`
- `program_name`
- predicted score
- for baseline outputs: `baseline_name`
- recommended context: `cohort_id`, `split`
- optional auxiliary outputs such as uncertainty or latent features

## Why it exists

The evaluation layer should not have to rerun the model to inspect predictions.
Predictions should be explicit artifacts.

---

## 17. Evaluation certificate

## Purpose

Defines the formal outcome of one run under the frozen contract stack.

## Minimum contents

### Run-level
- `run_id`
- contract IDs
- primary intervention axis

### Program-level
- `overall_spearman`
- clustered CI
- slide summaries
- baseline comparisons
- optional oracle analysis block

### Audit
- leakage status
- notes

## Why it exists

This is the most important artifact in the project.
It is the explicit answer to:
> does this run deserve belief?

---

## 18. Rejection ledger

## Purpose

Records samples that failed resolution or validation.

## Minimum contents

- `sample_id`
- split if known
- reason
- optional failure stage

## Why it exists

Without a rejection ledger, sample loss becomes invisible and can bias conclusions.

---

## 19. Leakage report

## Purpose

Records overlap detected between splits.

## Minimum contents

- overlapping split pair
- audit column (`patient`, `specimen`, `slide`)
- overlapping IDs
- timestamp or run reference

## Why it exists

Leakage is a fatal benchmark event and deserves a dedicated artifact.

---

## 20. Artifact formats

Recommended formats by artifact type:

### JSON
Good for:
- contracts
- evaluation certificates
- small config objects

### NDJSON
Good for:
- manifests
- assignments
- rejection ledgers
- record-oriented artifacts

### Parquet
Good for:
- large tabular score/prediction artifacts
- high-scale intermediate tables

### Binary tensor formats
Possible for:
- embeddings
- large prediction matrices

But even binary artifacts should have a small metadata sidecar or corresponding manifest entry.

---

## 21. Artifact naming conventions

Artifacts should use names that make them legible in version control and storage.

Suggested patterns:

- `assignments__breast_visium_strict_v1.ndjson`
- `manifest__breast_visium_strict_v1.ndjson`
- `scores__breast_visium_hallmarks_v1__singscore_v1.parquet`
- `embeddings__uni2__visium_context_224px_0_5mpp_v1.parquet`
- `evalcert__<run_id>.json`
- `rejections__manifest_pass2_v1.ndjson`

Avoid generic names like:
- `results.csv`
- `final.json`
- `test_output.parquet`

---

## 22. Artifact immutability

Artifacts should be treated as immutable once published for a run or version.

If the contents must change materially:
- emit a new artifact
- bump the relevant contract version if needed
- do not silently overwrite a meaningfully different object under the same identity

This is especially important for:
- manifests
- target scores
- evaluation certificates

---

## 23. Artifact relationships that must remain explicit

A valid evaluation certificate should be traceable to:

- a run config
- a prediction artifact
- the manifest
- the score artifact
- the frozen contracts

A valid score artifact should be traceable to:

- the raw expression artifact
- the scoring contract
- the target definition

A valid embedding artifact should be traceable to:

- the image artifact
- the alignment contract
- the encoder identity

These relationships are what make Spatial-CI a system rather than a collection of scripts.

---

## 24. Artifact anti-patterns

These are forbidden or strongly discouraged:

- unlabeled CSV dumps
- rerunning target scores in notebooks without emitted score artifacts
- silent overwriting of manifests
- baseline results without a run config
- certificates that cannot be traced back to predictions
- mixing raw and derived expression artifacts in one field
- implicit split logic with no assignments artifact

---

## 25. Minimal artifact graph for a serious v1 run

A minimally serious v1 run should have the following explicit chain:

1. frozen contracts
2. split assignment artifact
3. sample manifest
4. score artifact
5. embedding artifact
6. run config
7. prediction artifact
8. evaluation certificate
9. rejection ledger if any failures occurred

If any of these are missing, trust should go down sharply.

---

## 26. One-sentence summary

Spatial-CI artifacts exist to make every meaningful scientific assumption, data dependency, and evaluation result concrete enough to audit, compare, and trust.
