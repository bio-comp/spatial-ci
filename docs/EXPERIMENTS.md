
---

## `docs/EXPERIMENTS.md`

```markdown
# Spatial-CI Experiments

This document defines how experiments are structured, named, and interpreted in Spatial-CI.

The goal is to stop experiments from collapsing into “experiment soup” where many things change at once and no one can tell what caused the result.

Spatial-CI treats an experiment as a **declared intervention under frozen contracts**, not just a training run.

---

## 1. Experiment philosophy

A good experiment answers a specific question.

A bad experiment changes:
- target definition
- split logic
- alignment
- model
- normalization
- context strategy

all at once, then reports a single number and calls it progress.

Spatial-CI is designed to make bad experiments harder.

---

## 2. What an experiment is

An experiment is a run that binds together:

- a target definition
- a scoring contract
- an alignment contract
- a split contract
- a baseline contract
- a bootstrap contract
- a model/configuration
- an explicit intervention axis
- input artifacts
- output evaluation artifacts

If any of those are unknown, the experiment is under-specified.

---

## 3. Single primary intervention axis

## Rule

Every experiment must declare **exactly one primary intervention axis**.

Allowed v1 examples:
- `baseline`
- `encoder`
- `spatial_context`
- `normalization`
- `target_definition`

This does not mean only one thing can ever vary in reality.
It means the experiment must name the one thing it is trying to interpret.

---

## 4. Compound experiments

If more than one major dimension changes materially, the run must be marked as a **compound experiment**.

Compound experiments are allowed for exploration.
They are **not** to be interpreted as clean evidence for one isolated change.

Examples of compound runs:
- new encoder + new context model
- changed scoring + changed target set
- changed split + changed baseline family

Spatial-CI allows these, but they should be labeled honestly.

---

## 5. Frozen context vs intervention

Every experiment consists of:

### Frozen context
What is held fixed:
- target definition
- scoring contract
- alignment contract
- split contract
- baseline contract
- bootstrap contract
- input manifest version

### Intervention
What is changed deliberately:
- one primary axis

This distinction is the heart of experiment clarity.

---

## 6. Example v1 experiment families

### 6.1 Baseline family
Question:
> How much signal is already captured by trivial or nonparametric baselines?

Intervention axis:
- `baseline`

Examples:
- `global_train_mean`
- `mean_by_train_cohort`
- `knn_on_embeddings`
- `ridge_probe`

### 6.2 Simple learned head family
Question:
> Does a simple learned mapping from frozen pathology embeddings beat honest baselines?

Intervention axis:
- `baseline` or `encoder` depending on framing

Examples:
- pooled embedding + linear head
- pooled embedding + MLP head

### 6.3 Context family
Question:
> Does adding explicit local spatial context improve results beyond a simpler head?

Intervention axis:
- `spatial_context`

Examples:
- no-context pooled head
- local context smoother
- modest graph/context extension

### 6.4 Normalization family
Question:
> Does a changed preprocessing/normalization choice materially alter the benchmark?

Intervention axis:
- `normalization`

These experiments are risky and should only be run after the main stack is stable.

---

## 7. Experiment naming

Every experiment should have a stable, parseable identifier.

Recommended pattern:

```
<task>__<targetset>__<split>__<axis>__<variant>__<runid>

Example:

morph2expr__breast_visium_hallmarks_v1__breast_visium_strict_v1__baseline__ridge_probe__r001
```

The exact naming format can vary, but it should encode:

- task
- target set
- split
- primary intervention axis
- variant name
- run identity

## 8. Experiment metadata requirements

Every experiment record should include at minimum:

- run_id
- task_name
- target_definition_id
- scoring_contract_id
- alignment_contract_id
- split_contract_id
- baseline_contract_id
- bootstrap_contract_id
- manifest_id or manifest artifact hash
- intervention_axis
- variant_name
- notes

This makes runs auditable and comparable.

## 9. Input artifact rules

An experiment must point to explicit input artifacts, not vague directory assumptions.

At minimum:

- frozen manifest
- score artifact(s)
- embedding artifact(s), if applicable
- experiment config

No experiment should silently regenerate its own target labels under drifting settings.

## 10. Output artifact rules

Each experiment should emit explicit artifacts.

Recommended outputs:

- training summary artifact
- prediction artifact
- evaluation certificate
- optional diagnostics
- optional error analysis summaries

The most important output is the evaluation certificate.

## 11. What counts as a clean comparison

A comparison is considered clean only if all of the following are fixed:

- target definition
- scoring contract
- alignment contract
- split contract
- baseline contract
- bootstrap contract
- input manifest
- evaluation logic

and only the declared primary intervention axis changes.

If any of those drift, the comparison is no longer clean.

## 12. What counts as experiment soup

Experiment soup happens when:

- multiple major factors drift without being named
- one run uses different targets than another but they are compared directly
- split definitions drift midstream
- external holdouts get used for tuning
- hidden preprocessing changes occur
- model architecture changes are mixed with target changes
- score generation is rerun with different code but the same target ID is reused

Spatial-CI exists largely to prevent this.

## 13. Baseline-first rule

Before complex learned models are interpreted, the corresponding baseline family must be run under the same frozen context.

You do not get to say:

> "the deep model works"

until you have shown:

> "the deep model adds something beyond simple honest alternatives."

This is one of the core anti-theater rules of Spatial-CI.

## 14. Progression of experiment complexity

Recommended experiment order:

1. manifest-only sanity runs
2. score-generation sanity runs
3. baseline experiments
4. simple linear/MLP head
5. modest context-aware extension
6. only then more sophisticated spatial modeling

This order is important.
It makes sure each additional layer earns its existence.

## 15. External holdout discipline

The external same-assay holdout is not:

- a tuning sandbox
- a model-selection playground
- an error-analysis target used to rewrite contracts

It is a stress test for transportability.

External results should be examined honestly, but not used to retroactively optimize the benchmark.

## 16. Reproducibility requirements

An experiment should be reproducible from:

- contract IDs
- input artifact references
- environment lockfile
- experiment config
- code revision
- output artifact set

If a run cannot be reconstructed from those, it is not a Spatial-CI-quality experiment.

## 17. Minimum experiment config contents

A run config should include:

- run ID
- task name
- variant name
- model family
- optimizer/training settings if applicable
- contract IDs
- input artifact paths
- output paths
- seed(s)
- intervention axis
- freeform notes

This can be YAML, TOML, or JSON, but it must be explicit and versionable.

## 18. Error analysis expectations

Important experiments should include at least some structured error analysis.

Recommended slices:

- per target program
- per slide
- per patient
- per cohort
- highest-error slides
- worst-decile performance regions

This helps distinguish:

- model weakness
- cohort shift
- target ambiguity
- possible data issues

## 19. What a failed experiment means

A failed experiment is still useful if it tells the truth.

Examples of productive failures:

- simple baselines perform as well as a complex model
- external holdout collapses
- one target is not morphologically learnable enough
- context modeling does not help
- uncertainty intervals overlap baseline performance

These are scientific findings, not embarrassing accidents.

## 20. What a successful experiment means

A successful experiment is not just one with a good number.

It is one where:

- the contracts were frozen
- the intervention was clear
- the comparison was clean
- the baselines were honest
- the uncertainty was credible
- the external holdout behavior was interpretable
- the result survives scrutiny

That is the Spatial-CI standard.

## 21. Recommended experiment folders

Suggested structure:

```
configs/experiments/
├── baseline/
│   ├── ridge_probe_v1.yaml
│   ├── knn_probe_v1.yaml
│   └── global_mean_v1.yaml
├── simple_model/
│   ├── linear_head_v1.yaml
│   └── mlp_head_v1.yaml
└── spatial_context/
    └── local_context_v1.yaml
```

And outputs:

```
artifacts/runs/
├── <run_id>/
│   ├── config.yaml
│   ├── predictions.parquet
│   ├── evaluation_certificate.json
│   ├── diagnostics.json
│   └── logs.txt
```
## 22. What should never happen

These are anti-patterns Spatial-CI should forbid:

- tuning on external test
- changing target scoring without a new target/scoring contract
- comparing runs with different split contracts as if they were the same benchmark
- hiding rejected samples
- burying the true intervention axis
- using oracle baselines as if they were fair competitors
- writing broad claims from one lucky run

## 23. First experiment slate for v1

A sensible v1 experiment slate:

**A. Baseline slate**

- global mean
- train-cohort mean
- kNN on embeddings
- ridge probe

**B. Simple learned slate**

- pooled frozen embeddings + linear head
- pooled frozen embeddings + MLP head

**C. Context slate**

- one modest local-context extension only after A and B are stable

That is enough for a serious v1.

## 24. Decision rule for moving to the next experiment family

Do not advance to a more complex family unless the previous family has produced:

- valid evaluation certificates
- stable baseline comparisons
- interpretable external holdout behavior
- clear unresolved question that justifies the next complexity step

Complexity should answer a question, not satisfy curiosity alone.

## 25. One-sentence summary

Spatial-CI experiments are designed so that each run is a declared intervention under frozen contracts, making results interpretable rather than merely executable.
