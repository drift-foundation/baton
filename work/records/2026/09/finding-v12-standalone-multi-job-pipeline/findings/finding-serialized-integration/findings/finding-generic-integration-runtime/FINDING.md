# Establish the generic integration runtime boundary

Ledger Work: W101490

Parent: `work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-serialized-integration/`

## Confirmed scope

Compose the accepted target-global coordinator with one generic managed
integration runtime. The profile selects the agent/image, mounts, capabilities,
instructions, target access, durable exchange paths and generic result
contract. Neither the profile contract nor the coordinator parses Git or
requires a VCS adapter; a model uses ordinary Git only when its Work
instructions call for it.

K owns this shared boundary, including its public interfaces, documents,
schemas, exports and integration with existing Worker Manager lifecycle
primitives. Communication is restart-independent and file-based; manager or
container standard streams are observability only, never the authoritative
exchange. This leaf does not implement candidate admission, mutate a target,
record Authority completion or automate interrupted recovery.

## Acceptance boundary

- One fixed integration participant/profile can be launched for an exact
  target, queue entry, attempt and fence.
- The runtime receives only generic inputs, instructions and mount locations;
  no core document names commits, refs, branches, trees or merges.
- Ready/refusal, progress, result and quiescence are durable manager-custodied
  files with closed schemas and atomic publication.
- Writable target access is unavailable without the coordinator's currently
  live grant and the prior runtime is proved unable to mutate before another
  writer may start.
- Restart or ambiguous runtime state produces an inspectable hold for later
  operator action; this leaf performs no automatic recovery.

## 2026-09-06 — revalidation before implementation

The pinned decisions this leaf inherits were re-read against the tree rather
than against their prose, and three of them are STRONGER or narrower than this
record assumed. Recorded here because the implementation reaches for them.

**The durable file exchange already exists and is generic.**
`worker_manager/exchange.py` (W81857) is one attempt's whole production control
path: a `command/` namespace the manager writes and the container mounts
read-only, an `events/` namespace the container writes and the manager reads as
untrusted input, closed schemas for the receipt, per-operation state and one
terminal document, atomic five-step publication, and an `observation()` that
reports unreadable worker material as an observation rather than raising. It is
attempt-scoped and names nothing about version control.

So this leaf mints NO second exchange, and the acceptance clause "durable
manager-custodied files with closed schemas and atomic publication" is
satisfied by composing that one rather than by writing another. A second
transport would be a second thing to keep restart-correct and a second place
for a worker's claim to be mistaken for a settlement.

**The manager's runtime primitives are the lifecycle.** `launch.py` delivers
one versioned read-only document, `workspaces.py` and `source_boundary.py`
compose the mounts, `attempts.py` owns the runtime axes and their transitions,
and `output.py` owns the freeze. `job_manager/delegation.py` states the rule
this leaf follows: THERE IS NO SECOND STATE MACHINE. What is added is when to
compose these and what the composition must prove — not a parallel account of
runtimes.

**Agent quiescence is not runtime quiescence, and the tree says so louder than
this record did.** `sessions.satisfies_runtime_quiescence_gate` always answers
false by construction: a finished conversation is not evidence that the runtime
holding the generation is gone. The only positive answers live on the runtime
axes in `attempts.TRANSITIONS["execution_runtime"]`, where `uncertain` may
never become `destroyed` because destruction is a fact about the world. This
leaf's "the prior runtime is proved unable to mutate" therefore reads that
axis's vocabulary and accepts only its positive states — it does not spell a
second quiescence rule, and it does not accept a session fact for a runtime
claim.

**The VCS-neutral separation already has a working shape.** `source_profiles/`
is a separate package precisely so `worker_manager` stays Git-agnostic, it
imports nothing from the manager, and `tests/manager/test_dependencies` holds
the manager to a vocabulary in which none of its words appear. That is the
pattern this boundary follows rather than a new invention: the generic contract
lives here, any Git-shaped plan lives outside it, and a NAME GATE over this
module's own documents is what keeps it that way.

## 2026-09-06 — the boundary, decided

**One assignment document, composed only from a proved live grant.**
`baton.v12.integration-assignment/1` binds the exact target, entry, lease,
fence, attempt and integrator participant, plus the profile's closed kind,
version and instructions digest and the access this runtime was composed with.
It is authored by this module over its own member tuple rather than copied from
a caller's mapping, for `launch_document`'s reason: a caller supplies values,
never a document shape.

**Target access is decided here and is not an operand.** `writable` requires
BOTH the coordinator's currently live grant, proved through
`integration.queue.live_grant` at the moment of composition, AND a positive
prior-runtime observation from the manager's own execution-runtime vocabulary.
Absent either, composition refuses; there is no read-only fallback that quietly
starts a runtime with less than it asked for, because a runtime that cannot
write the target cannot perform the integration it was launched for and should
be refused rather than launched to fail.

**The runtime's result is a claim, never a settlement.**
`baton.v12.integration-result/1` is adopted as untrusted input with the same
three outcomes the coordinator settles with — `integrated`, `refused`, `held` —
so that a later leaf can carry a claim to `settle_integrated`, `refuse_entry`
or `block_target` without translating a vocabulary. Adopting it here does not
settle anything, and this leaf calls none of those three verbs.

**Ambiguity produces a hold account and nothing else.**
`baton.v12.integration-hold/1` is a closed account whose members are exactly
what `block_target` takes as its reason and detail. Under the owner ruling of
2026-09-06 an interruption or an inconsistent runtime state is surfaced for an
operator, never retried, accepted, completed, cleaned up, released, discarded
or reassigned — so this module produces the account and does not act on it.
`observed()` classifies and refuses to recover.

**What this leaf deliberately does not do:** admit a candidate, mutate a
target, run any version-control operation, record an Authority receipt, or
reconcile an interrupted integration. Those are the sibling leaves', and the
boundary is written so each of them composes rather than widens it.

## 2026-09-06 — clarification: a third DELIVERY, and the earlier sentence it narrows

The revalidation above says this leaf "mints NO second exchange", and that
sentence was written before the acceptance clause about durable files had been
carried out. It is narrowed here rather than left to be read as more than it
is, because both halves are true and a reader needs to know which is which.

WHAT STANDS: no second exchange MECHANISM and no second state machine. Every
rule the integration delivery uses is `worker_manager/exchange.py`'s -- the
same five-step atomic publication, the same directory modes and the reasons
for them, the same no-follow bounded regular-file read proved on the
descriptor, and the same split between an INTEGRITY refusal, where this build
and its own state disagree, and an UNTRUSTED one, where the least trusted
program in the deployment wrote outside its contract.

WHAT IS NARROWED: this leaf DOES materialize its own two namespaces, and
`exchange.py`'s own argument for being a third delivery is the argument for
this being a fourth. Its `command/` and `events/` namespaces carry one
attempt's OPERATION SEQUENCE -- `describe` then `work` -- and an integration
assignment is not one of those two operations, so publishing it there would
either widen another record's closed vocabulary or smuggle a document through
a member that means something else. `inputs` is frozen before the runtime
starts and closed over W19784's protocol pair, so an assignment cannot join it
without changing that record's contract. Anything under `workspace` is
reachable through the runtime's own writable mount, so an assignment placed
there could be replaced by the very program it is addressed to.

The delivery is therefore `integration/assignment/` -- manager-written,
world-readable, mounted read-only at a fixed target -- and
`integration/result/` -- created in the deployment's configured workspace
group and written by the runtime, read here as untrusted input.

AND UNREADABLE RUNTIME MATERIAL IS AN OBSERVATION THAT ARRIVES AS A HOLD.
`exchange.observation` reports it rather than raising, because a manager that
raised would let the least trusted program in the deployment stop the sweep for
every other stage. The same material here also means an integration nobody may
settle, so the observation IS the account `block_target` takes: a link at the
fixed name, material wider than the bound, bytes that do not decode, a result
outside the contract, a result answering another integration, and an assignment
replaced underneath the observation each produce a closed hold and nothing
else. `waiting` is deliberately not rounded into one -- an integration with no
result yet may still be running, and only positive evidence about the runtime
turns that into anything, which is the prior-runtime witness's job.

## 2026-09-06 — the workspace group coupling, recorded rather than worked around

`materialize_delivery` requires a `WorkspaceGroup`, which refuses to be
constructed: only the manager's own record of what the deployment configured
mints one, because a type any caller can build is a group any caller chose.
That makes this leaf's own tests open a `ControlStore` to obtain one, which
looked at first like a test-fixture inconvenience worth designing around.

It is not. The result namespace must be writable by a container whose fixed uid
is not this manager's, and `--group-add` against the deployment's configured
group is how that share exists at all. A boundary that took a gid would be
validating whatever its caller chose, in the one place where the answer decides
who may write beside a live target. The coupling is the contract's and is
recorded here so the next reader does not remove it as ceremony.

## 2026-09-06 — first independent implementation review: changes requested

The append-only review at
`review-2026-09-06T12-55-42Z.md` found five correction boundaries. The runtime
assignment does not bind its caller-supplied attempt to the coordinator's live
grant; quiescence and absence are caller-authored dictionaries rather than
durable Worker Manager observations; the runtime profile kind is not compared
with the entry's accepted profile kind; assignment publication copies the old
fixed-staging/single-write/rename algorithm that the shared exchange already
superseded; and restart adoption follows paths without proving exact directory
modes or configured group custody.

W101714 concurrently superseded the coordinator's earlier three-member profile
binding. `profile_version` and `profile_account_digest` are not accepted
candidate evidence because they have no producer; `profile_kind` remains and is
derived from checkpoint evidence. The correction here must bind that one
candidate-side kind without moving deployment profile version or instructions
into eligibility.

The focused implementation tests remain green, and a separate 52-case review
probe reproduces all reported bypasses. This is not approval of candidate
bytes: no immutable proposal digest was supplied.

## 2026-09-06 — the review's corrections, and the two rules they leave behind

`review-2026-09-06T12-55-42Z.md` found three [P0]s and two [P1]s. All five are
corrected. Two of them changed decisions recorded above rather than only code,
so the changes are written here.

**SUPERSEDED: the prior-runtime witness is not a caller document.** The
boundary decision above says the proof "reads that axis's vocabulary and
accepts only its positive states". It did — of a dictionary a CALLER handed
in. The record was right that agent quiescence is not runtime quiescence and
still shipped the same unsupported claim one layer out: a witness naming an
unrelated attempt as `destroyed` authorized a writer, and omitting the operand
authorized one unconditionally.

There is no witness operand now. WHICH attempt held the previous grant is the
coordinator's answer, derived from its own lease history in the same
relationship as the live grant; WHAT that runtime is doing is
`attempts.attempt_runtime_of`, the manager's durable row for exactly that
runtime. Absence is durable too: a target with no earlier grant has no
predecessor to prove, and a predecessor the manager holds no attempt for is a
contradiction between two stores rather than a quiet "nothing was running".

The rule this leaves behind, which is the part that generalizes: OWNING THE
SHAPE OF A CLAIM IS NOT OBSERVING THE FACT IT CLAIMS. A closed document, typed
member by member and checked against a frozen vocabulary, is still whatever its
author chose to write. If the answer decides whether a second writer may touch
a live target, it has to be read from the store that owns it.

**The one-snapshot proof grew to carry what a composition needs.**
`granted_context` is added to the coordinator: the live grant, the accepted
entry under it, and the grant it follows, out of ONE relationship pass.
`live_grant` is now a projection of it, which also closes a smaller instance of
the same defect the eighth W71878 review named — it read the lease and the
target in two separate snapshots.

**SUPERSEDED: publication reused the RULE, and the rule it reused was the old
one.** The clarification above says every rule the delivery uses is
`exchange.py`'s. It was that module's superseded shape: one fixed staging name,
one unchecked `os.write`, umask-dependent creation and `os.rename`. Reproduced:
a stale staging file wedged publication forever, a short write published a
truncated document as successful, a restrictive umask produced a mode-000 file
under a declared `0444` contract, and `rename` could replace a concurrent
winner. The current invariants are now present and driven — unique staging
name, whole-write loop, `fchmod` on the descriptor, file sync, no-clobber
`link` publication with winner comparison, directory sync, and staging cleanup
on every path.

The second rule: COPYING A MECHANISM COPIES THE VERSION YOU READ. The finding
above claims a lineage, and a claim about lineage is exactly the kind that
stops being true without anybody editing it. What would have caught this
earlier is driving the invariants rather than naming the module they came from,
which is what the new cases do.

**Also corrected:** the assignment's attempt is the grant's rather than the
caller's, and the runtime profile kind must equal the accepted entry's — both
from the same relationship — and adoption proves its namespaces on no-follow
descriptors at exact modes with the result namespace's group checked against
the manager-minted `WorkspaceGroup`.

## 2026-09-06 — second independent review: parent custody remains open

The re-review at `review-2026-09-06T13-13-54Z.md` confirms all three [P0]
corrections and the current publication algorithm. The adoption correction is
not complete: it proves the two final namespaces but never opens the
manager-created `integration/` parent. `O_NOFOLLOW` on the absolute child paths
does not cover that intermediate component, so a symlinked parent and a parent
whose mode moved from `0700` are both adopted. The parent must be proved first
and its children opened descriptor-relative to it.

The correction also leaves the superseded caller-witness schema exported:
`WITNESS_MEMBERS` still includes `evidence`, while the manager-derived helper
returns no such member. The public boundary must remove that obsolete shape or
define and test one coherent manager-observation document. Finally, the live
publication docstring still specifies `rename` although the corrected
mechanism uses no-clobber `link`, and the module introduction retains the
pre-clarification claim that there is no second file transport.

The focused 269-case gate remains green with one skip. A retained diagnostic
probe at `/tmp/w101490-rereview.py` drives the remaining custody and schema
counterexamples. No immutable proposal digest was supplied or approved.

## 2026-09-06 — the re-review: a proof that stops at the last component

`review-2026-09-06T13-13-54Z.md` accepted the three [P0] corrections and the
publication mechanism and found two [P1]s and one [P2]. All three are
corrected, and the first one is worth recording as a rule rather than as a fix.

**`O_NOFOLLOW` BINDS THE FINAL COMPONENT AND NOTHING ELSE.** Adoption opened
`<root>/integration/assignment` and `<root>/integration/result` no-follow, at
their exact modes, on their own descriptors -- and said nothing whatever about
`integration`. A symlink at that name was followed, so an arbitrary correctly
shaped tree behind it was reported as this manager's own delivery, and a root
whose mode had drifted was adopted too.

The correction is the same rule applied to every component instead of the last
one: the delivery root is opened no-follow and proved at its own established
mode, and both namespaces are then opened RELATIVE TO ITS DESCRIPTOR. The mode
it is proved at is also now established with `chmod` rather than requested
through `makedirs`, because a umask decides what the request gets and a mode
adoption checks has to be one this manager set.

The rule: A PATH PROOF IS ONLY AS DEEP AS ITS COMPONENTS. `O_NOFOLLOW` on a
multi-component path proves one edge of the walk, and the previous finding --
`isdir` follows links -- was corrected for the leaves while the parent kept
exactly the property that finding was about.

**A public contract must describe what a function returns.** The
caller-authored witness document was removed from composition, and its exported
`WITNESS_MEMBERS` tuple stayed behind declaring three members while the
manager-derived helper returns two. `evidence` was the CALLER's word for why it
believed itself; the manager's row needs no such member because the row IS the
evidence. The tuple is now `OBSERVED_RUNTIME_MEMBERS`, it is exactly what
`prior_runtime_witness` answers with, and a case asserts that equality rather
than trusting it. A superseded shape is not left as a public compatibility
surface for a candidate that has never been accepted or deployed.

**And the live prose now describes the reviewed mechanism.** The publication
docstring still specified `rename`, which the correction had already replaced
with no-clobber `link`, and the module header still said "no second file
transport" where this record had narrowed that to no second transport
MECHANISM. Both are corrected in the code contract; FINDING keeps the history.
Contradictory present-tense instructions beside corrected code are how the next
reader learns the wrong rule.

## 2026-09-06 — the re-review: a proof that stops at the last component

`review-2026-09-06T13-13-54Z.md` accepted the three [P0] corrections and the
publication mechanism and found two [P1]s and one [P2]. All three are
corrected, and the first is worth recording as a rule rather than as a fix.

**`O_NOFOLLOW` BINDS THE FINAL COMPONENT AND NOTHING ELSE.** Adoption opened
`<root>/integration/assignment` and `<root>/integration/result` no-follow, at
their exact modes, on their own descriptors -- and said nothing whatever about
`integration`. A symlink at that name was followed, so an arbitrary correctly
shaped tree behind it was reported as this manager's own delivery, and a root
whose mode had drifted was adopted too.

The correction is the same rule applied to every component instead of the last
one: the delivery root is opened no-follow and proved at its own established
mode, and both namespaces are then opened RELATIVE TO ITS DESCRIPTOR. The mode
it is proved at is now established with `chmod` rather than requested through
`makedirs`, because a umask decides what a request gets and a mode adoption
checks has to be one this manager set.

The rule: A PATH PROOF IS ONLY AS DEEP AS ITS COMPONENTS. The previous finding
-- `isdir` follows links -- was corrected for the leaves while their parent
kept exactly the property that finding was about.

**A public contract must describe what a function returns.** The
caller-authored witness document was removed from composition and its exported
`WITNESS_MEMBERS` tuple stayed behind declaring three members while the
manager-derived helper returns two. `evidence` was the CALLER's word for why it
believed itself; the manager's row needs no such member, because the row IS the
evidence. The tuple is now `OBSERVED_RUNTIME_MEMBERS`, it is exactly what
`prior_runtime_witness` answers with, and a case asserts that equality rather
than trusting it. A superseded shape is not left as a public compatibility
surface for a candidate that has never been accepted or deployed.

**And the live prose now describes the reviewed mechanism.** The publication
docstring still specified `rename`, which the correction had already replaced
with no-clobber `link`, and the module header still said "no second file
transport" where this record had narrowed that to no second transport
MECHANISM. Both are corrected in the code contract while FINDING keeps the
history. Contradictory present-tense instructions beside corrected code are how
the next reader learns the wrong rule.

## 2026-09-06 — third independent review: safety corrections pass, contract account remains open

The append-only review at `review-2026-09-06T13-33-05Z.md` confirms the parent
no-follow/mode/descriptor-relative custody correction, the two-member manager
observation and the publication wording at the function and module
introductions. The focused runtime/coordinator gate passes 284 cases with one
host-group skip.

The review finds bounded consistency residue: `runtime.__all__` exports
`OBSERVED_RUNTIME_MEMBERS` twice; other live prose still calls this the third
delivery after the recorded fourth-delivery clarification; PLAN items 3 and 4
still describe corrected findings as open; and the retained recheck now fails
on the concurrent accepted profile change before it reaches the checks it is
claimed to drive. The immediately preceding correction section also appears
twice in this FINDING and needs an explicit duplicate annotation rather than
being read as two rounds. W101490 remains changes-requested. No immutable
proposal digest was supplied or approved.

## 2026-09-06 — fourth independent review: code complete, append-only record correction required

`review-2026-09-06T13-44-19Z.md` confirms both prior code/contract [P2]s: the
public export is unique and resolving, live prose identifies the fourth
delivery consistently, plan items 3 and 4 are complete, and the current-profile
recheck reaches every intended boundary. The focused suite passes 287 tests
with one host-group skip.

One record-policy correction remains. The duplicate label was inserted into
the earlier duplicated FINDING section instead of appended as a new dated
clarification, rewriting chronological history in place. Restore that earlier
section and append the clarification after current history while retaining the
duplicated bytes. W101490 remains changes-requested only for that durable-record
repair. No immutable proposal digest was supplied or approved.

## 2026-09-06 — clarification: two sections above are one accidental duplicate

**This is a later clarification, appended. It changes no byte above it.**

The section headed `## 2026-09-06 — the re-review: a proof that stops at the
last component` appears TWICE in this file, once immediately after the other.
They are ONE correction round, not two. A first script that appended it failed
part-way through a later step, and I re-ran a repaired version without noticing
that the append itself had already landed.

THE TWO ARE NOT BYTE-IDENTICAL, which I only discovered while restoring them: I
reworded a few sentences between the failed run and the repaired one, so the
file holds two DRAFTS of one correction rather than one text twice. The earlier
of the two is the first draft. Nothing in either is a second decision, and no
sentence in one contradicts the other -- the differences are wording. I am
recording this because "identical" is what I said before I checked, and the
difference is exactly the kind a later reader would otherwise try to interpret
as significant.

Both sets of bytes stay exactly as they were written. The third review of
2026-09-06 asked for the duplicate to be marked, and I marked it by inserting a
note under the second heading -- which rewrote an earlier chronological entry
in place, and is precisely what this repository's append-only rule forbids. The
fourth review caught that, the inserted note is removed, and this section is
where the clarification belongs.

The rule I got backwards, stated so the next reader does not: A LATER ACCOUNT
IS APPENDED, NEVER WOVEN INTO AN EARLIER ONE. Marking history in place makes
the correction look like it was always there, which is the same defect as
silently deleting the superseded text and is why the policy has no exception
for "but the edit is small and helpful".

## 2026-09-06 — final independent review: bounded sign-off

`review-2026-09-06T13-48-09Z.md` signs off W101490 with no findings. All
runtime, custody, public-contract, evidence and durable-record corrections from
the four earlier reviews are accepted. The focused runtime/coordinator gate
passes 287 tests with one host-group skip and the working-tree whitespace gate
is clean.

No immutable proposal digest was supplied, so this is a bounded semantic and
current-working-tree sign-off rather than digest-bound approval of candidate
bytes. Candidate admission, target mutation, Authority completion and automatic
recovery remain in their separately scheduled leaves.
