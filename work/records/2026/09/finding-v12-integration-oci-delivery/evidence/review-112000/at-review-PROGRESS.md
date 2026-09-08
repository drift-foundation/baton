# Progress

## 2026-09-07 — baton.claude — the boundary revalidated and adopted

PLAN item 2, complete; accepted by independent review at claim 111240. The
revalidation, the pinned names, the pinned binding companion, the free
container target, the confirmed-absent public assignment reader and the
confirmed import cycle are in `FINDING.md`.


## 2026-09-07 — baton.claude — the three-mount family, implemented

PLAN item 3, complete. State: **awaiting independent review of the seven-path
candidate**. Nothing in the adopted boundary was superseded; every pinned name
and decision is implemented as written.

### The owner, and why the mounts could not be ordinary ones

`integration/oci_delivery.py` is new and VCS-neutral. It mints one frozen
`IntegrationMountBoundary` from the real coordinator and manager stores, the
fixed integration profile, the exact `IntegrationDelivery`, the published
assignment, the manager-minted `WorkspaceGroup` and an explicit nominated
target. Three fixed binds and no fourth: the assignment namespace read-only at
`/run/baton/integration/assignment`, the result namespace writable at
`/run/baton/integration/result`, and the configured canonical target writable
at `/target`.

A plain mapping, a bare triple, a direct construction or a caller-authored
writable flag authorizes none of it — the same rule the credential, launch,
exchange and source families are already under, and four cases drive it.

### The assignment is compared three ways, and they are three questions

The published document, a freshly composed one, and the digest. **The fresh
composition is the live proof and the published one is the identity**, and
conflating them is the trap this boundary exists to avoid: an assignment stays
readable after the grant that authorized it has ended, so a boundary that
compared only the published bytes would compose a mount plan for a lease
nobody holds. `compose_assignment` reads the grant from the coordinator in the
same call, so a blocked, abandoned or re-fenced target refuses here. One case
publishes an assignment, blocks the target, and asserts the reader still
answers the document while the composition refuses — which is the distinction
stated as an executable fact rather than as prose.

### The target is nominated, never derived, and never repaired

The canonical target id is an opaque coordinator identity; where that target
lives is a deployment fact. So it arrives as an `IntegrationTarget` minted over
a `nominate_source` proof rather than as a locator computed from the id — a
host path derived from an opaque id would let whoever controls the id choose
the directory. A target replaced between nomination and composition resolves to
the same spelling and a different inode and is refused rather than re-resolved
into a new acceptable directory.

**A nominal RW bind does not make the target writable**, and the module says so
where somebody would otherwise assume it. `prove_target_posture` answers the
one thing a deployment can be told before a container exists — that the target
root carries the configured group and is group-writable — and an incompatible
target refuses for exact operator provisioning. No recursive repair, no
ownership change, no ACL workaround, no stronger container privilege; a case
asserts the mode is untouched after the refusal.

### The private immutable companion

`mount-binding.json` at `<delivery.root>/mount-binding.json`, beside the two
mounted namespaces and never inside one — a document describing a mount,
written where that mount exposes it, is a document the runtime could rewrite to
describe itself. Closed members, published through `runtime`'s own no-clobber
atomic write. **No runtime id and no lifecycle state**: `oci.py` owns the
runtime journal and a second document carrying one would be a second account of
one lifecycle. A conflicting retained binding is an inspectable refusal and is
never reconstructed as though it had always been this plan, because what the
old container was actually given is the evidence an operator needs.

### The final proof is a cutpoint, and the module says so

`revalidate_boundary` re-asks every question with nothing between it and
`EnginePort` but the call: the grant from the coordinator again, the published
assignment again, the retained binding again, and each of the three directories
re-identified by device and inode. It is wired into `OciAdapter.start` AFTER
the duplicate probe, the workspace proof and the vector, because all three can
spend time and a grant can be blocked inside that window. Two cases inject a
change during that window — a block at the duplicate probe, and a target swap —
and assert **zero engine run calls**.

**And what it cannot claim is stated rather than left implied.** A grant
blocked after the bind does not unmount it; no label, timeout or fence stops a
running writer; the existing predecessor-runtime and settlement gates are what
keep a successor from starting behind an unquiesced writer. An atomic guarantee
across a hostile concurrent operator action and the daemon's own resolution is
not proved by this slice and is not asserted by it.

The boundary carries the exact stores and profile it was composed against, so
the proof reads the coordinator the composition used. A callback returning
`True`, or handles supplied at proof time, would be the substitute the plan
forbids.

### The observed mounts are asked of the engine

`observed_disagreement` names the same four mistakes `_mounts_disagree` does —
unreadable, missing, foreign source, wrong access — plus the fifth that is easy
to forget: an extra bind at or below one of the three fixed targets, which a
comparison that only looked for what it expected would never see. An engine
whose shape cannot be read returns a REASON rather than agreement: an
integration whose mounts are unproved is uncertain, and uncertain is held.

### The import cycle, handled where the adoption said it must be

`worker_manager` imports nothing from `integration`, so the resolution is
inside `_integration_mounts` and inside the two adapter methods. Two cases
hold it: fresh subprocess imports in both orders, and an AST walk asserting
`oci.py` names no integration module at import time.

### One measured fact recorded rather than contrived

The both-directions containment loop in `run_vector` is currently
**unreachable through the accepted families**: `_mounts` confines every
ordinary mount to the two assignment roots' fixed targets and refuses a
`/target` mount on its own rule before the integration family is composed. The
case records that measurement instead of manufacturing a collision the public
surface cannot produce. The loop stays, as a second fence for whatever is added
next.

### Verification

    PYTHONPATH=src python3 -m unittest tests.manager.test_oci_integration -q
    PYTHONPATH=src python3 -m unittest tests.integration.test_runtime -q
    PYTHONPATH=src python3 -m unittest tests.manager.test_dependencies -q
    PYTHONPATH=src python3 -m unittest tests.tools.test_parallel_runner -q
    PYTHONPATH=src python3 -m unittest discover -s tests -t .

`tests.manager.test_oci_integration` is 38 passing, new.
`tests.integration.test_runtime` is 126 passing — 120 before, plus six.
`tests.manager.test_dependencies` and `tests.manager.test_oci` pass together at
147. The registry gate reports only its previously recorded condition.

**One defect this Work introduced and corrected before handoff:** the reader
class first subclassed `TheDeliveryIsDurableAndManagerCustodied`, which is a
live `TestCase` — so all of its cases re-ran under a second name and the
subtree count was inflated by twenty-two. It composes its own delivery now.
Recorded because the inflated number reached one gate run.

**The canonical subtree gate: 4731 tests in 248.5s, 13 failures, 1 error, 21
skipped.** It is handed over red and the attribution is exact:

- **Eleven failures and the one error are the standing baseline**, unchanged in
  count and distribution from the run before this change: six
  boundary-inventory failures over `attempts.py`, `lanes.py` and
  `review_cycles.py`; two `test_worker_container`, one
  `test_credentials_engine` and one `test_output_custody_engine` cleanup
  failure from a live Docker daemon's leftovers; one authority-catalog failure
  over an unregistered `test_work_label_exposure.py`; and the registry error
  naming `tests.integration.test_driver` and
  `tests.job_manager.test_review_driver`.
- **`test_every_public_parameter_is_a_declared_operand` was mine and is
  fixed.** The new `integration_delivered` operand needed declaring in
  `test_dependencies.py`, which is one of this Work's seven paths. Only the
  `run_vector` spelling is declared: that inventory walks public FUNCTIONS, so
  declaring `OciAdapter`'s constructor parameter made the staleness gate beside
  it fail, which is the correct answer and is recorded in the comment there.
- **Two failures are NOT this Work's and are not mine to fix while I hold it.**
  `TheWorkerCompletionTraversesPublicCustody`'s two cases appeared in
  `tests/job_manager/test_review_driver.py` during this turn — that file
  changed under me from `65b9e9fe…` to `048f79a1…`, it is W110772's owned path
  rather than one of this Work's seven, and their assertion is about a
  `cleanup` step in the review ending. Nothing in this change touches
  `review_driver.py` or anything it calls. Reported rather than silently
  absorbed or quietly repaired in somebody else's file.

### Candidate

| Path | SHA-256 |
| --- | --- |
| `v12/python/src/baton_v12/integration/oci_delivery.py` | `85c6ff810d74beaa07e87dcd0be3817d66763d5269106433f5714a45bce0b5f9` |
| `v12/python/src/baton_v12/integration/runtime.py` | `d20960b7e255bae0479bd0b500925dd5f50ac39e56a835680dd5b25e5cc4bcab` |
| `v12/python/src/baton_v12/worker_manager/oci.py` | `b3940f22ad19a04eb96cdf1f50573877d95182b2e038610b68d2c7be16f43d18` |
| `v12/python/tests/manager/test_oci_integration.py` | `bb0402cf431c2ed93340d31fa7374469e02d55692004817375f1c9cbd3747824` |
| `v12/python/tests/integration/test_runtime.py` | `76dce0c03f1b94a5cad5df0cf146a5b96132eb5f7eba771377f34407b04c640d` |
| `v12/python/tests/manager/test_dependencies.py` | `89b00e126443f1e49227cffb57de956abaf3303dff84bbd4da0edc75abe74130` |
| `v12/python/tools/parallel_test.py` | `39b161a50e6e58ecfa6001c022532c23f9518779c85ce94c9dd1dace624318be` |

Exactly the seven paths `FINDING.md` scheduled. Nothing in `attempts`, `queue`,
`execution`, `stage_execution`, `single_worker`, `claude_agent`, worker recipes
or deployment configuration was edited. `test_dependencies.py` gained one
declared operand and its comment and no assertion changed; `parallel_test.py`
gained the one additive registration.

### What this does NOT claim

No live daemon ran for this slice, no container was created and no canonical
target was mutated: the run seam is a recorded callable throughout. The
candidate bundle and instruction-digest verification at `/input/source` remain
W110935's. Pre-admission attempt preparation and asynchronous integration
observation and settlement remain W110774's, which this delivers into rather
than performs.


## 2026-09-07 — baton.claude — the six findings, corrected

Reclaimed after `review-2026-09-07T16-04-48Z.md`. All six reproduced before I
changed anything and all six were real. Corrections are inside the existing
seven paths; the dated adoption above is unchanged and nothing was widened.
State: **awaiting independent review of the corrected candidate**.

### P1 — the family was composed regardless of posture

A consent runtime mounts nothing, holds no supplementary group and exists to be
asked a question. This family was appended independently of the posture
restrictions, so one started with a **writable result namespace and a writable
canonical target** — the opposite of what that posture means. Execution is now
required at both accepted surfaces: `run_vector` refuses the vector, and
`OciAdapter` refuses at construction the way source delivery already did. Two
cases drive both.

### P1 — nothing asked who the start was for

The final proof compared the boundary's stored assignment against a fresh
composition **through its own profile**, which is the document agreeing with
itself. The reviewer started one engine runtime labelled `baton.foreign` under
a grant held by `baton.merge`, and every check passed because none of them
asked. The labelled participant now crosses into `revalidate_boundary` and is
compared against the grant's `integrator_participant`. The case asserts zero
engine runs.

### P1 — the overlap check compared the three new sources with each other

`_no_overlap`'s `extra` operand was never supplied, and `run_vector` compared
container targets only. One host directory was bound writable at `/output` and
writable at `/target` — two names for one tree, with the ordinary workspace
rules applying to one and none of them applying to the other. The fixed
container-target enumeration cannot establish this: two distinct container
paths is exactly the arrangement, and the question is about the host.

Every other family's host sources now cross into the check, in both containment
directions — **and the assignment roots themselves**, whether or not a mount
names them. That last part is not a detail: `assigned` is empty when no
`mounts` operand is supplied, so a target aliasing the workspace would still
have been compared against nothing.

### P1 — the posture proof had no production caller

`prove_target_posture` was a helper nobody called, so a start reached the engine
with an incompatible target and the deployment learned about it from a failing
integrator. It is called at composition and again at the final proof.

**And group-write alone was not access.** A directory the runtime's group
cannot execute is one it cannot enter, so the write bit describes a permission
it can never reach; traversal is required too.

**The namespaces are re-adopted rather than re-identified.** Comparing inodes
says the directory is the same one and says nothing about its mode or group — a
result namespace changed to `0777` during the duplicate lookup still reached
the engine. `adopt_delivery` is the accepted owner of exactly those questions,
so the final proof asks it again. The group is bound to the boundary rather
than left for the adapter and the delivery to choose separately.

**And the published assignment's mode is proved.** The reader established
bounded regular content and not the mode, so an assignment sitting at `0666`
composed. `_read_bounded` takes an expected mode and proves it on the
descriptor, like the type.

### P1 — recovery could mint what it was recovering, and observation was optional

Publication and recovery were one act. It published whenever the companion was
absent, so **a removed binding was silently recreated with identical bytes** and
the evidence that it had ever gone was destroyed by the act of looking. And the
only minting path required a fresh grant, so a blocked target left a running
container nobody could reach through the public surface.

They are two functions now. `compose_mount_boundary` publishes and requires the
live grant, because that is the act that authorizes a writable bind.
`adopt_mount_boundary` **requires** the retained provenance, re-adopts the
namespaces at their exact modes and configured group, re-identifies every
recorded directory, grants nothing and composes nothing — and
`revalidate_boundary` refuses a recovered boundary outright, because the one
thing an adopted plan may never do is start a runtime.

**Observation is wired rather than offered.** A returned identity says the
engine created something and nothing about what it holds; `start` answered
success while ordinary observation reported a running runtime with no
integration binds at all. `start` now observes, and the two outcomes stay
different: a container the engine positively describes with the wrong binds
takes the same post-create settlement every other exit here takes, while an
observation that could not be READ answers the runtime id **with the
uncertainty beside it** — a caller that cannot name the container cannot stop
it, and inventing a teardown from an unreadable answer is the automatic
recovery this boundary does not have.

**The comparator missed ancestor shadowing.** It looked only at or below an
expected target, so `/run/baton/integration` — the parent of two of the three —
was reported as agreement while shadowing both. Both directions now, with an
unrelated bind still left alone.

### P2 — the boundary was frozen only at the top

Blocking attribute assignment while storing live dictionaries left the
assignment, the profile and every source editable through the public
attributes, and `boundary_mounts` then answered a caller's own access flag. The
copies are private and the public attributes are read-only views.

**Private copies rather than stored proxies**, deliberately: the accepted
boundary readers take exact built-in documents and refuse anything carrying
behaviour, so a proxy in the slot would make this object unusable by the very
owners it must be re-proved through.

### Two corrections to my own previous account

**`tests.integration.test_runtime` is 98 and was 92, not "126, 120 before".**
The earlier figure was measured while the subclassed-`TestCase` defect was
inflating it; I corrected the defect and did not re-measure the number I had
already written down. Six cases were added and six is right.

**The 4731 total in the previous entry was measured the same way** and is
superseded by the run below.

### Verification

    PYTHONPATH=src python3 -m unittest tests.manager.test_oci_integration -q
    PYTHONPATH=src python3 -m unittest tests.integration.test_runtime -q
    PYTHONPATH=src python3 -m unittest tests.manager.test_oci tests.manager.test_dependencies -q
    PYTHONPATH=src python3 -m unittest discover -s tests -t .

`tests.manager.test_oci_integration` is 58 passing — 38 before, plus the twenty
this correction adds. `tests.integration.test_runtime` is 98 passing. The four
focused suites run together at 303 passing.

**The canonical subtree gate: 4751 tests in 241.3s, 13 failures, 1 error, 21
skipped**, retained at
`evidence/implementation-111332/subtree-gate-corrected.txt`. Handed over red,
with the distribution **identical to the run before this correction** — no
failure was added and none was removed:

- six boundary-inventory, four engine-cleanup and one authority-catalog
  failure, plus the registry error naming the two untracked baseline modules:
  the standing baseline;
- two `TheWorkerCompletionTraversesPublicCustody` failures in
  `tests/job_manager/test_review_driver.py`, which is W110772's owned path
  rather than one of this Work's seven and which its own PLAN now records as an
  open blocker under separate disposition. Not mine to repair while holding
  this Work.

**On the previous handoff's "no live daemon" sentence**, which the review was
right to flag: it is true of this Work's focused mount fixture — the run seam is
a recorded callable and no daemon, container, provider or canonical-target
mutation is involved — and it is NOT a statement about the broad discover
command, which runs live-engine suites and produced four of the failures above.
The two claims are separate and are now written separately.

### Candidate

| Path | SHA-256 |
| --- | --- |
| `v12/python/src/baton_v12/integration/oci_delivery.py` | `5e5d8e1b57b26cd3e5697d9550fdb4daaafbf4b120dd6348bd94cd4c4c7f09c1` |
| `v12/python/src/baton_v12/integration/runtime.py` | `d76676e04d4917be39f723d670ce7ecb2fc5830ae9246e388a844e337806d2cb` |
| `v12/python/src/baton_v12/worker_manager/oci.py` | `2a7a23853e8d7a50cc357f9daa298d919f712c8978cac2b4acbda04608d354e4` |
| `v12/python/tests/manager/test_oci_integration.py` | `63fed3b757011ecc5e6c2f3a9b33766ff99690238d2befd08d9dfa5efca01cb0` |
| `v12/python/tests/integration/test_runtime.py` | `76dce0c03f1b94a5cad5df0cf146a5b96132eb5f7eba771377f34407b04c640d` |
| `v12/python/tests/manager/test_dependencies.py` | `89b00e126443f1e49227cffb57de956abaf3303dff84bbd4da0edc75abe74130` |
| `v12/python/tools/parallel_test.py` | `39b161a50e6e58ecfa6001c022532c23f9518779c85ce94c9dd1dace624318be` |

`test_runtime.py`, `test_dependencies.py` and `parallel_test.py` are
byte-identical to the reviewed candidate; four of the seven changed. Existing
assertions and prior registrations are preserved, and no manual-hold policy,
runtime journal ownership, fixed uid/gid or target byte or mode was touched.

### One case deliberately absent

A "target owned by another group" regression is not present: an ordinary uid
cannot `chown` a directory into a group it does not hold, so the case would
only run on some hosts. The group comparison itself is `adopt_delivery`'s and
has its own suite. Named rather than quietly skipped.


## 2026-09-07 — baton.claude — the five findings, corrected

Reclaimed after `review-2026-09-07T16-34-08Z.md`. All five reproduced before I
changed anything and all five were real. Corrections stay inside the seven
paths; the confirmed fixes from the previous round are untouched. State:
**awaiting independent review**.

### P1 — the start answer broke its own consumer's contract

I added `integration_mounts` to every integration start answer, and
`attempts._started` — the real consumer, one call after
`request_runtime_start` — admits `runtime_id` and `labels` and nothing else. So
every integration start refused at the parser **after the container existed**,
which is the worst place to fail. The nested tuple was a second, smaller
problem; converting it would not have helped, because the member itself is
unrecognised.

The answer keeps its closed shape. A case now asserts that shape and passes the
real adapter's real answer through the real `attempts._started`, so the
assertion is against the parser rather than against my copy of its member list.

### P1 — the overlap rule rejected a legitimate arrangement

Passing both the assignment roots and the ordinary mounts into one list, and
comparing every pair in the concatenation, meant the two lists were compared
against each other — and an assignment root is legitimately represented twice,
once as the logical root and once as the mount composed from it. A valid
`/output` bind therefore collided with its own workspace root, with zero runs.
The same rule threatened the accepted source-under-input nesting.

The pairs are now the integration sources among themselves, and each
integration source against each other capability. **Relationships among the
ordinary families stay with the owners that already decide them.** A positive
case composes ordinary `/input` and `/output` binds beside the integration
family and asserts all three arrive; the aliasing negatives still refuse.

### P1 — the uncertainty had no carrier

`attempts._observed` consumes `state` and `why` and deliberately ignores
`mounts`, and it is right to — mounts are not a runtime axis. So a container
inspected running with **no integration binds at all** reconciled as an
ordinary healthy runtime, the comparator that could have said otherwise was
optional and uncalled, and the start member I had added was not a usable
carrier either.

**The carrier is the state itself**, which is the one thing every consumer of
`observe` already reads. Missing, foreign or unreadable integration binds make
the observation `uncertain` with the reason attached — the manager's existing
vocabulary for "not evidence I can act on", and one that never stands for
absence, so nothing is released and no assignment advances on it.

Positive identity evidence is preserved: the runtime id, the candidate record
and the observed mounts all still travel, and stopping an exact runtime depends
on no fresh grant. Five cases drive it, including one through a **reconstructed**
boundary after a public target block, and one asserting an adapter with no
integration delivery observes exactly as before.

### P1 — the final custody proof was incomplete in three ways

The companion's mode was proved at publication and adoption and **not at the
final use point**, so changing `mount-binding.json` to `0666` during the
duplicate lookup still reached a run. The expected mode is supplied there now.

`_directory_identity` proved the leaf inode no-follow, which says nothing about
an **ancestor**: the reviewer moved a target's parent, put a link at its old
name, and the inode was identical while the engine — which canonicalizes what
it is given — would have bound the re-resolved path. The spelling this manager
holds must already be the one the kernel resolves to, which is
`nominate_source`'s own rule applied at every later use point.

And the group comparison was the boundary checking its own stored value against
itself. **The adapter's group crosses into the proof now**, because the
container is given the adapter's group and nothing established the two were one
grant.

### P2 — recovery accepted configuration drift

`adopt_mount_boundary` compared the opaque target id and then re-identified only
the paths in the companion, so a **different real directory** nominated under
the same id was accepted: the recovered object pointed at one tree while its
mounts still named another. The supplied nomination's place, device and inode
are compared against the recorded target source.

### What I proved and what I did not

The manager-parser case runs the real adapter's answer through the real
`attempts._started`. It is **not** a full `request_runtime_start` journal
episode, and I am not claiming one — the review's own probe was explicit about
the same limit. What is established is that the answer satisfies the contract
that refused it.

The observation cases drive the real `OciAdapter.observe` with a recorded
engine, which is the normal consumer path for that question, including through
a recovered boundary. They do not drive a full reconciliation sweep.

### Verification

    PYTHONPATH=src python3 -m unittest tests.manager.test_oci_integration -q
    PYTHONPATH=src python3 -m unittest tests.manager.test_oci tests.manager.test_dependencies tests.integration.test_runtime -q
    PYTHONPATH=src python3 -m unittest discover -s tests -t .

`tests.manager.test_oci_integration` is 69 passing — 58 before, plus eleven.
The four focused suites run together at 314 passing.

**The canonical subtree gate: 4762 tests in 239.2s, 13 failures, 1 error, 21
skipped**, retained at
`evidence/implementation-111332/subtree-gate-corrected-2.txt`. Handed over red,
with the distribution **identical to both previous runs** — nothing added,
nothing removed: six boundary-inventory, four engine-cleanup, one
authority-catalog, two `TheWorkerCompletionTraversesPublicCustody` failures in
W110772's owned path, and the registry error naming the two untracked baseline
modules. As before, the daemon-free claim is about this Work's focused fixture
and not about the broad discover command, which runs live-engine suites.

### Candidate

| Path | SHA-256 |
| --- | --- |
| `v12/python/src/baton_v12/integration/oci_delivery.py` | `4820072698107589c9deb5a2f3416a05f65b34d50b0481a2a9b1a933509a2a78` |
| `v12/python/src/baton_v12/integration/runtime.py` | `d76676e04d4917be39f723d670ce7ecb2fc5830ae9246e388a844e337806d2cb` |
| `v12/python/src/baton_v12/worker_manager/oci.py` | `68bb8831331ec1ac07b7b6bdb8a559573be348fe80ba796e50607d4b94af7b2f` |
| `v12/python/tests/manager/test_oci_integration.py` | `0c2907f5a7a4fd926c8bee1a4db3ad575a7aabcbf4c8d44c60c1cef88a435689` |
| `v12/python/tests/integration/test_runtime.py` | `76dce0c03f1b94a5cad5df0cf146a5b96132eb5f7eba771377f34407b04c640d` |
| `v12/python/tests/manager/test_dependencies.py` | `89b00e126443f1e49227cffb57de956abaf3303dff84bbd4da0edc75abe74130` |
| `v12/python/tools/parallel_test.py` | `39b161a50e6e58ecfa6001c022532c23f9518779c85ce94c9dd1dace624318be` |

Three of the seven changed; `runtime.py`, `test_runtime.py`,
`test_dependencies.py` and `parallel_test.py` are byte-identical to the
reviewed candidate. No `attempts.py` change and no document-contract change was
needed: the closed consumer boundary is satisfied by removing what I had added
to it rather than by widening it. Runtime journal ownership, manual holds and
fixed runtime permissions are untouched, and nothing repairs a permission.

### Two fixture facts recorded because both cost a debugging round

The adapter helper composed its default boundary unconditionally, so a case
supplying its own published a binding for the same attempt and then met its own
plan as a conflicting one. It is composed only when a case did not supply one.

And the ancestry probe's mutation fires once: the duplicate lookup calls the
engine more than once, and a second rename would be moving a symlink onto a
directory rather than reproducing the finding.

## 2026-09-07 — baton.tuner — claim111937 — recovery layout corrected

State: **awaiting independent review**. Owner reroute111935 and
`review-2026-09-07T16-58-23Z.md` assign the remaining fixed-layout correction.
I pinned scope and adoption in FINDING/PLAN before editing. All seven incoming
hashes matched the latest reviewed candidate.

The source change adds one complete sequence comparison in
`adopt_mount_boundary`, after its existing identity checks. The expected layout
comes from `_sources` of the re-adopted delivery and configured target. Recovery
now refuses role/path/access/order/multiplicity drift before returning its
nominal capability. The existing diagnostic refusals, read-only recovery,
start prohibition and grant-independent inspection/stop behavior are preserved.

Only `integration/oci_delivery.py`, `tests/manager/test_oci_integration.py` and
this dossier changed. The other five candidate paths retain their accepted
hashes. All previous mount-test bytes are preserved; nine methods were inserted
as a separate test class, with no changed or weakened prior assertion.

### Verification

Commands ran from `v12/python`:

    PYTHONPATH=src python3 -B -m unittest tests.manager.test_oci_integration.RecoveryRequiresTheCompleteFixedLayout -v
    PYTHONPATH=src python3 -B -m unittest tests.manager.test_oci_integration -v
    PYTHONPATH=src:. python3 -B ../../work/records/2026/09/finding-v12-integration-oci-delivery/evidence/tuner-111937/recovery_shape.py
    PYTHONPATH=src:. python3 -B ../../work/records/2026/09/finding-v12-integration-oci-delivery/evidence/tuner-111937/manager_path.py

- New recovery tests: **9 passed**. Complete mount module: **78 passed**
  (69 prior plus 9). Logs: `new-tests.txt`, `mount-module.txt`.
- The reviewer recovery probe was copied into this claim's evidence directory
  and run before/after the change. The three corrupt layouts previously adopted;
  all now refuse. The unchanged positive still adopts and observes running after
  grant loss. Results: `recovery-before.json`, `recovery-shape-results.json`.
- The copied public manager probe confirms one runtime start, reconstruction
  after a public block and stop to positive quiescence. Unreadable or later
  missing mounts preserve the uncertain axis and pending cleanup. Every scenario
  has exactly one engine run through the deterministic seam. Results:
  `manager-results.json`. Earlier review evidence was not edited or executed.
- `candidate.json` records the seven hashes, exact two-path scope and byte
  preservation audit. `delta-*.txt` and `candidate/` preserve the proposed bytes.
  Added lines pass whitespace checks.

The prior 245 affected-suite passes are reused for unchanged paths. The prior
broad evidence remains `evidence/implementation-111332/subtree-gate-corrected-2.txt`:
4762 tests, 13 failures, 1 error, 21 skipped. I did not repeat or declare that gate
green. Its recorded distribution is six inventory, four engine-cleanup, one
catalog, two W110772 custody failures and the registry error. This is the earlier
run's account, not a new verification of the current whole tree.

All execution in this claim used disposable fixtures and deterministic provider/
Authority/engine seams; no live daemon, container, provider, deployment or
canonical-target execution occurred. Public manager composition is proved, not
an entire live integration ending. W110774 remains gated pending review.

### Changed candidate hashes

- `v12/python/src/baton_v12/integration/oci_delivery.py`:
  `ccfa812ac3b6c4fa68d32bc4fcb25bf2c05c7220369af1b39dedc0aef8a08282`
- `v12/python/tests/manager/test_oci_integration.py`:
  `822bae5cb51c7f664c1f351aff9147957c930db3251c2e932330a7a125d301a6`

The complete seven-path account is `evidence/tuner-111937/candidate.json`.
Return to baton.bug for independent review of this bounded correction.
