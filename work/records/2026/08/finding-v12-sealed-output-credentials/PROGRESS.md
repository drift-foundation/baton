# Implementer progress — sealed output and assignment credentials

Created 2026-08-24 by `baton.claude` on claiming W6634, as the record requires.

## The dependency edges are installed

The assignment asked the route handler to add them before implementation, and
they are in: **W6634 → W6628** (seq 6902) and **W6634 → W6630** (seq 6903), each
with the rationale recorded on the edge itself.

## This Job is blocked, and that is the finding rather than a delay

The brief is explicit twice over: *"Consume the manager-owned output and
section-13 contracts"* and *"Do not invent manager envelopes or infer sealing
from engine prose."*

I revalidated against the current tree rather than taking the dependency
Works' status as the answer:

- **W6628** (manager output freeze and artifact receiver) — `open`, `queued`,
  **no dossier binding**.
- **W6630** (worker-control section 13 security surfaces) — `open`, `queued`,
  **no dossier binding**.
- In the Python distribution, `artifactOutput`, `freeze_operation` and the
  durable-secret rule occur **only in
  `contracts/schema/worker-control-1.0.schema.json`**. The manager package
  exports nothing that accepts an output observation, freezes, retains or
  authorizes cleanup; `seal_refusal` is the control store's refusal sealing and
  is a different thing wearing a similar word. `ARTIFACT_REF_MEMBERS` is a
  member list in the contracts layer, not a receiver.

So both contracts this Job is required to consume **do not exist yet**.

**What implementing now would mean.** Every deliverable in the assignment
terminates in one of them:

- quiescence-gated staging and manifest/count/bytes/digest observations have to
  be *accepted by the manager*, and the envelope that accepts them is W6628's;
- the exhaustive credential leak refusal has to apply *section 13's*
  durable-secret rule, which is W6630's.

I could write both. They would be **my invention of two other Works' contracts**
— the single thing this brief forbids — and W6628 and W6630 would then either
adopt my guesses or force this component to be rewritten. That is worse than
waiting, and it is worse in a way that is expensive to undo, because by then
tests would encode the guess.

**What I did not do:** start the parts that look independent. Bounded regular-
file collection reads a great deal like W6631's directory materializer and I
have just written that one, so it would have been easy to produce something
plausible. But *what may be collected* is decided by the declared outputs in the
manager's envelope, and *what must never be collected* is decided by §13 — so
the two rules that give collection its meaning are exactly the two that are
missing. A collector built without them would be a file walker with a Baton name
on it.

## Recommendation, not a decision

Route W6628 and W6630 first. When either lands, this Job can start against a
real contract; if the reviewer would rather I proceed against a **written,
reviewed provisional contract** stated in this record and explicitly owned by
W6628/W6630 to accept or replace, say so and I will — that is a different thing
from inventing one silently, and I would want it on the record before writing a
line of it.

## State

**Claimed, edges installed, no implementation.** Returned for the route
handler's decision.


## Revalidation on re-claim — 2026-08-26: the block is gone

**The entry above is superseded on its central fact and correct on its
reasoning.** It said both contracts this Job must consume do not exist. They
exist now: **W6628 and W6630 are both closed satisfying**, and I revalidated
that against the tree rather than against their status.

What is actually there to consume, with the symbols measured rather than
assumed:

- **W6628's output receiver** — `worker_manager/output.py`: `request_freeze`,
  `record_frozen_result`, `frozen_output_of`, `freeze_operation`.
- **W6630's section 13** — `contracts/secrets.py`: `check_no_durable_secret`
  and the live-value registry (`held_secret`, `live_secret`,
  `remember_secret`, `forget_secret`), applied at every durable and public
  surface in the manager package.
- And beside them, **W6629's intake**, closed after those two, which is what
  consumes what this component produces.

So the recommendation the last entry made was taken, and the wait was the
right call: neither envelope had to be invented, and both are now fixed
contracts with reviewed tests behind them.

## The two shapes this component must answer, read off the consumers

Measured from the code that will call it, not from prose:

- **`adapter.seal(request)`** is called by `request_freeze` with
  `{attempt_id, assignment, disposition, operation}` and its answer goes
  straight into `record_frozen_result`, which validates it as a
  `baton.worker-manifest/result`. So `seal` returns a RESULT MANIFEST, and
  `_compare_declared` then holds it against the input manifest's declarations
  both ways.
- **`adapter.collect(operands)`** is called by `request_intake` and its answer
  is compared member by member against the freeze by `intake._compared`:
  `{result_id, artifacts: [{artifact_id, content_digest, bytes,
  custody_locator}]}`. Only `custody_locator` is adopted; identity, digest and
  byte count are compared against what the freeze recorded.

**`OciAdapter` has `start`, `list`, `stop`, `destroy` and `observe`, and
neither `seal` nor `collect`.** Those two are exactly this Job's surface, and
the manager already types both as capabilities before it calls them
(`boundaries.capability(getattr(adapter, "seal", None), ...)`).

## Three things the revalidation decided before any code

**The declared outputs belong at CONSTRUCTION.** The seal request does not
carry them — it carries the attempt, the assignment, the disposition and the
operation. The declarations are assignment-scoped and fixed, exactly like
`identity` and `assignment_roots`, and this adapter already refuses to exist
without those: "an adapter that cannot say what its assignment owns never
reaches a delivery". Taking them per request would make what may be collected
a per-call argument, which is the property the acceptance is about.

**Reuse `workspaces.directory_manifest`, do not write a second walker.** It
already measures exactly what this Job needs — every entry opened once with
`O_NOFOLLOW`, bytes and size from that one descriptor so a replacement between
check and read is a file this component never sees, regular files only,
bounded entries and bytes, bytewise-sorted entries and a tree digest over that
order. The last entry worried that a collector here would duplicate W6631's
materializer; the answer is to consume its measured half rather than to
re-derive it. That half is also NOT the half W15232 removes — that Work owns
the acquisition surface, not the measurement one.

**Carry the output `type` OPAQUELY, and this is a cross-Work revalidation.**
W14251 (blocked on W15232) revises `artifactOutput` so `type` stops being a
three-value enum of result kinds and becomes an opaque id, with a new
`result_metadata` beside it. The manager already treats it that way —
`output.py:_compare_declared` does `expect["type"] != output["type"]` and
reads neither. So this component echoes the declared label and never branches
on it: that is correct against today's contract AND unchanged by the revision,
which is the difference between a component that survives W14251 and one that
has to be rewritten by it.


## The quiescence gate had an apparent gap, and it closes exactly

The acceptance requires the freeze/copy/hash to be ORDERED AFTER QUIESCENCE and
to detect replacement races. The manager proves quiescence from the axis before
it calls `seal` — but the seal request carries `{attempt_id, assignment,
disposition, operation}` and **no runtime id**, so at first reading this
component is asked to gate on a fact it is handed no way to check. `destroy` is
handed one; `seal` is not.

**It composes.** The frozen label set is exactly eight members:

    runtime_attempt_id, authority_uuid, work_id, participant, generation,
    profile_digest, policy_digest, adapter_digest

The request carries the first five — `attempt_id` plus the four parts of
`assignment` — and this adapter has owned the last three since construction as
its resolved identity. So the two halves compose into the full label document
and `self.list` discovers the attempt's runtimes without the manager passing an
identity it already decided not to pass.

**And that is better than being handed the runtime id**, which is why this is
recorded as a resolution rather than a gap to raise. Nothing is remembered
between calls, so a manager restarted between start and freeze gates exactly as
well as one that was never restarted — and `_CANDIDATE_LABELS` is deliberately
the single ownership key, so a runtime carrying this attempt under a stale
generation is DISCOVERED and refused rather than filtered away. Gating on a
remembered runtime id would have missed precisely that one.

## State

**Claimed and unblocked. Revalidation and design recorded; no code written
yet.** The next step is `sealing.py` — the module boundary is deliberate:
`oci.py` is W6632/W6633's file and W6633 is open and impl-routed, so this Work
adds two thin delegating methods to `OciAdapter` rather than several hundred
lines to a file another Work is editing.

**Item 4's mechanism is still unchosen and is the one real open question.**
`run_vector` composes no environment and no secret, the sandbox is
`--read-only` with one writable mount, and §13 forbids the value from argv,
labels, logs, the durable store and the collected output. That leaves the
delivery surface to be chosen and stated in this record before it is written,
not discovered while writing it. No repository state was mutated.


## Implemented — items 2, 3 and most of 5, 2026-08-26

`sealing.py`, plus two thin seams on `OciAdapter`. 19 focused cases in
`tests/manager/test_sealing.py`: the quiescence gate, declared-only
collection, missing/undeclared/linked outputs, the over-count and over-byte
limits, the measured manifest, the read-only freeze, the replacement race, and
the collection that answers the freeze rather than re-measuring it.

### The boundary inventory made two design decisions for me, and both were right

**`adapter.list` and `adapter.observe` have exactly one crossing each.** My
first version put the quiescence gate in `sealing.py`, which called them, and
the inventory refused the module outright: "adapter.list crosses at
attempts.py:reconcile_runtime and at sealing.py:_quiesced; a capability with
two crossings has two owners." That is a design signal, not a registration
chore. The gate moved into `OciAdapter._quiesced`, where those are the
adapter's own methods, and `sealing.py` became a pure function over data —
handed the roots, the declarations and the identity, deciding only what the
sealed result says. Better than what I wrote first.

**`clock` has one crossing too, the control store's.** I had injected a clock
into the adapter so a sealed result could stamp `created_at`. Same refusal. So
the MANAGER stamps the instant into the seal request it already composes,
which is the more honest account anyway: it is the instant of the freeze this
manager requested.

Neither was in my plan. The inventory found both before a reviewer had to.

### Three fixture defects of my own, found by measuring rather than reading

- The constraint document named only the two limits it enforces, so
  `boundaries.document` refused the frozen `outputConstraints`' other three
  members and **every real declaration failed as a schema error before any
  limit could be reached** — which also made two limit cases pass for the
  wrong reason.
- The collect operands omitted `result_manifest_digest`, which
  `request_intake` actually sends, so every real call refused.
- The replacement-race case mutated the tree before the FIRST measurement, so
  both measurements agreed and it proved nothing. It mutates between them now.

### What is NOT here

**Item 4, assignment-scoped credential delivery.** Nothing about it is
written, and the mechanism question I raised when I released this Work is
still unanswered: `run_vector` composes no environment and no secret, the
sandbox is `--read-only` with one writable mount, and §13 bars the value from
argv, labels, logs, the durable store and the collected output. That surface
has to be CHOSEN and stated here before it is written. The leakage and
cancellation halves of item 5 belong with it.

### Failures in the tree that are not this Work's

- `test_the_assignment_root_contract_is_artifact_neutral` and
  `test_no_git_metadata_root_survives_the_acquisition_cut` — W15232's own
  review case: `oci.ROOT_NAMES` still carries `git` and
  `assignment_workspace` still provisions that root after the acquisition cut.
  W15232 is queued and unclaimed, and this is a real gap in what I removed
  there.
- `test_a_retention_cannot_borrow_another_attempts_committed_act` — a W6629
  review case added after I passed that Work back; it is with the reviewer.
- The long-standing boundary-inventory gaps in `documents.py` and
  `sessions.py`, and `test_worker_image_build`, which is W6633's.

Measured: zero unowned boundary entries and zero witness-table gaps name
`sealing.py` or either new adapter seam.

## State

**Partly implemented and awaiting independent review.** Item 4 is open on a
question rather than on work. No repository state was mutated.


## Review corrections — 2026-08-26

### [P1] Freeze and collection had no immutable custody boundary

I froze the workspace IN PLACE and measured it there, then collected from the
same mutable path. A host-side write after the freeze changed what collection
returned, both locators named the live workspace, and retry identity depended
on a tree the worker still owns.

The dossier's own acceptance says the material is "copied into immutable
staging BEFORE its manifest/count/bytes/digest observation is emitted". I read
that, wrote a freeze that chmods, and did not notice the copy was missing —
the words were in the record I was working from.

Sealing copies each measured output into manager-owned custody, freezes the
COPY, re-measures it, and emits locators naming it; collection reads custody
rather than the workspace. The copy is entry-by-entry from the measurement
rather than a second walk, so what is copied is exactly what the measurement
admitted — a fresh walk could find something the first one refused.

**Custody is deliberately not a root.** `ROOT_NAMES` is the contract for what a
container may MOUNT, and custody is precisely the material the worker must not
reach after the freeze. Putting it there would hand the worker its own evidence
back.

**And it exposed a real retry defect.** Custody is frozen, so a second seal
faulted copying into its own read-only tree — an exact retry has to reproduce
its answer, and mine raised `PermissionError`. Staging is idempotent now.

### [P1] Two names could describe one tree

`declared_outputs` rejected duplicate NAMES and compared no paths, so
same-path and ancestor/descendant declarations both passed. Two declarations
over one tree make the same bytes two artifacts with two identities and two
digests, and cleanup then decides twice about material that is once.

Compared segment by segment rather than by prefix, because `out2` starts with
`out` and is not inside it.

### The credential decision is pinned rather than asked again

The review asked me to choose and pin it, and it is right that a third round of
asking would be worse than a decision somebody can overrule. `FINDING.md` now
records the boundary, the constraints that produced it, and why each rejected
option is rejected — including the one worth arguing, that an environment
variable puts the value in engine inspection where `observe` reads it and where
it outlives the process.

Decided: a private ephemeral file, bind-mounted read-only at a fixed
in-container path, removed by `authorize_cleanup` because that is the one act
that runs on every ending including a cancellation. Nothing reads it back. One
point is flagged as open to being overruled — the fixed path is a convention
this record invents.

**Item 4 is still not implemented.** What changed is that it is no longer
blocked on a question.

### Verification

`tests.manager.test_sealing` **21/21** with exit status 0.

## State

**Awaiting independent re-review.** No repository state was mutated.


## Re-review — three of four [P1]s corrected, 2026-08-26

### [P1] An exact seal retry still depended on today's workspace

I put the already-in-custody check INSIDE the staging helper, so the live path
was examined first. After one successful seal, deleting the worker's output
made the identical request refuse `precondition` instead of replaying the
immutable artifact this manager already holds.

Custody is consulted BEFORE the live workspace now. This is the same ordering
rule W6628's receiver was corrected for twice and that `intake.record` states
in its own words — replay sits above every state read, because nothing about
today is a precondition for reproducing an answer that already settled. I had
written that sentence about intake in this same campaign and then rebuilt the
defect one module over.

The fresh seal and the replay share one `_answered` constructor, so an exact
retry cannot return a differently-spelled version of the first answer.

### [P1] Path validation at construction was incomplete

`declared_outputs` owned paths only as non-empty text, so absolute, escaping
and non-canonical forms were accepted when the adapter was built and refused —
if at all — during seal. By seal time a worker has already run against a
declaration nobody could act on: the wrong party and the wrong moment.

`_relative` proves the frozen `relativePath` rules at construction: no leading
separator, no empty segment, no `.` or `..` anywhere, by segment rather than by
prefix.

**And it broke the inventory in a way worth recording.** My first version
passed the caller's noun as the boundary label, so the label had no literal
part and `owning_validators` refused the whole module: "owns a boundary with no
literal label; the inventory cannot attribute it". The label is literal now and
the caller's noun rides the diagnostics instead.

### [P1] The sealing receivers had no probes

Ten (entry, label) pairs across both requests, registered as `sealing_probes`.

**The member probes were vacuous on the first attempt.** I spoiled each member
by setting it to `None`, and the envelope owner's rule is PRESENCE — a member
set to `None` is present, so the probe never reached what it named. The gate
said so directly, listing those subcases as not reaching their boundary. They
remove the member now.

### [P1] The credential lifecycle is still absent

Not implemented, and the honest statement is that this is the Work's largest
remaining deliverable rather than a detail. Approver message 16691 settled the
mechanism and the reviewer has corrected this dossier so it is authoritative
over my earlier one-file proposal: closed logical slots named by the
assignment, a trusted runtime profile mapping each slot to a provider and
opaque reference, one manager-materialized private file per authorized slot,
the fixed read-only `/run/baton/credentials` root, live-bearer registration
retained through quiescence, staging, leak checks, container removal and root
cleanup, restart adoption only on exact attempt/container/mount/root agreement,
and bounded orphan cleanup otherwise.

What changed since the last round is that it is no longer blocked on a
question — the mechanism is pinned and the remaining work is to build it.

### Verification

`tests.manager.test_sealing` **23/23**; `test_oci` and `test_dependencies`
green beside it. Measured: zero unowned boundary entries and no inventory
failure names `sealing.py` or either adapter seam.

## State

**Awaiting independent re-review, with the credential lifecycle outstanding.**
No repository state was mutated.


## Second re-review — the two retry [P1]s, 2026-08-26

**Both are one defect wearing two faces, and the reviewer's own sentence names
the fix: directory existence is neither necessary nor sufficient evidence of a
committed result.**

- NOT SUFFICIENT — creating custody and copying into it are not atomic, so a
  stopped process leaves a PREFIX. Restart measured that prefix and published
  it as the complete output.
- NOT NECESSARY — `missing-optional` is a settled answer with no tree at all,
  so it had no marker, and the same freeze operation consulted today's
  workspace again. An optional path appearing later turned the answer from
  missing to present: one operation identity, two results.

The evidence is a RECORD OF THE WHOLE ANSWER now, absence included, published
LAST — after every declared output is staged and frozen. That ordering is what
makes it trustworthy: it exists only if everything it describes already
succeeded, which is the same publish-last discipline the worker contract puts
on `output.json`. What is stored is the sealed manifest itself, byte-stable, so
an exact retry reproduces the first answer rather than a re-derivation that
happens to agree — including its instant, which re-deriving would move.

This is the third time in this campaign I have been corrected on the same rule:
replay sits above every state read. W6628's receiver, then `intake.record`,
then this module — and I had already fixed the present-artifact half of THIS
module one round ago while leaving the whole-answer half inferred from a
directory.

### Measured, and the first attribution I wrote would have been wrong

Removing the committed-record replay fails the two retry cases. But removing
the partial-prefix reopen in `_staged` failed NOTHING — so my initial "both
halves carry this" would have been false.

The reopen is nevertheless reachable, and the window is precise: staging
freezes each output as it completes and the record is published last, so a
process can stop with custody complete and FROZEN and no record naming it.
Restart has no answer to replay, stages again, and writes into a read-only
tree.

`test_a_frozen_custody_without_its_record_is_re_staged` drives exactly that
state. Measured: without the reopen it raises `PermissionError` instead of
sealing. Code that no case reached is code I should not have shipped a round
ago, and covering it was cheaper than arguing for it.

### The credential lifecycle is still absent

Third round of saying so. It remains the Work's largest deliverable, the
mechanism is pinned by approver message 16691, and nothing about it is written.

### Verification

`tests.manager.test_sealing` **26/26** (23 → 25 with the review's two, → 26
with the window case).

## State

**Awaiting independent re-review, with the credential lifecycle outstanding.**
No repository state was mutated.


## Third re-review — the two replay [P1]s, and the credential lifecycle BUILT

### [P1] Publication was last but not atomic

`open` on the final name creates or truncates it before a single byte of the
answer is there, so a process stopped inside the write left `sealed.json`
existing and empty — and replay, which read existence as settlement, handed
those zero bytes to a JSON decoder and raised a fault that is not a refusal.
The reviewer's sentence is exact: publishing LAST is not publishing ATOMICALLY.

The bytes are written under a fixed private name, forced to the device, then
renamed. A fixed name rather than a unique one on purpose: `os.replace` is
atomic within one directory, so the final name only ever holds bytes that were
already complete, and a leftover from a stopped writer is truncated by the next
write rather than accumulating.

And adoption OWNS what it reads now, in three separate ways, because they are
three different questions:

- bytes that do not decode → `integrity/schema`, fails closed rather than
  re-deriving. Re-deriving would move `created_at` and could contradict an
  answer a caller already holds;
- a body whose stored `manifest_digest` does not re-derive → `integrity/digest`.
  This is the COMPLETENESS proof: a successful decode says the bytes are JSON,
  not that every member arrived;
- and the binding below.

### [P1] Replay was selected by attempt custody alone

Custody is keyed by ATTEMPT and an attempt is not an operation, so a second
freeze under a different operation id and signature received the first
operation's answer. Six members now bind the stored answer to the request
before it is returned — `result_id`, `assignment_ref`, `disposition`,
`freeze_operation`, `input_manifest_digest`, `policy_digest` — and a
disagreement is `ambiguous/operation`.

**The sentence I had been repeating was half a rule.** "Replay sits above every
state read" was never "replay before identity proof", and reading it that way
is exactly what this defect was. I have been corrected on the ordering three
times; this is the first time I have been corrected on what the ordering is
*for*.

### Both new guards started out unmeasured, and two of four still were

Removing the operation binding and removing the decode guard each failed the
review's own additive case. Removing the digest re-derivation and removing the
atomic rename failed NOTHING — so two of the four rules I had just written were
code no case could drive. Added:

- `test_a_committed_record_whose_bytes_moved_is_not_evidence` — a record that
  decodes and binds correctly and describes something other than what it says;
- `test_the_final_record_never_exists_before_its_bytes_do` — stops the process
  between the write and the rename and asserts the final name is absent.

Both now fail when their rule is removed.

## The credential lifecycle — built, not deferred a fourth time

`src/baton_v12/worker_manager/credentials.py`, and it implements the approver's
ruling as superseded by message 16691 rather than re-deciding any of it.

**The four parties, which is the whole design.** The ASSIGNMENT names closed
logical slots and nothing else — an assignment handing a document rather than a
name is one trying to carry a provider reference, a host path or the bytes, and
that is refused by construction. The TRUSTED PROFILE maps each slot to a
provider and an OPAQUE reference; opaque is load-bearing, because the moment
this module read a meaning out of a reference the profile would be a second
place that decides what a credential is. The PROVIDER is an injected capability,
trusted to be the deployment's and not trusted to be correct. The WORKER sees
one thing: entries of the fixed read-only root `/run/baton/credentials`.

**Where the bytes are allowed to be**, in full: one 0600 file per slot under a
0700 assignment-private root, and the in-memory live-secret registry. That is
the entire list.

**The order is the security property**, so it is written as a rule rather than
left to the reading: the provider answers, the value is REGISTERED LIVE, and
only then does it reach a file. Registering after the write would leave a window
in which the bytes exist and the registry says there is nothing to find — the
one shape a leak check cannot survive. Measured: moving the registration after
the write fails six cases.

**One mount per slot, and the SOURCE IS THE FILE.** The ruling fixes the
container-side root and says the closed slot names determine its entries;
mounting each file names exactly those entries, so anything that ever lands in
the manager's volatile directory beside them is unreachable regardless.
Mounting the directory would satisfy the same sentence and make that guarantee
depend on the directory only ever holding what this module put there.

**A separate mount owner from `_mounts`, deliberately.** `_mounts` admits a
source only because this manager created the assignment ROOT it lives under —
and W15232 has just finished removing a third root from that contract. A
credential is not assignment material and must not become a third mountable
root: it is delivered at a fixed path from a volatile root `credentials.py`
owns outright, and an assignment mount that would CONTAIN `/run/baton/
credentials` is refused, because it would decide what the worker reads there.

**§13 got two new teeth, and both were missing before.**

- The whole start vector is walked. Every process on the host can read
  another's command line, so an argv carrying a live bearer is a durable
  surface; this was an intention in the record and is now a rule.
- **The artifact's own CONTENT is walked at staging.** The sealed result and
  the collection observation were already walked, but those are documents this
  manager composes — a worker that wrote its credential into the output it
  produced put the bearer somewhere no walk of a manager document had ever
  looked. Staging is the one moment the content is in hand, and it is the copy
  that makes the bytes this manager's. Decoded leniently on purpose: refusing
  to look at non-UTF-8 would make "write it to a PNG" the way past this.

**One ordered teardown on every ending.** Files, then the root, then the durable
record — each PROVED absent — and only then is the bearer forgotten. Uncertainty
REFUSES with `policy/credential-lifetime`, and the bearers stay live so anything
sealed afterwards is still checked against them. `destroy` is what runs on
success, failure and cancellation alike, so there is no second teardown path
that could drift from this one; a case asserts the adapter contains exactly one
call to `tear_down`.

**A runtime not proved gone stops it.** A container this manager cannot say is
absent may still be reading the mount, and removing the file under it would be
reporting an ending that has not happened. `destroy` answers `unresolved` then —
never something a caller can read as settlement.

**Restart adopts only an exact agreement**, of the attempt, the container, the
mount targets and the root, and refuses everything else into bounded orphan
cleanup that unlinks without ever reading a byte. The cleanup REPORTS its bound:
a pass that stopped at its limit and answered like one that finished would be
cleanup uncertainty reported as success.

**And adoption RE-REGISTERS the bearer**, which is the one place I departed from
the superseded proposal's "nothing reads it back" — deliberately, and it is the
argument most worth attacking. A restarted manager that adopted an attempt
without re-registering would seal that attempt's output with the leak check
silently disarmed, and a check that cannot fail is worse than no check because
it reads as evidence. Nothing publishes, compares or observes the value; this
manager reads its own 0600 file to put it back in its own registry.

### Two rules I wrote were unreachable, and measurement said so

- `_unlink` and `_rmdir` proved absence with near-identical code. No filesystem
  removes a directory while a file is still inside it, so the directory's proof
  answered for both and the file's was code no case could drive. They are one
  `_gone` helper now, and `test_a_removal_that_did_not_happen_is_not_a_teardown`
  drives it with a removal that reports success and does nothing.
- `Delivery.record` walked §13 and so did `written_state`. Every path to
  durability went through the second one, so the first was unreachable. Removed:
  two copies of one rule is one rule holding in one of the two places, which is
  what `errors.py` says about `name_of` in its own words.

### Verification

`tests.manager.test_credentials` **39 cases**, and 21 of the 21 guards this
Work added were measured by removing them one at a time; every one now fails at
least one case. `test_sealing` 30, `test_oci`, `test_output`, `test_intake`,
`test_dependencies` green beside them — 281 in that focused set with exit
status 0.

`test_dependencies` needed the seven new operand names declared, with the reason
each is an operand rather than bookkeeping written beside it.

### Three smaller decisions, named because a reviewer should not have to find them

**`authorize_cleanup` is not where teardown lives, and the supersession says so.**
My superseded proposal put removal there because it is the one act that runs on
every ending. Message 16691 corrected that: `authorize_cleanup` alone is not
permission to discard the live-secret registry before container removal and root
cleanup are proved. Teardown is therefore at `destroy`, which is downstream of
the authorization and is still the single path all three endings take.

**`slot_name` takes no caller noun.** Every rule in `boundaries.py` takes a
`what`, and that layer is the one place it belongs — it is excluded from the
derived inventory precisely because it IS the layer. A public function anywhere
else that took one would add a receiving entry carrying nothing but prose, so
this rule owns its own literal label and the refusal names the value instead.

**The artifact-content walk decodes each staged file.** That is a second copy
of the bytes in memory, bounded by the declaration's own `max_bytes` — the same
bound that already governs the read beside it. Stated rather than hidden: it is
a real cost, and the alternative is a leak check that a worker defeats by
writing to a file this manager declined to look at.

### What is NOT covered, said plainly

The credential root's ORPHAN path is covered for roots this manager can name and
remove. A root whose removal fails for reasons outside this process — a
filesystem that refuses, a mount that is gone — is reported as remaining rather
than discarded, and no case drives that state end to end because the ending it
belongs to is an operator's rather than this manager's.

### The boundary inventory, and the two defects registering it found

The reviewer required probes for the sealing receivers a round ago, so the
credential lifecycle arrives with its own: **26 probes** across `credentials.py`
and the two new `oci.py` entries, plus **8 stated owners** with witnesses for
the shapes that are not boundary kinds — a list is not a crossing, a closed
vocabulary is a comparison against this module's own constant, and a delivery
is proved by BEING one because its constructor owned every member.

**Registering it changed the design twice, and both changes are improvements
rather than concessions to a test.**

- **The public surface was too wide.** `home` was a parameter of eight public
  functions, so one deployment fact was eight crossings with eight rules to
  keep true. It is `CredentialHome` now — owned once at construction, the same
  shape `OciAdapter` uses for its resolved identity and its assignment roots.
  Twenty-three unowned entries became eight.
- **`materialize` created the volatile root before it proved the resolution it
  was handed.** Writing the witness is what found it: a spoiled resolution left
  a directory behind. A door that refuses AFTER making something is a door
  whose refusal has a side effect. Every operand is proved before anything
  exists on disk now.

`slot_name` is public for the same reason: the adapter applies the identical
rule to the CONTAINER side of a mount, and one rule with two spellings is a
rule that holds in one of the two places.

### Verification, and the finding that is not mine

`tests.manager.test_credentials` **44 cases**; `test_sealing` **30**;
`test_oci`, `test_output`, `test_intake`, `test_dependencies`,
`test_workspaces`, `test_secrets` and `test_parallel_runner` green beside them.
Every one of the **30 guards** this round added was measured by removing it;
the four that failed nothing were covered or removed rather than kept.

The boundary inventory, computed over the derived universe: **zero** W6634
entries unowned, orphaned, owned-but-unprobed, or probed-but-unowned. The
remaining 21 unowned, 23 orphans and 11 unprobed are the long-standing set in
`documents.py`, `sessions.py`, `intake.py`, `posture_slots.py` and
`interrogation.py`, unchanged in count and in name.

Aggregate: `V12_STATUS=1`, 1372 tests, 8 failures and 1 error. Six are the
long-standing inventory gaps. Two are W6633's `test_worker_image_build`.

**And one is a finding I am reporting rather than fixing.**
`test_frozen.test_the_tracked_build_copy_is_not_a_fourth_contract` fails:
`v12/python/build/lib/baton_v12/contracts/schema/worker-control-1.0.schema.json`
still carries the superseded acquisition schema. That case was added by
W14251's own review while this round ran, and it is the same class of miss I
recorded against myself there — I called three copies "all three" and a fourth
tracked one exists. It belongs to W14251, whose dossier already owns the
supersession; this claim did not touch it, because owning only what I claimed
is the rule that stops one Work quietly editing another's contract.

`tests/manager/test_credentials.py` is registered in `tools/parallel_test.py`,
whose own completeness gate is what caught its absence.

## State

**Awaiting independent re-review, with all three [P1]s addressed.** No
repository state was mutated.


## Fourth re-review — all four [P1]s, 2026-08-26

### [P1] Restart adoption proved document consistency, not the boundary

The reviewer's sentence is the correction: *a self-authored record agreeing
with its own local files is not proof that the live container has the same
mount sources and targets.* `adopt` compared a record this manager wrote
against paths this manager derived and files this manager owns — three
statements by one party. And nothing in production called `read_state`,
`adopt` or `discard_orphans` at all, so the recovery path existed only in a
test. **A recovery path that exists only in a test is a recovery path this
manager does not have.**

Two things were built.

**The engine now reports what the container actually has.** `observe` reads the
binds out of the SAME inspection that decided the state, so the two facts are
one observation of one runtime rather than two questions asked at two moments.
`mounts` is `None` when no document was read — the honest value for "this
adapter did not see", which `_mounts_disagree` refuses outright.

**`OciAdapter.recover_credentials` is the production path.** It reads the
lifecycle record, finds the runtime by labels, observes it, and compares four
things because they are four different mistakes: a bind that is missing, one
sourced from somewhere else, one that is WRITABLE, and — the one easy to
forget — an EXTRA entry under the fixed root, which a comparison that only
looked for what it expected would never see.

**The disagreement path is the approved one and it is conditional.** No output
accepted, the worker stopped, then bounded orphan cleanup — and the cleanup
keeps this attempt's root ALIVE unless the stop was proved, because removing a
mount source out from under a container this manager cannot say is gone is the
one act worse than leaving it. The refusal says `UNRESOLVED` when that happens.

### [P1] An engine-declined start stranded the credential

Correct, and the fix is wider than the case. Every refusing exit from `start`
now settles the delivery, because the materialization happened before the
adapter was built: the single `destroy` path cannot reach a delivery it cannot
name, and without a runtime id there is no name. The duplicate-start and
disagreeing-label exits are the same shape, so they are corrected with it
rather than after the next review.

**And it asks rather than assumes.** A declined start is strong evidence that
nothing holds the mount and it is not proof — an engine can create a container
and then fail. So the settlement lists: no runtime carrying this attempt's
labels means the delivery settles; anything else is `unresolved`, and the
refusal carries that word so a caller can tell a clean failure from a dirty
one.

### [P1] A failed multi-slot adoption leaked registrations

The registry is reference-counted and every entry is forgotten by the act that
acquired it — and the act that acquired those had raised. A value no object
owns stays live for the process, which turns every later §13 walk into a check
against a bearer nobody is delivering.

Adoption proves the WHOLE delivery before registering any of it, and the one
registering act unwinds itself. Both halves are driven: the reviewer's case
covers the validation half, and a new one patches the constructor to fail
between registrations.

### [P1] A short write delivered a truncated credential

`os.write` may accept fewer bytes than it was handed, and a short write is
ordinary — a pipe, a signal-interrupted call, a filesystem near its limit.
Nothing downstream could have noticed: the registry holds the whole value, the
leak checks look for the whole value, and the worker reads a prefix that simply
does not authenticate.

Every byte is written now, and a writer that makes no progress REFUSES rather
than spins. Measuring that guard is what found the second half: without it the
suite does not terminate, which is the strongest evidence it is load-bearing
and also a hazard in my own measurement harness. The harness is bounded now and
reports a non-terminating run as a failed mutation.

### Two things the correction changed beyond the four findings

- **A delivery with no slots is refused.** It would be a root and a record
  describing nothing, and every mount comparison over it would be vacuously
  satisfied — a restart would adopt any container at all. An assignment that
  authorizes no credential gets no delivery, which the adapter already
  expresses as `credential_delivery=None`.
- **The source-text call count is gone.** The reviewer said not to substitute
  it for driven endings, and it was replaced by two: a cancellation that stops
  and then destroys, and a failure ending that destroys under a different
  authorization. Both assert the credential settled once, at the end.

### Verification

`tests.manager.test_credentials` **61 cases**, `test_oci` 74, `test_sealing`
30; the adjacent set is green. **Twenty of the twenty-one guards this round
added fail at least one case when removed**, and the twenty-first is recorded
as a measured EQUIVALENCE rather than claimed: `observe` answering `()` instead
of `None` for an unreadable inspection produces the identical refusal, because
a lifecycle record now names at least one slot and an empty bind list fails the
same rule. `None` is still the true value; no case can currently tell them
apart, and a comment claiming a distinction nothing can drive is the vacuity
this campaign keeps correcting.

The boundary inventory, recomputed over the derived universe: **zero** W6634
entries unowned, orphaned, owned-but-unprobed or probed-but-unowned. Two of
those were regressions this round introduced and then corrected — a dict
literal keyed `bearer` made the derivation invent a `record.slots.bearer`
crossing that does not exist, and owning the recovery assignment inside a
private helper left its rules owning nothing. The first is a tuple now; the
second is owned at the public door.


## Fifth re-review — four defects, and the dependency settled, 2026-08-26

### [P1] A delivery could start under another attempt's runtime identity

Nothing compared `credential_delivery.attempt_id` with the start label's
`runtime_attempt_id`, so an attempt-2-labelled container could mount attempt-1's
credential root — and reconciliation and restart would then look for that
delivery under an identity it was never recorded against.

The comparison happens FIRST now, before the engine is asked anything. **And
this exit deliberately tears nothing down.** The settlement asks the engine
which runtimes carry THESE labels, and these are the wrong attempt's: an empty
answer about attempt-2 says nothing about whether attempt-1's runtime holds the
mount. A refusal that acted on it would be inferring absence from the wrong
question — which is precisely the correction being made everywhere else in this
Work.

### [P1] The promised all-refusal settlement was not exhaustive

`_refused_start` covered the checks above it and the engine's own answer, and a
`ContractRefusal` raised while COMPOSING the vector went straight past it — a
mount collision, a malformed operation id, an unmountable delivery. I claimed
"every refusing exit" last round and delivered most of them.

Composition and creation are inside one guarded block now. Those exits are the
ones where the duplicate probe has already proved the candidate set empty, so
they are where settling is both safe and most obviously owed.

### [P1] Live-mount agreement accepted shadowing and multiplicity

Two holes in one comparison, and they are different mistakes.

- **Shadowing.** The check looked for unexpected DESCENDANTS of the fixed root
  and never for a bind ON it. So a bind at `/run/baton/credentials` passed:
  every per-slot bind underneath agreed with the record, the root bind shadowed
  all of them, and this manager reported exact agreement while the worker read
  whatever that root contained. The rule is `at or below` now.
- **Multiplicity.** Observations were collapsed into a dict keyed by target, so
  two binds on one path became one and the second was never compared. Which of
  the two a path inside the container reaches is the ENGINE's decision, not
  this manager's, so a duplicate is a runtime nobody can say the contents of.
  Exact agreement is one and only one.

### [P1] Recovery deleted roots it had not proved stale

`discard_orphans(live=[])` on a per-attempt path, and a `CredentialHome` is
ASSIGNMENT-scoped — it holds sibling attempts. So recovering attempt-1 deleted
attempt-2's materialized root while attempt-2's lifecycle record and live
bearer were both still there. **"No record for THIS attempt" is not evidence
about any other**, and a pass that removes what it has not proved stale is not
cleanup; it is a second failure caused by the first.

`discard_orphan(attempt_id)` removes exactly one root, proved stale by its
caller. `discard_orphans(live=…)` stays for the broad pass, which needs the
complete live set and says so in its own signature. Both branches of recovery
use the targeted one, and the failed branch uses it only when the stop is
proved.

## [P1] The W14251 dependency, now settled

W14251's second review landed the ownership split while this Work waited, so
this is a revalidation against a contract that now exists rather than a
deferral.

**The exact alignment, measured.**

| | who | what | where |
| --- | --- | --- | --- |
| `/output/output.json` | the WORKER (W6633) | `baton.worker-manifest/completion` | inside `/output/` |
| `sealed.json` | this Work's manager | `baton.worker-manifest/result` | `<home>/custody/<attempt>/` |

**W6634's publisher, name and location are correct as built.** `sealed.json` is
the MANAGER's receipt in manager custody, published atomically after every
declared output is staged and frozen — which is exactly what the split assigns
to this side. Nothing here needed moving or renaming.

**What this round added is the binding.** The receipt now carries
`completion_manifest_digest` when the manager has validated a worker envelope,
and the member is part of the replay binding — a receipt settled over one
worker document is not the answer for another. It is OPTIONAL in the frozen
schema and ABSENT rather than null when there is none, which is every worker
until W6633 publishes one.

**What remains, named rather than built.** Nothing in `worker_manager/` yet
READS `/output/output.json` — measured, the string appears zero times there.
Validating the worker's envelope before freezing is a manager duty the contract
now states, and it belongs with W6633 actually publishing one: building a
consumer for a document nothing writes would be an unexercised path, which is
the shape this campaign has corrected me on repeatedly.

### Verification

`test_credentials` **67 cases**, `test_sealing` 32, `test_oci` 74; the adjacent
set green. All eight guards this round added fail at least one case when
removed.

The boundary inventory is back to baseline on all four gates with **zero**
W6634 entries outstanding — two new stated owners for the completion digest,
one for the attempt-identity comparison with its own witness, and one probe for
the targeted orphan discard.

**One thing the widened filter surfaced and I am naming rather than leaving.**
Six of the 23 standing orphan-owner entries are `sealing.py`'s, from an earlier
round of this Work: `declared_outputs` and `_relative` own boundaries the
derivation cannot attribute to an entry, because their subjects are members of
a list the tracker loses through a helper call. They are inside the
long-standing failure rather than new, and they are still this Work's files.


## Sixth re-review — four [P1]s, and a boundary I had on the wrong side

### [P1] The receipt bound a caller's claim, not a validated envelope

**The correction that matters here is not a member, it is which side of the
boundary I put a duty on.** I wrote that consuming `/output/output.json`
belonged with W6633 "because that Work publishes the document". The reviewer's
answer is exact: W6633 owns the worker that PUBLISHES; this Work's manager owns
VALIDATING before freeze and the receipt over what it validated. Reasoning from
who writes a document to who reads it would have left the envelope permanently
unread by the only party that needs to check it — and I had written the
justification into PROGRESS.md as though it were a boundary rather than a
deferral.

`sealing._completion_envelope` opens the worker's document before anything is
frozen — the order W14251 §7.3 states — and does three things that are three
different questions:

- the SHAPE and its standalone semantics, by **W14251's settled validator**,
  consumed rather than reimplemented. That Work put the completion rules in the
  shipped layer precisely so this manager would not carry a second copy;
- the DIGEST, recomputed over the bytes this manager read;
- and **§12 rule 15**, which needs the input manifest and so cannot live in a
  validator handed one document: one answer per declaration, no extras, no
  omissions, exact `name`/`type`/`path`, and no `missing-optional` answer for a
  declaration the manager marked required.

The `completion_manifest_digest` operand is GONE from `OciAdapter`. An optional
caller-supplied digest is not evidence that validation occurred, and keeping it
would have let the receipt keep saying so.

**A completed freeze with no envelope refuses.** The envelope IS the completion
signal, so a worker that published none has not completed whatever it told the
manager. The other dispositions may have none — those are the endings where a
worker may have died before publishing.

### [P1] Post-engine answer refusals bypassed the lifecycle

The guard stopped at the vector, so the run itself, the reading of its answer
and the ownership of the returned identity all escaped without a lifecycle
decision — and those are precisely the exits where a container may already
exist. I said "every refusing exit" last round and meant "every exit I had
looked at", which is the second time this Work has caught me generalising from
the paths I happened to enumerate.

Everything from the run to the lifecycle record now routes through
`_refused_start`, including a record this manager cannot publish: a container
is running by then, so a delivery nothing can later adopt or name is exactly
the state the settlement exists to report rather than to leak.

### [P1] A proved failed recovery left a record that could never converge

`discard_orphan` removed the volatile root and left the lifecycle record saying
`live`, still naming a root and a container that no longer exist. The next
recovery reads it, finds no runtime, can neither adopt nor reach ordinary
absence — and with an empty candidate list the failure path proves nothing
gone, so the state is unresolved for ever. **An ending that cannot be reached
twice is not an ending.** The record is removed in the same ordered act that
removed what it describes, and its absence is proved like everything else here.

### [P1] Six inventory orphans that I called zero and six in one document

The fairest finding of the four. My evidence said this Work had zero
outstanding entries and then listed six of its own orphan owners; being inside
an older shared failure does not make entries in this Work's files somebody
else's debt, and a durable record must not claim both.

**All six are resolved rather than attributed away**, and the cause was one
habit in two places: iterating the copy a helper returns instead of the
caller's own sequence, which loses the origin the derivation follows.
`declared_outputs` now iterates `outputs`, `collected_result` iterates
`output_names` and sorts afterwards, and the declared path is owned at the site
it arrives rather than inside `_relative`. Six probes came with them. The
standing orphan count went 23 to 17 — the six were mine and they are gone.

### Verification

`tests.manager.test_sealing` **36 cases**, `test_credentials` 69,
`test_oci` 74; the adjacent set 432 with one skip. Ten of the eleven guards
this round added fail at least one case when removed; the eleventh — computing
the envelope digest rather than lifting the verified member — is recorded as a
measured EQUIVALENCE with the reason it is still computed.

The boundary inventory: **zero** W6634 entries unowned, orphaned,
owned-but-unprobed or probed-but-unowned, and this time the number is the whole
number.

The sealing and credential fixtures gained a published worker envelope and a
hex, prefixed Work identity — an identity that could not exist would be refused
before it reached the rule a case aims at, which is the vacuous shape rather
than a passing test.


## Seventh re-review — four [P1]s, and one of them was a rule I wrote wrong

### [P1] Exact replay depended on the transient worker envelope

**This is the fourth time in this module I have been corrected on one rule, and
the third time I have written the inversion of it myself.** Replay sits above
every state read. `/output/output.json` is worker state -- it lives in a tree
the worker owns and which cleanup is entitled to remove -- and I read it
BEFORE consulting the committed receipt. So an exact retry after successful
custody refused, with the settled answer sitting in custody carrying the
envelope digest already bound.

The read moved below the replay. And the envelope came OUT of the replay
binding with it, which is the part worth stating: a changed `output.json` is
not an operand of an already committed operation. The operation was settled
over the envelope this manager validated at the time, and the receipt records
which one that was; the request that replays it does not carry one at all.

**So my own case pinning the opposite is revised**, under the authority the
review recorded. `test_a_replay_under_another_worker_envelope_is_refused`
asserted that a receipt settled over one worker document refuses to replay
under another. It reads well and it is wrong, and it was mine.

### [P1] The completion reader followed a worker-created link

`os.path.isfile` and an ordinary `open` both follow symlinks, so a worker could
leave an `output.json` pointing anywhere on the host and this manager would
read it -- turning a path the CONTRACT fixed into a path the WORKER chose, and
contradicting the linked-output refusal this Work applies to every other byte
it takes.

Opened with `O_NOFOLLOW` now, proved a regular file on the OPENED DESCRIPTOR
rather than on the path -- so nothing can be swapped between the check and the
read -- and read from that same descriptor under the existing bound.

**And covering that rule found one more.** `O_NOFOLLOW` refuses a link and
refuses nothing else a worker can put at that name. A directory opens quite
happily; a named pipe opens and then BLOCKS until somebody writes to it, so a
worker could hang the manager's freeze with one `mkfifo` and the mode check
could never reach it. Measured: the case did not terminate. `O_NONBLOCK` is on
the open, and the case covers both a directory and a pipe.

### [P1] An envelope for another assignment was accepted

Standalone validation proves the reference is well formed and the declaration
comparison proves the answers match -- and two assignments of one Work can
declare identical outputs, so neither says the document is THIS attempt's. A
generation-2 envelope was being bound into generation 1's receipt. The
`assignment_ref` is compared before any custody is touched.

### [P1] Zero-runtime recovery could never converge

`bool(stopped) and all(stopped)` is False for an empty list, so a stale record
whose exact engine query returned nothing reported UNRESOLVED and kept both the
root and the record -- for ever. **That is the same non-convergence the last
round corrected one layer up, arriving through an empty-sequence idiom instead
of through a missing removal.**

A successful query naming no runtime is the engine answering about this exact
attempt: there is nothing to stop, so nothing can hold the mount. `list`
refuses rather than returning empty when it could not ask, so an empty answer
here is an answer.

### Verification

`test_sealing` 40 and `test_credentials` 69, including all four additive
regressions. The adjacent set 436 with one skip. Six guards this round added,
all six measured by removal -- including the two open flags separately, because
they refuse different things.

`stat` is declared in the manager's standard-library set with the reason: the
mode is read on a descriptor, and the ruled-validator rule is about third-party
packages.

## Design checkpoint — current contracts and residual risk, 2026-08-26

Written at the operator's safe boundary, at the direction of the
"Operator-requested design checkpoint" ruling in `FINDING.md`. **This is not an
eighth correction round and no protocol or application code was changed to
produce it.** The reviewer's own packet is
`evidence/design-checkpoint-2026-08-26.md`; this is the implementer's half of
the same instruction — the concise current-contract and residual-risk summary
the ruling asks me for.

### What this component now contracts to do

**Output custody — `worker_manager/sealing.py`.**

1. **Replay is proved before worker state is read.** `sealed_result` proves the
   request-to-receipt binding over `_BOUND` and returns the committed receipt
   without consulting `/output/`. An exact retry after custody succeeded no
   longer depends on a transient worker document still existing.
2. **The completion signal is opened, not resolved.** `O_NOFOLLOW |
   O_NONBLOCK`, then `S_ISREG` on the descriptor, then a bounded read of that
   same descriptor. A worker-selected link, a directory or a FIFO cannot turn
   a fixed path into a host-side read of somewhere else.
3. **The envelope must answer THIS attempt.** The owned `assignment_ref` is
   compared with the manager's assignment before any custody mutation, because
   two assignments of one Work can declare identical outputs and the
   declaration comparison alone cannot tell them apart.
4. **§12 rule 15** — one answer per declaration, exact name/type/path, no
   `missing-optional` for a required declaration.
5. **The receipt is the manager's**, distinct from the worker's envelope, and
   binds the digest of the envelope this manager actually validated. Commit is
   write → fsync → `os.replace`.
6. **Staged artifact content is walked for §13 secrets** before it is retained.

**Credential delivery — `worker_manager/credentials.py`, `oci.py`.**

1. Materialization is **fresh-run and authorized-slot only**, into a volatile
   root at `0700`/`0600` under `/run/baton/credentials`.
2. Delivery is a **fixed read-only bind per slot**, one and only one, and
   `_mounts_disagree` refuses a target that is neither the fixed path nor
   beneath it.
3. Bearers are registered as live secrets so the §13 leak checks see them.
4. **Teardown fails closed**: it is ordered, and it does not report success
   unless container absence and volatile-root absence are both proved.
5. A stale record whose exact engine query names **zero** runtimes is positive
   absence — nothing can hold the mount — so targeted cleanup converges instead
   of looping.

**Upstream integration, revalidated against the current tree.** W19784's
`/input/assignment.json` was approved and implemented after the seventh
correction. It is an **upstream delivery, not an alternate identity source
here**: it gives the worker somewhere to read the identity from, and rule 3
above is unchanged and still compares the envelope's identity with the
manager's own assignment. I re-ran W6634's gates after that Work landed —
`test_sealing` + `test_credentials` **110 green**, adjacent set **446 green,
one skip** — so the seventh-correction contracts still hold on the tree as it
stands today.

### Residual risk, stated as risk rather than as coverage

1. **Restart adoption and broad orphan recovery are fail-closed, not
   certified.** They are exercised against a faked engine seam. Nothing here
   has been run against a real daemon across a real manager restart, and the
   sixth and seventh rounds each found a non-convergence in this area arriving
   by a different route. I would not claim these paths are proved. They belong
   in W6636's lifecycle matrix.
2. **The two systems cross at quiescence and settlement**, which is the
   coupling the checkpoint names. Every success, refusal, retry, cancellation,
   restart and uncertain-engine path exists once per system and again at the
   crossing. That multiplication is why seven rounds each found a real [P1]:
   the surface was still growing faster than the review of it.
3. **Docker mount agreement is asserted from parsed engine output.** The
   adapter refuses on disagreement, but the parse is of a format the engine
   owns. A daemon that changed its inspect shape would be a refusal rather than
   a silent acceptance — fail-closed — but it has not been exercised against
   more than one engine version.
4. **No real credential provider has been used.** Every bearer in these gates
   is minted by an injected capability. The leak checks are real; the provider
   is not.
5. **`compose_input_root` (W19784) has no in-package caller**, and neither does
   its sibling `assignment_workspace`. The launch sequencer that would tie
   allocation, composition and `run_vector` together is unassigned. Whichever
   Work takes it inherits the ordering obligations of both.
6. **The standing baselines are unchanged and were deliberately not touched**
   under this ruling: six long-standing shared boundary-inventory failures, and
   W6633's own open contradiction in `test_worker_image`. Neither is W6634's.

   **Correction, made while writing this.** Running the addendum found the
   worker suites at six failures rather than two, because W19784's reviewer had
   added four additive regressions after I passed that Work — and both findings
   are real and are mine: the worker never recomputes either delivered
   manifest's own digest over its own bytes, and a `compatibility_assignment`
   alias survives delivery because the worker extracts the members it needs
   instead of proving the document is closed. That second one is exactly the
   compatibility alias the W19784 ruling rejected. They are recorded here and
   corrected under W19784, which is with its reviewer; neither is a W6634
   defect, because `sealing.py` already recomputes every digest it reads and
   already validates against a closed definition.

### What I did NOT do

No eighth code iteration; no opportunistic repair of the shared
boundary-inventory baseline; no change to `sealing.py`, `credentials.py` or
`oci.py` beyond the W19784 comment noted above. W6634 was already routed to
`baton.ops` by the reviewer at 2026-08-26T22:48:48Z, so there was no pass for
me to perform — it is queued and unclaimed there now.

**Acted on separately:** the ruling's operational finding that `baton.codex`
could not remove W17110's obsolete dependency on W6634 because a reviewer is
not a resolved `baton.impl` handler. That edge is a coordination fact rather
than an implementation change, and the ruling names the implementer as one of
the two parties who may remove it.
