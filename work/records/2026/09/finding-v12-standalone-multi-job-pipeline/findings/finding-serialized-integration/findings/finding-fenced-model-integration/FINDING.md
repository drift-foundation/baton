# Execute one fenced model-driven integration

Ledger Work: W101492

Parent: `work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-serialized-integration/`

## Confirmed scope

Compose the accepted candidate-admission and generic-runtime leaves into the
first ordinary target integration. The coordinator grants one live fenced
attempt; the generic runtime gives that attempt exclusive writable target
access; and the model follows the supplied Work instructions to preflight,
import and verify the candidate. For Baton's repository those instructions use
ordinary Git tools. Baton does not provide or require a VCS-aware adapter.

K owns this shared cross-component assembly. The first slice proves the clean
happy path and bounded pre-mutation refusal. It does not stage or commit Git,
make policy decisions, repair a candidate, or automatically recover an
interrupted attempt.

## Acceptance boundary

- Only the smallest eligible entry for a target receives the live lease and
  writable target access; independent targets remain concurrent.
- The runtime revalidates its exact live grant before target mutation and a
  stale or competing runtime cannot write.
- The model performs the Work-described whole-candidate preflight before its
  first target change and publishes durable progress, result and verification.
- A clean, quiescent success records an integrated coordinator settlement;
  ordinary preflight refusal changes no target bytes.
- Final Git index and history ownership remains with Slawomir.

## 2026-09-06 — revalidation, and the assembly decided

Both blockers closed, so this leaf revalidates what it composes rather than
what the plan remembered about them.

**The runtime boundary already proves more than this plan assumed.**
`runtime.compose_assignment` reads the live grant, the accepted entry and the
grant it follows from ONE coordinator relationship pass, refuses an attempt or
a profile kind that is not the grant's, and refuses a predecessor the manager
has not observed stopped. So the "live-grant-to-exclusive-target-access seam"
this plan's item 2 names is not something to build here: it exists, and this
leaf's job is to call it and to decide what happens to the answer.

**The admission leaf owns every member of the account.** `admit_candidate`
re-reads the checkpoint, the writer's assignment and frozen output, the
Authority proposal and its three receipts, and the owning Job before it
enqueues. This leaf therefore never composes an account and never re-proves
one; it starts from a queued entry.

**What is genuinely this leaf's, and it is the decision the runtime boundary
deliberately deferred: WHICH COORDINATOR VERB A CLAIM EARNS.**
`runtime.observed_result` adopts what the model wrote, in the coordinator's own
three terminal words, and settles nothing. Choosing between
`settle_integrated`, `refuse_entry` and `block_target` is a decision about the
world, and it belongs where the whole attempt is visible.

## 2026-09-06 — the four rulings this assembly is built on

**THE MODEL IS AN INJECTED CAPABILITY, NEVER AN ARGV HERE.** The deployment
supplies a runtime port whose contract is one verb and whose answer is typed.
This module composes the delivery, hands the port a proved assignment, and
reads the durable files back; it never learns what the model ran, and for
Baton's repository the model uses ordinary Git tools under its Work
instructions. `AGENT_ADAPTER` is the shape this follows.

**A CLAIM IS SETTLED ONLY BEHIND TWO PROOFS, AND THE SECOND ONE IS NEW HERE.**
The live grant is re-read immediately before settlement, which is the ruling's
second cutpoint. And the runtime that wrote the claim must be observed
QUIESCENT first: a model still running is a model that can still write the
target, and settling behind it would record a result about a tree that is
still moving. The manager's `execution_runtime` axis answers that, through the
same reader the runtime boundary uses for a predecessor.

**AN UNANSWERED ATTEMPT IS NOT A FAILED ONE.** `waiting` is reported and
nothing is settled. Under the owner ruling of 2026-09-06 an interruption
surfaces for an operator; this leaf composes no recovery, retries nothing, and
leaves the grant exactly where it was. W101493 owns what happens next.

**A REFUSAL BEFORE MUTATION IS THE ENTRY'S, NOT THE TARGET'S.** The targeted
review of 2026-09-05 already ruled the split: an ordinary policy, scope or
target failure found before any mutation terminally refuses that immutable
entry and the queue moves on, while an integrity or ambiguous-custody failure
is a statement about the TARGET. So a model answering `refused` reaches
`refuse_entry` and a model answering `held` -- or material this manager cannot
read -- reaches `block_target`. This leaf chooses the verb; it does not invent
a fourth outcome.

## 2026-09-06 — the review's two safety corrections, and the rules they leave

`review-2026-09-06T14-35-14Z.md` accepted the coordinator verb mapping and
found two [P0]s and one [P1]. All three are corrected.

**ADMISSION IS A PROOF ABOUT A MOMENT, AND EXECUTION IS A DIFFERENT MOMENT.**
Every member of the account was proved from its accepted producer when the
entry received its rank -- and an entry waits. Authority may advance the
canonical target, or a producer may cease to agree, while it sits in the queue.
This assembly gave a stale entry writable access and could settle it.

The correction re-runs ADMISSION'S OWN RESOLUTION under the live grant and
before the model is asked. `admit_candidate` is now `resolved_account` plus
`enqueue`, so the second proof is the same function rather than a second
reading of the same sources -- which is the difference between a check and a
copy that drifts. The selectors come out of the stored entry, never from a
caller, and every member of the fresh answer must equal the member the entry
was admitted with. A difference is ordinary STALENESS: this candidate is not
integrated now, refused before any delivery is made or any target byte is
reachable.

**A WRITER ALREADY OBSERVED STOPPED IS NOT A WRITER.** The quiescence proof
before settlement was real and could be satisfied by an observation made BEFORE
the model ran, because nothing bound the port to the manager's lifecycle for
that attempt. The reviewer found it in the fixture -- which recorded
`destroyed` and then invoked the writer -- and was right that the fixture could
only demonstrate it because the code permitted it.

So the attempt must NOT already be quiescent when the port is asked, and must
BE quiescent before its claim settles. The rule generalizes past this seam: A
POSITIVE OBSERVATION IS ABOUT AN INSTANT, AND A PROOF THAT DOES NOT SAY WHICH
INSTANT PROVES NOTHING. The pair of checks is what pins the observation to the
interval that matters.

**AND A TEST THAT NEVER TOUCHES THE TARGET CANNOT PROVE ANYTHING ABOUT IT.**
The suite's model wrote only `result.json`, so a "clean import" marked an entry
integrated and released its lease when no candidate byte had moved:
`imported_paths` was prose in an untrusted claim. The port now performs a
bounded transformation against a disposable target, every case snapshots bytes
and modes, and refusal, stale evidence and malformed output are each proved to
change neither.

One thing that correction made explicit rather than fixed, and it is recorded
because it is a real boundary: THIS SEAM CANNOT TELL whether the model imported
what it claims. The coordinator records the runtime's account, and proving that
account against the target is the verification the model performs under its own
Work instructions -- which is why the settlement's `verification` member is the
model's and core invents none. A deployment wanting an independent check adds
it to the profile's instructions, not to this module. A case states that
plainly rather than leaving the gap to be discovered.

## 2026-09-06 — the re-review: two cutpoints, one start state, one ruled verb

`review-2026-09-06T15-03-04Z.md` accepted the execution-time re-resolution and
found two [P0]s and two [P1]s. All four are corrected, and three of them are
rules rather than fixes.

**TWO GRANT CUTPOINTS ANSWER TWO RACES.** The grant was proved when the
assignment was composed and again after the model answered, and the gap between
them held a cross-store producer proof. The reviewer ended and abandoned the
lease from inside that proof and watched the port write anyway. So the grant is
re-read immediately before the port receives writable work as well: one check
for "did it end while I was proving", one for "did it end while the model ran".
Neither substitutes for the other, and a proof that takes time needs a cutpoint
at BOTH of its edges.

**A WRITER INTERVAL NEEDS A START, NOT JUST AN END.** Refusing only `quiescent`
and `destroyed` before asking the port let five states through, and none of
them says no runtime is writing: `start-requested` and `running` have one,
`cancel-requested` and `stopping` are taking one down, and `uncertain` is the
state the manager's own table will not let become `destroyed` because nobody
looked successfully. `not-started` is the ONE state this assembly asks a port
in. That also makes `materialize_delivery`'s contract realizable rather than
nominal -- the fixed namespaces exist before the runtime that will mount them,
because there is no runtime yet.

The general form: A POSITIVE OBSERVATION BOUNDS AN INTERVAL ONLY IF BOTH OF ITS
EDGES ARE OBSERVED. "Not terminal before, terminal after" bounds nothing.

**AN ORDINARY STALENESS HAS A VERB, AND THIS RECORD ALREADY RULED IT.** The
execution-time re-resolution raised, leaving the entry `leased` behind a live
lease -- fail-closed, and turning an ordinary stale candidate into manual
recovery while rank two waited. The targeted review of 2026-09-05 had already
ruled the disposition: an ordinary policy, scope or target failure found before
mutation terminally refuses THAT entry and the queue moves on, while an
integrity or ambiguous-custody account is a statement about the target. The
split is made on the coordinator's OWN refusal category, so the two branches
cannot drift from the vocabulary that defines them.

A real operational consequence, recorded because it is not obvious: an attempt
recorded for an integration that refuses before starting still has to be
RECONCILED by the manager. The next grant's predecessor is that attempt, and
`target_access` proves a predecessor stopped; an attempt whose port was never
asked has no runtime, and saying so is the manager's own
`not-started -> destroyed` transition. This assembly does not perform it --
that is the deployment's reconciliation -- but a deployment that omits it wedges
the target's next grant.

**AND A VERIFICATION THE MODEL DID NOT DERIVE IS NOT EVIDENCE.** The fake's
verification was a constant, so the case checked the target independently while
the recorded account said nothing about it. The model now reads back the bytes
and mode it wrote, the persisted verification is compared with those exact
facts, and every imported path's mode is asserted against one an importer
ESTABLISHED rather than one an ambient umask left. The core limitation is
unchanged and still stated: this is the model's account, and core invents no
verification of its own.
