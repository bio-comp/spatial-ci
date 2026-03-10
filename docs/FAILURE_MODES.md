# Spatial-CI Failure Modes

This document records the main ways Spatial-CI can fail.

The purpose of this file is not pessimism for its own sake.
It is to make failure modes explicit enough that the project can defend against them.

A system designed for honest benchmarking should know not only what success looks like, but how it can quietly go wrong.

---

## 1. Why a failure-modes document exists

Many research systems fail in subtle ways before they fail in obvious ways.

Examples:
- the model trains
- the metrics look fine
- the plots are clean
- but the benchmark is quietly wrong

Spatial-CI is particularly vulnerable to this because it touches:
- pathology
- spatial omics
- metadata engineering
- image pipelines
- target construction
- evaluation logic

This document exists to keep those risks visible.

---

## 2. Top-level failure categories

Spatial-CI can fail in at least seven broad ways:

1. scientific target failure
2. alignment failure
3. split/leakage failure
4. provenance failure
5. baseline/evaluation failure
6. experiment-design failure
7. rhetorical/claim failure

Each category contains multiple specific failure modes.

---

## 3. Scientific target failures

## 3.1 Target drift
The biological target changes without a version change.

Examples:
- changing the scorer
- dropping genes
- relabeling EMT as stromal
- silently modifying the source set

Why it matters:
the benchmark is no longer evaluating the same task.

## 3.2 Overclaiming target specificity
The target is described more specifically than the source set justifies.

Example:
- claiming fibroblast activation when the target is actually EMT/mesenchymal-like signal

Why it matters:
the biological interpretation becomes stronger than the evidence.

## 3.3 Choosing targets that are not plausibly morphology-linked
The project chooses targets that have little realistic visible footprint in tissue architecture, then interprets weak results as model failure rather than task mismatch.

Why it matters:
the benchmark becomes unfair or scientifically confused.

## 3.4 Score instability masquerading as biology
The score construction is too unstable, too cohort-dependent, or too implementation-sensitive.

Why it matters:
the labels themselves become noisy enough to distort the entire benchmark.

---

## 4. Alignment failures

## 4.1 Pretending spot-plus-context is exact-spot
The crop contains context, but the project talks as if it is exact-spot-only.

Why it matters:
the scientific claim about what signal is being learned becomes false.

## 4.2 Missing or wrong scalefactor usage
The project uses coordinates without correct scale metadata or misapplies scaling assumptions.

Why it matters:
spot-to-pixel correspondence becomes physically unreliable.

## 4.3 Mixing incompatible image sources
Different cohorts or runs use different image sources without explicit declaration:
- original TIFF vs. downsampled PNG
- different resolution assumptions
- inconsistent preprocessing

Why it matters:
the visual task shifts while pretending to stay constant.

## 4.4 Undeclared stain or image normalization drift
Image normalization changes between runs without becoming a declared intervention axis.

Why it matters:
the model comparison is no longer clean.

---

## 5. Split and leakage failures

## 5.1 Patient leakage
Related samples from the same patient end up in multiple splits.

Why it matters:
the model can appear to generalize by memorizing patient-specific structure.

## 5.2 Specimen or slide leakage
Even if patient IDs are clean, specimen or slide overlap can still contaminate the split.

Why it matters:
the holdout is not truly independent.

## 5.3 False separation from bad fallback IDs
Missing patient IDs are naively replaced with sample IDs, allowing related samples to look artificially distinct.

Why it matters:
the benchmark silently leaks while appearing clean.

## 5.4 False overlap from un-namespaced IDs
Generic specimen or slide IDs collide across cohorts.

Why it matters:
the audit becomes noisy or misleading, and real signal is obscured.

## 5.5 Validation becomes cohort tuning
A whole discovery cohort is treated as validation, and the system slowly tunes itself to that cohort’s style.

Why it matters:
internal “generalization” becomes disguised batch memorization.

---

## 6. Provenance failures

## 6.1 Silent attrition
Samples fail resolution or validation and disappear without a rejection record.

Why it matters:
the benchmark may end up evaluating only the easiest subset of the intended dataset.

## 6.2 Raw and derived artifact conflation
A derived `.h5ad` or processed matrix is treated as if it were the raw assay object.

Why it matters:
the provenance chain becomes scientifically ambiguous.

## 6.3 Broken or incomplete manifests
The manifest omits:
- patient ID source
- alignment-supporting files
- file hashes
- explicit split membership

Why it matters:
the benchmark can no longer be audited reliably.

## 6.4 Filesystem-layout assumptions masquerading as truth
The resolver assumes a path convention that happens to work locally but is not actually part of the contract.

Why it matters:
reproducibility and transportability of the pipeline collapse.

## 6.5 Untracked artifact mutation
Artifacts are overwritten or regenerated under the same name after their scientific meaning has changed.

Why it matters:
reproducibility becomes an illusion.

---

## 7. Baseline and evaluation failures

## 7.1 Weak baselines make the model look smarter than it is
The benchmark compares the model only to trivial baselines and avoids the strongest honest simple alternatives.

Why it matters:
performance claims become inflated.

## 7.2 Oracle baselines are passed off as fair
A baseline secretly uses test-label information but is presented as a legitimate comparator.

Why it matters:
evaluation becomes conceptually dishonest.

## 7.3 iid spot bootstrap produces fake confidence
Visium spots are resampled independently, creating artificially tight uncertainty intervals.

Why it matters:
confidence claims become overstated.

## 7.4 Aggregate metrics hide catastrophic subsets
A decent overall score masks terrible performance on some slides or cohorts.

Why it matters:
the benchmark overstates robustness.

## 7.5 External holdout is too small to support the rhetoric
A small external set is used to justify broad generalization language.

Why it matters:
transportability claims become larger than the evidence.

## 7.6 Score artifact drift across runs
Different runs recompute targets differently while claiming to evaluate the same target.

Why it matters:
the benchmark stops having a stable label object.

---

## 8. Experiment-design failures

## 8.1 Experiment soup
Multiple major factors change at once without explicit declaration.

Why it matters:
results become uninterpretable.

## 8.2 Hidden intervention axes
A run claims to be about model architecture but also changes:
- alignment
- scoring
- target definition
- preprocessing
- split logic

Why it matters:
the causal interpretation of improvement is false.

## 8.3 External test peeking
The external holdout influences model selection, target choices, preprocessing, or narrative shaping.

Why it matters:
the stress test becomes part of the fitting process.

## 8.4 Complexity without earned necessity
The project moves to fancy context models or graph layers before proving that simple baselines and simple heads are insufficient.

Why it matters:
the code gets more impressive while the science gets less clear.

## 8.5 Notebooks become the hidden source of truth
Important logic lives only in ad hoc notebooks.

Why it matters:
the project becomes irreproducible and silently mutable.

---

## 9. Claim and rhetoric failures

## 9.1 Saying “deployable” when the artifacts support only research claims
Why it matters:
it confuses benchmark rigor with product readiness.

## 9.2 Saying “generalizes” when the evidence is only same-assay external stress testing
Why it matters:
it inflates the scope of the result.

## 9.3 Saying “captures stromal biology” when the target is just EMT-like signal
Why it matters:
the language outruns the contract.

## 9.4 Saying “morphology replaces spatial transcriptomics”
Why it matters:
the project is not designed to support that claim.

## 9.5 Hiding negative results
Only successful targets or successful runs are discussed.

Why it matters:
the benchmark becomes a curation exercise instead of a scientific system.

---

## 10. Infrastructure failures

## 10.1 Environment drift
Dependencies change without a corresponding lockfile or contract update.

Why it matters:
reruns are no longer comparable.

## 10.2 Platform-specific breakage hidden in base assumptions
Linux/GPU-only packages are treated as universal dependencies.

Why it matters:
the setup becomes brittle and the system looks reproducible when it is not.

## 10.3 Unpinned target-scoring implementation
The scorer is installed from a moving branch or vague version tag.

Why it matters:
target values can drift silently over time.

---

## 11. Social / process failures

## 11.1 The project becomes reputation-seeking instead of truth-seeking
Decisions start optimizing for:
- impressive demos
- flashy plots
- portfolio optics
- quick publishability

rather than benchmark honesty.

Why it matters:
Spatial-CI loses its identity.

## 11.2 Critique is treated as attack rather than signal
If design criticism is resisted because it is inconvenient, hidden failure modes persist.

Why it matters:
the project will slowly accumulate comforting falsehoods.

## 11.3 The docs stop matching the code
Contracts and docs drift while the code changes underneath.

Why it matters:
the project becomes persuasive in prose and unreliable in practice.

---

## 12. Most dangerous failure modes

If forced to prioritize, the most dangerous failures are:

1. patient leakage hidden by fallback identity logic
2. silent sample attrition in the external holdout
3. target drift under score-generation changes
4. oracle or weak baselines inflating model claims
5. iid uncertainty estimates creating fake confidence
6. rhetorical overclaiming from small external results
7. experiment soup that hides what actually changed

These should be watched constantly.

---

## 13. Failure modes that can still produce pretty results

Some of the most dangerous failures still produce:
- high scores
- clean figures
- persuasive demos

Examples:
- leakage
- silent attrition
- target drift
- weak baselines
- tiny external holdouts with strong rhetoric

This is why “the result looks good” is one of the least useful safety checks.

---

## 14. Failure detection strategies

Spatial-CI defends against failure by forcing:

- explicit contracts
- manifest/rejection artifacts
- leakage audits
- frozen scoring
- baseline contracts
- clustered uncertainty
- external holdout discipline
- honest non-goals
- explicit claim templates

Each of these is a defense against a specific failure mode.

---

## 15. When to halt the pipeline

The system should halt, not warn, when encountering at least:

- fatal leakage
- missing required canonical metadata
- missing required artifacts for an assigned sample
- manifest validation failure under strict mode
- contract mismatch between expected and observed artifacts

These are not recoverable “soft issues” for a benchmark run.

---

## 16. When to weaken claims instead of halting

Some failures do not require halting, but do require softer interpretation.

Examples:
- large rejection ledger under `--allow-missing`
- wide clustered CIs
- strong external degradation
- target with weak morphology plausibility
- fallback identity resolution dominating the cohort

These should reduce claim strength even if the pipeline technically completes.

---

## 17. What success looks like in relation to failure modes

Spatial-CI succeeds when:
- the main failure modes are visible
- failures can be detected early
- failures do not get buried
- negative outcomes remain publishable internally
- the benchmark can say “this does not hold up” without collapsing socially

That is much more valuable than a project that can only report flattering outcomes.

---

## 18. One-sentence summary

Spatial-CI failure modes are the specific ways the benchmark can become scientifically flattering but wrong, and the system is designed to make those modes visible before they become claims.
