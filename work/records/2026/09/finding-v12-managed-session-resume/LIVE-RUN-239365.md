# The first live managed correction: what happened, from its own records

Claim 239365, baton.claude. Recorded BEFORE any implementation, as owner
reroute 239355 requires. Every fact below is read out of the run's own retained
evidence or out of the manager's own readers. Nothing in
`/home/sl/baton-runs/managed-correction-236087/run` was modified, and no
cleanup, rerun or destructive act was performed.

Preserved copies of the evidence are in `live-239365/` beside this file:
`outcome.json`, `PACKET.json`, `task.json`, the implementation attempt's four
exchange events and both provider logs.

## What the run did

`outcome.json` (schema `baton.managed-correction-outcome/3`, claim 238827):

    state              held
    stopped            exceptional
    admissions         implementation 1, review 0
    stage_states       implementation exceptional, review blocked
    served_seconds     46.3
    cleanup_sweeps     59
    serving_failure    null          interruptions  []
    final_canonical_read  true       unexpected_attempts  []

One implementation runtime started. The stage went exceptional; the review
stage never left `blocked` and no review runtime was ever admitted.

## Finding 1 — the implementation agent reviewed its own work

**This is the defect, and it is mine.** The worker's exchange events record
`describe` answered and then:

    events/terminal.json   ending "faulted", fault_code "agent",
                           disposition null, manifest_digest null

The provider itself succeeded — `subtype: success`, `is_error: false`,
`terminal_reason: completed`, 12 turns, session
`c9204611-82a0-5e41-b24c-7444c08ea541`. What it returned was a **review
verdict**:

> Verdict: **accept** … Checked against `ACCEPTANCE.md` … Run sequence:
> **Implementation** … **First review** … **Correction** … **Final review** —
> accepted; no second correction request, so the one-run selection closes
> cleanly.

The implementation agent performed all four stages of the workload by itself
inside one provider turn, including both reviews, and answered with a verdict.

**The exact check that raised is now established** (claim 239485, from the
retained line checkout, read without running any version-control command).
`run/workspaces/.baton-review-lines/line-e56cb73b.../checkout/.git` holds:

    HEAD                 ref: refs/heads/proposal
    refs/heads/main      1790c2fea3d01bcacede93051702d1c9f06f13e2
    refs/heads/proposal  46d1af70d710476e261c3ae4475333a6df81254e
    reflog  1790c2fe -> 1790c2fe  node <node@14690a98be82.(none)>
                                  checkout: moving from 1790c2fe to proposal
            1790c2fe -> 1dfe0dd   sl  commit: Print ready from harness.py
            1dfe0dd  -> 46d1af7   sl  commit: Print READY from harness.py

The provider created a `proposal` branch inside the container -- `node@14690a98be82`
is the runtime `14690a98...` this attempt started -- and authored BOTH commits
itself. Its prose claim of `1dfe0dd` and `46d1af7` is corroborated by the
reflog. `harness.py` in that worktree is `print('READY')\n`.

`ClaudeAgent._unmoved(candidate, entry)` runs after the provider turn and
raises `TaskRefusal` when HEAD is not the revision the turn was admitted at:
"this adapter authors exactly one commit per turn, and a history it did not
write is not one it can give an account of". HEAD moved from `1790c2fe` to
`46d1af7`, so that is the check that raised. **The adapter owns the commit and
the publication; the provider owns the edit.** Nothing was published: the
terminal carries no manifest.

So the causal chain is established end to end -- scripted four-stage task ->
agent performed all four and committed its own history -> `_unmoved` refused ->
terminal `faulted` with `fault_code: agent` -> stage exceptional -> review never
admitted. The earlier wording in this record called the fault a consequence of
"publishing no proposal", which described the outcome rather than the check;
that is superseded by this paragraph.

**Cause.** `task["instructions"]` is not a script; it is the REQUIREMENTS. The
worker composes two different prompts from the same string and says so in as
many words: `claude_agent._prompt` gives the implementation role "…you are
working in a private copy of the source tree… Edit files here directly", while
`claude_agent._review_prompt` gives the review role "The change was made to
satisfy these requirements: …Assess whether the change meets them", under a
docstring that states "THE INSTRUCTIONS ARE PRESENTED AS REQUIREMENTS TO
ASSESS, not as work to do. This is the difference between a reviewer and a
second implementer."

Under claim 238310 I wrote `packet_bindings.TASK_INSTRUCTIONS` as four labelled
stages — IMPLEMENTATION, FIRST REVIEW, CORRECTION, FINAL REVIEW — including the
exact finding the first review was to return and the criteria the final review
was to accept on. Handed to the implementation role as work to do, the agent
did all of it. The product separated the roles correctly; the packet's task
document put both roles' instructions into the one string the implementation
role executes.

It also follows that the review role would have been handed the same four-stage
script as "requirements to assess", which is not a requirement at all.

## Finding 2 — a projection attempt identity was reported as a started runtime

`outcome.json` lists two `admitted_attempts`. Asked about them directly:

    implementation  attempt-b1d818b0…  runtime 14690a98…,
                                       execution_runtime "quiescent",
                                       cleanup "pending"
    review          attempt-d215cc8f…  attempt_runtime_of → None
                                       cleanup_of → refuses: no runtime attempt

The review identity has **no attempt row at all**. It is an episode identity
the status projection carries for a stage that never started anything, and this
run's admission gate never launched it — the gate records every `launch` before
delegating, so its absence there is a positive fact about this run.

`supervise` merges projection identities into `admitted` and then requires a
positive committed `runtime.destroy` for each. For an attempt no runtime was
ever allocated for, that record cannot exist, so the run reported three
held-reasons about a runtime that was never started — noise that obscures the
one real failure and makes every run of this shape unsettleable.

**This is not licence to treat absence as quiescence.** The correction
distinguishes three states and names each, rather than collapsing them.

## Finding 3 — the implementation runtime is quiescent and NOT cleaned up

`attempt-b1d818b0…` holds runtime `14690a98be8298b66d3c2b4f231a6f05f35958ae7a033af1788e4ca1d5be7a66`
with `execution_runtime: quiescent` and `cleanup: pending`; `cleanup_of`
answers `None`, so no `runtime.destroy` committed. Fifty-nine cleanup sweeps
did not settle it.

The supervisor reported this correctly and held. It remains **genuinely
outstanding**: a container that stopped is not a container that was removed,
and this manager holds no positive absence for it.

**Why 59 sweeps could not settle it** (claim 239485, from source and the
already-retained axis values; no store was re-opened). `intake.authorize_cleanup`
reads the attempt's intake receipt FIRST and, finding none, records
`blocked-on-intake` without calling the adapter. An intake receipt exists only
after the ending has frozen and collected a result -- and this turn ended
`faulted` with `manifest_digest: null`, so there was nothing to freeze, nothing
to collect and no receipt to write. The ordinary ending therefore never reached
`authorize_cleanup` at all.

The retained axis discriminates the two possibilities: the cleanup axis reads
`pending`, not `blocked-on-intake`. Had `authorize_cleanup` been called it would
have written the latter. `pending` means the act was never attempted, which is
consistent with an ending that stopped before intake.

What recovery remains is therefore the deployment's own faulted-attempt path --
end the assignment at the Authority, then authorize cleanup so the runtime can
be positively excluded. That is a manual owner act against the prepared
instance. This correction does not perform it, reruns nothing, and makes no
claim that the runtime is gone.

## Finding 4 — the qualification grant is spent

`qualification_grant_of` still answers the grant for `managed-correction-236087`
and `_grant_consumer` names context
`context-f9c2e0ef94794b91a99f743f86557cd5ee2b63b9d19349d669d811c077c84e58` --
the opening admission this run performed. Consumption commits inside that
admission, which is what makes it exactly-once.

A candidate profile executes only under its own one-run grant, so a relaunch
under the same `run_id` is not a replay. Minting a new grant under a new
`run_id` for the unchanged profile is the documented path and is an owner
decision; nothing here does it.

## Operational finding — the prepared control store refuses a read-only open

Review 2026-09-22T14:05:58Z recorded that `ControlStore.open_readonly` on this
instance refused with `OperationalError`. The assessment above used the
ordinary `ControlStore.open` with its own incarnation, which succeeded.

**That was a write-capable fallback and this record now says so plainly.** The
earlier wording here said "not worked around", which was wrong: a write-capable
opener used after a non-writing one refused IS a workaround, and it records an
incarnation. Claim 239485 opened no store: every fact added under it comes from
retained files and from reading the product's own source. The read-only
opener's refusal remains reported and uninvestigated, outside this scope.

## Scope selected under this claim

1. Make the packet's task document state REQUIREMENTS only, and tell the
   implementation role explicitly that reviewing is not its stage.
2. Classify attempts by what this run actually started, and stop demanding a
   destroy record for a runtime that was never allocated — without asserting
   quiescence for anything.
3. Focused deterministic regressions for both.
4. Refresh candidate and packet provenance; return for independent review.

Not in scope, and not done: any live rerun, any cleanup of the outstanding
runtime, production enabling, and Work closure.
