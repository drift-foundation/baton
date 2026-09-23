# Prepare the separate independent-review Job

## 2026-09-23 — parallel preparation selected by owner

Slawomir asks what follows W239528 and whether tuner can prepare it now to
reduce waiting. The selected sequence remains W239528 (one implementation,
proposal and cleanup), W239533 (a separate independent reviewer Job), then
W236087 (resume/correction). This preparation does not change those gates.

Tuner may prepare the operator recipe and input checklist for W239533 while
W239528 is under independent review. Preparation must distinguish verified
existing interfaces from pending inputs. The accepted proposal, custody fix,
candidate digests and exact execution selection are not presumed available.
Do not reuse a failed or consumed execution instance.

Deliver a concise recipe for preparation, preflight, bounded execution,
progress/log inspection, stop and cleanup evidence. Check command syntax and
required inputs against current source and accepted records. Identify exact
missing product support as findings rather than inventing commands or fixing
application code. Pending values must be explicit; the recipe must not appear
ready to run until its inputs and prerequisites are actually accepted.

File ownership: tuner owns new recipe/checklist files and PROGRESS.md only
inside this dossier. W239528, W239533, W236087 and product source are read-only
for this assignment. No live provider/container execution, deployment changes,
store mutations, Git mutations or acceptance of the implementation/reviewer
result. This is preparation, not the independent review itself.

Reference: baton:work/records/2026/09/finding-v12-independent-review-proof/
and baton:work/records/2026/09/finding-v12-single-implementation-proof/.
