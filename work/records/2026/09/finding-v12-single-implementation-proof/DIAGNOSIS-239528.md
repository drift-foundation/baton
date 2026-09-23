# Why W236087's live implementation faulted, and why its cleanup stalled

Claim 239653, baton.claude, for W239528. The owner's Job description requires
this diagnosis to be accepted together with the baseline proof, and requires
"provider versus adapter Git ownership" to be explicit. Nothing here re-opens a
store, re-runs anything, cleans anything up or touches
`/home/sl/baton-runs/managed-correction-236087/run`.

The evidence was read under W236087 claims 239365 and 239485 and is preserved
in `../finding-v12-managed-session-resume/LIVE-RUN-239365.md` and
`live-239365/`. What is new here is the corroboration from the product's own
source and its own existing regression, and the statement of what this
baseline does about it.

## The run, from its own retained outcome

`outcome.json`, schema `baton.managed-correction-outcome/3`:

    state              held          stopped        exceptional
    admissions         implementation 1, review 0
    stage_states       implementation exceptional, review blocked
    served_seconds     46.3          cleanup_sweeps 59
    serving_failure    null          interruptions  []

One implementation runtime started. The stage went exceptional; the review
stage never left `blocked` and no review runtime was ever admitted.

## Finding A — the provider committed, and the adapter refused to adopt it

**Confirmed.** The worker's exchange events record `describe` answered and then
a terminal with `ending: "faulted"`, `fault_code: "agent"`, `disposition: null`
and `manifest_digest: null`.

The provider itself SUCCEEDED -- `subtype: success`, `is_error: false`,
`terminal_reason: completed`, 12 turns -- and returned a review verdict
("Verdict: **accept**"), describing all four stages of the workload performed
inside its single turn.

The retained line checkout says what it did on the way there. Read without
running any version-control command, `.../checkout/.git` holds:

    HEAD                 ref: refs/heads/proposal
    refs/heads/main      1790c2fea3d01bcacede93051702d1c9f06f13e2
    refs/heads/proposal  46d1af70d710476e261c3ae4475333a6df81254e
    reflog  1790c2fe -> 1790c2fe  node <node@14690a98be82.(none)>
                                  checkout: moving from 1790c2fe to proposal
            1790c2fe -> 1dfe0dd   sl  commit: Print ready from harness.py
            1dfe0dd  -> 46d1af7   sl  commit: Print READY from harness.py

`node@14690a98be82` is the runtime that attempt started. The provider created a
branch inside the container and authored BOTH commits under an identity that is
not the adapter's.

**The check that raised is `ClaudeAgent._unmoved`.** It runs after the provider
turn and before anything is measured or published, and it refuses when HEAD is
not the revision the turn was admitted at:

> "the private line's HEAD moved during the provider turn; this adapter authors
> exactly one commit per turn, and a history it did not write is not one it can
> give an account of"

HEAD moved from `1790c2fe` to `46d1af7`, so that is the refusal. The causal
chain is complete: a task document scripting four stages -> an agent that
performed all four and committed its own history -> `_unmoved` refused ->
terminal `faulted` with `fault_code: agent` -> stage exceptional -> the review
stage never admitted.

### The ownership boundary, stated exactly

**The provider EDITS and VERIFIES. The adapter COMMITS and PUBLISHES.**

`claude_agent._prompt` tells the implementation role it "is working in a private
copy of the source tree... Edit files here directly". `ClaudeAgent._commit` is
the single act that turns those edits into history, under
`user.name=Baton worker`, `user.email=worker@baton.invalid`, with a message this
module composes from the task id and nothing a child wrote. `_identical` then
proves the committed tree, restricted to candidate material, IS the measured
tree; `_claim` publishes `base`, `head`, `transport` and `recap` and nothing the
manager owns.

None of that is available for a history the adapter did not write, which is why
`_unmoved` refuses rather than adapting. **The product behaved correctly.** The
defect was the packet's task document, which was a four-stage script.

**This is not a hypothesis about the product.** The behaviour has an existing
deterministic regression in the product's own suite:
`v12/python/tests/manager/test_claude_agent.py::ThePreparedLineRefusesWhatItCannotAccountFor::test_a_provider_that_committed_refuses_rather_than_being_adopted`,
which drives a fake provider that commits and asserts the `HEAD moved` refusal.
That test predates this Work and was not edited by it.

### What this Job does about it

Two things, and both are in this dossier's own code rather than in prose.

1. `baseline_bindings.TASK_INSTRUCTIONS` states the requirement, says that
   judging is not this stage, and says who owns the commit -- naming the
   commands that move HEAD and saying plainly that committing your own work is
   how it gets thrown away. `test_baseline_bindings` asserts the instructions
   carry no stage script and do carry that paragraph.
2. `baseline._attributions` does not take the adapter's authorship on trust. It
   reads the commit object out of the manager's own durable line and requires
   author and committer to be `Baton worker <worker@baton.invalid>` and the
   parents to be exactly the declared base.
   `test_baseline.TheProposalIsTheAdaptersOwnAccount` proves the positive shape
   over a real commit, REPRODUCES this live failure through the same real code
   (a provider that commits, the real `_unmoved`, the run reported and not
   settled), and proves the check can fail on a well-formed answer carrying a
   foreign identity.

## Finding B — why 59 cleanup sweeps could not settle the runtime

**Confirmed from source and from the already-retained axis values.** No store
was re-opened for this record.

`attempt-b1d818b0...` holds runtime
`14690a98be8298b66d3c2b4f231a6f05f35958ae7a033af1788e4ca1d5be7a66` with
`execution_runtime: quiescent` and `cleanup: pending`; `cleanup_of` answers
`None`, so no `runtime.destroy` committed.

`intake.authorize_cleanup` reads the attempt's intake receipt FIRST and, finding
none, records `blocked-on-intake` without calling the adapter. An intake receipt
exists only after an ending has frozen and collected a result -- and this turn
ended `faulted` with `manifest_digest: null`, so there was nothing to freeze,
nothing to collect and no receipt to write.

**The retained axis discriminates the two possibilities.** It reads `pending`,
not `blocked-on-intake`. Had `authorize_cleanup` been called it would have
written the latter. `pending` means the act was never attempted, which is
consistent with an ending that stopped before intake.

So the sweeps were not failing to remove a container; they never reached the
act that removes one.

**This remains genuinely outstanding.** A container that stopped is not a
container that was removed, and that manager holds no positive absence for it.
Recovery is the deployment's own faulted-attempt path -- end the assignment at
the Authority, then authorize cleanup -- which is a manual owner act against the
prepared instance. This Job does not perform it, reruns nothing, and makes no
claim that the runtime is gone.

## Finding C — the qualification grant is spent

`qualification_grant_of` still answers the grant for
`managed-correction-236087`, and `_grant_consumer` names context
`context-f9c2e0ef94794b91a99f743f86557cd5ee2b63b9d19349d669d811c077c84e58` --
the opening admission that run performed. Consumption commits inside that
admission, which is what makes it exactly-once.

A candidate profile executes only under its own one-run grant, so a relaunch
under the same `run_id` is not a replay. **W239528's operator packet therefore
selects a NEW `run_id`**, and `authorize_qualification_run` mints a new grant
for it. Nothing here mints one; `baseline.prepare` does, inside the owner's own
selected command.

## Operational finding carried forward

`ControlStore.open_readonly` on that prepared instance refused with
`OperationalError`. The W236087 assessment used the ordinary write-capable
`ControlStore.open`, which succeeded and recorded an incarnation. That was a
write-capable fallback used after a non-writing one refused, and the record says
so. The read-only opener's refusal is still reported and uninvestigated, and is
outside this Job's scope.
