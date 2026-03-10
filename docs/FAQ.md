# Spatial-CI FAQ

This document answers common questions about Spatial-CI.

The goal is not marketing polish.
The goal is to make the project legible to someone who wants to understand what it is doing and why.

---

## 1. What is Spatial-CI?

Spatial-CI is a contract-driven, leakage-resistant, decision-grade research platform for evaluating **morphology-to-expression** claims in **virtual spatial transcriptomics** and **multimodal pathology AI**.

It is not just a model repo.
It is a system for deciding whether a result deserves belief.

---

## 2. What does “CI” mean here?

It refers to the broader **Circuit-CI** lineage of thought:
- contracts
- explicit assumptions
- evidence gates
- certificates
- reproducible evaluation

Spatial-CI is a domain-specific instantiation of that philosophy.

---

## 3. Is this a clinical pathology product?

No.

Spatial-CI is **not**:
- a diagnostic tool
- a pathology sign-out system
- a medical device
- an FDA-ready package

It is a research platform.

---

## 4. What is the main task in v1?

The v1 task is:

> predict fixed, per-spot biological program scores from H&E morphology in breast cancer standard Visium data

The key words are:
- fixed
- per-spot
- program-level
- breast
- standard Visium

That narrowness is intentional.

---

## 5. Why not predict the whole transcriptome?

Because that would make the first benchmark broader, noisier, and harder to interpret.

Spatial-CI v1 prioritizes:
- interpretable program-level targets
- reproducible evaluation
- tractable scope
- transportability-aware benchmarking

Whole-transcriptome prediction may be interesting later, but it is not the right first target for a disciplined platform.

---

## 6. Why use Hallmark programs?

Because they are:
- standardized
- public
- easier to defend than ad hoc signatures
- biologically interpretable enough for a first benchmark

The point is not that Hallmark is perfect.
The point is that it is a strong enough, explicit source to reduce arbitrary target drift.

---

## 7. Why those three target programs?

The v1 targets are:

- `HALLMARK_HYPOXIA`
- `HALLMARK_G2M_CHECKPOINT`
- `HALLMARK_EPITHELIAL_MESENCHYMAL_TRANSITION`

They were chosen because they are:
- biologically meaningful
- plausibly linked to tissue morphology
- narrow enough for a serious first benchmark

They are also not equally easy, which is useful.

---

## 8. Why not call EMT “stromal”?

Because that would overstate the specificity of the target.

`HALLMARK_EPITHELIAL_MESENCHYMAL_TRANSITION` is best described as an EMT/mesenchymal-like program.
It may reflect stromal influence, but it is not equivalent to a pure stromal or CAF-state label.

Spatial-CI insists on this kind of semantic discipline.

---

## 9. Why single-sample scoring?

Because Spatial-CI wants target scores that depend as little as possible on the rest of the cohort.

If the target score changes because the dataset composition changes, the benchmark target drifts.

Single-sample rank-based scoring is a better fit for frozen target contracts than more cohort-dependent score constructions.

---

## 10. Why not use standard scanpy scoring for v1?

Because for the main frozen target layer, Spatial-CI prefers a scoring method that more clearly depends only on the current spot’s expression vector.

This is a design choice about benchmark stability, not a claim that scanpy-based scoring is bad in general.

---

## 11. What does “spot-plus-context” mean?

It means the image crop is larger than the Visium spot itself.

In v1:
- crop size: `224 px`
- resolution: `0.5 µm/px`

That covers about `112 µm`, while a Visium spot is roughly `55 µm` in diameter.

So the model sees:
- the spot
- plus surrounding neighborhood context

Spatial-CI calls this what it is rather than pretending it is exact-spot-only.

---

## 12. Why not exact-spot extraction by default?

Because the chosen v1 crop geometry does not honestly support that language, and exact-spot masking introduces another layer of assumptions that are better treated as a later intervention axis.

The default should be the honest simpler statement:
- spot plus context

---

## 13. Why is the split done at the patient level?

Because splitting related samples from the same patient across train and validation/test can make the model look better than it really is.

Patient-level splitting is the default biological exclusion unit in v1.

Specimen and slide overlaps are still audited separately.

---

## 14. Why not use one whole cohort as validation?

Because if you tune repeatedly on one whole cohort, you risk learning that cohort’s style and calling it generalization.

Spatial-CI instead prefers:
- pooled discovery cohorts
- patient-level deterministic train/val split within them
- separate external holdout cohorts

This gives a more honest validation design.

---

## 15. Why are leakage checks such a big deal here?

Because leakage is one of the easiest ways to get persuasive but false results.

In this setting, leakage can happen through:
- patient overlap
- specimen overlap
- slide overlap
- poor fallback identity logic
- ambiguous metadata

A beautiful result with leakage is not a beautiful result.

---

## 16. Why is the manifest so important?

Because the manifest is what connects the benchmark to real physical artifacts.

Without a strong manifest, you cannot reliably tell:
- what samples entered the benchmark
- what split they belong to
- how identity was resolved
- what files back each sample
- whether raw and derived molecular files are being confused

The manifest is part of the science, not just pipeline plumbing.

---

## 17. Why is there a rejection ledger?

To prevent silent attrition.

If some of the hardest or messiest samples quietly disappear, the benchmark can look cleaner and more transportable than it really is.

The rejection ledger forces that missingness into the open.

---

## 18. Why separate raw and derived expression files?

Because they are not the same scientific object.

A raw 10x output and a project-derived `.h5ad` may both be useful, but they play different roles in provenance and interpretation.

Conflating them is a provenance error.

---

## 19. Why are baselines so central?

Because if you cannot beat honest simple baselines, then a complicated model may not be teaching you much.

Spatial-CI wants complexity to be earned.

That means:
- strong baselines first
- simple learned models next
- more complex models only if justified

---

## 20. What are the baseline families in v1?

At minimum:

- global train mean
- mean by train cohort
- kNN on embeddings
- ridge probe

These are the main honest comparators.

Oracle analyses may exist, but must be clearly separated.

---

## 21. Why use Spearman as the primary metric?

Because the targets are program-like scalar scores where monotonic relationships matter and strict linearity is not always the most useful assumption.

Spearman is not the whole story, but it is a good primary v1 metric.

---

## 22. Why not bootstrap spots iid?

Because Visium spots are not independent.

They share:
- spatial structure
- slide-level context
- patient-level biology

Bootstrapping spots iid creates falsely narrow confidence intervals.

Spatial-CI uses clustered uncertainty instead.

---

## 23. Why does every run need an intervention axis?

To prevent experiment soup.

If everything changes at once, it becomes hard to interpret why the result changed.

Declaring a primary intervention axis forces the run to say:
- what changed
- what was supposed to be learned from the change

---

## 24. What is an evaluation certificate?

It is the formal artifact that says what happened in a run under the frozen contract stack.

It summarizes:
- the run identity
- the contract IDs
- the metrics
- the uncertainty
- the baseline comparisons
- the leakage status

It is the main “does this deserve belief?” object in the system.

---

## 25. Is Spatial-CI trying to prove morphology can replace spatial transcriptomics?

No.

It is trying to test whether morphology contains enough stable signal for certain fixed targets to justify deeper work.

That is a very different and much narrower claim.

---

## 26. Is Spatial-CI about splicing, isoforms, or APA?

Not in v1.

Those are important future directions, especially given the limits of common spatial assays for transcript-structure resolution, but v1 is about gene-program-level targets.

If Spatial-CI grows into isoform-aware work, that should happen through new target and scoring contracts, not by silently stretching v1.

---

## 27. Why is the project so obsessed with wording?

Because wording often drifts before code does.

Bad wording can make a target sound more specific, a result sound more general, or a benchmark sound more mature than the artifacts justify.

Spatial-CI uses wording discipline as a scientific safeguard, not just a style preference.

---

## 28. Is this too much structure for a research project?

That depends on what kind of project you want.

If the goal is:
- quick exploration
- flashy demos
- loose prototypes

then yes, Spatial-CI is too structured.

If the goal is:
- a benchmark you can trust
- explicit assumptions
- auditable claims
- reproducible decisions

then this structure is the point.

---

## 29. Can Spatial-CI still produce interesting negative results?

Yes. It should.

A negative result like:
- weak morphology-linked signal
- no improvement over ridge
- external collapse
- one target being much harder than expected

is scientifically useful and fully compatible with the design.

---

## 30. What would make Spatial-CI successful?

Not just a high score.

Spatial-CI is successful if it can honestly answer:
- what signal is present
- what signal is absent
- what is robust
- what is brittle
- what deserves deeper work
- what does not

That is a much more valuable outcome than a flattering benchmark headline.

---

## 31. One-sentence summary

Spatial-CI is a deliberately narrow, contract-driven system for making morphology-to-expression claims in spatial pathology explicit enough to test honestly rather than merely present attractively.
