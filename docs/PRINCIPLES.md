# Spatial-CI Principles

This document defines the core principles that govern Spatial-CI.

Principles are different from:
- contracts
- configs
- implementation details
- roadmap phases

A contract can change versions.
A config can change values.
A roadmap can change priorities.

A principle is a deeper rule about how the system should think.

These principles are what make Spatial-CI *Spatial-CI* rather than just another pathology-ML repository.

---

## 1. Why principles matter

Without explicit principles, a project slowly becomes whatever is easiest in the moment.

That usually means:
- more convenience
- less rigor
- more impressive models
- weaker provenance
- nicer plots
- softer language around uncertainty
- more hidden assumptions

Spatial-CI exists to push in the opposite direction.

The principles below are not decorative.
They are meant to constrain design, implementation, and claims.

---

## 2. Principle: explicitness over convenience

If a choice could materially affect interpretation, it should be made explicit.

Examples:
- target definition
- scoring method
- split logic
- alignment policy
- baseline semantics
- bootstrap semantics
- provenance resolution

Convenience is not a sufficient excuse for implicit behavior.

If the pipeline “just does something” important without naming it, that is a bug in the design.

---

## 3. Principle: truth in advertising

Spatial-CI must describe targets, experiments, and conclusions no more strongly than the artifacts justify.

Examples:
- call EMT-like signal EMT-like signal
- do not call same-assay external stress testing “universal generalization”
- do not call a research platform “deployable”
- do not call a proxy label direct biological truth

If the rhetoric and the contracts disagree, the rhetoric must lose.

---

## 4. Principle: provenance is part of the science

Data engineering is not separate from scientific validity.

A result that cannot be traced back to:
- a manifest
- hashes
- contracts
- score artifacts
- run configs

is not just inconvenient.
It is scientifically weaker.

Provenance is not bureaucracy.
It is one of the things that makes the benchmark real.

---

## 5. Principle: targets are scientific objects, not preprocessing side effects

Target generation is not just a data-cleaning step.

A target embodies:
- biological meaning
- scoring assumptions
- missingness policy
- interpretation boundaries

If target construction changes, the task changes.

Spatial-CI therefore treats target definitions and scoring contracts as first-class scientific artifacts.

---

## 6. Principle: the benchmark must be harder to fool than the model is to tune

A central goal of Spatial-CI is to make it difficult to obtain flattering results through weak process.

That means the benchmark should defend against:
- leakage
- target drift
- weak baselines
- silent attrition
- fake certainty
- vague claims

A powerful model on a weak benchmark is less interesting than a simple model on a strong benchmark.

---

## 7. Principle: no silent attrition

Samples must not disappear quietly.

If a sample is excluded, rejected, or unresolvable, that fact should become an artifact.

Silent attrition is dangerous because it can:
- clean up the hardest cases
- shrink external holdouts
- inflate transportability
- hide pipeline brittleness

Spatial-CI prefers an annoying rejection ledger over a flattering silence.

---

## 8. Principle: baselines are moral objects

Baselines are not box-checking exercises.

They define what “better than simple” actually means.

A project that avoids strong honest baselines is usually trying to protect a flattering story.

Spatial-CI requires baselines strong enough to make complex models earn their existence.

---

## 9. Principle: negative results are not failures of the project

A result like:
- ridge beats the MLP
- the external holdout collapses
- one target is not morphologically learnable enough
- uncertainty is too wide for strong conclusions

is not a project failure.

It is a successful execution of the project’s purpose:
to determine what deserves belief.

Spatial-CI is not optimized to always look good.
It is optimized to be able to say no honestly.

---

## 10. Principle: uncertainty must respect structure

Spatial-CI rejects fake precision.

Visium spots are not iid.
Slides are not iid in the same way spots are.
Patients are not interchangeable noise sources.

If the uncertainty method ignores the biological and technical dependence structure, the confidence intervals are misleading.

Cluster-aware uncertainty is not an optional flourish.
It is part of the honesty standard.

---

## 11. Principle: one intervention at a time when possible

Clean experiments are better than crowded experiments.

A result is more interpretable when:
- target is fixed
- split is fixed
- baseline stack is fixed
- scoring is fixed
- one primary axis changes

This does not mean complex experiments are forbidden.
It means clean comparisons are privileged.

Spatial-CI prefers interpretable progress over theatrical complexity.

---

## 12. Principle: complexity must be earned

A graph model, fancy context model, or larger architecture is not intrinsically more interesting than:
- a good baseline
- a linear probe
- a ridge model
- a simpler head with clean evaluation

Complexity becomes interesting only when:
- the baseline stack is honest
- the evaluation stack is trustworthy
- the new complexity answers a real question
- the result survives external stress

Spatial-CI is not anti-model.
It is anti-unearned complexity.

---

## 13. Principle: external holdouts are for stress, not comfort

The external holdout is not there to decorate the paper.
It is there to challenge the result.

That means:
- do not tune on it
- do not narratively overfit to it
- do not overclaim from it
- do not quietly prune it through missing data without explicit records

A good external holdout is a source of discomfort.
That is its value.

---

## 14. Principle: contracts before claims

Claims should emerge from:
- contracts
- manifests
- score artifacts
- evaluation certificates

—not from intuition alone.

If a claim cannot be grounded in a visible chain of artifacts and frozen assumptions, it should be weakened.

Spatial-CI is a claim-disciplining system as much as it is a benchmark system.

---

## 15. Principle: docs must constrain code, not trail behind it

Documentation in Spatial-CI is not meant to be aspirational fluff.

The docs should:
- constrain implementation
- make drift visible
- define the meaning of artifacts
- preserve the rationale of the system

If the code changes and the docs do not, one of them is lying.

---

## 16. Principle: narrowness is strength in early versions

Spatial-CI v1 is intentionally narrow:
- one disease family
- one assay family
- one extraction mode
- a few targets
- same-assay external holdout

This is not timidity.
It is discipline.

A narrow benchmark that tells the truth is more valuable than a sprawling benchmark that flatters itself.

---

## 17. Principle: every strong statement should survive a hostile reread

A useful test for Spatial-CI language is:

> Would this sentence still sound fair if read by a skeptical reviewer?

If the answer is no, the statement is probably too strong.

This principle should apply to:
- docs
- READMEs
- experiment notes
- result summaries
- talks
- manuscripts

---

## 18. Principle: contracts can evolve, but not invisibly

Spatial-CI is not frozen forever.

Targets may change.
Scorers may improve.
Split logic may get refined.
Future assays may be added.

But every meaningful change should happen through:
- a new version
- a new identifier
- an explicit rationale

Invisible evolution is just drift.

---

## 19. Principle: the benchmark should make self-deception harder

This is the deepest principle in the project.

The point is not to eliminate all error.
That is impossible.

The point is to design the system so that common forms of self-deception become:
- more visible
- more annoying
- harder to rationalize

That includes:
- flattering baselines
- quiet exclusions
- target mutation
- external-test peeking
- rhetorical inflation
- uncertainty laundering

Spatial-CI should increase the cost of fooling yourself.

---

## 20. Principle: the result is not the metric, the result is the evidence state

A run does not “result in a number.”
It results in an evidence state.

That evidence state includes:
- the metric
- the uncertainty
- the baselines
- the target semantics
- the external holdout behavior
- the leakage status
- the manifest integrity
- the rejection ledger
- the intervention axis

Spatial-CI cares about the whole evidence state, not just the headline value.

---

## 21. Principle: respect the assay

Spatial-CI should not pretend the data are more informative than the assay can support.

That means respecting:
- Visium spot geometry
- assay chemistry limitations
- image-resolution constraints
- target granularity
- spatial versus molecular ambiguity

When the assay imposes a limit, the project should acknowledge the limit rather than write around it.

---

## 22. Principle: the benchmark is allowed to say “not enough”

A mature benchmark must be able to conclude:
- not enough signal
- not enough stability
- not enough transportability
- not enough evidence to escalate complexity
- not enough support for the claim

Spatial-CI is allowed to stop at “not enough.”
That is a strength, not a failure.

---

## 23. One-sentence summary

Spatial-CI is governed by principles that prefer explicitness, provenance, honest baselines, structured uncertainty, and contract-bounded claims over convenience, hype, and model theater.
