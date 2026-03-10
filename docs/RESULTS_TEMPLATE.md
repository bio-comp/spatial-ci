
---

## `docs/RESULTS_TEMPLATE.md`

```markdown
# Spatial-CI Results Template

This document provides a standard template for reporting Spatial-CI results.

The point of this template is not presentation polish.
The point is to make sure every result summary includes the information needed for honest interpretation.

A Spatial-CI result should communicate:

- what was tested
- under what contracts
- against what baselines
- with what uncertainty
- on what holdout regime
- with what caveats

If a result summary cannot answer those, it is incomplete.

---

## 1. Results philosophy

Spatial-CI results are not just metrics.
They are structured evidence states.

A useful result summary must preserve:

- task identity
- target identity
- contract identity
- baseline context
- uncertainty
- external-holdout behavior
- limitations

This template exists to prevent “pretty number, weak explanation” reporting.

---

## 2. Standard result package

A complete result package for one run should include:

1. run header
2. contract stack
3. data/split summary
4. target summary
5. baseline comparison table
6. primary performance table
7. uncertainty summary
8. slide/patient dispersion summary
9. external holdout summary
10. interpretation notes
11. limitations
12. explicit claim statement
13. artifact references

This is the minimum reporting spine.

---

## 3. Run header template

```markdown
## Run Summary

- Run ID:
- Variant Name:
- Task:
- Primary Intervention Axis:
- Date:
- Code Revision / Commit:
- Environment Lock Reference:

Example:

## Run Summary

- Run ID: morph2expr__breast_visium_hallmarks_v1__breast_visium_strict_v1__baseline__ridge_probe__r001
- Variant Name: ridge_probe
- Task: morphology-to-expression
- Primary Intervention Axis: baseline
- Date: YYYY-MM-DD
- Code Revision / Commit: <git-sha>
- Environment Lock Reference: uv.lock @ <hash or commit>
## 4. Contract stack template

## Contract Stack

- Target Definition ID:
- Scoring Contract ID:
- Alignment Contract ID:
- Split Contract ID:
- Baseline Contract ID:
- Bootstrap Contract ID:
- Manifest ID / Manifest Hash:

This section is non-optional.

A result without its contract stack is not a Spatial-CI-quality result.

## 5. Data summary template

## Data Summary

- Discovery Cohorts:
- External Holdout Cohorts:
- Total Samples:
- Train Samples:
- Validation Samples:
- External Test Samples:
- Unique Patients:
- Unique Slides:
- Rejected Samples:
- Rejection Ledger Reference:
- Leakage Status:

Include whether rejected samples existed and whether they were allowed under any escape hatch.

## 6. Target summary template

## Targets Evaluated

- Program 1:
- Program 2:
- Program 3:

### Target Notes
- Missing-gene policy:
- Score artifact reference:
- Any program-specific exclusions:

This section should explicitly preserve the truth-in-advertising rule.

Example:

> report HALLMARK_EPITHELIAL_MESENCHYMAL_TRANSITION as EMT/mesenchymal program, not stromal/CAF.

## 7. Baseline comparison table template

Use one table per target program.

## Baseline Comparison

| Program | Global Train Mean | Mean by Train Cohort | kNN on Embeddings | Ridge Probe | Best Honest Baseline |
|--------|--------------------|----------------------|-------------------|-------------|----------------------|
| ...    | ...                | ...                  | ...               | ...         | ...                  |

If oracle analyses are included, they must be shown separately.

## 8. Oracle analysis table template

## Oracle / Analysis-Only Upper Bounds

| Program | Oracle Slide Mean | Notes |
|--------|--------------------|-------|
| ...    | ...                | ...   |

Important:
This table must be clearly labeled as analysis-only and not mixed with deployable baselines.

## 9. Primary performance table template

## Primary Performance

| Program | Run Variant | Overall Spearman | 95% Clustered CI | Best Honest Baseline | Margin vs Best Baseline |
|--------|-------------|------------------|------------------|----------------------|-------------------------|
| ...    | ...         | ...              | ...              | ...                  | ...                     |

This is the main quantitative summary table.

## 10. Dispersion summary table template

## Slide / Patient Dispersion

| Program | Median Slide Spearman | IQR Slide Spearman | Worst-Decile Slide Spearman | Notes |
|--------|------------------------|--------------------|-----------------------------|-------|
| ...    | ...                    | ...                | ...                         | ...   |

This section is required because means alone can hide catastrophic subsets.

## 11. External holdout summary template

## External Holdout Summary

| Program | Internal Validation Spearman | External Holdout Spearman | Delta | Interpretation |
|--------|-------------------------------|---------------------------|-------|----------------|
| ...    | ...                           | ...                       | ...   | ...            |

The interpretation column should be conservative.

Examples:

- "modest degradation, still above ridge"
- "severe degradation, weak transportability evidence"
- "near-baseline on external holdout"

## 12. Uncertainty summary template

## Uncertainty Notes

- Bootstrap clustering unit:
- Number of bootstrap replicates:
- Any instability warnings:
- Any programs with broad or overlapping CIs:

This makes the uncertainty procedure legible even outside the tables.

## 13. Interpretation template

## Interpretation

### What this run supports
- ...

### What this run does not support
- ...

### Comparison to strongest honest baseline
- ...

### External transportability read
- ...

### Most important caution
- ...

This section should read like a disciplined scientific interpretation, not a marketing summary.

## 14. Limitations template

## Limitations

- External holdout size limitations:
- Target semantic limitations:
- Manifest or rejection caveats:
- Identity fallback caveats:
- Assay-specific limitations:
- Model or baseline limitations:

This section is not optional.
It is part of the claim discipline of the project.

## 15. Claim statement template

Every result should end with one explicit claim statement.

**Stronger template**

## Claim

Under `<contract stack>`, `<variant>` predicts `<program>` above `<best honest baseline>` with `<uncertainty summary>` and `<external holdout interpretation>`.

**Negative template**

## Claim

Under `<contract stack>`, there is insufficient evidence that `<variant>` predicts `<program>` beyond `<best honest baseline>` in a transportable way.

Claims should be narrow and artifact-backed.

## 16. Artifact reference template

## Artifact References

- Manifest:
- Score Artifact:
- Embedding Artifact:
- Run Config:
- Predictions:
- Evaluation Certificate:
- Rejection Ledger:
- Leakage Report:

This keeps every summary traceable back to the actual output objects.

## 17. Example compact result summary

# Result Summary: ridge_probe__r001

## Run Summary
- Run ID: morph2expr__breast_visium_hallmarks_v1__breast_visium_strict_v1__baseline__ridge_probe__r001
- Variant Name: ridge_probe
- Primary Intervention Axis: baseline

## Contract Stack
- Target Definition ID: breast_visium_hallmarks_v1
- Scoring Contract ID: singscore_v1
- Alignment Contract ID: visium_context_224px_0_5mpp_v1
- Split Contract ID: breast_visium_strict_v1
- Baseline Contract ID: standard_baselines_v1
- Bootstrap Contract ID: clustered_patient_or_slide_v1

## Primary Performance
| Program | Overall Spearman | 95% Clustered CI | Best Honest Baseline |
|--------|------------------|------------------|----------------------|
| HALLMARK_HYPOXIA | ... | (...) | ... |
| HALLMARK_G2M_CHECKPOINT | ... | (...) | ... |
| HALLMARK_EPITHELIAL_MESENCHYMAL_TRANSITION | ... | (...) | ... |

## Dispersion
| Program | Median Slide Spearman | IQR | Worst-Decile |
|--------|------------------------|-----|--------------|
| ...    | ...                    | ... | ...          |

## External Holdout
| Program | Internal | External | Delta |
|--------|----------|----------|-------|
| ...    | ...      | ...      | ...   |

## Claim

Under the frozen v1 contract stack, ridge on frozen embeddings retains signal for `HALLMARK_G2M_CHECKPOINT` above simpler mean baselines, with moderate external degradation and non-catastrophic clustered uncertainty.

## 18. What this template is designed to prevent

The result template is specifically designed to prevent:

- metric-only reporting
- baseline omission
- uncertainty omission
- contract-free claims
- hidden rejection caveats
- broad rhetoric from small external data
- overclaiming target specificity

## 19. Minimal result summary for internal iteration

If a full report is too heavy during development, a minimal result summary should still include:

- run ID
- contract IDs
- primary intervention axis
- primary metric per target
- clustered CI per target
- best honest baseline per target
- external holdout result per target
- leakage status
- rejection count
- one narrow claim sentence

Anything smaller than that is likely too easy to misread.

## 20. One-sentence summary

The Spatial-CI results template exists to force every result to carry its contracts, baselines, uncertainty, caveats, and claim boundaries alongside the metric.
