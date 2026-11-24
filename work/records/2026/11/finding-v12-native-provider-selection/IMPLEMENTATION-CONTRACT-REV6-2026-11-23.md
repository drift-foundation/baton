# W385830 — proposed implementation contract, revision 6 (delta)

Author: baton.prompt (K, model Fable 5.2), interactive copilot, no claim.
2026-11-23. Authority: M385859 and the FINDING entry "Stable retained
provider homes — owner 2026-11-23".

**PROPOSED — NOT APPROVED.** Research and design only. Nothing built,
launched or tested; no provider call; no credential read; no runtime edit.

Base text: `IMPLEMENTATION-CONTRACT-PROPOSED-2026-11-23.md` as amended by
`-REV2-` to `-REV5-`; all five preserved unchanged. This file replaces the
"Home and credential" paragraph of first contract §4.5 and its decision D6,
withdraws REV5 §6 (the private memory mount I recommended was not selected),
adds the home's verification, records the overlap with W385853, and raises
the next decision.

## 1. Settled

| Settled by the owner | Source |
| --- | --- |
| The provider home is a **retained, disk-backed work area managed mechanically by Baton** | M385859 |
| **Each worker has its own stable home.** Implementation and review never share one, even on the same provider | M385859 |
| Baton does not rely on a provider or model choosing non-colliding subdirectories | M385859 |
| The home survives container stop, removal and replacement, and supported restart and resume. Its identity is not regenerated because a container or attempt restarts | M385859 |
| It is outside the source checkout and the proposal paths | M385859 |
| Credentials remain separately delivered. The operator's home is never exposed | M385859 |
| No elaborate access controls, and no extra permission gate for a successor to use the home: it is retained work storage | M385859 |
| Concurrent writers are kept apart by the existing execution ownership mechanism | M385859 |
| Retaining files does not assert that provider-session resume is implemented or qualified | M385859 |
| More elaborate sharing and model-switch behaviour is deferred | M385859 |

## 2. What exists today (surveyed for this revision)

| Fact | Where | Status |
| --- | --- | --- |
| No directory today is both writable in the container and keyed by worker. Per-attempt disk scratch is keyed by attempt; the Claude context store by Job and Work; the review line is a checkout | `worker_manager/workspaces.py:2184, 5682`; `provider_context.py:762-837`; `review_cycles.py:1219-1240` | Surveyed |
| The only per-worker path is the read-only source nomination `<instance>/repo/source-<worker_id>`; it shows the derivation pattern | `tools/pool.py:790-791` | Confirmed |
| An instance is one root with `db`, `repo`, `logs`, `state`; workers share `state/workspaces`, `state/launch`, `state/credentials` | `tools/pool.py:779-787`; `tools/instance.py:43-53` | Confirmed / Surveyed |
| Container mounts are fixed typed families composed in one place, each checked against nesting in another; there is no generic mount list | `worker_manager/oci.py:1551-1807` | Surveyed |
| Writable binds work because manager and worker share one execution identity and a workspace group | `oci.py:1438-1460`; `workspaces.py:464-488` | Surveyed |
| **One live allocation per worker** is a uniqueness rule in the Job store: a second admission to an occupied worker cannot be written | `job_manager/schema.py:312-314`; `scheduler.py:372-396` | Confirmed |
| A worker's slot is released when cleanup is `complete` or `retained`; a failed cleanup or uncertain runtime keeps it held as recovery-required | `scheduler.py:573-622` | Confirmed |
| A slot is also released for five ending kinds (`abandoned-after-restart`, `declined`, `expired`, `claim-refused`, `settlement-expired`) after a release-blocker check, without this code itself reading the runtime's state | `scheduler.py:33, 585-589` | Confirmed; whether a container can still be alive there is **not established** |
| Today's fresh Claude turn builds its home in private memory scratch, new for each child process; the context-bound path uses a per-use copy at `/run/baton/context/home` | `worker/claude_agent.py:3530`; `provider_context.py:32` | Confirmed |
| Nothing sweeps the instance root. The one enumerating deletion removes entries under the credential home that are not live attempts | `worker_manager/credentials.py:851-879` | Surveyed |
| The context store already refuses a storage root that overlaps the workspace root | `context_delivery.py:74-89` | Surveyed |

## 3. The provider home (replaces first contract §4.5 "Home and credential")

### 3.1 Binding: one worker, one home

- **Key.** Instance and worker id, nothing else. Not the attempt, the
  container, the Job, the phase, the profile digest, the model or the CLI
  build.
- **Place.** A new instance directory beside the existing ones:
  `<instance>/state/provider-homes/<worker_id>/`, containing `home/` (what
  the container sees) and a small manager-owned record beside it that the
  container never sees. Derived from the worker id exactly as the source
  nomination is; a deployment cannot name another location.
- **Declared.** One new member of the worker's deployment document, under a
  new deployment schema version. Workers composed under the earlier version
  have no home member and get exactly today's container.
- **Distinct.** Two workers of one instance always have different worker
  ids, so an implementation worker and a review worker cannot resolve to the
  same directory. No subdirectory convention inside the home is assumed or
  needed.
- **Mounted** writable at one constant container path, as a new typed mount
  family with the same no-nesting checks as the others. The path is not
  under `/tmp`, `/scratch`, `/input` or `/output`. Its exact spelling is
  fixed when the pinned builds are inventoried in their images, because the
  spike measured a build refusing some locations.
- **Used by every worker of the new composition**, Claude and Codex alike.
  The provider's home environment value points at it. The Claude
  context-bound path keeps its own home and is unchanged.

### 3.2 Outside the checkout, the proposal and the operator's home

Composition and start both refuse a home that is, contains or lies inside:
the workspace root, any source nomination, the launch home, the credential
home, the context store, the repository, or the operator's own home
directory entries for either provider. The existing overlap refusal for the
context store is the pattern. The home is not an output, is not in any
manifest, and is never sealed, collected or published.

### 3.3 Lifecycle

| Event | The home |
| --- | --- |
| First start of the worker | Created empty by the manager, owner-only, with the shared execution identity. Never seeded from the operator's home or any host configuration |
| Container stop, removal, replacement | Unchanged |
| Attempt end, cleanup, discard of execution roots | Unchanged. No existing cleanup names it, and it lies outside every directory one enumerates |
| Next attempt of the same worker — any Job, any phase that worker serves | The same directory, as left |
| Manager restart, reconcile, replay | The same directory; the path is re-derived, never re-minted |
| Correction, continuation, successor work on that worker | The same directory, with no additional gate |
| Removal | Only by an explicit operator act on the instance. Nothing automatic |

The record beside the home holds: worker id, creation time, and the attempt
currently holding it or the last one that did. It is how diagnostics can say
"this home was last written by attempt X".

Not selected and therefore not specified: any size bound on the home; any
expiry; what happens when a worker id is recomposed with a different
provider or model (the deferred model-switch question).

### 3.4 One writer at a time

1. **Primary: the worker's allocation.** One home per worker and one live
   allocation per worker means at most one admitted attempt can be entitled
   to the home.
2. **At the mount: the holder record.** Starting a container records the
   attempt as holder. A start that finds a different holder proceeds only
   when that holder's runtime is proved gone by the facts the system
   already settles (runtime absent or destroyed, cleanup `complete` or
   `retained`); otherwise it is refused and held, with a typed cause.

Step 2 exists because of the unestablished row in §2: I could not confirm
that every path which frees a worker's slot has first proved the previous
container gone. It reuses existing settled facts and adds no permission
gate: a successor passes automatically once the predecessor is known to
have stopped. If the implementer shows the allocation alone always implies
cessation, step 2 reduces to an assertion.

### 3.5 Credentials stay outside

- The credential is still delivered read-only at its existing place.
- The adapter makes it reachable from the home by a **link only**, created
  at each start and checked to point at the delivery. It is never copied
  into the home.
- At each start the adapter removes whatever is at the credential's home
  location if it is not that link. A provider that replaced the link with
  its own file therefore does not leave a credential in retained storage
  past the next start — but it would be there until then. Whether a pinned
  build does that is exactly what the next decision (§7) turns on.

### 3.6 What retention does and does not mean

Files persist. That is all. No resume flag is passed, no session is
selected, and no result may be described as continued from an earlier
session because the home held one. Provider-session reuse remains what it
was: the separate, Claude-only context path (first contract F12), unchanged
and not extended here.

## 4. Overlap with W385853 (worker instruction delivery, codexpc)

Read: its checkpoint E385856, `HANDOFF.md`, `LOADING-BOUNDARIES.md`, and
M385858/M385860 on T385853.

**Why the home matters to it.** Both provider programs look in their home
for global instructions and configuration. A retained, writable home means
a file a model wrote there in one attempt can be loaded as instruction or
configuration in a later one, covered by no digest. W385853's proof
obligations 4 ("private home cannot import unrelated host instructions")
and 6 (byte budget over the whole chain, global files included) therefore
have to treat this directory as part of the chain. Which home paths each
pinned build auto-loads is an inventory item for the image gate.

**What this contract provides for it.**

| Provision | Effect |
| --- | --- |
| The home is never seeded from the operator's home or host instruction files (§3.3) | Host-only guidance cannot arrive by that route |
| Each adapter has a closed list of **managed home entries** that Baton places at every start from digest-bound deliveries, replacing whatever is there. Today the list is the credential link | A fixed, reviewed place where a delivered worker-instruction or configuration file can be put, should W385853 select home placement |
| The managed-entry list and any delivered policy digest are part of the per-worker adapter identity (REV2) | The instruction selection is bound into admitted execution identity, which is what W385853's audit says is required |

**What it does not decide.** Whether worker policy is delivered by a home
file, a command-line operand or something else; how host-only guidance is
excluded; and whether retained provider-written files outside the managed
list should be neutralised. The first two are W385853's selector question.
The third would be an access control the owner has not selected; I flag it
and leave it.

**Shared paths and a proposed order (coordination proposal, not an
assignment).** Both Works touch `worker/claude_agent.py`,
`worker/Dockerfile.claude`, the context prompt/argv builders and the future
Codex adapter. Neither has started. Proposed: serial, slice N2 first, then
W385853's delivery delta on top of it — N2 creates the per-worker
command-and-configuration identity that W385853's digest has to bind into,
so the other order would build that binding twice. W385853's editorial
candidate (three document paths) overlaps nothing here and can be reviewed
now. Whether to record this as an explicit dependency, or to have W385830
consume W385853's policy candidate, is the owner's selection per W385853's
handoff; it is listed in §8.

## 5. Slices (amends first contract §5)

| Slice | Change |
| --- | --- |
| N2 | Adds: the provider-home hook in the adapter (where the home is, managed entries, credential link); the home family in the run vector; the deployment member and its derivation; the holder record and start check. The fresh-turn environment for new-composition workers is part of adapter identity /2 |
| N3 | No longer contains a mount of its own; the Codex adapter declares its managed entries against the 0.169.0 inventory |
| N4 | Engine-only gate additionally fixes the mount path spelling and records which home paths each pinned build reads at start |

## 6. Verification added (deterministic; N2)

Binding and identity:

1. Two workers of one instance — same provider, different roles — resolve
   to different homes; one worker resolves to the same home on every
   derivation.
2. A deployment naming a home other than the derived one is refused.
3. A file written in attempt 1 is present, byte-identical, in attempt 2 of
   the same worker — after a normal end, after a failed attempt, after
   container removal, and after a manager restart between them.
4. A different Job served by the same worker sees the same home; no
   approval or extra record is required for it.
5. A worker composed under the earlier deployment version has no home mount
   and an unchanged run vector, byte for byte.

Placement:

6. A home overlapping the workspace root, a source nomination, the launch
   or credential home, the context store or the repository is refused at
   composition and again at start.
7. The home never appears in an input manifest, an output, custody, a
   proposal or a sealed result.
8. Attempt cleanup, discard of execution roots and the credential-orphan
   sweep leave it untouched.
9. The mount source is always under the instance root; the operator's home
   is never a source or an ancestor of one.

One writer:

10. A second admission to a worker with a live allocation is refused
    (existing behaviour, asserted with a home present).
11. A start whose home names another holder whose runtime is not proved
    gone is refused and held; once that runtime is settled, the same start
    succeeds with no owner action.
12. Restart between recording the holder and starting the container replays
    to the same holder, not a second one.

Credentials and seeding:

13. The credential in the home is a link to the read-only delivery; its
    bytes exist nowhere under the home after a turn.
14. A regular file left at the credential location by a previous attempt is
    removed and replaced by the link before the provider starts.
15. A new home is empty apart from managed entries; nothing from the host
    is copied in.
16. Managed entries are re-placed at every start; a modified managed entry
    from a previous attempt does not survive.

Honesty:

17. No argv carries a resume or session operand because the home is
    non-empty, and no result or diagnostic describes a turn as resumed.
18. Diagnostics show the home's worker id, its holder and that it is
    retained.

## 7. The next decision for the owner

**Which kind of credential does the Codex worker use?** (D3.)

It comes next because the retained home changes what is at stake. With a
disposable home, anything a provider wrote beside its credential vanished
with the container. With a retained disk home, it stays.

What is known: the August spike ran Codex with a login credential file. A
login credential is refreshed by the program, which then writes the new one
back. The delivered credential here is a read-only file outside the home.
What 0.169.0 does when it cannot write a refreshed credential, or whether it
replaces the link with its own file, is unmeasured. I have read no
credential and no registry.

- **A — An API-key credential (recommended).** A fixed secret, delivered
  read-only like the Claude worker's, with nothing to refresh and nothing
  for the program to write back. The home never needs to hold credential
  material, so "credentials remain separately delivered" holds without
  depending on the program's behaviour. Cost: usage is billed and limited
  as API usage rather than under a login plan, and a key has to exist in
  the credential registry.
- **B — The login credential file, kept read-only.** Uses the existing
  login. Cost: once the delivered token ages, the program must refresh and
  cannot store the result; whether the turn then fails, continues, or
  writes a credential into the retained home is unknown until the first
  real-provider question is run — and the six-hour invocation ceiling makes
  a mid-turn refresh likely rather than rare.
- **C — The login credential file, with the program allowed to keep its
  refreshed copy in the home.** Long turns keep working. Cost: live
  credential material sits in retained work storage that any later attempt
  on that worker can read, and the registry's copy goes stale — which
  departs from "credentials remain separately delivered".

I recommend A. I have not assumed it. The answer names a kind only; which
registry entry it is, and any access to it, remain separate.

## 8. Decisions still open after that

| # | Decision | Unblocks |
| --- | --- | --- |
| W385853 order | Record the proposed serial order (N2, then W385853's delivery delta) as an explicit dependency, or select a different decomposition | Assignment of N2 and of W385853's continuation |
| D1 (Claude) | Whether the Claude pin stays on 2.1.247 or moves | N4 |
| D2 (values) | Selector and mapped identity for the Fable reviewer and the Codex implementer | N5 |
| D7 | Selection of the engine-only image gates and the two real-provider calls | N4, N5 |
| Deferred by M385859 | Model-switch and sharing behaviour for a home; not raised until selected | — |

## 9. Limits

- Nothing executed. The table in §2 comes from one read-only survey; I
  re-read the allocation uniqueness rule, the release logic, the instance
  layout and the current home construction myself, and took the rest as
  surveyed.
- §3.4 step 2 is my addition to close a gap I could not rule out. It is
  the one place this revision adds a check the ruling did not name; it
  consumes existing facts and gates nothing on the owner.
- The managed-entry list (§4) is my proposal for where delivered files go.
  It replaces only named entries and is not a control over the rest of the
  home.
- No size bound is proposed for the home because none was selected; a full
  disk would surface as an ordinary write failure in the worker.
- Applying the home to Claude workers of the new composition follows "each
  worker gets its own stable home". It moves the fresh Claude turn's home
  from per-child memory to retained disk for those workers, which changes
  what a later Claude turn can see; existing compositions are unaffected.
