# Spatial-CI Manifest Pipeline

This document defines the data-engineering pipeline that turns raw metadata and filesystem artifacts into a frozen, auditable Spatial-CI manifest.

The manifest pipeline is where a large fraction of benchmark corruption usually happens.

Spatial-CI therefore treats manifest generation as a first-class scientific process, not just preprocessing.

---

## 1. Manifest philosophy

The manifest is not a convenience file.

It is a **provenance artifact** that must make the following auditable:

- what samples were included
- why they were included
- which split they belong to
- how patient/specimen/slide identity was resolved
- which physical artifacts were used
- whether the sample was rejected
- what raw vs derived molecular files exist
- how image–spot alignment can be reconstructed

The pipeline must make silent errors difficult.

---

## 2. Pipeline overview

Spatial-CI uses a **two-pass manifest builder**.

### Pass 1: logical assignment
Fast, metadata-centered, deterministic.

Responsibilities:
- schema discovery
- schema normalization
- canonical field enforcement
- optional field injection
- vocabulary normalization
- cohort filtering
- auditable ID resolution
- deterministic split assignment
- leakage audit
- sorted split-assignment output

### Pass 2: physical materialization
Slow, artifact-centered, provenance-heavy.

Responsibilities:
- sample directory resolution
- artifact-by-artifact probing
- pre-hash validation
- file hashing
- final manifest validation
- rejection ledger writing
- deterministic manifest output

---

## 3. Why two passes exist

Hashing pathology artifacts while still experimenting with metadata logic is a great way to ruin iteration speed.

Two passes give:

- fast metadata iteration
- resumable provenance work
- cleaner failure boundaries
- explicit distinction between logical sample inclusion and physical file realization

Pass 1 should be cheap.
Pass 2 is allowed to be expensive.

---

## 4. Pass 1: schema discovery and normalization

## 4.1 Goal

Convert raw source metadata into a canonical staging schema that can support:
- filtering
- deterministic splitting
- leakage auditing
- final manifest generation

## 4.2 Required canonical fields

At minimum, the staging schema must contain:

- `sample_id`
- `cohort_id`
- `assay_platform`
- `tissue_type`

If any of these are missing after normalization, the pipeline must halt.

## 4.3 Optional canonical fields

The following should be injected explicitly if missing:

- `patient_id`
- `specimen_id`
- `slide_id`
- `site_id`

These should be added as null columns if absent, so downstream logic does not crash.

## 4.4 Loud failure

Schema normalization must fail loudly on missing required canonicals.

No silent best-effort behavior.

---

## 5. Vocabulary normalization

## 5.1 Goal

Prevent legitimate samples from being lost because metadata strings vary.

## 5.2 Example normalization targets

For tissue:
- `breast`
- `breast cancer`
- `brca`
- `mammary`

For assay:
- `visium`
- `10x visium`
- `visium spatial`

These should be normalized before filtering.

---

## 6. Auditable ID resolution

## 6.1 Why it exists

Real metadata are messy.
Patient IDs are often missing or inconsistently available.

Naively falling back to `sample_id` can produce false separation and let leakage slip through undetected.

## 6.2 Required derived fields

The staging table must derive:

- `resolved_patient_id`
- `patient_id_source`

Recommended `patient_id_source` values:
- `true_patient_id`
- `specimen_fallback`
- `sample_fallback`

## 6.3 Fallback rule

Preferred order:
1. true patient ID
2. specimen ID as patient proxy
3. sample ID as last resort

## 6.4 Namespacing

All resolved IDs must be namespaced by cohort to avoid false collisions across cohorts.

Required:
- `resolved_patient_id`

Recommended:
- `resolved_specimen_id`
- `resolved_slide_id`

## 6.5 Null discipline

If `specimen_id` or `slide_id` is null, the resolved namespaced field must remain null.

Do **not** produce artifacts like:
- `cohort:null`

That creates fake overlap signals.

---

## 7. Deterministic split assignment

## 7.1 v1 split design

Discovery cohorts are pooled.
External same-assay cohorts are held out.

### Discovery cohorts
Used to create:
- `train`
- `val`

### External cohorts
Used as:
- `test_external`

## 7.2 Assignment logic

Patient assignment must be:

- deterministic
- patient-level
- stable across reruns

Recommended strategy:
- isolate unique `resolved_patient_id` values in discovery cohorts
- compute split assignment once via deterministic hash
- join assignments back to the staging table

## 7.3 Why not row-wise mapping

Row-by-row split callbacks are:
- less elegant
- less auditable
- easier to misuse

The patient join-table pattern is preferred.

---

## 8. Leakage audit

## 8.1 Required overlap checks

The pipeline must audit overlap across split pairs for:

- patient
- specimen
- slide

Split pairs in v1:
- `train` vs `val`
- `train` vs `test_external`
- `val` vs `test_external`

## 8.2 Required behavior on overlap

If overlap exists:
- write a fatal leakage report
- include overlapping IDs
- halt immediately

No warnings-only behavior.

## 8.3 Why

A benchmark with leakage is not salvageable by downstream metric sophistication.

---

## 9. Pass 1 output

Pass 1 writes a **sorted split-assignment staging artifact**.

Recommended output:
- `assignments.ndjson`

The staging table should include at least:

- `sample_id`
- `cohort_id`
- `split`
- `resolved_patient_id`
- `patient_id_source`
- optional resolved specimen/slide IDs
- any metadata needed for Pass 2 path resolution

Sort before write, e.g. by:
- `split`
- `cohort_id`
- `sample_id`

This makes diffs deterministic.

---

## 10. Pass 2: physical artifact materialization

## 10.1 Goal

Turn logical assignments into a final, validated manifest with physical provenance.

Pass 2 is responsible for:
- locating real files
- validating sample structure
- hashing artifacts
- recording failures
- emitting final manifest rows

---

## 11. Sample directory resolution

## 11.1 Principle

Do not assume:
- `data_dir / sample_id`

unless that convention is itself frozen and documented.

The pipeline should use one of:
- path mapping metadata
- explicit path manifest
- validated filesystem convention

Sample path resolution must be a declared assumption.

---

## 12. Artifact-by-artifact resolver

## 12.1 Principle

Do not infer one global root and assume all artifacts live there.

Probe each required artifact independently.

## 12.2 Required artifact classes

At minimum:

- spatial coordinates
- scalefactors metadata
- raw expression matrix
- image artifact

Optional:
- derived expression artifact

## 12.3 Example coordinate candidates

- `outs/spatial/tissue_positions.csv`
- `outs/spatial/tissue_positions_list.csv`
- `spatial/tissue_positions.csv`
- `spatial/tissue_positions_list.csv`

## 12.4 Example scalefactor candidates

- `outs/spatial/scalefactors_json.json`
- `spatial/scalefactors_json.json`

## 12.5 Example raw matrix candidates

- `outs/filtered_feature_bc_matrix.h5`
- `filtered_feature_bc_matrix.h5`

## 12.6 Example image candidates

Priority:
1. explicit TIFF if the dataset/project provides one
2. `outs/spatial/tissue_hires_image.png`
3. project-specific root-level fallback if documented

---

## 13. Why scalefactors are required

Coordinates alone are not enough for fully reconstructable spot-to-pixel alignment.

The scalefactors metadata ties:
- the original image
- the spatial output image
- the array geometry

to each other.

Without it, the alignment contract is incomplete.

---

## 14. Raw vs derived expression artifacts

## 14.1 Rule

Raw and derived molecular files must be distinguished explicitly.

## 14.2 Required fields

If both exist, keep separate fields such as:

- `raw_expression_uri`
- `raw_expression_sha256`
- `derived_expression_uri`
- `derived_expression_sha256`

## 14.3 Why

A derived `.h5ad` is not the same artifact as the raw 10x matrix.
Conflating them destroys provenance.

---

## 15. Pre-hash validation

Before expensive hashing, each candidate manifest row should pass a lightweight validation step.

This pre-hash contract should confirm at least:

- required fields exist
- resolved paths exist
- split/cohort/sample identifiers are coherent
- raw vs derived artifact distinctions are valid

This prevents wasting time hashing obviously invalid samples.

---

## 16. Final manifest validation

After hashing, the final emitted row must be validated against the real `SampleManifest` schema.

Pre-hash validation is not enough.

Spatial-CI requires:
1. pre-hash validation
2. final manifest validation

Both are mandatory.

---

## 17. Hashing policy

## 17.1 Required behavior

All required resolved artifacts must be hashed using a stable content hash.

Recommended:
- SHA256

## 17.2 Why

Hashes make it possible to:
- detect file drift
- audit data reuse
- guarantee provenance integrity
- separate “same filename” from “same artifact”

---

## 18. Rejection policy

## 18.1 Philosophy

No silent attrition.

## 18.2 Required rejection behavior

If a sample fails:
- path resolution
- validation
- required artifact presence
- final schema validation

then it must be written to a rejection ledger.

Recommended output:
- `manifest.rejections.parquet`

Include at minimum:
- `sample_id`
- split if known
- reason

## 18.3 Default behavior

If any assigned sample is rejected, Pass 2 should halt by default.

## 18.4 Explicit escape hatch

An optional `--allow-missing` flag may allow completion, but:
- the rejection ledger must still be written
- the pipeline must emit a visible warning
- downstream evaluation must know missing samples occurred

---

## 19. Final manifest output

The final manifest should be:

- validated
- sorted
- deterministic

For an output path like `manifest.parquet`, sibling artifacts should be:

- `manifest.assignments.parquet`
- `manifest.assignments.leakage.parquet` when pass-1 leakage is found
- `manifest.rejections.parquet` when pass-2 rejections occur
- `manifest.parquet` for accepted final rows
- auditable

Recommended output:
- `manifest.ndjson`

Each row should include at least:

### Identity and split
- `sample_id`
- `split`
- `cohort_id`

### Auditability
- `resolved_patient_id`
- `patient_id_source`
- optional `resolved_specimen_id`
- optional `resolved_slide_id`

### Metadata
- nested metadata block

### Image/molecule alignment artifacts
- image URI/hash
- spatial coordinates URI/hash
- scalefactors URI/hash

### Molecular artifacts
- raw expression URI/hash
- optional derived expression URI/hash

---

## 20. Deterministic sorting

Sort the flattened staging/output table before serialization.

Recommended keys:
- `split`
- `cohort_id`
- `sample_id`

Do not rely on incidental row order.

This keeps version-control diffs meaningful.

---

## 21. Failure modes the pipeline is designed to prevent

The manifest pipeline is specifically designed to make these failures hard:

- hidden patient leakage through missing IDs
- false uniqueness from naïve `sample_id` fallback
- false overlap from un-namespaced generic IDs
- dropped samples due to brittle file-layout assumptions
- raw/derived expression conflation
- missing alignment metadata
- silent external-cohort attrition
- non-deterministic manifests

---

## 22. What a “good” manifest means

A good manifest is one where:

- every included sample is explainable
- every rejected sample is explainable
- every split is reproducible
- every critical artifact has provenance
- every fallback is auditable
- the final table can be reconstructed deterministically

That is the standard Spatial-CI aims for.

---

## 23. One-sentence summary

The Spatial-CI manifest pipeline exists to ensure that every downstream model result is grounded in a frozen, auditable, leakage-resistant representation of what data actually entered the experiment.
