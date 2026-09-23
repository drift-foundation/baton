# The one question this Job's live run would ask, and why a fake cannot answer it

Claim 239653, baton.claude, W239528. Required by the FINDING: "The later bounded
real-provider run asks whether the actual provider follows the adapter's
edit-only contract and its actual output passes collection through cleanup; a
fake cannot establish provider behavior. State that question and why
deterministic coverage cannot answer it."

Recording the question is not requesting the run. The owner selects it.

## The question

> **Does the production Claude CLI, given implementation-only requirements and
> an explicit instruction not to move HEAD, leave its change in the working
> tree -- so that the adapter authors the one commit, and the resulting
> proposal is collected, frozen, published and positively cleaned up?**

It has exactly two parts, and the second is not implied by the first:

1. **Behaviour.** Does the real model, in a real container, with a real
   repository under it, refrain from committing? W236087's run is the only live
   evidence there is, and it answers NO for a four-stage task document. Whether
   the corrected instructions change that is a fact about the model, not about
   this code.
2. **Collection.** If it does refrain, does the actual output -- a real diff,
   real verification output, a real recap -- pass `_identical`, the seal, the
   intake receipt, retention, publication, the checkpoint freeze and
   `authorize_cleanup`? The deterministic provider writes small, well-formed
   edits. A real one produces whatever it produces.

## Why the deterministic coverage cannot answer it

`test_baseline` drives the real `ClaudeAgent`, real version control, the real
ending driver and the manager's real cleanup journal. What it substitutes is
the provider subprocess. That substitution is exactly the thing in question:

* The fake edits files because the fixture told it to. It cannot be evidence
  about what a model chooses to do when it has a shell and an opinion.
* `TheProposalIsTheAdaptersOwnAccount::test_a_provider_that_commits_is_reported_and_never_settles`
  makes the fake commit, to prove the REFUSAL path is real and reported. That
  establishes that this run reports the failure; it establishes nothing about
  how often a real provider produces it.
* The engine seam means no container ever starts, so nothing here exercises the
  image, the credential, the network or the CLI's own behaviour under
  `--model`.

Per the standing v12 verification default (AGENTS.md, owner 2026-09-12), a live
provider run is reserved for a specific question that needs the real provider.
This is that question, stated so the owner can decide whether it is worth
asking now.

## What the live run would and would not establish

**Would**, on a settled outcome: that one real container, under one candidate
qualification grant, received implementation-only requirements; that the
retained proposal's commit is authored and committed by
`Baton worker <worker@baton.invalid>` with exactly the declared base as its
parent; that execution stopped; and that a positive `runtime.destroy` committed.

**Would not**: anything about review, correction or session resume -- those are
W239533's and W236087's runs. It would not certify a production context profile,
enable anything, or advance a deployment. One run is one sample of a
probabilistic system: a single success is not a rate.

**Would also not** re-answer W236087's outstanding items. The faulted attempt
from that run stays quiescent-with-cleanup-pending until an owner performs the
faulted-attempt recovery, and its grant stays spent. This packet selects a NEW
`run_id` for that reason.

## Preconditions the owner must hold before asking it

1. `OPERATOR-239528.md` step 5a: the Authority prepared for the participants
   this deployment configures. `baseline_bindings.preflight` answers the exact
   missing preparations and grants none of them.
2. A fresh `run_id`. The `managed-correction-236087` grant is consumed;
   `authorize_qualification_run` mints a new one for a new identity.
3. The bounded egress network the deployment provides. `none` is refused by the
   composer, because a worker that cannot reach the API cannot answer this.
4. Independent review of this packet, which is what W239528 is returning for.
