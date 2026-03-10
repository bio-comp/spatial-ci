# Spatial-CI Claims

This document defines the kinds of claims Spatial-CI is designed to support, the claims it is not designed to support, and the standards required before a claim should be stated.

The purpose of this file is to stop the most common failure mode in ambitious technical projects:

> saying something much bigger than the artifacts actually justify.

Spatial-CI is not only a modeling system.
It is a **claim-disciplining system**.

---

## 1. Claim philosophy

A claim is not just a sentence in a README or presentation.
A claim is the meaning implied by the experiment.

Examples:
- “morphology predicts hypoxia signal”
- “spatial context improves performance”
- “the model generalizes externally”
- “this target is morphologically learnable”

Spatial-CI exists to make those claims explicit enough that they can be:
- supported
- weakened
- rejected
- revised

A good benchmark does not merely produce results.
It constrains what can honestly be said about them.

---

## 2. What kinds of claims Spatial-CI can support

Spatial-CI is designed to support claims of the following kinds.

### 2.1 Target-specific predictive claims
Example:
> Under frozen target, scoring, alignment, and split contracts, H&E morphology predicts `HALLMARK_HYPOXIA` better than the strongest honest baseline on held-out breast Visium data.

### 2.2 Intervention claims
Example:
> Adding a declared spatial-context mechanism improves external-holdout performance relative to a simpler pooled-embedding model under otherwise unchanged contracts.

### 2.3 Baseline-relative claims
Example:
> A learned head provides signal beyond kNN and ridge on frozen embeddings for `HALLMARK_G2M_CHECKPOINT`.

### 2.4 Transportability stress-test claims
Example:
> Performance degrades on same-assay external cohorts, but remains above the strongest simple deployable baseline.

### 2.5 Benchmark integrity claims
Example:
> The result was produced under patient-level split discipline, explicit artifact provenance, and clustered uncertainty rather than iid spot assumptions.

These are the kinds of claims Spatial-CI is built to support.

---

## 3. What kinds of claims Spatial-CI is not built to support

Spatial-CI does **not** support the following claims in v1.

### 3.1 Clinical deployment claims
Examples:
- “this is ready for clinical use”
- “this is a digital pathology diagnostic tool”
- “this can replace pathology sign-out”

### 3.2 Regulatory claims
Examples:
- “this is FDA-ready”
- “this is validated as a medical device”
- “this meets clinical-grade validation standards”

### 3.3 Replacement claims
Examples:
- “morphology replaces spatial transcriptomics”
- “wet-lab assays are unnecessary”

### 3.4 Broad universality claims
Examples:
- “this generalizes across all cancers”
- “this will work on all assays”
- “this is a universal pathology omics translator”

### 3.5 Isoform/splicing claims in v1
Examples:
- “this captures intron retention spatially”
- “this is an isoform-aware pathology benchmark”
- “this recovers APA structure from morphology”

Those may become future branches, but are not supported in the current design.

---

## 4. Minimal requirements for making a claim

A serious Spatial-CI claim requires all of the following:

1. a frozen target definition
2. a frozen scoring contract
3. a frozen alignment contract
4. a frozen split contract
5. a frozen baseline contract
6. a frozen bootstrap contract
7. an explicit input manifest
8. an explicit run config
9. an evaluation certificate
10. no unresolved leakage

If any of these are missing, the claim should be weakened or withheld.

---

## 5. Claim strength levels

Spatial-CI encourages claims to be phrased at different strengths depending on evidence.

### 5.1 Weak exploratory claim
Example:
> There may be morphology-linked signal for this target in the discovery setting.

Use when:
- evidence is early
- external holdout is weak or absent
- uncertainty is broad
- baselines are not fully established

### 5.2 Moderate benchmark claim
Example:
> Under frozen contracts, the model outperforms the strongest simple deployable baseline on this target and retains some signal on the external same-assay holdout.

Use when:
- baselines are honest
- uncertainty is reasonable
- external holdout exists
- contract stack is intact

### 5.3 Strong benchmark claim
Example:
> Under frozen contracts and explicit provenance, morphology carries stable, externally stress-tested signal for this target program beyond simple baselines.

Use only when:
- baseline comparisons are solid
- external holdout behavior is credible
- uncertainty is honest
- slide/patient summaries do not hide catastrophic failures

### 5.4 Unsupported overclaim
Examples:
- “this proves morphology can replace ST”
- “this is clinically deployable”
- “this solves virtual spatial transcriptomics”

Spatial-CI explicitly rejects this style of claim inflation.

---

## 6. Claim templates Spatial-CI encourages

These templates are intentionally narrow and disciplined.

### 6.1 Target learnability claim
> Under `<target_definition_id>`, `<scoring_contract_id>`, `<alignment_contract_id>`, and `<split_contract_id>`, morphology predicts `<program_name>` with performance above `<baseline_name>` and clustered uncertainty `<ci_summary>`.

### 6.2 Intervention claim
> Changing `<intervention_axis>` from `<variant_a>` to `<variant_b>` improved/degraded `<program_name>` performance under otherwise fixed contracts.

### 6.3 External holdout claim
> Relative to internal validation, `<program_name>` showed `<degree_of_change>` on `<external_cohort>` while remaining above/below `<baseline_name>`.

### 6.4 Negative claim
> Under the current frozen contracts, there is insufficient evidence that morphology predicts `<program_name>` beyond simple baselines.

Negative claims are fully legitimate outputs in Spatial-CI.

---

## 7. Why negative claims matter

A core design belief in Spatial-CI is:

> a benchmark that cannot truthfully report failure is not scientifically trustworthy.

Examples of valid negative conclusions:
- target not learnable enough from morphology under current setup
- external transportability collapses
- complex model adds nothing beyond ridge on embeddings
- uncertainty overlaps baseline performance
- one program is much weaker than expected

These are not embarrassing outcomes.
They are part of the scientific value of the platform.

---

## 8. Claim dependence on contracts

Every meaningful claim in Spatial-CI is conditional on the contract stack.

That means a claim is never just:
> “the model works”

It is always closer to:
> “the model works under these target, scoring, alignment, split, baseline, and bootstrap assumptions”

This is a feature, not a weakness.
It prevents vague generalization.

---

## 9. Claim dependence on external holdout scale

External same-assay holdouts in v1 are stress tests, not universal guarantees.

So claims about external performance should be phrased carefully.

Allowed style:
- “external same-assay stress test”
- “retains signal on held-out external cohort”
- “degrades but remains above baseline”

Not allowed style:
- “broadly generalizes”
- “ready for deployment”
- “validated across pathology settings”

Small external sets must not carry giant rhetorical weight.

---

## 10. Claim dependence on target semantics

A claim can only be as precise as the target definition permits.

Example:
If the target is `HALLMARK_EPITHELIAL_MESENCHYMAL_TRANSITION`, the supported claim is about an **EMT/mesenchymal program**.

The following claim is too strong:
> the model predicts fibroblast activation state

The target semantics do not justify that specificity.

This is why truth in advertising is mandatory.

---

## 11. Claim dependence on baseline strength

A claim that ignores strong simple baselines is weak.

If ridge on embeddings or kNN is already doing well, then:
- a complex model may still be useful
- but the claim must be framed as incremental, not revolutionary

Spatial-CI therefore treats baseline-relative claims as more meaningful than absolute claims alone.

---

## 12. Claim dependence on uncertainty

A claim must weaken when uncertainty is large.

Examples:
- if the clustered CI overlaps strong baseline performance, the claim of superiority is weak
- if worst-decile slide performance is catastrophic, the average claim must be weakened
- if external holdout variance is extreme, transportability claims must be softened

Spatial-CI does not allow certainty language when the uncertainty artifacts do not support it.

---

## 13. Claim dependence on rejections and missingness

Claims should weaken if:
- many samples were rejected
- missingness filtering removed many target instances
- external cohorts suffered disproportionate attrition
- fallback identity resolution dominates the manifest

This is because the result may now represent only a cleaner subset of the intended benchmark universe.

The rejection ledger is therefore part of claim interpretation.

---

## 14. Claim audit questions

Before stating a claim, ask:

1. Which contracts does this claim depend on?
2. Which artifacts support it?
3. Which baseline is the real comparator?
4. Does clustered uncertainty support the phrasing?
5. Does external behavior support the phrasing?
6. Does target semantics support the biological language?
7. Were there major rejections or weak fallback IDs?
8. Is the claim stronger than the benchmark actually supports?

If the answer to the last question is yes, rewrite the claim.

---

## 15. Examples of acceptable claims

### Example 1
> Under frozen breast Visium contracts, a ridge probe on frozen pathology embeddings predicts `HALLMARK_G2M_CHECKPOINT` above global mean and train-cohort mean baselines, with stable clustered uncertainty and non-catastrophic external degradation.

### Example 2
> A simple learned head improves internal and external performance on `HALLMARK_HYPOXIA` relative to kNN and ridge under otherwise unchanged contracts.

### Example 3
> Under the current v1 setup, `HALLMARK_EPITHELIAL_MESENCHYMAL_TRANSITION` remains harder to predict than `HALLMARK_G2M_CHECKPOINT`, suggesting weaker or noisier morphology-linked signal under the current target definition.

These are scoped, contract-aware, and interpretable.

---

## 16. Examples of unacceptable claims

### Example 1
> Spatial-CI proves pathology images can replace spatial transcriptomics.

Too broad. Not supported.

### Example 2
> Our model generalizes across pathology.

Far too broad. v1 does not support this.

### Example 3
> The model recovers stromal state.

Too specific if the target is actually EMT/mesenchymal.

### Example 4
> This approach is deployable.

Not supported by the benchmark design.

### Example 5
> Context modeling works.

Too vague. Works on which target, under which contracts, against which baseline, with what external behavior?

---

## 17. Claims as project outputs

Spatial-CI should treat carefully written claims as a legitimate output artifact.

This means:
- claims may appear in reports
- claims may appear in evaluation summaries
- claims may appear in technical memos
- but they should always remain traceable to certificates and contracts

A claim without artifact traceability is just rhetoric.

---

## 18. Relationship between claims and roadmap

Different roadmap phases support different claim strength.

Examples:

### Early phases
Allowed:
- “manifest is leakage-resistant”
- “scores are reproducible”
- “baselines can be evaluated honestly”

### Mid phases
Allowed:
- “simple learned heads beat certain baselines on specific targets”

### Later phases
Allowed:
- “certain intervention axes improve external stress-test behavior under frozen contracts”

What you are allowed to say should grow only as the evidence stack grows.

---

## 19. Final claim discipline rule

If a claim cannot be written in the form:

> Under these contracts, on these artifacts, against these baselines, with this uncertainty, we observed this result

then it is probably too vague for Spatial-CI.

That sentence structure is the project’s moral center.

---

## 20. One-sentence summary

Spatial-CI claims are intentionally narrow, artifact-backed statements about what the benchmark actually supports, not a license for broad hype about pathology AI or virtual spatial transcriptomics.
