# The real continuation input, and the selection it needs

Prepared by baton.claude under claim 250376, answering owner reroute 250274:
*"Prepare bounded separate resume proof using actual retained
context/provenance and actual executable deterministic path. W239533 verdict
was accepted: do not fabricate changes-requested; establish real continuation
input and identify any additional selection needed."*

**Nothing was started, no deployed store was written, no runtime was reached.**
Both retained stores were opened through the public `open_readonly`
constructors and every product module that answered came from the pinned
snapshot `/home/sl/baton-runs/independent-review-247947/manager-source`
(`resume_state.py` prints each module's `__file__` and SHA256;
`not_from_snapshot` is empty).

## The answer, stated first

**Half of the continuation input exists and is in good order; the other half
does not exist and cannot be made to exist on this subject.** That is not a
defect in either prerequisite — it is what an honest acceptance costs — and the
additional selection this Job needs is a **new subject**, not a repair.

| What a managed resume needs | On the retained subject |
| --- | --- |
| A finalized provider context to resume | **PRESENT.** `context-8f2855c6…`, use `context-use-1b3648d3…`, generation 0, status `ready`, revision 3 |
| A frozen checkpoint the correction would revise | **PRESENT.** `checkpoint-ab8207ba…`, `frozen`, revision 1 |
| A verdict of `changes-requested` | **ABSENT.** The line's verdict is `accepted` |
| A line in `correction-ready` | **ABSENT.** The line is `accepted` |
| An owner-committed correction operation | **ABSENT.** `operation_record` answers `None` |

## What was read, and from where

Subject, as W239533's own `ATTRIBUTION-248565.json` records it: v12 Authority
`7ea319da93384b77bc3ddea38602d7a3`, Work `7ea319da-W1`, control store
`/home/sl/baton-runs/single-implementation-244216/db/control.sqlite3`.
`RESUME-STATE-250376.json` is the full read; `test_resume_state.py` asserts it
in 10 checks so it fails when it stops being true.

  * **The line is `accepted`** at revision 1, current checkpoint
    `checkpoint-ab8207ba…`. Read through `review_cycles.line_of`.
  * **The accepted verdict is the line's own integration eligibility.**
    `integration_checkpoint` refuses unless the line is `accepted` and the
    eligibility row names a verdict with matching digests; it answers
    `verdict-82578027…`, and `verdict_of` — which proves the row against its
    committed act — reports `disposition: accepted`.
  * **The producer's provider context is ready to resume.**
    `context_use_of(attempt-4842e704…)` reports generation 0, status `ready`,
    reason `None`. That status is not cosmetic: the same reader answers `held`
    with `generation-damaged` when the retained generation no longer
    validates. The container was destroyed and cleanup recorded `retained`;
    the context survived both.
  * **No agent-session rows exist** for the producer attempt
    (`sessions.agent_sessions_of` answers `[]`). The resume mechanism here is
    the provider CONTEXT, not the session axis — a distinction `sessions.py`
    opens by insisting the two are different vocabularies.
  * **No correction operation exists** for the frozen checkpoint. Asked by
    derived identity — `episodes.correction_operation_id(job_id, checkpoint)`
    — rather than by scanning for something that looks like one.
  * **The product refuses to build a restore prompt here**, in its own words:
    `correction_feedback_of` answers `provider context: serving feedback
    belongs to a restore invocation`, because the producer's only context use
    is generation 0, which is an `open` invocation.

## Why the subject cannot be corrected, in product terms

Three gates, each cited against the pinned snapshot rather than paraphrased:

1. `review_cycles.record_verdict` maps dispositions to line states
   `{"accepted": "accepted", "changes-requested": "correction-ready",
   "rejected": "rejected"}`. **`changes-requested` is the only disposition
   that produces `correction-ready`**, and `grant_writer` admits a correction
   writer from `idle` or `correction-ready` alone.
2. `review_cycles.attach_review` refuses unless `line["state"] ==
   "review-ready"`. The line is `accepted`, so **no second review can attach
   to it** — the door to a different verdict on this proposal is shut by the
   first one having been recorded.
3. `provider_context.correction_feedback_of` holds the opening verdict's
   `disposition` to `changes-requested` **and** the retained report's own
   `verdict` member to the same string, both read from frozen custody. So even
   with a restore invocation admitted, an acceptance could not serve it
   however it were presented.

## The acceptance was a judgement, not an artefact of the criteria

This matters, because if the review packet had steered the reviewer toward
accepting, the answer would be to fix the packet rather than to select a new
subject. It did not. The executed criteria
(`/home/sl/baton-runs/independent-review-248377/run/task.json`) say in terms:
*"Every one of the three is a valid review result. `changes-requested` and
`rejected` are not failures of your stage and there is no outcome here that is
better for you than another one."* The reviewer read a change that met its
stated requirement and said so.

## A pinned product seam that is no longer needed

PLAN.md pins a product change on `v12/worker/claude_agent.py` as unavoidable
for stage-specific requirements, reasoned from one Job carrying one
digest-sealed input manifest so both roles necessarily read the same task
string. **The owner's split retires it.** W239533's review Job carried its own
task document — review criteria the implementation Job never saw — and that
document is retained and readable. Separate Jobs already deliver different
requirements to the two roles; it was the combined-Job shape that needed a
seam. `test_resume_state.py` asserts this against the executed criteria so the
retirement is checked rather than argued.

**No product byte has been changed under this claim, and none is proposed.**

## The selection this Job needs

A resume proof needs a subject whose review honestly asks for a correction. The
honest difficulty is that **no packet can guarantee its own precondition**: a
real reviewer judging real bytes may accept them, exactly as this one did.
Three options, with what each costs:

1. **A new implementation + review pair, and a packet that reports either
   outcome honestly.** The implementation Job states a requirement; the review
   Job judges it under neutral criteria; if the verdict is
   `changes-requested`, the correction Job restores the producer's context and
   makes the correction; if it is `accepted`, the run records that no
   correction was required and holds rather than manufacturing one. This is
   the only option that keeps every verdict honest, and its cost is that a
   selected live run may end with nothing to resume.
2. **A requirement with a verifiable acceptance criterion the first turn is
   unlikely to satisfy** — for example a requirement whose verification
   command exercises a case the instructions do not spell out. The reviewer
   still judges freely and the verdict is still the provider's; what changes
   is the prior probability, not the honesty. Cost: it is engineering the odds,
   and the packet should say so rather than presenting the correction as
   incidental.
3. **Wait for a correction to arise from other selected work.** Cost: this Job
   stays open on somebody else's schedule.

**My recommendation is option 1 with option 2's criteria design named openly in
the packet** — a real requirement with a real verification command, neutral
review criteria, and an outcome document that treats `accepted` as a valid end
state for the run and not a failure of it.

## What else the selection must carry

  * **A fresh run identity.** The old qualification grant for
    `managed-correction-236087` is consumed; a relaunch under the same
    `run_id` is not a replay. This is a preserved fact from the failed run,
    not a new one.
  * **The retained subject stays untouched.** Its line is integration-eligible
    and its context is intact; nothing here proposes reopening, recovering or
    cleaning it.
  * **A bounded correction Job** that admits exactly one restore invocation,
    stops, and records positive cleanup — the same shape W239528 and W239533
    were accepted in, not a combined run.

## What remains unproved after this claim

That the production CLI restores a real conversation. The deterministic
evidence in this dossier drives the open → restore sequence through the real
manager, real review cycles, real verdicts and the real provider-context
readers, with the provider subprocess as its one seam. **The seam is exactly
the question a live run would answer**, and it is the reason this Job exists.
Nothing here claims otherwise.
