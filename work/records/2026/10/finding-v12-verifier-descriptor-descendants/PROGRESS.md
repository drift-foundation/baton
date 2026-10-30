# Implementer progress

## 2026-10-18T19:41:35.541124+00:00 — baton.codxpc claim325806

Preparation incomplete at concrete mechanism boundary; preparation-325806/CHECKPOINT.md
records exact remaining operation and two candidate designs, neither asserted safe.
Read detail325805, claimed325806, complete work-events and both thread messages
through325733, full FINDING/PLAN. PROGRESS absent ENOENT on first read; no historical
implementer record inferred. Source revalidated at9debba18, no source edits.

Inert mechanism probe0.042094075s: self-fd descendant failure; holder-fd survives
closure and rename but exact nested validator rejects and holder closure invalidates
path; realpath fallback redirects to candidate surrogate. All probe processes
awaited and marker tree cleaned. No product tests, provider/engine, credentials,
Git mutation or runtime change. Missing supported operation: stable object-bound
canonical verifier roots with whole-verifier-tree lifetime. Current policy offers
no worker mount privilege or distinct UID boundary. Recommend reviewing manager
mount-root delivery scope versus proved holder-fd/validator/lifetime composition;
no runnable packet or launch selected. Return through baton.bug as required, not
a product acceptance or permission gate. Preserve W321528/W321776 ownership and
real graph unchanged.

Cumulative evidence: prior W321528186 tests7.688s complete (8.220848 wall),
descriptor reproduction7.145s (7.671801 wall), initial incomplete reviewer view
0.782s (1.314968 wall). These are inherited observations, not reruns or acceptance
of a correction. Earlier research probe duration unknown; this episode adds
0.042094075s inert mechanism work,0 product verification. No historical total
manufactured or reset. Manifest SHA256 08499aa8d1ff3583ca3b62b14b5747adb404c7baaa2723a2d032671192b71c04.


## 2026-10-18T19:47:47.734366+00:00 — baton.codxpc claim325842

Read detail325841, standalone claim325842, full new events through325842 and both
thread messages through325733; current FINDING/PLAN/latest review19:43:03. Direction
now manager-created mount roots; previous mechanism-choice checkpoint superseded
by reviewer selection, evidence preserved. Prepared preparation-325842 at actual
current committed2aa8ca56.112 runtime resources and3 supervisor helpers pinned.

Concrete authoring OPERATOR/TASK plus proposed kernel proof, immutable-parent roots,
explicit private identity/modes, new-profile compatibility and unchanged aggregate
80MiB scratch/96MiB including log decoy. Layout reference positive and10 negatives
pass; not product or kernel proof. Separate bounded one-object non-provider engine
procedure includes detached descendant and exact cleanup; scripts parsed only.
Stage/bootstrap/bind and8 artifact/task checks pass; inert prompt7267 bytes passes.
No product change/test, Job/provider/engine, credential read or Git mutation.
W321528 retained bytes and W321776 scope preserved; overlap coordination required
before execution, no reverse graph gates. Old authoring image formal environment
limitation explicit; manual retained collection and independent acceptance remain.

Measured prep {'stage': 0.12604478399953223, 'bootstrap': 0.5932287970008474, 'bind': 0.36401481100074307};
layout0.000100536s, argv0.000768398s, product verification0. Prior probe0.042094075s
and reviewer0.042847596s plus all inherited timings above remain cumulative.
Historical aggregate unknown. Return concrete packet for independent review, then
separate authoring selection and later corrected-image kernel proof selection.
Manifest SHA256 6047f122504adbd3ac198cdd05fda86ca712f649b37e2c5853920cdc30c0d38f.


## 2026-10-18T19:52:46.626854+00:00 — baton.codxpc claim325908

Read detail325907, claimed325908, new complete events through325908 and all thread
messages through325733; current FINDING/PLAN/review19:49:22. Preserved325842 and
reviewer failure evidence unchanged. New preparation325908 corrects only the proof
runner/receipt/identity/deadlines and rebinds authoring packet to current committed
14e52d80679de5e844f72324df632da5e01cf393 (pinned product source unchanged).

Exclusive durable reservation, create intent and acquired ID saved before subsequent
engine operations; cleanup errors and uncertain inspect responses retain state.
Explicit reviewed selection binds image, UID/GID, layout/payload/runner; no ambient
identity. Internal120s deadline/40s cleanup reserve and20s receipt window, each call
bounded by remaining phase time. No-retry applies even to partial receipts.
Mocked engine/clock verification:5 methods,16 execution scenarios and6 selection
negatives passed. No Docker/provider or sleep. Kernel payload unexecuted, mount
design and unproved kernel/capacity limits unchanged. Source ownership and graph
unchanged; W321528/W321776 overlap coordination still required before execution.

New stage/bootstrap/bind and8 generated artifact checks pass; prompt7267-byte inert
exec passes. No actual Job/attempt, product source/test changes or Git mutation.
First mock run0.024s reported; final mock 0.02152002100046957s. Preparation {'stage': 0.12569757799974468, 'bootstrap': 0.5877486640001734, 'bind': 0.3509512040000118};
argv0.001012571s. Product verification0; inherited timings above preserved, no
aggregate total invented/reset. Return revised packet for independent review.
Manifest SHA256 34f80cd19db542f479545285555a8b5844260e9729c33e1c2fe13018c73414fb.

## claim371040 — descendant-compatible verifier roots

Owner E371012 selects bounded direct implementation. Written **before the
first source edit**.

### Revalidated at claim (read-only)

    HEAD                 f36bcd75ed22430355efe1b274b8f236cb591f6b  (the base the PLAN names)
    v12 porcelain        clean
    claude_agent.py      b014ea3f5f58af573a0cbaa4b8838a270953806a89ef274682d5cca6627efe7c
                         — identical to the digest REVALIDATION-370978 pins
    _pinned_environment  line 3262, still emitting /proc/self/fd/N
    _revalidated_directories  line 3305, still validating those descriptors
    _verify              line 4113, still passing them to the immediate child only

### Why the defect is what it is, stated so the correction can be judged

The descriptor alias exists to defeat a **check/use race**: the provider runs
as the same uid, knows the scratch layout, and can rename a checked verifier
root to a link at the candidate between the check and the verifier's use. An
already-open directory object cannot be redirected that way, so
`/proc/self/fd/N` is the verifier's authority rather than the pathname.

It breaks for **descendants** because `/proc/self/fd/N` is relative to the
process: the immediate child gets fd N through `pass_fds`, but an ordinary
grandchild spawned with Python's default `close_fds=True` does not, so its
`TMPDIR` names a path that does not exist. The `AdapterCase` tests build
nested workspaces under `TMPDIR`, so compatibility breaks before the intended
assertions run — 40 failures / 20 errors against a command that passes 186 on
ordinary paths.

The three simple workarounds are each refused by the dossier with a reason I
re-read rather than assumed:

* resolving the alias to an ordinary provider-writable path **reopens the
  race** the alias exists to close;
* `/proc/<holder-pid>/fd/N` survives a grandchild's descriptor closure but the
  nested adapter rejects lexical-versus-realpath disagreement, and the alias
  dies with its holder;
* marking the descriptors inheritable does not override a descendant's own
  `close_fds` default.

### The mechanism the retained preparation proposes, and why it is the answer

Same-uid DAC cannot protect a parent directory: the provider can `chmod` any
mode this worker sets. What the provider **cannot** do is rename or unlink a
**mountpoint** — the kernel refuses with `EBUSY` while it is mounted,
regardless of uid. So a verifier root that *is* a mountpoint is safe under an
ordinary pathname, and an ordinary pathname is what descendants and nested
canonical-path checks need.

That is why the correctness of this mechanism rests on kernel mount semantics,
and why the actual corrected-image/kernel proof is a **separately selected**
stage that source tests cannot discharge. This claim delivers the source
boundary: the proof, the adoption, the refusals, and the compatibility gate.

### The change — `v12/worker/claude_agent.py`

Three new members on `ClaudeAgent`, one wiring line, and one extension to the
post-provider revalidation. Nothing existing was removed.

**`_mount_points(place=None)`** reads `/proc/self/mountinfo` and returns the
mount points the kernel holds for this process. `os.path.ismount` is *not*
used and the docstring says why: it compares `st_dev` against the parent,
which a bind mount inside one filesystem does not change — so it answers "no"
for exactly the topology this correction depends on. Field 5 is decoded for
the four octal escapes `mountinfo` uses and nothing else; an unreadable table
**refuses** rather than being assumed.

**`_mount_bound_root(place, points, *, name)`** proves one root and returns
its descriptor. Five facts, each with its own refusal: opens as a directory
under `O_NOFOLLOW`; is listed as a **mount point**; is mode 0700; is owned by
this runtime's uid *and* gid; and the opened object is the same inode on the
same device as the named one.

**`_mount_bound_environment(scratch, environment)`** returns the
descendant-compatible environment — **ordinary pathnames** — or `None` when no
root is a mount point. A **half-converted** layout refuses by name rather than
choosing a topology nobody selected.

`_pinned_environment` tries the bound form first and otherwise falls through to
exactly the code it ran before. `_revalidated_directories` now accepts either
form: the descriptor form must still name `/proc/self/fd/<n>`, and the bound
form must still be a mount point **and** still be the same object — because a
root unmounted while the provider ran is one whose non-replaceability has
expired, which is the precise lifetime failure the holder-alias workaround was
refused for.

**Why a mount point is the answer.** Same-uid DAC cannot protect anything: the
provider can `chmod` back any mode this adapter sets. The kernel refuses to
rename or unlink a mount point while it is mounted, `EBUSY`, regardless of uid.
So the root is safe under an ordinary pathname — and an ordinary pathname is
what descendants and nested canonical-path checks need.

**Why detection rather than a declaration.** The frozen task and launch shapes
are closed and this correction is explicitly not authorized to extend them, so
the layout is not announced to the worker — it is *proved* by the worker, from
the kernel's table and the objects themselves. An image that provides the
layout gets the fix; an image that does not gets today's behaviour exactly.

### Tests — `tests/manager/test_claude_agent.py`, one new class, 20 cases

| group | cases |
| --- | --- |
| the kernel's table | real `mountinfo`, compared against an independently parsed second reading; an ordinary scratch root is *not* a mount point; an unreadable table refuses |
| the compatibility gate | an image without the layout keeps the descriptor form; a half-converted layout refuses and names both sides |
| the correction | the bound environment hands out ordinary paths; **a real grandchild** creates and reads a file under `TMPDIR`; lexical and canonical spellings agree |
| **the control** | the same real grandchild under today's descriptor form **fails** — without this the case above proves nothing |
| refusals | not a mount point, removed, link-replaced, widened mode, a file; the new mode/mount/`O_NOFOLLOW` checks driven **directly**; no descriptor leaks when a later root refuses |
| after the provider | the bound roots revalidate; an unmounted root refuses; a root **swapped for another surviving object** refuses; the descriptor form's revalidation is unchanged |

Four of the refusal cases turned out to be caught by the **existing**
`_checked_directory` component guard, which runs first — so they assert the
refusal that actually happens and the new composition is shown to be a second
line behind a guard that still works. My first draft asserted the new wording
and failed; the product was right and the assertions were wrong.

The swap case renames the original root *away* rather than removing it, so the
held inode survives and the existing `st_nlink == 0` check does not fire
first — otherwise it would have been measuring that check instead of the new
object comparison.

### Verification

    tests.manager.test_claude_agent     261 tests  OK   (241 before)
    tests.manager.test_worker_image     106 tests  5 failures (pre-existing)
    tests.manager.test_source_boundary   75 tests  1 failure, 2 skipped (pre-existing)

Both adjacent failure sets are **identical on the pristine committed worker**,
checked by extracting it with `git show HEAD:…` to a temp file and swapping it
in. Not caused by this change and not fixed by it.

Against that pristine worker, 18 of the 20 new cases error on the missing
seam. That is weak evidence on its own, so the **control** case carries the
demonstration: it reproduces the descendant failure on the code path today's
images run, and it passes under the candidate too, because the descriptor form
is still there.

### What this does NOT establish — the honest boundary

* **No image provides the layout.** `source_boundary` is unchanged and no
  Dockerfile was touched, so on every current deployment the gate keeps the
  descriptor form and behaviour is **unchanged**. The descendant fix activates
  only on a corrected image.
* **The kernel question is not answered.** That a mount point cannot be
  renamed under the selected topology, that mount identity and options bind as
  required, and that immutable ancestors hold — all of it remains the
  separately selected corrected-image/kernel proof. Source tests cannot
  discharge it and these do not claim to.
* **The positive bound composition substitutes the mount TABLE**, because an
  unprivileged test cannot create a mount. Substituted: the topology.
  Not substituted: the parsing, every refusal, the object checks, the real
  grandchild, and the canonical agreement.
* **The capacity partition is not implemented.** `source_boundary` still
  declares `/tmp` 64 MiB plus `/dev/shm` 16 MiB; the proposed
  32/16/4/16/4/8 split and its 96 MiB total remain unproved and un-landed.
* No engine, provider, deployment or live operation was involved, and
  `preparation-325908` was neither executed nor rewritten.

### Boundaries

Changed: `v12/worker/claude_agent.py`,
`v12/python/tests/manager/test_claude_agent.py`, this PROGRESS and
`evidence/claim-371040/`. Nothing else in `v12`. The retained preparation
directories, their manifests and all prior evidence are untouched. W321776's
Stage-A additions and W321528's timeout reporting are both preserved — the
`_verify` timeout path is byte-unchanged. No Git mutation; the only
version-control calls were `rev-parse`, `status`, `diff` and `show`, all reads.

## claim371184 — detection replaced by explicit selection; R3 still owed

Answers `review-2026-10-28T03-09-09Z.md`. **R1 and R2 are corrected. R3 is
not done**, so this is returned as **incomplete** with exact remaining scope
rather than offered as the selected correction.

### The review was right on all three, and R1 was my mistake

I reasoned that the frozen task and launch shapes are closed, so the layout
had to be *detected*. The review's answer is the one the retained `TASK.md`
already gives: bind it through the **runtime-profile/adapter configuration
boundary** with a **new schema/name** — which is not the frozen task shape at
all. *"No auto-detection of arbitrary directories"* is in `TASK.md` in those
words. My detection let an arbitrary mounted directory opt into new semantics
with no profile, image or adapter agreement, and let a broken new-layout
deployment degrade silently to the known defective path. Both are exactly as
described.

### R1 — the layout is now selected, and absence is explicitly legacy

A new document under a new schema, `baton.v12.verifier-layout/1` at
`/run/baton/verifier-layout.json`, delivered by the manager and **read**, not
guessed. It carries the fixed `roots`, the `filesystem`, the `options`, the
trusted `uid`/`gid` and the `image_digest`/`adapter_digest`/`policy_digest`
the layout is bound to. Every member is required and no extra member is
accepted.

* **Absent → legacy**, and it costs nothing: `_selected_layout` returns
  `None` on `lexists` alone, so a legacy deployment reads **no mount table**.
  The review asked for that by name, and the test replaces `_mount_facts`
  with a function that fails the case if it is called.
* **Present but malformed → refuses.** A deployment that tried to select the
  new topology and could not state it does not fall back to the old one.
* **Wrong schema → refuses before the provider**, which is the old-image /
  new-layout direction.
* The trusted identity is the **selection's**, never the ambient process —
  `TASK.md` forbids both a hardcoded 65532 and an inferred login group.

### R2 — presence is not the topology

`_mount_facts` now keeps the mount id, parent id, device, root, per-mount
options, **filesystem type** and **superblock options**; the first cut kept
only the path, which is why the reviewer's `ext4,rw` records at mutable
scratch roots passed straight through. `_proved_root` now proves, each with
its own refusal: the canonical selected pathname, `O_NOFOLLOW` open, the
mount's presence, its **filesystem type**, its **exact options**,
**immutable ancestors**, mode 0700, the **selection's** uid/gid, and the
opened object's identity against the named one. `_revalidated_directories`
re-asks the mount, the type and the options after the provider, so a root
remounted writable or unmounted mid-run refuses — the lifetime failure the
holder-alias workaround was refused for.

The mutable scratch environment is **no longer the input** to the new path:
the roots handed to the verifier are the selection's own fixed paths.

### The agreement happens before the provider

`_child_environments` — which runs before either child — now calls
`_layout_preflight`, which proves the selection and **releases** what it
proved. `TASK.md` requires worker/manager agreement before provider launch
and requires both incompatibility directions to refuse there. A check that
waited for verification would let a provider turn spend a model invocation
against a deployment that could never verify.

### Tests — the old class is gone, replaced

`TheVerifierRootsReachDescendants` tested the auto-detection that had to
change and is removed under standing test authority, keeping its real
descendant, control and object-binding coverage in the new class.

`TheVerifierLayoutIsSelectedAndProved` (25 cases) and
`TheSelectedPolicyConstants` (3): selected legacy reading no mount table; the
compatible pair handing out ordinary stable paths that are **not** the scratch
paths; a **real grandchild** resolving them; the **control** showing the same
grandchild failing on the legacy form; both incompatibility directions;
malformed, missing-member, wrong-roots and relative-root refusals; wrong
filesystem; missing options; writable-ancestor and foreign-owned-ancestor
refusals **driven directly** against real paths, plus a positive ancestor
case; widened mode; foreign identity; link replacement; no descriptor leak;
the pre-provider refusal; the preflight releasing its descriptors; and the
post-provider re-proof including remount and unmount.

**What is substituted, at one point each and labelled there:** the mount
table, and the root-owned 0755 image scaffolding — an unprivileged test can
create neither. `TheSelectedPolicyConstants` pins the shipped constants
(`tmpfs`, the four options, uid 0, mode 0755, the schema and the document
path) so the relaxation cannot hide a changed policy, and parses the host's
**real** mountinfo with every field.

### Verification

    tests.manager.test_claude_agent   269 tests  OK, 1 skipped  (241 originally)

The skip is the positive ancestor case, which needs a root-owned 0755 `/run`
and says so rather than asserting nothing.

**All 27 new cases fail against the pristine committed worker** — checked by
extracting it with `git show HEAD:…` to a temp file and swapping it in.

| | sha256 |
| --- | --- |
| `v12/worker/claude_agent.py` | `a73b8820397ac755e7762c835cebb574a427347d574f9585bc6b6ecd3d1c0ba5` |
| `v12/python/tests/manager/test_claude_agent.py` | `e079b844c403d755baa13459291b28bf130c843409105a409ad9937816e0c5bc` |

base `f36bcd75ed22430355efe1b274b8f236cb591f6b`; `v12` porcelain shows only
those two paths.

### R3 IS NOT DONE — the exact remaining scope

I did not complete the configured-topology half, and I am not presenting this
as the selected correction:

* **no manager-side composition** of the `verifier-layout/1` document — the
  worker reads a selection nothing yet writes, so on every deployment today
  the document is absent and the behaviour is **unchanged legacy**;
* **no OCI/`source_boundary` composition** of the four private
  `rw,noexec,nosuid,nodev` tmpfs mounts, their fixed roots or their delivery;
* **no capacity partition** — `source_boundary` still selects `/tmp` 64 MiB
  plus `/dev/shm` 16 MiB; the proposed 32/16/4/16/4/8 split and its 96 MiB
  total are not implemented and `TASK.md`'s per-root ENOSPC behaviour is not
  tested;
* **no image recipe** scaffolding or trusted layout marker;
* **no connected acceptance** across worker and configured topology, which
  the review asks for as one result.

The corrected-image/kernel proof remains separately selected and is not
claimed. W321776's `/3` work is downstream and untouched, as the review
directs.

### Why I am returning it rather than continuing

The remaining half spans the manager composition, the OCI vector,
`source_boundary` capacity and the image recipe, and the review rightly wants
them accepted as one connected result. I do not have the room in this claim
to build and verify that to the standard the two prior rounds were held to,
and a third partial offered as complete would be worse than an honest return.
R1 and R2 are the security core the reviewer's probe counterexampled, they are
complete and tested, and they are safe to carry forward: with no selection
document present, every current deployment behaves exactly as it does today.

### Boundaries

Changed: `v12/worker/claude_agent.py`,
`v12/python/tests/manager/test_claude_agent.py`, this PROGRESS and
`evidence/claim-371184/`. Nothing else in `v12`. The retained preparation
directories and all prior evidence are untouched; W321528's `_verify` timeout
reporting and W321776's Stage-A additions are preserved. No engine, provider,
deployment or live operation. No Git mutation — only `rev-parse`, `status`,
`diff` and `show`, all reads.

## claim371379 — the connected topology milestone

Answers `review-2026-10-28T03-25-24Z.md`, which names the next bounded
milestone as **completion of manager-to-worker topology composition and its
connected deterministic proof, correcting the helper gaps as part of that
result**, under existing owner E371012. Continuing rather than asking for a
fresh approval, as that review directs.

### Revalidated at claim, read-only

    HEAD                      f36bcd75ed22430355efe1b274b8f236cb591f6b  (unchanged)
    claude_agent.py           a73b8820397ac755e7762c835cebb574a427347d574f9585bc6b6ecd3d1c0ba5
    test_claude_agent.py      e079b844c403d755baa13459291b28bf130c843409105a409ad9937816e0c5bc

Both retained candidate hashes **MATCH** the reviewed `claim-371184` binding
byte for byte, so this claim continues from the reviewed bytes rather than
from a drifted tree. Read-only at claim: the new review, `PLAN.md`'s current
continuation, `preparation-325908/TASK.md`'s selected mechanism, the complete
`work-events` handoff (33 events) and the complete thread (9 messages, no
pagination outstanding).

### The three helper gaps, confirmed in the source before changing anything

Each one was read at the line rather than taken on the review's word, and all
three are real:

1. `_selected_layout` ends with a loop that accepts **any nonempty string**
   for `image_digest`, `adapter_digest` and `policy_digest`. Nothing compares
   them to a trusted expectation, so the document's own claims are the only
   authority — which is carrying a claim, not establishing agreement. And
   `if not os.path.lexists(place): return None` makes absence
   **unconditionally** legacy, so a new image whose layout delivery failed
   runs the defective path silently.
2. Roots are checked only as canonical absolute strings. `/run/baton-verifier/`
   appears nowhere in the worker, and nothing requires the four to be
   **distinct** — one mounted directory named for all four roles passes.
3. `_proved_root` computes `present = carried["options"] |
   carried["super_options"]` and `_revalidated_directories` computes the same
   union. A union answers *"is this option present at either layer"* when the
   question is *"what are the effective semantics at the layer that decides"*,
   so a mount whose per-mount options are `ro` passes on a superblock `rw`.
   And `_revalidated_directories`' own comment says the immutable ancestors
   are asked again; it never calls `_proved_ancestors`. The claim and the
   enforced lifecycle disagreed, which is the specific thing the review told
   me to make match.

### Boundaries for this claim

Source and tests I own, plus this PROGRESS and `evidence/claim-371379/`.
Prior evidence and the three retained preparation directories are preserved
untouched. `FINDING.md`, `PLAN.md` and every review are the reviewer's.
W321776's `/3` work is excluded and untouched. No engine, provider,
deployment, image build or live operation — the real image/kernel proof
remains separately selected. No Git mutation.

### What this claim built — the connected topology, manager to worker

The three helper gaps are corrected **as part of** the composition rather than
as a separate pass, which is what the review asked for.

**1. The digests are now bound to an owner, not carried as claims.**
`_selected_layout` used to accept any nonempty string for the three digests.
The document now carries the WHOLE resolved identity — `image_digest`,
`profile_digest`, `policy_digest`, `adapter_digest`, `oci.RESOLVED_IDENTITY`
member for member — and `OciAdapter.__init__` refuses a delivery that
disagrees with the one identity it was constructed under. That adapter's
identity is what the argv names and what the labels must agree with, so the
comparison is against the manager's own account of which runtime is starting,
not against the document's opinion of itself. `profile_digest` is the member
a three-digest document left unbound.

**The execution identity is a capability, not two integers.**
`compose_verifier_layout` takes a `workspaces.WorkspaceIdentity` — minted
only by `workspaces.identity_for`, whose uid is this manager's own effective
uid behind the deployment's minted workspace group. It is the SAME object
`oci.run_vector` composes into `--user`, and `run_vector` refuses a document
whose uid/gid is not the pair it is about to write into that flag. So the
identity the verifier proves its root ownership against cannot be an identity
the container will not run as, and a caller holding the right two integers
still cannot compose a selection. TASK.md's "not hardcoded 65532, not ambient
login group" is satisfied by construction rather than by a range check.

**2. Fixed, disjoint roots.** `source_boundary.VERIFIER_ROOTS` is the one
table both sides read: four names, four targets under
`/run/baton-verifier`, four byte bounds. Disjointness and name-uniqueness are
asserted at import. The worker compares the selection against
`LAYOUT_ROOTS` by equality, so one mounted directory named for all four roles
— the review's own counterexample — refuses.

**3. Effective mount semantics at the deciding layer.** `_proved_options`
replaces the union: `noexec`/`nosuid`/`nodev` are required in the per-mount
options and a superblock copy does NOT satisfy them, while writability is the
conjunction of both layers because the kernel treats it that way.
`_revalidated_directories` now calls `_proved_ancestors` — its comment said
it did and it did not — and re-compares the mount id, device, subtree root
and mount point retained when the roots were proved, so a root unmounted and
replaced by another tmpfs with the same type and options refuses.

**The manager composes, materializes and delivers.**

| | |
| --- | --- |
| `source_boundary.compose_verifier_layout` | the selection, against the image's marker |
| `source_boundary.materialize_verifier_layout` | the bytes on disk, in manager-owned storage |
| `source_boundary.LayoutDelivery` | the typed capability the adapter receives |
| `oci._layout_mount` | one read-only bind at one fixed target |
| `oci.run_vector` | the `--user` and image agreements, and containment |
| `OciAdapter` | the resolved-identity binding |
| `Dockerfile.claude` | root-owned 0755 scaffolding and the shipped marker |

Materialization follows `launch.materialize`'s byte discipline — exclusive
creation, `O_NOFOLLOW`, created unreadable and made readable on the
descriptor after the last byte, whole-write or refusal. It differs in one
place and for a stated reason: an existing document that is byte-identical is
ADOPTED rather than refused, because this selection is a pure function of the
topology, the marker and the resolved identity, so a second start of one
deployment composes the same bytes and refusing them would mean a deployment
could serve exactly one runtime. **Different** bytes at the name still refuse.

**Containment is symmetric with the launch document's.** The first cut
composed the layout mount and added it to nobody's list, so an exchange, log,
scratch, source, integration or context target could have landed over the one
document the verifier's roots are proved against. It is now in every later
family's list. **I am precise about what that is worth:** only the assignment
`mounts` operand has a caller-chosen target, so the collision is reachable
only there, and that is the case driven. Every other family lands on a
constant of its own contract, so those entries are DEFENCE IN DEPTH and the
tests say so — what is asserted for them is the invariant they protect (no
fixed target contains the layout document) and the structural symmetry with
the launch document's identical entries.

**The capacity partition is landed.** `/tmp` 32 MiB + `/dev/shm` 16 MiB +
home 4 + tmp 16 + cache 4 + pycache 8. The aggregate is still 80 MiB and
asserted at import; `MIN_WORKSPACE_BYTES` is now derived from the whole
scratch table rather than from two of its names, and is the same 80 MiB it
was. With the existing 16 MiB legacy log decoy the total tmpfs is 96 MiB.

**Both documents are read under one bounded discipline.** `_bounded_document`
reads at most 64 KiB; the previous cut used `json.load` on a file object,
which reads to EOF. Every other document this workload consumes is bounded at
the read and these two were not.

### Verification

    tests.manager.test_verifier_topology    55 tests  OK      (new, joined)
    tests.manager.test_claude_agent        279 tests  OK, 1 skipped
    tests.manager.test_oci                 143 tests  OK
    tests.manager.test_source_boundary      75 tests  1 failure, 2 skipped

The `test_source_boundary` failure is PRE-EXISTING — `boundary_mounts`
composes the attempt-log room, which is not in `SCRATCH_MOUNTS`, and the
identical failure occurs on the pristine committed module, checked by
extracting the committed bytes read-only and swapping them in.

Also checked for attribution, because this claim adds `boundaries.*` calls
and changes a capacity constant:

* `test_boundary_inventory` + `test_workspaces` — 28 failures, and the
  failure NAME SETS are **identical** with the candidate and with the
  pristine committed `oci.py` and `source_boundary.py` swapped in. They are
  about `review_cycles`, `intake` and `custody` declarations and none of them
  names a module this claim touched.
* `tests.tools.test_single_worker` — 243 tests, 1 failure, pre-existing by
  the same swap. The capacity references in the tools suites are all
  symbolic (`MIN_WORKSPACE_BYTES`), which is why a redistribution that keeps
  the aggregate is value-stable for them.

One earlier full-tree run was ABANDONED AND IS NOT REPORTED: I swapped source
files in for attribution checks while it was still running, so its results
describe no single tree. It was stopped and re-run clean.

### What is NOT established, and please weigh the candidate against this list

1. **No deployment configuration selects it yet.** The composition, the
   delivery and both agreement directions are complete and tested, but the
   operator configuration member that names an image's marker is NOT added:
   `single_worker.CONFIG_SCHEMA` holds a closed member list on a versioned
   document, so the member requires a new schema version
   (`baton.v12.single-worker-deployment/6`, alongside `/4` and `/5` as the
   existing `provider_context` precedent does). That is a deployment-contract
   version, which I will not mint under an implementation claim. Until it
   exists, every deployment composes no selection, the worker reads no
   document and behaviour is **unchanged legacy** — which is also why nothing
   here can break a current deployment.
2. **The kernel question is untouched.** Mount-point rename refusal under the
   selected topology, mount identity and options, and immutable ancestors
   remain the separately selected proof. Source tests cannot discharge it.
3. **The mount table and the root-owned 0755 scaffolding are substituted**, at
   one labelled point each: an unprivileged test can neither mount four
   private tmpfs filesystems nor create a root-owned directory. Not
   substituted: the parsing, every refusal, the object checks, the real
   grandchild, the canonical agreement, the composition, the materialized
   bytes, the engine argv and the recipe's own text.
4. **The image is not built.** The recipe's scaffolding and marker are
   asserted as text and as bytes equal to `image_layout_marker()`; that a
   BUILT image carries them is the image proof.
5. **Per-root ENOSPC behaviour is not exercised.** The bounds reach the engine
   argv, which is where they are real, but a full root's refusal is a kernel
   behaviour and belongs with the kernel proof.
6. No engine, provider, deployment or live operation; `preparation-325908`
   was neither executed nor rewritten.

### An operational finding, and a correction to the attribution wording above

The shared working tree carries **concurrent uncommitted work from another
owner**, which was NOT there when this claim started. `v12` porcelain now
also shows `schema.py`, `tokens.py`, `workspaces.py`,
`tests/manager/test_boundary_inventory.py` and `DESIGN.md` modified, plus new
`stopped_settlement.py` and `test_stopped_settlement.py`. None of those is
this candidate and none was edited under this claim.

Two consequences, stated rather than smoothed over:

* The `test_boundary_inventory` failures above are **not attributable to this
  candidate** — which is what the identical failure name sets establish — but
  I should not have called them "pre-existing", because the tree they were
  measured on is not the committed tree. That foreign change adds 138 lines
  to that very test module. The claim I can defend is the narrow one: with
  the pristine committed `oci.py` and `source_boundary.py` swapped in, the
  failure set is unchanged, so none of them is mine.
* My composition now depends on `workspaces.WorkspaceIdentity` and
  `workspaces.identity_for`, and `workspaces.py` is one of the foreign
  modified files. I read that diff: it is at `preparation_completed` and
  touches neither. So this candidate's dependency is intact at the bytes I
  measured against — but a reviewer re-running these suites should re-check
  it, because I do not control that file.

`evidence/claim-371379/BINDING.json` records the eight candidate paths and
their hashes, and names the foreign paths explicitly so the candidate cannot
be read as including them.

## claim375947 — the three confirmed composition blockers

Answers `review-2026-10-28T17-58-14Z.md` under existing owner E371012, which
also settles the version-bookkeeping question: *"Necessary closed deployment
schema evolution within this already-approved outcome is not a new owner
gate."* That is the permission I declined to assume last claim, and it is the
reason B1 below is now in scope rather than named as remaining.

Serialization resolved before editing: E375838 blocks W375445 on this Work
(M375839, confirmed by the reviewer in M375854), so this Work holds FIRST
`tools/single_worker.py` configuration/adapter ownership.

Revalidated at claim: all eight retained candidate hashes match
`evidence/claim-371379/BINDING.json`, so this continues from the reviewed
bytes. Read-only: the new review, `COMPOSITION-GAPS.json`, the complete
`work-events` handoff (41 events) and the complete thread (12 messages).

Attribution method CORRECTED per the review: no shared-checkout file swaps
while anything may read the tree. Baselines are taken as isolated snapshots,
and residual sets are compared by cause rather than by failure name.

### What this claim corrected

**Blocker 3 — unselected compatibility.** `SCRATCH_MOUNTS` is restored to the
committed legacy pair, 64 MiB and 16 MiB, and a new `SELECTED_SCRATCH_MOUNTS`
carries the 32/16/4/16/4/8 split. `run_vector` composes the selected table
ONLY for a runtime holding a layout delivery: the unselected argv is 51 words
again — the pre-W325695 value — contains no verifier root, no `uid=` and no
`mode=`, and is identical to `layout_delivered=None`. Both tables are asserted
at import to hold the same 80 MiB aggregate, so the workspace floor is one
number either way and a deployment neither gains nor loses room by selecting.

**Blocker 2 — the mount now carries what it promises.** `_selected_scratch`
emits `uid=`, `gid=` and `mode=0700` on each of the four roots, from the SAME
minted `workspaces.identity_for` capability this vector writes into `--user`
and the same `VERIFIER_MODE` the document names. The reviewer is right that
setting `--user` is not a declaration of filesystem-root ownership and that the
image's root-owned 0755 mountpoint is not the mounted root. No worker check was
weakened — `claude_agent.py` is byte-identical to the reviewed bytes.

The layout agreements (execution posture, minted identity) moved EARLIER, to
where the scratch table is decided, because a vector that reached that line
without an identity would be composing mounts for a runtime it could not
describe. A consent runtime refuses there and acquires no root by a side door.

**Changed test reasons.** `test_oci`'s argv-length expectation goes BACK to 51
from the 59 my earlier claim set — that change was the defect, and the case now
also counts `--tmpfs` operands against the legacy table.
`test_verifier_topology`'s capacity cases are rewritten for two tables, and
`test_the_engine_mounts_every_root_with_its_own_bound` is replaced by
`test_no_root_is_in_the_unconditional_restrictions` plus six new cases driving
the selected identity, the mode, both vectors and the redistribution.

### Blocker 1 is NOT done — exact remaining scope

`tools/single_worker.py` still never delivers the selection. What remains:
a `baton.v12.single-worker-deployment/6` schema beside `/4` and `/5` carrying
the image's marker; `_held` validation of it; `compose_verifier_layout` against
the minted identity and the configuration's four digests;
`materialize_verifier_layout` and `layout_delivery=` at BOTH `OciAdapter`
construction sites; and the compatible/legacy/both-incompatible cases driven
through the supported deployment entry rather than through helpers.

**And a correction I owe rather than a repetition.** Last claim I said every
deployment stays unchanged legacy. For the candidate IMAGE that is false, as
the review found: `Dockerfile.claude` copies the marker unconditionally, so a
new image with no configuration meets the worker's marker-present/
document-absent refusal. That refusal is correct fail-closed behaviour; what is
missing is the configuration half. Existing images are unchanged; the new image
REQUIRES the new configuration, and that is the compatible pair.

### Verification

    tests.manager.test_verifier_topology    63 OK   (was 55)
    tests.manager.test_claude_agent        279 OK, 1 skipped
    tests.manager.test_oci                 143 OK
    tests.manager.test_source_boundary      75, 1 failure, 2 skipped
    combined                               560, 1 failure, 3 skipped, 18.033s

ATTRIBUTION BY CAUSE, NOT BY NAME, and with NO shared-checkout swap, as the
review instructs. That one failure compares `boundary_mounts`' operands against
`SCRATCH_MOUNTS` and reports the attempt-log decoy as an extra element.
`boundary_mounts` is untouched here and `SCRATCH_MOUNTS` now holds exactly the
committed tuple — asserted in `evidence/claim-375947/BOTH-VECTORS.txt` — so
both operands of that assertion are byte-identical to the committed tree and
the cause cannot be this candidate's.

Serialization survives this return: E375838 blocks W375445 on this Work, so the
first `tools/single_worker.py` configuration/adapter ownership stays here.

## claim376027 — blocker 1: the installed configuration now selects and delivers

The last remaining blocker. Blockers 2 and 3 were accepted at source level in
review 2026-10-28T18-21-11Z; this completes the joined path.

**The configuration half.** `baton.v12.single-worker-deployment/6` joins `/4`
and `/5`, which are UNTOUCHED and remain supported -- the same way `/5` added
`provider_context` beside `/4`. `/6` carries one more member,
`verifier_layout`: the marker its image declares, or `null` for an explicitly
legacy deployment. A `/4` or `/5` configuration composes nothing, writes
nothing and adds no mount.

**The delivery half.** `single_worker.layout_delivery(given, group)` composes
through `source_boundary.compose_verifier_layout` under
`workspaces.identity_for(group)` -- the deployment's own minted identity, the
same capability the run vector writes into its user flag and the same one the
four private roots are created under -- and the configuration's four resolved
digests. It materializes under the manager's own `launch_home`, which is
manager-owned storage rather than an assignment root. Both `OciAdapter`
construction sites now pass it: the ordinary `_adapter` and the STATIC
PREFLIGHT, so a `/6` configuration whose marker names another topology is
refused before admission rather than at the first start.

**Verification.** `test_verifier_topology` 69 OK (was 63; six new cases drive
the three supported schemas, the legacy no-op, the joined
deployment-to-worker read, the minted identity, the marker-mismatch refusal
and the adapter's acceptance of the delivery). Combined with `test_oci` and
`test_claude_agent`: 491 tests OK with one skip.
`tests.tools.test_single_worker` 243 tests with ONE failure --
`test_a_real_observing_status_run_mutates_no_durable_state`, the same
environmental case that failed before this claim's edits and is not caused by
them; no file was swapped in the shared checkout to establish that.

Candidate this claim: `tools/single_worker.py` 807cc6b3 and
`tests/manager/test_verifier_topology.py` 70be13f3, plus the eight paths from
claim-375947 unchanged.

## claim376107 — the /6 schema conflated layout with context; corrected

The reviewer's CONFIG-PROBE and ROLE-PROBE found a real defect in my own last
claim and the diagnosis was exact. `_held` treated `/6` as CONTEXTUAL, so
`provider_context` became a required member and every `/6` deployment went
through the retained-implementation-only rule at :433-438. A fresh `/6`
configuration therefore refused for a context it never selected, a null one
refused, and a review-role one refused outright. My new cases missed it
because they called the helper with a partial dictionary and compared schema
constants, which is exactly the bypass the review names.

**Corrected in one place:** `contextual` is now `said == CONTEXT_CONFIG_SCHEMA`
alone. `/5` keeps its context rules untouched — the member stays required and
retained-implementation only — and `/6` selects a verifier layout and says
nothing about context. No required-context check was weakened and no receipt
is fabricated.

**And the tests now drive the real entry.** Seven cases in
`tests/tools/test_single_worker.py` call the actual `_held` with a COMPLETE
configuration document taken from the serving-context fixture: a fresh
implementation `/6` admitted with no `provider_context`, a review-role `/6`
admitted, a null selection admitted as explicitly legacy, four non-document
selections refused, a `/4` carrying the member refused because those lists are
closed, `/5`'s own context rules still enforced, and the admitted
configuration composing a real delivery whose image digest is the
configuration's.

One fixture correction worth recording: the context fixture's implementation
manifest declares a `provider-context-receipt` output, and the existing
"reserved context receipt requires context implementation deployment" rule
correctly refuses one with no context mode. The FIXTURE drops that output and
re-digests; the product check is right and was not relaxed.

    tests.tools.test_single_worker        250 tests, 1 failure
    tests.manager.test_verifier_topology   69 OK

The one failure is `test_a_real_observing_status_run_mutates_no_durable_state`,
the same environmental case that failed before any of this Work's edits. No
file was swapped in the shared checkout to establish that.

Candidate this claim: `tools/single_worker.py`
`007b54a48bf24c6c2319fcbcf0330bd4ce5f95f83aed9b14107282338fb026ba` and
`tests/tools/test_single_worker.py`
`8612711f3cd84ee161c4b8125f382f447326bae3448fa76ec0704050371a1672`.

## claim376187 — context and layout were mutually exclusive; corrected

Review 2026-10-28T18-40-44Z found the remaining defect and it was mine again.
My `/6` carried the layout member INSTEAD of the context one, so a valid
retained-implementation context deployment that also selected a layout refused
BOTH ways: `/5` for an unexpected `verifier_layout` and `/6` for an unexpected
`provider_context`. Testing `/5` alone could not see it.

**Corrected: `/6` is `/5` PLUS the layout, and the VALUE decides which rules
apply rather than the version.** A `/6` naming a null context is a fresh
deployment; a `/6` naming a context is held to exactly the `/5` rules --
required mode, retained implementation only, and the receipt declaration. `/5`
itself is unchanged: its member is still required and a null one still refuses
there. No receipt is fabricated and no context is dropped.

Three new cases drive the combined contract: a context deployment also
selecting a layout is admitted with both members intact; a combined deployment
is still held to retained-implementation-only (a review role refuses); and a
malformed context beside a valid layout still refuses. The fresh and review
cases now assert `provider_context` is null rather than absent, which is what
the closed `/6` member set means.

One fixture note: a context deployment declares its `provider-context-receipt`
output, so the combined cases restore the context fixture's own manifest
rather than the receipt-stripped one the fresh cases use. The product's
receipt enforcement is right and was not relaxed.

    tests.tools.test_single_worker        253 tests, 1 failure
    tests.manager.test_verifier_topology   69 OK

The one failure is the same environmental
`test_a_real_observing_status_run_mutates_no_durable_state` that failed before
any of this Work's edits; no shared-checkout swap was used to establish that.

Candidate this claim: `tools/single_worker.py`
`4b834b33124cf8a751e9ca3bf3d3ca7a69991a81430da937a34ee3dd0d03f931` and
`tests/tools/test_single_worker.py`
`a67db34da2aeb33dea584da24c1cf6f6c7592d360ac1b42f2bb2e0c1b4507f68`. The other
eight paths are unchanged.

## claim376514 — Selection A executed: one candidate image build

Owner E376511 selected preparation-376414 Selection A only. Integrity first:
`PACKET-PINS.json` hashes to
`c4cf8e64d959a8345145812757be74255d40d744e58f9b1e90a5f739fbb3ecf7`, the exact
selected manifest; an independent walk re-hashed all 32 pinned files with no
mismatch, and `packet.py check` answered the same digest with
`engine_invoked: false`.

**The build.** One `docker build` through the packet, `--owner-selected`, with
the selected 1800s timeout and the requested 2 GiB / 1 CPU:

    status        candidate-built
    exit_code     0
    image         sha256:47e733834bb690fd4601e102f81e527a08b6ffe55da8b8cb345f45edfcb1517e
    seconds       0.414
    provider_invoked  false

**I am flagging the 0.414 seconds rather than presenting it as a cold build.**
That is cache reuse for every layer, not a from-scratch assembly — this
Work's two added layers are a `mkdir`/`chmod` and a 433-byte `COPY` over an
already-built base, so a warm cache can finish that in well under a second.
What IS established independently: the image exists locally and `docker image
inspect` reports it created `2026-10-28T19:20:32Z`, i.e. by this invocation.
No retry, no prune, no deletion, no publication, no model call.

**Selection.** `packet.py select` read that receipt and wrote `SELECTION.json`:

    selection SHA256  7ab020e2d08f74296fb08bf1d0a44b8bfd1b8d8b76a34f96727502520fd6eac1

and printed the concrete probe command for owner Selection B:

    python3 -B <preparation-376414>/packet.py run --owner-selected \
        --selection-sha256 7ab020e2d08f74296fb08bf1d0a44b8bfd1b8d8b76a34f96727502520fd6eac1

**The kernel probe was NOT run**, as the owner directed. Selection B is the
owner's: that exact image ID, that selection digest and the proposed
65532:65532 diagnostic identity.

Verification spending this claim: the read-only packet check, an independent
32-file pin walk, one selected build (0.414s) and one `select`. No provider,
no deployment, no probe, no Git action. The Work stays open for the real
kernel/capacity acceptance and the human source checkpoint.

## claim376735 — Selection B executed once; failed-or-uncertain with zero effects

Owner E376729 selected Selection B at selection digest
`7ab020e2d08f74296fb08bf1d0a44b8bfd1b8d8b76a34f96727502520fd6eac1`.
Integrity first: `packet.py check` answered manifest
`c4cf8e64…` with `engine_invoked: false`.

**One probe invocation, exactly as printed. It did not succeed.** The durable
`ENGINE-RECEIPT/state.json` records:

    state              failed-or-uncertain
    success            false
    calls              one preflight `inspect w325695-proof-376414`, status 1
    errors             one execution-phase ValueError
    exact_absence      false
    create_intent      false
    owned              false
    container_id       null
    provider_invoked   false
    elapsed_seconds    0.0189

So **nothing was created, nothing is owned and no provider ran** — the
fail-closed path held. No retry and no rebuild, as the owner directed.

**The cause, and only what is measured.** I checked the preflight call two
ways: a direct `docker inspect w325695-proof-376414` answers `[]` with
`error: no such object` and exit 0 at the shell, and the SAME call through a
nested `subprocess.run` answers `returncode 1` with that identical
`no such object` stderr. **So this is NOT a socket denial** — the nested call
reached the daemon and got the ordinary absence answer. The receipt shows the
runner took that status 1 and left `exact_absence` false, after which the
execution phase raised `ValueError`. The blocker is therefore in the packet
runner's own classification of an ordinary absent-container answer, not in
the environment.

I am deliberately not asserting more than that. The review already corrected
one causal claim of mine this Work — the all-layers-cached explanation for the
0.414s build, which `build.log` contradicts — and I am not replacing it with a
second guess. What is established is the receipt, the two measurements above
and the zero-effect state.

**Still unproved, and this is the whole point of the probe:** actual mount
replacement resistance, descendants and nested validator use inside the real
image, root binding, per-root ENOSPC and exact-container cleanup. The payload
never ran.

Verification spending this claim: one read-only packet check, one selected
probe invocation (0.0189s to its refusal) and two read-only `inspect`
measurements. No rebuild, no retry, no provider, no deployment, no Git action.

## claim376852 — the corrected absence harness, separately retained

Answers review 2026-10-28T19-49-07Z. New directory `preparation-376852/`;
`preparation-376414` and both its receipts are READ-ONLY references and were
not edited. No engine probe, build, provider, deployment, removal or version-
control mutation. E376729 is spent and corrected execution needs a later exact
owner selection — I made none.

    absence.py        5666e981f94a255801846eb8557dbbf1f1552f3bc20fd4ae0696830745fee8ac
    test_absence.py   4ec0a3e70e477e1087dfe265991578627fbcfdf1e44c6d5e6ec7e9e6c841e7cf
    PINS.json         aa10d888619c41a04394a6d7830e0e542ac15c459885888f1a0781bd153850b7

**The defect, as the review names it.** `engine-proof.py`'s `Proof.inspect`
required a non-empty stdout and an uppercase-only error, so it refused the
SUPPORTED exact-name absence answer — exit 1, `[]`, lowercase
`error: no such object`. `exact_absence` stayed false and the execution phase
raised with nothing created. The same defect sat in the final cleanup absence
check, which is the worse half: a cleanup that cannot recognise "gone" cannot
report that it is.

**AND A CORRECTION TO MY OWN CLAIM, which the review was right about.** I
reported that failure as "not a socket denial", reasoning from two shell
measurements I took afterwards. That is unproved: the original receipt records
no stdout or stderr, so what the runner actually saw is not in evidence. I am
withdrawing the causal assertion. `absence.classify` now records BOTH streams
with the status and the name on every answer, so the next run cannot leave the
same question open.

**The closed classification.** `ABSENT` only when the engine answered, for
THIS exact name, that it is not there; `PRESENT` only with a document for this
exact name; `UNCERTAIN` for everything else — permission denied, daemon
unreachable, malformed JSON, a document for a DIFFERENT name, mixed output, an
unrecognised exit status. `proved_absent` is true for `ABSENT` alone, so an
unreadable answer never stands in for absence and nothing may be removed or
declared clean on one. The uncertain-create, exact-identity, deadline and
cleanup protections are preserved rather than relaxed.

**Verification:** 16 focused deterministic cases, all passing, no engine
invoked. They include the exact observed shape Selection B met, empty-stdout
and uppercase variants, the no-such-container spelling, the zero-status empty
array, present-for-this-name, a document for ANOTHER name as uncertain,
permission/daemon/malformed/mixed/multi-object/unknown-status refusals, the
lost-create answer staying uncertain, and both streams retained.

### Remaining

The corrected harness is not wired into a runnable packet and no selection
command is proposed as executable: the review's own handoff keeps execution
behind a later owner selection, and the `engine-proof.py` call sites that
would consume `classify` — preflight and final cleanup — are in the preserved
packet I may not edit. Composing a successor packet around this classifier,
with its own pins and selection command, is the next bounded step.

## claim376896 — all four counterexamples closed; the runner still absent

Answers review 2026-10-28T19-55-29Z. All four were real and all four were
mine. `preparation-376852/` updated in place (it is my own preparation, not
the preserved 376414):

    absence.py       55461a9ffdcbc7bf45c19d5a50578ebf33508ac2620c3b60975eaf6808413410
    test_absence.py  086f14e0d58c16975896a27e8424e3c47dd07555e071692990bb80bb9587b34d
    PINS.json        5970fb26264473d06be874cbcf4cc4822f04b70e32e079a074b75a01b2c821ee

1. **Foreign-name absence was accepted.** The substring test matched
   `no such object` anywhere, so a message about `somebody-else` classified
   this object ABSENT. `_names_this_object` now requires the reason to name
   THIS object immediately after the phrase; otherwise the answer is
   `no such object, but not this one` and uncertain.
2. **A mixed denial plus no-such-object became ABSENT** — the dangerous
   direction. Any access/reachability word anywhere in the error text now
   makes the answer uncertain BEFORE the object phrase is considered.
3. **Zero status with `[]` and a denial on stderr became ABSENT.** An answer
   this caller could not fully obtain is uncertain whatever the status says.
4. **`[{}]` became PRESENT**, because a missing `Name` was tolerated. The
   document must now positively identify this name by `Name` or `Id`; one
   that does not say which object it describes describes none.

**And two of my own test expectations were wrong, which is why 16 cases
passed over four defects.** One variant asserted ABSENT for a reason naming
another object (`x`) — exactly counterexample 1 — and my "observed direct
shape" label claimed more than I measured: what I observed was a shell and a
child process, not this runner. Both are corrected in place, and the module
docstring now withdraws that claim alongside the socket-denial one.

    21 focused deterministic cases, all passing, no engine invoked

The four counterexamples are each driven directly, plus identity matching by
`Name` with and without the leading slash and by `Id`.

### Remaining — the composed runner

There is still **no runnable successor**. The review is explicit that
preserving `preparation-376414` prohibits editing it, not composing a
successor, so this is in scope and simply not done: a successor runner that
calls this classifier at BOTH preflight and final cleanup, with bounded safe
durable diagnostics, its own pins and provenance, a proposed exact selection
command and an unused-receipt check, and deterministic proof of occupied
refusal without removal, lost-create uncertainty, removal and final absence,
and deadline/receipt behaviour. The classifier is the piece those call sites
need and it is now correct; composing them around it is the next step.

No engine, build, provider, deployment, cleanup or version-control action.
E376729 is spent and I made no selection. Kernel acceptance unproved.

## claim376978 — returned without a fifth classifier-only patch

Review 2026-10-28T20-00-26Z. The tree is unchanged by this claim:
`preparation-376852/absence.py` `55461a9f…` and `test_absence.py` `086f14e0…`
are exactly the claim376896 bytes, and `preparation-376414` with both its
receipts is untouched.

**Why no edit.** The review says to keep ONE COUPLED MILESTONE and that helper
tests alone cannot establish the required behaviours. I have now submitted the
classifier alone twice; a third pass at it, without its two consumers, would be
the same shape refused four times. The design below is exact enough to
implement with the runner in one claim, which is what the milestone asks for.

### The four retained counterexamples

1. `_names_this_object`'s `startswith` accepts an EXACT-NAME-OTHER identifier —
   `no such object: <name>-other` begins with `<name>` and passed.
2. The keyword blacklist misses a mixed I/O error at status 1.
3. It misses the same at status 0.
4. It REJECTS a supported response, `Error response from daemon: No such
   container: <exact reference>`, because `daemon` is a blacklisted word.

Counterexamples 2–4 are one fault with two faces: a blacklist both
over-rejects and under-rejects, which is why the review says not to grow one.

### The closed design, replacing the blacklist entirely

**Match the WHOLE stderr against a closed set of supported responses, each
generated from the exact identifier bytes.** Strip, compare
case-insensitively, and accept only an exact whole-message equality against
one of:

    Error: No such object: <reference>
    Error: No such container: <reference>
    Error response from daemon: No such container: <reference>

Nothing else is absence. Extra text, a prefix, a suffix, several messages, or
any other error is UNCERTAIN — by construction rather than by keyword, so
there is no list to grow and no supported response to accidentally reject.
`<reference>` is the exact name or id the caller asked about, so
`<name>-other` fails equality instead of passing a prefix test.

**Zero-status `[]` becomes UNCERTAIN.** The review is explicit that it stays
uncertain absent concrete support; I had admitted it on my own reading of
"some engines", which is not support.

### What must ship with it, in one claim

The composed successor runner calling the classifier at BOTH preflight and
final cleanup; bounded safe durable diagnostics; preserved image, payload,
layout and ORIGINAL receipts; its own pins; a proposed exact selection command
and an unused-receipt check. Then the deterministic proof the review lists:
exact supported absence through the composed runner; foreign, mixed, malformed,
permission and daemon-uncertain answers; occupied refusal WITHOUT removal;
strict acquisition; lost-create uncertainty despite a later absence; removal
and final observation; and deadline with cleanup reserve.

Verification spending this claim: read-only reading of the review. No run,
because nothing was changed. No engine, build, provider, deploy, cleanup or
version-control action. E376729 is spent; kernel acceptance unproved.

## 2026-10-28 — baton.codxpc claim E377003, successor preparation

Canonical state read then standalone claim succeeded. Complete 88 work events through E377003 and all 15 T325695 messages through M376434 read, no continuation; full FINDING/PLAN/PROGRESS and newest reviews consumed. Current E376998 reassigns serial preparation only. Revalidated original 32-file packet manifest c4cf8e64…; source build/selection already accepted, original invocation remains failed with unknown original streams. Original parser requires EMPTY stdout, not nonempty. New preparation-377003 owns runner/packet/tests/evidence; copies payload and layout exactly, preserves preparation-376414 including both receipts and preparation-376852 (PROVENANCE.json hashes all retained files). No product edits or engine/build/provider/operational execution selected. W321776 gate unchanged. Historical measured spending above remains; aggregate unknown. New claim verification starts at zero.

Implementation follows current pinned exact-response ruling: normalize supported diagnostic prefix only, preserve identifier bytes; no blacklist, extra diagnostics or status-zero empty array as absence. Both preflight and final cleanup must use the same reader, with strict full ID/image/label/user acquisition and bounded safe durable classification evidence. Original 120s total, 40s cleanup reserve, 20s receipt window and lost-create uncertainty preserved.

### E377003 completed successor — awaiting independent review

New preparation-377003 is a complete check/run packet; OPERATOR.md contains proposed exact command and boundaries. Packet manifest SHA256 cdfd88a8cce5191251bae49a0ce28034a1cb2f69936eb659b1e03dbd6762dc53; selection SHA256 48bf5fc7a890c652f3a64f817b25279113e7617b85c3e2f59df812fe677753b2. Inline classifier in engine-proof.py is bound by the existing selection runner digest, so there is no unbound helper dependency. Same image, diagnostic UID/GID, layout and payload; fresh proof identity377003. No rebuild proposed and no ENGINE-RECEIPT created in retained packet. All42 original/historical input pins match; both preparations and original receipts remain unchanged.

Both preflight and final cleanup use closed complete diagnostic matching (prefix case only; identifier bytes exact); no blacklist/status-zero-empty absence. Present observation requires full ID and queried reference, then acquisition checks Name/image/label/user and saved ID. Lost-create absence remains uncertain. Bounded durable diagnostics store stream lengths/hashes and closed classification, never arbitrary text; successful fixed fields and validated capacity/PID evidence are retained. The original subprocess capture mechanism remains; this is not a streaming memory-bound claim. Existing deadlines and independent final observation survive remove errors.

Tests: copied original runner cases (Name fact added to synthetic inspect for stricter ownership); new test_successor.py drives reviewer counterexamples through BOTH consumers plus acquisition, lost-create, removal/deadline and safe diagnostics; new test_packet.py drives check, refusals, exact selected entry with fake engine, used receipt and drift. Final20/20 pass, 0.224364272s measured wall (focused.log, VERIFICATION.json). Prior5 tests 0.038694574s measured;11 tests0.117s and3 tests0.021s rounded unittest reports. Claim test spending approximately0.401058846s with that precision caveat; final read-only packet check 0.021092733s separately. Historical cumulative total remains unknown and earlier evidence/costs above are preserved. No failures in these runs, engine/provider/build/deployment/operational cleanup/product edits or Git mutations.

Handoff to baton.bug for exact packet review. Remaining AFTER preparation acceptance: later owner selection of corrected probe, actual kernel/capacity/cleanup proof and independent joined acceptance. E376729 remains spent and W321776 gate unchanged. No kernel result claimed from simulated responses.

## claim377728 — the one selected probe ran, and the kernel acceptance PASSED

Owner selection E377680 (baton.slaw) selected one `preparation-377003` probe.
This claim executed it **once**, collected the receipt, and changed no source.
The packet is baton.codxpc's (E377003) and I did not edit it; what is mine here
is the invocation, the evidence and this section.

### Integrity before the run, as the selection required

    python3 -B .../preparation-377003/packet.py check
    {"engine_invoked": false, "packet_sha256": "cdfd88a8cce5191251bae49a0ce28034a1cb2f69936eb659b1e03dbd6762dc53",
     "receipt_unused": true, "selection_sha256": "48bf5fc7a890c652f3a64f817b25279113e7617b85c3e2f59df812fe677753b2"}

The selection digest equals the one the owner named and the one
review-2026-10-28T20-14-59Z.md accepted; `ENGINE-RECEIPT` did not exist.

### The invocation — exactly the reviewed command, once

    python3 -B work/records/2026/10/finding-v12-verifier-descriptor-descendants/preparation-377003/packet.py run \
        --owner-selected --selection-sha256 48bf5fc7a890c652f3a64f817b25279113e7617b85c3e2f59df812fe677753b2
    EXIT=0

Nine engine calls, no retry, **0.710 s elapsed** against a 120 s budget with a
40 s cleanup reserve. I added no engine call of my own: the pre-run socket
reading was `ls`/`test` on the socket file, not an engine invocation, and I did
not probe `docker version` — the packet is built to classify whatever the
engine answers, including a denial, and an extra probe would have been an
unselected engine call.

### The outcome

    state finished | success true | exact_absence true | errors []
    create_intent true | owned true | provider_invoked false
    container f901652af7aca4262d4de13ad5ad1be6dde77e414b37d152730e016f526e9667
    cleanup_status 0 | proof_observed true

**The payload — this is the kernel/mount question this Work opened on
2026-10-18, answered:**

    mount_binding         passed
    ordinary_grandchild   passed      <- the defect itself
    nested_validator      passed
    descendant_started    9
    product_mount_checks  passed
    image_bytes           passed
    capacity_enospc       passed
      HOME                4190208 of 4194304 bytes, then ENOSPC
      XDG_CACHE_HOME      4190208 of 4194304 bytes, then ENOSPC
      PYTHONPYCACHEPREFIX 7520256 of 8388608 bytes, then ENOSPC
      TMPDIR             16773120 of 16777216 bytes, then ENOSPC

So: the verifier roots arrive as **ordinary pathnames a grandchild can
resolve** — nine descendants started and the ordinary-grandchild and
nested-validator checks passed, which is exactly the failure
`/proc/self/fd/<n>` roots produced and exactly what `ef703336` corrected. The
per-root tmpfs quotas are **real and kernel-enforced**: each of the four roots
wrote to within 4 KiB of its configured size and then took `ENOSPC`, which is
the `SELECTED_SCRATCH_MOUNTS` table behaving as composed rather than as
documented.

### The corrected classifier is what made the run possible

Every inspection classified by exact closed response, both streams recorded as
length plus SHA-256 and no engine text copied:

    preflight         absent   exact-no-such-object   status 1
    acquire-created   present  exact-object           status 0
    running           present  exact-object           status 0
    confirm-absence   absent   exact-no-such-object   status 1

The **preflight** line is the one that matters for the history of this Work:
Selection B died there because the old parser refused the supported absence
answer. The successor accepted it, and the independent `confirm-absence` after
`rm --force` closed the cleanup honestly rather than assuming it.

### Integrity after the run, and the no-retry guard

All **10 packet pins** and all **42 preserved inputs** still match; the only
new byte in the tree is
`preparation-377003/ENGINE-RECEIPT/state.json` (15152 bytes,
`992a374394a43d9ced6e7edc10d2ce97f1e3c2e25ae97d1a97fac3de3be29123`).
`packet.py check` now raises `successor receipt already used; no retry` — the
guard works, the selection is spent, and I did not and will not re-run it.
`preparation-376414` with both receipts and `preparation-376852` are untouched.

### What this does and does not establish

It establishes the mount topology, descendant path resolution and per-root
capacity behaviour of image
`sha256:47e733834bb690fd4601e102f81e527a08b6ffe55da8b8cb345f45edfcb1517e`
under the selected diagnostic parameters. It is **not** a live-latency,
full-workload-fit or installed-manager execution claim, and no provider or
credential was involved (`provider_invoked: false`, `--network none`,
`--pull never`, no host binds). Acceptance is the reviewer's; I am not closing
this Work and W321776's gate is unchanged until that review lands.

Evidence: `evidence/claim-377728/RUN.json`, and the receipt itself at the path
and digest above.

Verification spending this claim: the read-only packet check, one selected
probe of nine engine calls totalling 0.710 s, and the post-run integrity
recomputation. No build, pull, rebuild, retry, provider, credential,
deployment, retained-instance mutation, product source change or Git action.
