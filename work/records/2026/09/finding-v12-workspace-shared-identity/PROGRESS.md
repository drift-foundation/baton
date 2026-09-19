# Implementer progress — W194457

Implementer-owned. The decision and the acceptance boundary are FINDING.md's.

## claim194465 — revalidation (PLAN step 1), and what it found

No product or test file was edited under this claim. What follows is the
revalidation PLAN step 1 asks for, recorded so the next claim starts from it.

### The defect site, exactly

`src/baton_v12/worker_manager/workspaces.py:881`, `_provision_line_access`.
Its `visit` appends `(descriptor, fstat)` to `held` for **every** file and
directory it reaches and closes them only in the `finally`, after the whole
preflight *and* the whole `fchown`/`fchmod` pass. So the peak descriptor count
is one per entry plus the root — 18,078 for the measured checkout, against the
manager's soft `RLIMIT_NOFILE` of 1024. The mutation loop that follows is the
permission-only whole-tree pass the owner's decision removes.

Its one production caller is
`src/baton_v12/worker_manager/review_cycles.py:1014`, inside `create_line`'s
`act(connection)` — so the walk runs **inside** the `review-line.create`
transaction, which is why a failure leaves the line `materializing` and
ungranted rather than half-committed. The refusal text the owner quoted is this
function's `except OSError` branch, and it is also where the original errno is
discarded: it reports `type(failure).__name__` and nothing else.

`_prove_line_access` (line 864) is a different thing and is NOT the defect: it
measures the ROOT only — identity pin, group, mode `02775` — and repairs
nothing. `review_cycles.py:1090` and `:2633` call it. It is the shape
creation-time access should leave behind.

### The decision's real cost, which is where the next claim starts

The owner selected a trusted workspace UID/GID shared by the manager and the
worker, with host/container mapping. In this build the two identities are
deliberately different, and that difference is load-bearing in more places than
the workspace module:

- `oci.RESTRICTIONS` pins `--user 65532:65532` (oci.py:181) and
  `custody.py:1672` pins the same pair for the custodian. The primary identity
  is deliberately NOT composed per deployment: oci.py:1158 records that a
  rejected cut composed `--user 65532:<gid>` and that W6632's vector cases and
  W6633's image assert the pinned pair.
- `--group-add <workspace gid>` (W33936, approver ruling M34916) exists
  *because* 65532 is not the manager's uid.
- The credential slot is `0640` rather than `0600` (W52800, approver ruling
  2026-08-31) *because* a manager-owned owner-only file is one uid 65532 can
  `stat` and cannot open.
- `custody.normalize_directory` grants the workspace GROUP rwx instead of
  chowning (W39358) *because* the manager does not own what uid 65532 created.
- `workspaces.py:2316` records a measured `EPERM` from exactly that asymmetry.

Nineteen test files assert `65532`.

None of this contradicts the ruling — FINDING.md says the numeric identities and
the engine mapping are implementation choices to revalidate — but it is the
actual size of "shared UID", and it is why this was not landed in a hurry. The
three rulings above were each written to work AROUND the split identity; under
a shared one each needs re-deciding on its own terms rather than being left to
mean something new by accident.

### What the next claim should do first

1. Decide the shared identity's shape: the manager's own euid/egid carried into
   the container, or a deployment-configured pair both sides map to. Either way
   it belongs beside `WorkspaceGroup` as a minted capability, obtained from the
   deployment's record — not an integer a caller supplies.
2. Replace the `create_line` call with creation-time access: the parent
   workspace root is already `02770`/setgid, so a materialized line needs its
   ROOT put in the configured group at `02775` and nothing else. `_prove_line_access`
   is then the whole admission check, and `_provision_line_access` goes.
3. Re-decide, explicitly, each of the five accepted decisions listed above.
4. The tests the acceptance names: a tree larger than 1,024 entries with the
   peak descriptor count measured, an operation count showing no permission
   walk proportional to unrelated entries, a worker-created `0600`/`0700` file
   the manager consumes, and a repeated preparation.

### Preserved, unchanged

The failed v12 Work `a2b0d14b-W1` and its attempt
`attempt-7a06eb4497395f38e6d45044ec437f9c40e93ba47fd12fc10655958432c6b072`
were not touched: no store was opened, no claim released, no line removed, no
resubmission. No installed runtime was updated. No provider, engine, model or
network was reached, and no version-control mutation was performed.

## claim194532 — the pass is gone, and half the identity is carried

The permission-only whole-tree pass is removed rather than made cheaper, which
is what the ruling asked for. `establish_line_access` does the ROOT's group and
mode `02775` and nothing else — two acts whatever the checkout holds, counted in
`workspaces.PERMISSION_ACTS` so the check asserts the SHAPE. "It got faster"
would have been a different and weaker claim, and it is not the one made here.

`prove_line_integrity` keeps everything that used to ride along with the removed
pass — special files, hardlinked regular files, the entry, byte and depth
ceilings, and that the tree belongs to this deployment's execution identity —
and performs no permission act at all. It is bounded by DEPTH, as is
`_prove_line_consumable`, which the reviewer found exhausting descriptors too:
each child is closed as soon as its subtree is proved, so `held` is the open
path rather than the whole tree. The no-follow open at every component, the root
pin, the counted-not-followed symlink and the special-file refusal are untouched.

The reviewer's own reproducer says it better than I can: provision is gone, and
consume now opens 1,101 entries at a peak of **two** tracked descriptors and
returns, where it measured EMFILE at 1,021.

The identity is a minted capability, `WorkspaceIdentity`, with the shape
`WorkspaceGroup` already has and for the same reason — a pair a caller can
construct is a pair a caller chose. Its uid is this manager's own, because that
is the one trustworthy statement available here; its gid is the configured
workspace group; root is refused.

**What I did not do, and it matters.** The execution vectors still pin
`--user 65532:65532`. So the manager side is now consistent — it materializes,
proves and grants as one identity and walks nothing — while the WORKER still
runs as somebody else. The descriptor exhaustion this Work was raised for is
fixed. The owner-only consumption case the FINDING also names is not: a worker
still creates 0600 entries this manager cannot open, and
`_prove_line_consumable` still refuses them honestly rather than repairing them.
That half needs the four dependent decisions re-decided on their own terms — the
supplementary group, the 0640 credential slot, custody's group grant, `/input`
readability — rather than 65532 replaced everywhere, which the review warns
against. The exact remaining scope is in EVIDENCE-194532.json.

675 checks pass across the five affected suites, 15 new or rewritten. Eight
reversal probes, all valid kills. Four proved nothing first, and two of those
were gaps in my own coverage rather than wrong tokens: I bounded the consumption
walk and then only checked it against fixtures too small to notice, and I
pointed the create_line probe at a case that looks at modes, which stay 0600
whether the integrity walk runs or not.

## claim194622 — the guard I removed without noticing

Finding 1 was a real regression and it was mine. The pass I deleted did two
things, and I only saw one of them: it applied permissions per entry, and it
re-`fstat`ed every retained descriptor afterwards to check that nothing had
changed between the look and the grant. Closing each child to bound the
descriptors threw the second one away with the first, and the reviewer's
interleaving — an outside hardlink added to an already-checked file while the
next sibling is opened — walked straight through.

The fingerprints are kept instead of the descriptors now: one pass records
`(dev, ino, uid, nlink, mode)` per path, a second bounded pass re-opens each
entry no-follow and compares, and a directory's child count is compared too. A
replaced entry fails on identity, a hardlinked or chmoded one on the rest, and
an entry that disappeared on the count. The peak is still one descriptor per
level in both passes, so nothing proportional to entries comes back.

Writing the race checks taught me something I should have known: `os.scandir`
answers in directory order, not creation order. My first interleaving hard-coded
which sibling to act on, fired before that entry had been fingerprinted, and
proved nothing. The helper observes which child is opened first and acts on that
one.

Finding 3 was fair too. I asserted the product's own counter, which would miss a
chmod added beside it — and my M3 probe incremented that same counter instead of
restoring a syscall, so its kill looked stronger than it was. The check wraps
`os.fchown`, `os.fchmod`, `os.chown` and `os.chmod` and counts what the kernel is
actually asked; the new probe inserts a real per-file `fchmod` and increments
nothing.

Finding 4: I ran the reviewer's script, whose output path is fixed, and
overwrote a digest-bound baseline. This claim writes only claim-specific names,
and I will not run a script whose output path I do not own.

Finding 2 is still open and still blocking, and the review sharpened why: the
partial combination is worse than one-sided. Removing the normalization without
changing launch leaves MANAGER-created restrictive contents unreachable by the
old worker identity, not only worker-created ones unreachable by the manager. It
should not be deployed as a pair. The remaining scope is in EVIDENCE-194622.json.

680 checks pass across the five affected suites, 6 new. Five reversal probes,
all valid kills; N4 proved nothing first and earned a case — with the child
count gone, an entry that APPEARS is still caught by its missing fingerprint,
and only an entry that GOES needs the count.

## claim194683 — the identity reaches the vectors

`identity_for(group)` derives the shared identity behind the deployment's
already-minted `WorkspaceGroup`: the gid is the group's, the uid is
`os.geteuid()`. Both vectors already receive that capability, so **nothing grew
a uid operand a caller could choose** — which is the property the pinned
`65532:65532` was protecting, and it is the one I kept. `run_vector` substitutes
`--user` at the RESTRICTIONS table, exactly where `--network` already is;
`custody_vector` substitutes the same pair, because a custodian that is not the
owner of the worker's objects cannot `chmod` them. Consent keeps the pinned pair
and is still refused a group.

A probe taught me something about that posture condition: a consent start
carries no workspace group at all, so dropping the condition asks
`identity_for(None)` and the consent vector stops composing entirely. It is what
keeps consent working, not merely what keeps its uid pinned.

`supported_identity_mapping` asks the question the review insisted on — equal
REQUESTED numbers are not proof. `test_worker_entry_engine` measured this host
relabelling a container-created file to uid 65534, so the function asks of an
observation and refuses an unmeasured mapping with its own sentence. **It is not
yet wired to a live observation**, and I am saying that plainly rather than
letting the existence of the function imply otherwise: nothing calls it in the
launch path, so a remapping engine is not refused in production today.

The supplementary group was revalidated rather than dropped. Under the shared
identity the primary gid is already the workspace group, so `--group-add` is
redundant — and it is the grant that survives if a deployment ever runs the
manager under another primary group, which is the case it was written for.

Superseded expectations updated where they are about THIS deployment's execution
identity: the oci restriction sweeps and launch cases, the custodian, and the
real Docker composition. Not touched: the credential-engine, worker-image and
entry-engine assertions, which are about the image's own user and the transport.
The review warned against replacing every 65532 and I did not.

Still not done, and the candidate is still not deployable: the live mapping
observation, a private writable HOME/cache, restrictive-file checks in both
directions, simulated mapping fixtures, the three remaining re-decisions (the
0640 credential slot, custody normalization, `/input` readability), and the
written compatibility and update/recovery instructions.

An operational finding, measured rather than assumed:
`tests/manager/test_dependencies.py` has **56 pre-existing failures** in its
declared-operand sweep. My own addition briefly made it 57 — the new parameter
was `observed`, which that vocabulary does not declare; it is `observed_identity`
now, which it does, so this candidate adds none.

830 checks pass across seven suites, 7 new. Five reversal probes, all valid
kills; P2 and P5 proved nothing first, and P5 twice.

## claim194767 — the observation exists; the wiring does not, and I say why

`oci.observe_runtime_identity` runs ONE bounded probe of the deployment's own
image — same restrictions, no network, read-only root, one writable mount of a
directory this manager made — and reports the HOST-side owner of the file that
runtime creates, then removes the directory. A failed run, an unreachable engine
and a run that leaves no file all answer `None`, which
`supported_identity_mapping` refuses as an unmeasured mapping in its own words.
The answer is keyed by (engine, image, uid, gid), so any change invalidates
reuse rather than carrying a measurement about something else.

My own compliant-engine case caught a real defect while I wrote it: `EnginePort`
answers a **document**, not a tuple, and my first cut unpacked it — binding the
keys — so a compliant engine reported an unmeasured mapping.

The remedy sentence is corrected. The reviewer is right that "run the manager
under the identity the mapping produces" is not a general fix: the requested
container identity is derived from that account, so moving it moves both sides
of the comparison at once. The refusal now names running the engine without an
id mapping and re-checking, and says the account change is not a general fix.

**The wiring is not in place, and this is the honest reason.** I wired it into
`worker_preflight`, ran it, and roughly a hundred existing cases failed —
correctly. Every deployment fixture in this tree stands the engine in with its
own ad-hoc object that answers a status for any argv and creates no file, so the
probe reports an unmeasured mapping and preflight refuses. Those failures are
about the fixtures, not the product. I would not weaken the guard to fit them:
assuming compliance is the exact thing this correction exists to avoid. So the
call sits at its exact line as a comment explaining where it goes and what has
to happen first, and teaching those stand-ins to model the probe is the next
claim's first task.

730 checks pass across six suites, 6 new. Five reversal probes, all valid kills;
Q1, Q2 and Q4 proved nothing first, all three because the token named the wrong
outcome — including `assertFalse` printing "True is not false", which is the
fourth operand-order slip of this kind I have now recorded.

## claim194830 — five defects in my own probe, found by simulation

Every one of these was real, and none needed a container to find.

The probe directory was a fixed `place/.identity-probe` removed with
`ignore_errors=True` — so it would delete whatever a previous attempt or
anybody else had left at that name, having proved nothing about owning it. It
is `mkdtemp` now, and removal pins the directory's `(dev, ino)` at creation and
refuses a name that has since become something else.

The cache is gone entirely. Its key named neither the port nor the place, so a
second, unavailable engine was answered "supported" with zero calls to it. For
a question whose wrong answer is "you may launch", conservative is the only
safe direction.

`os.stat` follows a symlink, so a runtime that wrote one pointing at a
manager-owned file outside the mount had that file's ownership read back as its
own. The output is opened `O_NOFOLLOW` and must be a regular file with one
link — which also refuses a hardlink to something outside.

A client-side timeout stops waiting, not the engine. The helper is removed by
name on every path, a reclamation that fails makes the observation unmeasured
instead of being swallowed, and an unremovable probe directory is refused.

And the remapped fixture patched `stat` inside the producer, which proved
nothing about a remapped *observation*; it replaces what the host reports for
the produced file, and says SIMULATED in its own docstring.

My new class also hard-coded `/var/tmp`, which is read-only on the reviewer's
host and cost them 13 fixture errors. It honours the configured root and
otherwise takes the interpreter's default; I ran it both ways.

Two probes proved nothing first and earned two cases: the uniqueness check
compared a directory *listing*, which a fixed name that is created and removed
leaves unchanged. What a fixed name actually costs is somebody else's
directory, and what an unpinned removal costs is a replaced one.

The wiring is still not in place, for the same fixture reason as last claim,
and the rest of the original scope — private HOME/cache, restrictive files both
directions, three re-decisions, written instructions — is still open.

736 checks pass across six suites, 8 new. Six reversal probes, all valid kills.

## claim194882 — cleanup that proves what it is about to destroy

Three more of mine, and the pattern in all three is the same: I checked
something and then acted on a *different* thing.

An engine reports failure with a **status**, not an exception, and I discarded
the removal document — so run=0 with rm=1 answered a matching identity while
the helper persisted. There are three outcomes now, not two: verified absence
(the inspection finds no object of that name, which is what `--rm` ordinarily
leaves), a removal that reported zero, and anything else — which makes the
observation unmeasured.

A unique **name** is not ownership. The container carries a nonce this
invocation minted, as a label, and nothing is removed whose label is not that
nonce. The reviewer's case — `run` failing 125 on a name conflict, then
`rm --force` deleting somebody else's object — now inspects, sees another
nonce, removes nothing, and names what it found.

And the directory: an `lstat` pin followed by a path-based `rmtree` resolves
the name a second time, so a replacement in between was what got deleted while
the owned directory survived elsewhere. Every unlink goes through the
descriptor opened when the directory was created; the pin is compared on *that*
descriptor; the final `rmdir` is relative to a pinned parent.

What cannot be reclaimed is now **named** rather than abandoned: `UNRESOLVED`
collects the engine object and why, because a resource nobody can name is one
nobody can clean up.

The engine fixture models statuses rather than exceptions now, which is the
shape the review found missing — my `removes=False` raised, and a real engine
would simply have reported 1.

S5 proved nothing because it had **no baseline**: I had rewritten the class and
the case it pointed at no longer existed, so it proved nothing about anything.
The descriptor pin has its own case now. S4's token was backwards again.

739 checks pass across six suites, 5 new. Six reversal probes, all valid kills.
Still not wired, still not deployable, and the rest of the original scope is
unchanged.

## claim194939 — the whole outcome, not one error shape at a time

The reviewer put it in a table because I kept correcting one failure and
accepting another. Four things must hold now and any unknown refuses: the run
succeeded, the observation is a fresh regular file with one link read
`O_NOFOLLOW`, the engine is settled, and the filesystem cleanup this call owns
finished.

**Absence is established, not inferred.** I read a non-zero `inspect` as "no
such object" — and a daemon this manager cannot reach answers non-zero too, so
an unreachable engine was reported clean and the observation accepted. The
question is a *listing* now: a command that succeeds and names nothing is
absence; a command that fails at all, or raises, is unknown.

**Removal is by the immutable ID.** Inspecting a name and then removing that
name is two lookups, and the object behind a name can be replaced in between —
which deleted an unrelated container in the reviewer's simulation.

**The cleanup outcome propagates.** A failed unlink appended to `UNRESOLVED`
and the observation was accepted anyway: a diagnostic nobody read.

And a probe found that the run term in my own matrix carried nothing — a
failing run that wrote nothing is refused by the observation term regardless.
The observation is taken whatever the status now, because a container can write
its file and *then* exit non-zero, and the matrix is where that is decided. The
case uses exactly that shape.

743 checks pass across six suites, 9 new. Seven reversal probes, all valid
kills. Still not wired, still not deployable; the rest of the original scope is
unchanged.

## claim195007 — a prefix is a name, not an identity

Two residuals, both mine, both the same mistake in different clothes: I treated
something that identifies *approximately* as though it identified exactly.

`{{.ID}}` defaults to a **twelve-character prefix**. So after all the work of
authenticating an object and removing it by its id rather than its name, the
inspection and the removal were still naming a prefix — and a replacement
sharing it was inspected and removed in the reviewer's simulation. The listing
asks `--no-trunc`, and anything that is not 64 lowercase hex characters is
refused and named rather than used.

And settlement is owed by the **attempt**, not by the reading: an `OSError` from
the ownership read escaped past the reclamation entirely, so a container this
call started was never asked about and never named. It is in a `finally` now.

745 checks pass across six suites, 2 new. Six reversal probes, all valid kills,
and none proved nothing this time.

Still not wired, still not deployable; the rest of the original scope —
preflight wiring and its fixtures, private HOME/cache, both-direction
restrictive files, three re-decisions and the written instructions — is
unchanged.

## claim195045 — I wired it, and it is not a fixture problem

I put the call in `worker_preflight`, exactly where the review and I have both
said it belongs, and ran the suite. It **hung**, and the traceback says why:
the probe reaches the engine through `EnginePort(effective_engine_run(engine_run))`,
and `effective_engine_run(None)` is `_engine_run` — `subprocess.run` on the real
argv. So a preflight that does not inject an engine attempts a **real
`docker run`**.

That supersedes what I said twice before. The fixtures are a *consequence*; the
cause is that the probe is a live engine round-trip sitting in a function whose
engine defaults to the live runner and which is reached by callers that are not
starting anything — `operations_from` composes it, and the composed judgment
workers do the same.

The wiring is out, the comment naming the exact line is back, and the six
affected suites are green. I checked for real side effects afterwards: no
container named `baton-identity*` and no `.identity-probe-*` directory anywhere.
Whether a `docker` invocation actually started during the killed run is not
something I can prove after the fact, and I am not going to claim it did not.

**The design that follows.** The mapping becomes a deployment-recorded fact,
exactly as the workspace group already is: `configure_identity_mapping` records
a proved observation with the journal-and-projection cross-check
`configured_workspace_group` uses, and preflight only *reads* it — an early,
enforced refusal before any Job execution effect, with no engine round-trip in
preflight at all. The observation is taken once, by the deployment, where a real
engine is already in use. The fixtures then record one fact in the shared setUps
that already configure the workspace group, instead of dozens of ad-hoc engine
stand-ins learning to model a container run.

745 checks pass; nothing was changed by this claim, so there is nothing to probe.

## claim195084 — the probe is gone, and the candidate is complete

The owner ruled at 14:28Z, mid-claim, and the ruling is the good kind: stop
trying to prove the arrangement and trust the configured one. So this claim is
mostly a **removal**, and what is left after it is smaller than what the last
five claims were correcting.

### What went

`oci.observe_runtime_identity` and everything under it —
`_reclaim_probe`, `_probe_owner`, `_remove_probe`, `UNRESOLVED`,
`_unresolved`, `_FULL_ID` and the four `_PROBE_*` constants: 264 lines. With it
went the whole consumer side in `workspaces` — `ExecutionIdentityMapping`,
`_ACTIVE_IDENTITY`, `activate_execution_identity`,
`require_execution_identity`, `proved_execution_identity`,
`forget_execution_identity`, `_mapping_place`, `_mapping_engine`,
`_mapping_digest` and `supported_identity_mapping` — the gate at the top of
`OciAdapter.start`, `single_worker.activate_execution_identity`, and the
activation seam the test tree stood up for 119 fixtures that were never about
identity. Two imports each Work had added for the probe and nobody else used
(`shutil` in `oci`, `oci as oci_module` in `single_worker`) went with them.

A case asserts the ABSENCE of all twelve names rather than trusting this
paragraph, because "unwired" and "gone" read the same in a review.

**What stayed, deliberately: the live-engine guard in `tests/__init__.py`.**
It was installed because of the probe, but it is not about the probe — it is
one environment lookup that turns an unintended `docker run` from a hang with
no traceback into a failure with one. A tree that could hang once can hang for
a reason nobody has thought of yet.

### What replaces it, and it is three things rather than one

**The arrangement, written down.** `workspaces.SUPPORTED_IDENTITY_MAPPING` and
the paragraph above it say what an operator must configure — a non-root manager
account in the configured workspace group, an engine with no id mapping for
this deployment — and say what is NOT supported and why changing which account
the manager runs as is not a general fix. That prose was previously a refusal
message that only existed if a probe ran.

**The cheap declared check.** `declared_identity_mapping(identity, declared)`
compares the `uid:gid` string a vector is about to hand the engine against the
minted capability. It reaches no engine and no filesystem — a case proves that
by making `os.open` and `os.stat` raise — and it is called from both places the
pair is spelled: `oci.run_vector` and `custody._custody_vector`. It is worth
having precisely because it catches the failure a change to THIS module can
introduce: two spellings of one identity that stop agreeing.

**The access failure, made actionable.** `_access_failure` is the other half of
trusting configuration: if the arrangement is wrong, the first symptom is a
real `EACCES`/`EPERM` on a real path, and that refusal is the operator's whole
diagnostic. It names the operation, the path, the exception, the errno NAME and
the kernel's own sentence, and for a permission errno it points at the engine's
id mapping — while saying "before treating the entry itself as the fault",
because a `0000` file the worker made is `EACCES` too and this claims no cause
it did not measure. It replaced four refusals that said `OSError` and dropped
the number; the one in `establish_line_access` is the same shape as the one
that lost this Work's own incident errno. A case proves an `ENOSPC` gets NO
mapping hint, because sending an operator to read engine settings about a full
disk is the failure mode of a helpful sentence.

Also cleaned up while I was there: the custodian's identity was being minted by
constructing `WorkspaceIdentity` directly with `_MINT` and a dead
`del WorkspaceGroup`. It goes through `identity_for` now, from the same durable
read the mount and the group already come from.

### The two remaining scope items, and one of them needed no code

**Owner-only `0600`/`0700`, both directions.** The worker→manager direction is
the one this Work exists for and it is now a case: a `0700` directory with a
`0600` file inside it, created after materialization, is consumed with nothing
repaired — same modes before and after, `PERMISSION_ACTS` unchanged. Before the
shared identity that file was one the manager could `stat` and could not open,
which is why the old code walked the tree.

The manager→worker direction is asserted as the fact the worker's access
actually depends on: the entries are owned by the very uid the execution vector
declares. It cannot be run as another uid here — that needs privilege this
suite does not have and an engine the owner ruled out starting — and the case
SAYS so rather than implying a measurement it did not take.

**Private HOME/cache: preserved, and it needed no product change.** I expected
this to need an `--env HOME` and a tmpfs, because the images own
`/home/nonroot` at 65532 and a uid with no passwd entry gets `HOME=/` on a
read-only rootfs. It does not: `claude_agent._scratch` makes its home with
`tempfile.mkdtemp` under the adapter's `/tmp` tmpfs at mode `0700`, and
`_child_environments` composes `HOME`, `TMPDIR`, `XDG_CACHE_HOME` and
`PYTHONPYCACHEPREFIX` for its children member by member. A tmpfs is
world-writable and sticky, so that home is private and writable for ANY uid the
vector declares, and nothing reads the ambient `HOME`. The case asserts the
half the adapter owns — both bounded scratch mounts still composed, with their
sizes and `noexec,nosuid,nodev`, under the shared identity, with `--read-only`
still on. **No `--env` was added**, so the retired `BATON_WORKER_*` transport
stays retired and `test_lifecycle_composition`'s `assertNotIn("--env", run)`
still holds unchanged.

### The compatibility conclusions, which is the third re-decision item

The owner asked for the actual conclusion rather than an approval gate around
each historical decision. All four are **compatible and unchanged**, and all
four are now REDUNDANT rather than wrong — which is a different sentence and is
the one that matters, because each is the grant that survives if a deployment
ever runs the manager under a different primary group.

- **`--group-add <workspace gid>` (W33936, ruling M34916).** Kept. Under the
  shared identity the PRIMARY gid is already the workspace group, so the add is
  redundant today.
- **The `0640` credential slot (W52800, ruling 2026-08-31).** Kept, and this is
  the one I looked hardest at. `0600` would now suffice, so the group bits are
  wider than necessary — but the ruling's argument has two halves and the
  second one still bounds the exposure: the root above the slot stays
  manager-owned at `0700`, so host members of that group cannot traverse to the
  bearer. Narrowing it to `0600` is a safe follow-on and is NOT this Work: it
  re-opens an approver ruling, and the owner has just told me to keep this
  bounded and converging.
- **`custody.normalize_directory` granting the group rather than chowning
  (W39358).** Kept and still correct. Under the shared identity the custodian
  IS the owner, so a `chown` would now be possible — and granting the group is
  still the least-privilege act that achieves the same thing.
- **World-readable `/input` (W33935).** Unchanged. It is evidence rather than a
  bearer and it is mounted read-only; the identity change neither widens nor
  narrows it.
- Noted rather than decided: `claude_agent`'s per-command `safe.directory`
  overrides exist because the worker was not the owner of the line. Under the
  shared identity Git's dubious-ownership check no longer fires, so they are
  redundant too. Left alone — they write no configuration file and outlive
  nothing.

### What was NOT written, on the owner's instruction

No installed-runtime update procedure and no failed-attempt recovery
instructions. `OWNER-VERIFICATION-CADENCE-20260917.md` supersedes that scope:
after acceptance a fresh instance is built at
`/home/sl/baton-v12-instance-<UTC-ISO-timestamp>`, the old one is preserved as
diagnostic evidence, and the first Job's task is submitted afresh. Building
recovery tooling for that failed Job is explicitly out of scope. Recording this
so the next review does not ask for it a twelfth time.

### Verification, at the cadence the owner set

Short first, then broadened once — because this IS the complete candidate,
which is the condition `OWNER-VERIFICATION-CADENCE-20260917.md` names for
broadening.

- `tests.manager.test_workspaces` alone after each correction: 126 → 129 checks,
  0.63–0.65s. That is the failing-reproduction-plus-nearest-neighbour set.
- Then the adjacent pairs actually touched: `test_oci` + `test_single_worker`
  (282, 9.6s), `test_review_cycles` + `test_custody` (283, 4.9s),
  `test_lifecycle_composition` + `test_launch` (69, 5.0s).
- Complete candidate, once: **763 checks across seven suites pass, 20.131s by
  unittest, 20.410025954s measured wall.** 1 skip (the real-engine lifecycle
  case, which needs Docker).

Two existing checks changed, both because the message they assert got strictly
better, and both recorded exactly: `test_a_failure_while_establishing_NAMES_its_errno`
and `test_review_cycles.test_a_failure_while_establishing_keeps_materializing_and_retry_finishes`
asserted the literal `errno 1`, and now assert `EPERM`, the kernel's sentence
and the mapping hint. Seven checks are new.

**One measurement I am reporting rather than claiming.** `tests.manager.test_boundary_inventory`
fails 25 checks against this candidate. At `HEAD` — without any of this Work —
the same suite fails 129 and errors 8, so it is drifting independently of this
change; and none of the 25 names a symbol this claim added or removed (they are
`OciAdapter.observe`, `OciAdapter.destroy*`, `canonical_source`,
`compose_input_root`, `_configured_gid` and the declared-operand tables). What I
could NOT do is establish a pre-claim CANDIDATE baseline: the pre-edit bytes of
the seven files were not preserved before I edited them, so "this claim did not
change that number" is reasoned from the failure names rather than measured.
This is the same family as the 56 pre-existing `test_dependencies` failures
already recorded in FINDING.

### Preserved untouched

v12 Work `a2b0d14b-W1` and attempt
`attempt-7a06eb4497395f38e6d45044ec437f9c40e93ba47fd12fc10655958432c6b072`. No
v12 store opened, no claim released, no partial line removed, no resubmission,
no installed runtime updated, no production retry. No provider, engine, model,
network or version-control mutation. No container was started by anything in
this claim.

## Claim 195725 — the two bounded corrections of review 195685

Two findings came back, both confirmed with a reproduction I could run before
changing anything, and both real. The product change is confined to one
function, `workspaces.prove_line_integrity`. Nothing else in the candidate
moved: nine of the eleven paths the reviewer bound still carry the hashes they
verified.

### P1 — a checked regular file could become a symlink and still be granted

The second pass skipped a symlink **before** it compared anything. So an entry
the first pass had fingerprinted as a regular file, replaced by a symlink while
a sibling was being opened, had nothing to fail against: `visit` never saw it,
its directory's entry count was unchanged, and `establish_line_access` then
granted the root `02775` on a tree only the first pass had proved. The
historical permission walk refused that exact interleaving, so this was a
regression in the invariant the grant rests on — not a missing guarantee about
arbitrary writers, which is not what anything here claims.

The correction is that **every entry the walk observes is fingerprinted**,
including the ones it never opens. That is what `account` now is, shared by
`visit` and the symlink branch. `st_mode` carries the type, so the transition
mismatches in either direction, and a link that simply stays put matches
itself, is still counted once and is still never followed.

There is a second window the fingerprints alone do not cover: an entry can
become a symlink between `entry.stat` and `os.open` **within** one pass, and
`O_NOFOLLOW` then raises `ELOOP`. That is refused as a change rather than
reported as an access failure — sending an operator to read engine id-mapping
settings because the tree moved under the walk would be exactly the wrong
answer.

Honestly about the reverse direction: a symlink that became a regular file was
**already** refused before this correction, but as "an entry appeared while it
was proved", because an unrecorded link has no fingerprint at all. A reversal
probe showed that. What is new is that it is now named as the change it is. The
case says so rather than implying a hole that was not there.

### P2 — an integrity access failure named neither the operation nor the entry

Two generic `except OSError` handlers turned every traversal failure into

> the development line cannot be proved: PermissionError (errno 13); nothing was changed

This is the first preparation path `create_line` takes, so that sentence was
the operator's whole diagnostic for one unreadable entry somewhere in an
18,078-entry checkout. It is also the same shape that lost this Work's own
incident errno one function further along, which is why the review is right to
call it the same defect rather than a cosmetic one.

Every boundary that actually touches the filesystem now reports through
`_access_failure`: the root open, the root `fstat`, an entry `stat`, an entry
open, an entry `fstat` and directory enumeration. **The relative entry goes in
the rendered slot and the line root in the sentence after it** — `name_value`
renders a bounded prefix, and an absolute checkout path spends all of it before
reaching the name that failed; the first cut of this put the joined path in the
slot and printed `'/tmp/…/block…`, which is worse than useless. One backstop
handler remains so an unforeseen `OSError` cannot reach a caller bare.

No cause is inferred. The `EACCES`/`EPERM` hint still ends with "before
treating the entry itself as the fault", and a case proves an `ENOSPC` while
walking gets no mapping hint at all.

### Verification — the cadence, not a sweep

The reviewer said explicitly that no broad rerun was needed to begin, and the
owner cadence says the same, so: reproduce, then the smallest adjacent set.

- `probes-195725.py`, the failing pair, run before and after: file-to-symlink
  granted `02775` before and refuses with the root left `0700` after; the
  unreadable entry's refusal gains the operation, the entry name and `EACCES`.
  The unchanged-tree control and the stable-symlink control pass both times.
- `InitialStableLineAccess` — **24 checks, 0.205s.**
- `test_workspaces` + `test_review_cycles`, the suite and its one production
  caller — **298 checks, 2.309s unittest, 2.503s wall.**
- The reviewer's own 195685 selection, now 71 with the seven new cases —
  **71 checks, 0.504s unittest, 0.703s wall.**
- Two reversal probes, in a scratch copy of `src/` that was removed afterwards:
  restoring the symlink skip makes the new P1 case raise nothing at all;
  restoring the two generic handlers fails all four new diagnostic cases.

Seven checks are new. **No existing check was changed or removed.** The
763-check seven-suite run from claim 195084 is reused rather than re-measured:
only `workspaces.py` and `test_workspaces.py` have changed since it, and the
product change is confined to one function whose only production caller is in
the 298 above. `test_boundary_inventory` was not re-run; its reported failures
and their stated baseline limits stand exactly as recorded.

### Preserved untouched

v12 Work `a2b0d14b-W1` and attempt
`attempt-7a06eb4497395f38e6d45044ec437f9c40e93ba47fd12fc10655958432c6b072`. No
v12 store opened, no partial line removed, no resubmission, no installed
runtime updated, no production retry. No container, provider, engine, model,
network or version-control mutation. The candidate diff carries no whitespace
defect.
