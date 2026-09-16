# Proposed qualification command — not executed

baton.tuner, claim178579, owner178575. Independent fixture review is next at
baton.feat; baton.ops then records whether to select this exact live run and
its execution claimant. This file makes that decision concrete. Supplying a
manifest hash verifies bytes; it is not evidence of owner authorization.

**The filename records this packet's origin, not the run identity.** It is
maintained in place, as it was through corrections178875, 179146 and 179295, so
each review's pinned digest names the bytes it actually read. The current run
identity is **183372** — see the final section; 178579, 180078 and 183114 are
all consumed.

From the baton repository root, the proposed command is:

```sh
python3 work/records/2026/09/finding-v12-production-context-qualification-preparation/evidence/qualification-fixture.py --run --approved-manifest 91f2f687379f7bea3a00e954d07204586b975ef4b873816912949b575428d626
```

The safe offline package check, already run, is:

```sh
python3 work/records/2026/09/finding-v12-production-context-qualification-preparation/evidence/qualification-fixture.py --audit
```

The selected local image is
`sha256:979f11d53433f2930d69b70d81e265332547895cbd674e3e8b190cafb236243f`.
The command never builds, pulls, installs or substitutes an image. Retained
W106673 help evidence supplies CLI version 2.1.247; this fixture does not repeat
that probe or mislabel the retained version as a fresh observation.

## Exact execution and custody

Run as the existing non-root Docker manager, a member of `baton-workspace`
GID1001. The fixture uses `/usr/bin/docker --host unix:///var/run/docker.sock`
with a closed client environment. It verifies the local image and creates one
nonce-labelled bridge network. Each runtime is UID65532:GID65532 with
supplementary GID1001, a read-only root filesystem, all capabilities dropped,
no-new-privileges, 64 PIDs, 2GiB memory, one CPU and a fresh 256MiB `/tmp`.
It checks the exact six bind mounts and private propagation before starting.
The runtime receives no Docker socket or source HOME mount.

The command exclusively creates these fixed roots **together, before the
controller starts and therefore before any credential or engine use**, and
refuses an existing identity at any of them:

- `/tmp/baton-w177936-qualification-178579`: private manager-owned run root.
- `/dev/shm/baton-w177936-qualification-178579`: private volatile credential slots.
- `/tmp/baton-w177936-qualification-178579-export`: closed export on completion.

Future selected execution reads only the fixed credential source
`/home/sl/.claude/.credentials.json` after checking regular-file, ownership,
mode, link-count and size boundaries. It creates a fresh group-readable volatile
slot for each turn and binds it read-only at `/run/baton/credentials/claude`.
The expected `.claude/.credentials.json` link points there. No credential source
was opened during preparation. The inventory checks this link without opening
its target; unexpected credential-shaped names, other links, hardlinks and
special files refuse collection. Opaque session contents are not certified free
of arbitrary embedded secrets; they stay protected and are never printed.

Manager-created use/HOME/work directories are 2770 with GID1001; new input and
reconstructed files are 0640. The fixture never chmods CLI-created protected
state to make it readable. It records observed UID/GID/mode metadata; a failure
to read actual CLI state is a qualification failure, even though the generic
group grant mechanism has prior acceptance.

## Two user turns and fixed acceptance

Each CLI starts in `/output` with only HOME, PATH, TMPDIR, XDG_CACHE_HOME and
PYTHONPYCACHEPREFIX in its environment. HOME is `/run/baton/context/home`;
configuration/cache are fresh, with no CLAUDE_CONFIG_DIR. Arguments are:

```text
claude --print --dangerously-skip-permissions --output-format json --model claude-fable-5[1m] --session-id UUID FIRST_PROMPT
claude --print --dangerously-skip-permissions --output-format json --model claude-fable-5[1m] --resume UUID SECOND_PROMPT
```

The fixture mints one UUID and a private continuity token. Turn1 must create only
`solution.py` multiplying by two and remember the token without writing it to the
workspace. Turn2 must multiply by three and write the remembered token to
`continuity.txt`; the second prompt does not carry the token. Both prompts are
hashed in exported argv evidence. Both selector and prompt change.

Each prompt delimits the expected bytes between `<<<BEGIN>>>`/`<<<END>>>` markers
and states that a final newline after the last line is optional. **`solution.py`
is accepted in exactly two forms: the expected bytes, or those bytes with their
one final LF absent** (owner179142, `review-2026-09-15T15-16-11Z.md`). Everything
else still refuses — an extra final LF, leading whitespace, horizontal trailing
whitespace, altered indentation, an altered multiplier, an added comment, CRLF
endings, and any extra or missing workspace entry. There is no `strip()`, Unicode
normalization, AST equivalence or general whitespace tolerance anywhere in this
check. **`continuity.txt` is unchanged and exact**: the token followed by one
newline. Wording is not acceptance — a prompt cannot guarantee compliance — so a
provider that ignores the markers still refuses.

Before collection, reconstruction or turn2 creation, turn1 must have a matching
image/nonce/container stopped inspection (`Running=false`, PID0, exited) and a
consumed shutdown receipt. Only one observed project directory under
`.claude/projects` and its exact expected `UUID.jsonl` may be copied. The project
key is not guessed from `/output`. Missing, nested or foreign session state
refuses; no whole-HOME fallback, widening, retry or third invocation exists.
Actual provider-created names stay in private metadata; export uses path hashes
plus type/size/hash/UID/GID/mode. Capture is bounded at 1024 entries, 32MiB, depth8.

The one-shot parser requires a single bounded JSON object with `type=result`,
`subtype=success`, `is_error=false`, matching `session_id`, provider exit0 and
verified output bytes. The proposed actual-model observation is an exact
`model=claude-fable-5` and/or a `modelUsage` object whose only key is that model,
with no conflicting model field. This mapping is a qualification hypothesis,
not a previously observed one-shot interface. Unknown/missing/conflicting model
fields cannot qualify. Unknown field names are hashed; provider prose, arbitrary
error strings, transcript bytes and raw path names are not exported.

**That acceptance is unchanged, and the export now also records why it was not
met.** Run179075 reported `actual_model: null` with `modelUsage` present, and
nothing in it could say whether the member held a non-object, an empty object,
one other key or several — the raw provider document is read from an anonymous
bounded pipe and never retained, so no later inspection recovers the difference.
Each arm now carries `model_diagnostic` (missing / wrong-type / expected /
other-string), `model_usage_diagnostic` (missing / wrong-type / empty-object /
expected-only / other-only / expected-plus-other), a key count bounded at 8 with
an explicit overflow flag, and an expected-key boolean. Those members must agree
with each other and with the closed `members` list — `missing` means the field
was absent and every other diagnostic means it was present, `expected-only` is
exactly one uncapped key, `empty-object` is zero, `expected-plus-other` is at
least two, and overflow requires exactly the cap on a shape that can hold more.
A record that contradicts itself is refused at the arm rather than exported. **No model name, value,
usage payload or raw JSON is exported**, an expected key inside a mixed object
does not qualify a model, and neither does the matching `--model` argument.

The worker bounds its anonymous stdout pipe at 64KiB and kills/reaps its owned
CLI process group on exit, timeout or overflow. Each CLI has 180s. The parent
allows 420s active controller time, then terminates that controller/client group
and reserves the remainder of the 600s envelope for bounded exact-identity engine
cleanup. Cleanup engine admissions stop at elapsed595s, allowing client reap.
This is process/engine supervision, not an absolute OS/filesystem scheduling
guarantee. Two CLI user invocations do not bound internal API/model/tool calls or
billing to two. `--max-turns` remains omitted because retained help does not list it.

## Evidence and failure handling

The parent records a closed result, per-arm terminal observations, intent versus
observed provider start, ordered shutdown/consumption/reconstruction events,
nonsecret inventory metadata, cleanup receipts and measured elapsed time.
`qualification.json` and `PROVENANCE.json` in the separate export directory are
the shareable outputs. Each artifact is recorded **before** it is judged, with
its observed digest, observed byte length, the separately named expected digest
and its `exact`/`missing-final-lf`/`mismatch` form, so a refusal no longer exports
a bare code the way run179075 did. `continuity.txt` gets lengths and a verdict
and no digest, because it holds the private token. The controller never writes to
the workspace: refused bytes are left exactly as the provider wrote them. Keep the run root private: requests contain the token,
private-layout.json contains raw names, and HOME/work files contain private data.

On uncertainty the fixture attempts only exact nonce/image cleanup, never
force-removes a foreign or uncertain runtime, and retains its credential slot
unless shutdown or absence is positively established. No replacement starts
through that failure. A nonzero exit or `cleanup_confirmed=false` requires an
operator to inspect the saved identity and settle that exact resource state;
do not rerun this command or remove its fixed marker to bypass the single-run
boundary. Partial preflight/export failure may leave only the private record;
absence of an export is not success. Known identities remain in identity.json.

Even a qualified result answers only this image/profile experiment. It does not
change production code, certify a deployed profile, accept W161234, waive
independent result review or permit another run. G1–G6 remain unqualified today;
G7 is selected for qualification only and G8 is deliberately not composed.

## Correction 178875 — R1 and R2

Two bounded changes from `review-2026-09-15T14-36-52Z.md`. **The approved
manifest above moved with them**: it is now
`73fe32b941b2c82bc0f7bc87a4fa512854dfd64b17b4c8656752607f45dc0481`, and the
older `26a0f742…` is refused by `--approved-manifest`. Exact bytes, the base
they were corrected from and the focused evidence are in `EVIDENCE-178875.json`.

**R1 — the restored working copy is writable by the runtime it is for.** The
reconstructed per-use session state is created `0660` in the workspace group;
the container holds that group and can now append to its own restored state.
Setgid on the parent supplies group identity, not file write permission, which
is the distinction the earlier `0640` lost. **Nothing else moved**: the
credential slot copy and the request document are the container's read-only
inputs and stay `0640`, manager-private files stay `0600`, and the immutable
source generation is untouched. One call site asks for the writable mode and a
test asserts it is the reconstruction and no other.

Without this, a negative result would not have meant what this packet says it
means — the experiment would have qualified a read-only input under the name of
a writable working copy. It is **not** a claim that the CLI would certainly have
failed: a group-writable parent may permit unlink-and-replace, and the provider's
actual write strategy is still unobserved.

**R2 — the whole run identity is reserved before anything is admitted.** The
export root used to be created after both live turns, so an existing one refused
only once the fixed identity had been consumed and both turns paid for. All
three roots are now taken exclusively up front; a foreign path at any of them
stops the run and is never chmodded, emptied or written into; and a partial
reservation unwinds so a refusal leaves no half-taken identity. Single-run
refusal and the operator-repair requirement are unchanged.

Focused offline verification: **29 tests, OK, 0.2638512429839466 s**, exit 0, no
timeout, owned process group positively absent — receipt in
`evidence/corrected-178875.json`. Four reversal probes, each reverting one guard
and each failing exactly where it should. No live execution, engine, model,
credential use, image work, product edit, broad suite or version-control
operation. **G1–G6 remain unqualified**; G7 stays the qualification-only image
selection; G8 is still not composed.

## Correction 179146 — the artifact contract and the model diagnostics

Two bounded changes from `review-2026-09-15T15-16-11Z.md`, selected by
owner179142. **The approved manifest above moved with them**: it is now
`9a1ddd250da674e956c707f043830863d74db9074814b5050dff5d5c6c5b78ff`, and
`73fe32b9…` — like `26a0f742…` before it — is refused by `--approved-manifest`.
Exact bytes and focused evidence are in `EVIDENCE-179146.json`.

**A — `solution.py` is accepted with or without its one final LF.** The failed
run179075 wrote the expected 38 bytes with the final newline absent. The
exact-byte guard refused correctly; requiring that newline was simply not part
of what this experiment asks. Owner179142 removed that one sensitivity and
nothing else. This **supersedes the exact-final-LF requirement** stated earlier
in this file and in FINDING's 178579 entry, and supersedes nothing else — see
the two-turn section above for the full list of what still refuses.

**B — the export records why a model did not qualify, never which one.**
Closed type/cardinality/expected-key diagnostics with a bounded, explicitly
capped key count. The `actual_model`/`model_fields`/conflict predicate is
**unchanged in every case**, and a terminal record whose diagnostics contradict
its own verdict is refused at the arm rather than exported.

The qualification worker is **unchanged** — it forwards the closed projection
whole, so the new members reach the controller without a worker edit, and its
digest in the manifest is the same one accepted at 178875.

Focused offline verification: **51 tests, OK, 0.2638050550012849 s**, exit 0, no
timeout, owned process group positively absent — receipt in
`evidence/corrected-179146.json`. Seven reversal probes, each reverting one
guard in an isolated copy and each failing exactly where it should, recorded in
`evidence/probes-179146.json`. No live execution, engine, model, credential use,
image work, product edit, broad suite or version-control operation.

**This corrects the fixture; it does not re-authorize a run.** The fixed
identity consumed by run179075 is **not** reused: a subsequent run needs its own
owner selection, its own run identity and a digest-bound packet, and the markers
from that run are left exactly as they are. **G1 remains partial** — first-turn
terminal and session evidence, no accepted actual model; G4/G6 are first-use
observations only; G2/G3/G5 and all resumed behaviour remain unobserved; G7
stays the qualification-only image selection; G8 is still not composed.

## Correction 179295 — the diagnostic relationships (R1)

One bounded change from `review-2026-09-15T15-39-27Z.md`, selected by
owner179288 inside the owner179142 scope. **The approved manifest above moved
with it**: it is now
`3d5684edae17c296827db26c2a1dcffbf5173d719ddb80fe8e5f1e25f6f98741`, and
`9a1ddd25…`, `73fe32b9…` and `26a0f742…` are all refused by
`--approved-manifest`. Exact bytes and evidence are in `EVIDENCE-179295.json`.

**The defect was real and it was in correction179146.** `consistent()` validated
the diagnostic members' types, ranges and boolean identity, and their agreement
with the verdict — and never checked that they agree with **each other**. Four
malformed terminal records reached `qualified` through the actual controller:
`expected-only` reporting two keys; `expected-only` reporting eight and overflow;
overflow at one key; and `modelUsage` credited with supplying the model while the
closed `members` list says the provider never sent that field. Four more
followed from the same gap. A guard that type-checks a vocabulary without
relating its terms is not a guard.

The finite relationships are now enforced: `missing` means the known member is
absent and every other diagnostic means it is present, for both `model` and
`modelUsage`; `empty-object` is count0 uncapped; `expected-only` is count1
uncapped; `other-only` has a positive count; `expected-plus-other` has at least
two; overflow requires exactly the cap and a shape that can hold more keys than
that. `MODEL_KEY_CAP` stays 8, the strict int/bool checks stay, and **the
actual-model predicate is untouched** — this qualifies no model that was not
already qualified, and refuses none that was.

**Scope of the defect.** It is a malformed-record admission gap, not a claim that
the pinned provider emitted these contradictions: the review's own 80-vector
matrix found the unchanged worker projection coherent throughout. It matters
because a strict closed boundary that admits self-contradictory evidence is not
strict. The contract and its tests changed; **the controller, the worker and the
whole artifact half are byte-identical to the accepted 179146 correction**.

Focused offline verification: **60 tests, OK, 0.2636633020010777 s**, exit 0, no
timeout, owned process group positively absent — receipt in
`evidence/corrected-179295.json`. Twelve reversal probes in
`evidence/probes-179146.json`, each reverting one guard in an isolated copy and
each failing exactly where it should. No live execution, engine, model,
credential use, image work, product edit, broad suite or version-control
operation. The consumed fixed identity is still not reused and run179075's
markers are untouched. **G1 remains partial**; G4/G6 first-use only; G2/G3/G5
unobserved; G7 qualification-only; G8 not composed.

## Identity 180078 — the fresh run identity

Owner 2026-09-15T18:04:42Z. **The 178579 identity is consumed and is not
reusable.** The failed operator run179075 took all three of its fixed roots, and
the fixture refuses a taken root rather than repairing it — so a rerun needs a
new name, not a reset marker. `/tmp/baton-w177936-qualification-178579`,
`/dev/shm/baton-w177936-qualification-178579` and
`/tmp/baton-w177936-qualification-178579-export` **stay exactly where they are**,
with their evidence, and nothing executable in the fixture can address them.

The fresh identity is **180078**, and its three roots are:

```text
/tmp/baton-w177936-qualification-180078            run root (private)
/dev/shm/baton-w177936-qualification-180078        credential slot copies
/tmp/baton-w177936-qualification-180078-export     export root (shareable)
```

All three are reserved exclusively before any controller, credential or engine
admission, exactly as accepted at 178875; the export root is derived from the run
root in one place so the declared and reserved names cannot drift apart.

**The manifest now binds the identity, not just the bytes.** `audit` requires the
manifest's `run_identity`, `private_root`, `credential_copy_root` and
`export_root` to equal the roots this fixture would actually reserve. Before
this, those fields were decorative: an approved manifest could have named one
identity while the code took another and the digest would still have verified.
Changing any one of them alone now refuses with `manifest-constants`.

**Nothing else moved.** The accepted image, two user turns, 180s per invocation,
600s overall envelope, the artifact and continuity contracts, the model
acceptance predicate and its diagnostics, the custody modes and the shutdown
discipline are all byte-identical to accepted correction179295 — the contract and
worker files are unchanged at `0efe61f5…` and `6d9d0a0b…`.

### The exact command

Run from the baton repository root. It is one line; the manifest digest is the
owner's approval token and the fixture refuses every other value.

```sh
python3 work/records/2026/09/finding-v12-production-context-qualification-preparation/evidence/qualification-fixture.py --run --approved-manifest 91f2f687379f7bea3a00e954d07204586b975ef4b873816912949b575428d626
```

The offline package check, which admits no engine, credential or network, is:

```sh
python3 work/records/2026/09/finding-v12-production-context-qualification-preparation/evidence/qualification-fixture.py --audit
```

Focused offline verification: **67 tests, OK, 0.26378964600735344 s**, exit 0, no
timeout, owned process group positively absent — receipt in
`evidence/identity-180078.json`. Fifteen reversal probes in
`evidence/probes-179146.json`, each failing exactly where it should, including
one that puts the consumed identity back and one that lets the manifest declare
an identity the code does not take.

**THIS PREPARES AN IDENTITY; IT DOES NOT AUTHORIZE A RUN.** No live model,
engine, credential, image or network operation occurred, no root was reserved,
and the fixture was never launched. Selecting the run, its executor and the
moment remains a separate baton.ops decision. **G1 remains partial** — first-turn
terminal and session evidence, no accepted actual model; G4/G6 are first-use
observations only; G2/G3/G5 and all resumed behaviour remain unobserved; G7 is
the qualification-only image selection; G8 is not composed.

## Correction 182264 — collection custody and closed collection diagnostics

`CORRECTION-PROPOSAL-180537.md` revision 2, selected by owner182261 after the
operator's fixed-path and walk results. **The approved manifest moved with it**:
it is now `3b0020baf600335d6e7f2d999f6b01e70507e4c515a8c3c7ee4f8a3e24824bde`; every
earlier digest is refused.

**What the walk established.** The runtime creates its own state `0o700`/`0o600`
and the host collector is a different uid holding the workspace group. **Setgid
gave group ownership and never group permission bits** — the same distinction
accepted R1 turned on at 178875, from the other side. One real `opendir:EACCES`.
A container umask cannot fix it, and the reason is narrower than first recorded
here: **an explicitly requested `0o600` cannot be made group-readable by
loosening umask.** The mixture of permissive and restrictive modes does not by
itself prove a `chmod` — different requested creation modes share one umask — and
the retained metadata does not identify the call that produced them.

**P1a — the owning identity opens two of its own objects.** At the end of the
**first** invocation the worker relaxes exactly the one observed project
directory to `0o2750` and its expected `<session>.jsonl` to `0o640`. Type, owner
and group are verified through **the same `O_NOFOLLOW` descriptor that is then
`fchmod`ed**, so a symlink refuses instead of redirecting the change and nothing
can be swapped in between. Ownership is checked against the worker's **own**
euid — an identity may only reopen its own objects — while the existing
`worker-identity` check separately pins that the worker is uid 65532.
**Turn 2 relaxes nothing**: its home is manager-reconstructed and its restored
state is the manager-owned `0o660` working copy accepted at R1. Everything else —
`.claude.json`, the credential link, other sessions, every cache entry — keeps
the modes the CLI gave it.

**P1b — unreadable content is tolerated; unreadable structure never is.** Every
absence this fixture asserts (no credential-shaped entry home-wide, exactly one
project directory, no foreign session) is read from **names**. So an unreadable
regular file is recorded with the new closed `content` field
(`read` / `excluded` / `unreadable:<errno>`) and the run continues, while a
failed `scandir` **or a failed per-entry `stat`** refuses
`state-coverage-incomplete` — both hide names. The **observed** operator result
was `opendir:EACCES` on a runtime-owned `0o700` directory; the `stat` seam, where
a `0o600` directory is readable and each child's `stat` fails instead, is an
additional synthetic regression rather than the observed shape. An unreadable **selected** session refuses at `subset`
with its own code rather than surfacing later as a digest mismatch. `content`
exists because a deliberate exclusion and an access failure both leave `sha256`
null and must not look alike. **The promoted set is unchanged.**

**P1c — every failure names where and what kind.** A closed step from the eight
collection operations, a category of `known-refusal` / `unregistered-refusal` /
`os-error` / `other`, and a bounded errno category. Never exception text, type
names, paths or arguments; a refusal reporting an errno is refused at the
projection boundary.

**What this does not promise.** If the blocking directory is not the project
directory, the run **refuses** rather than passes — at `state-coverage-incomplete`
with a named step and errno instead of `unclassified`. That is the honest
outcome and it is covered by a test.

Focused offline verification: **85 tests, OK, 0.3138183479895815 s**, exit 0, no
timeout, owned process group positively absent — receipt
`evidence/corrected-182264.json`. Twenty-two reversal probes, each failing
exactly where it should. No live execution, engine, model, credential use, image
work, product edit or version-control operation; both consumed identities are
untouched and no new run identity is prepared here.

## Correction 182771 — R1–R3 from review 2026-09-16T00-41-09Z

Three defects in correction182264, all in the gap between the boundary the code
enforced and the boundary it claimed. The approved manifest moved with them.

**R1 — the no-follow chain, not the final component.** `O_NOFOLLOW` on each
object protected each object and not the **path**: a symlinked `.claude/projects`
published an object outside HOME, a rename-and-replace between the directory
check and the session's pathname reopen redirected the change to a decoy, and a
hardlinked session was chmodded through its alias, which the manager's later
hardlink refusal cannot undo. Traversal is now anchored at the verified home and
every component is opened relative to its verified parent descriptor;
`O_NONBLOCK` keeps a special-file substitution from blocking before `fstat`; and
a multi-link selected file refuses before any mode change.

**R2 — refuse before, not after.** The complete bounded
name/type/ownership/shape survey now runs and the target descriptors are acquired
**before the first `fchmod`**, so a foreign session, a nested session, a
credential-shaped entry or a second project directory each refuse and relax
nothing. The expected credential link is still checked by `readlink` and never
opened.

**R3 — the coverage refusal keeps the errno it was raised for.** A closed `cause`
carries the wrapped errno across the refusal, and the projection boundary now
states both relationships: only an OS error has an `errno` of its own, only a
registered refusal can have wrapped a `cause`.

Focused offline verification: **95 tests, OK**, exit 0, no timeout, owned process
group positively absent, including the eight-step × four-kind fault matrix
injected at the **real** collection operations and the real worker publication
exercised through the composed controller path. **Twenty-eight reversal probes**,
each failing exactly where it should.

## Correction 182906 — completing R1 and R2

Review182843 verified R3 and found R1 and R2 still incomplete. Both findings were
right, and both were the same mistake: I had fixed the case the previous review
demonstrated instead of the class it belonged to. The approved manifest is now
`eaa757a494ec6dc10db5e1a5cd67a88d52710affd912a947f7a41482d3fad99d`.

**A digest correction found while making this one.** The command above still
advertised `3b0020ba…`, the manifest from before R1–R3: the 182771 section was
appended without moving the two command lines with it. Every earlier digest is
refused by `--approved-manifest`, so the stale line could only have produced a
refusal rather than a wrong run — but a packet whose command names bytes that are
no longer the candidate is exactly the kind of quiet drift the digest exists to
prevent. Both occurrences now carry the current manifest.

**R1 — I retained nothing.** The survey walked descriptors and then reopened the
targets **by path**, so the swap simply moved later: a regular decoy put in the
project's place *after* the survey redirected the chmod onto an unsurveyed file
while the original kept its mode. Verifying a descriptor is worthless if it is
not the one you then change. The mutation targets are now the descriptors the
walk itself opened, held through selection and mutation, and a survey that cannot
complete — an entry that vanishes or refuses mid-walk — refuses with a registered
code rather than letting a raw `OSError` decide.

**R2 — my "home-wide" survey was not home-wide.** It descended only `.claude` and
the projects chain, so a credential-shaped entry under `HOME/cache` or
`HOME/.claude/cache` was invisible and unselected invalid types elsewhere were
ignored; each published before the manager's inventory could refuse. The
preflight now descends the whole home under the existing entry and depth bounds
and applies the manager's own admitted-type rule, still never opening credential
or configuration contents.

Focused offline verification: **98 tests, OK**, exit 0, no timeout, owned process
group positively absent. **Thirty reversal probes**, each failing exactly where it
should. Turn-2 no-op, the restored `0o660` contract, complete-structure refusal
and the verified R3 diagnostics are unchanged.

## Identity 183114 — the fresh run identity, and what is still unqualified

Owner183105, after review182947 accepted candidate182906 **for the offline
fixture correction only**. That acceptance is not live qualification and not
permission to rerun a consumed identity. Approved manifest:
`dd28498767bbcaf0eeb1552549f39228c555069b6c48e939abec136fa7df2779`.

### The identity

**Two identities are consumed and neither is reusable**: `178579` by the
initial-artifact failure and `180078` by the collection failure. All six of their
roots keep their original timestamps, nothing executable in the fixture, contract
or worker can name either, and neither is repaired. The fresh roots are:

```text
/tmp/baton-w177936-qualification-183114            run root (private)
/dev/shm/baton-w177936-qualification-183114        credential slot copies
/tmp/baton-w177936-qualification-183114-export     export root (shareable)
```

All three were confirmed free and **none was created** — this preparation
reserves nothing and launches nothing. They are reserved exclusively before any
controller, credential or engine admission, and `audit` still requires the
manifest's declared identity to equal the roots this code would actually take.

### What a 183114 run would and would not settle

**It would test the custody correction in the field for the first time.** The
publication and coverage rules are verified only by same-UID synthetic fixtures;
no two-UID or live-provider observation supports them yet. That is the first
thing this run would put under load.

**It would not settle the model.** Run180078's `modelUsage` held **exactly two
keys, one of them the expected model**, with no direct `model` member —
`expected-plus-other`, which the strict predicate correctly refuses. **The other
key's identity and purpose are unknown and unrecoverable**: the raw terminal
document is read from an anonymous bounded pipe and never retained, so no fixture
change can answer it. Retaining more is a separate selection with its own privacy
question, and the predicate is **not** relaxed here.

**G2, G3 and G5 remain unobserved.** No `--resume` turn has ever run, so
restoration from a manager-rebuilt home is still the thing this campaign has
never done — and it is the reason C exists at all. **G4 and G6** have one `cwd`
and one HOME-mode observation each, from turns that never reached a second arm.
**G7** stays the qualification-only image selection; **G8** is not composed.

Everything else is unchanged: the accepted behaviour, the image, the strict model
predicate, the artifact and continuity contracts, the two-turn shape, 180 s per
invocation and the 600 s envelope.

Focused offline verification: **98 tests, OK**, exit 0, no timeout, owned process
group positively absent — receipt `evidence/identity-183114.json`. **Thirty-one
reversal probes**, each failing exactly where it should, including one per
consumed identity. No live execution, engine, model, credential use, image work
or production enabling; selecting the run, its executor and the moment remains a
separate baton.ops decision.

## Correction 183197 — publication diagnostics, after run183114

Run183114 failed at first turn with `publish-shape` **and nothing else**, after
the provider had started and exited; cleanup confirmed, 18.80640551802935 s, no
second turn. Owner-confirmed cycle
`OFFLINE-CORRECTION-CYCLE-183114.md`. Approved manifest:
`c5b325cd3b083b0ba5fd8952c48bbd27ff1efa67e0e27c326434e95c35901cc6`.

**Two defects, both mine, both the shape this campaign keeps finding.**

**One code stood for seventeen checks.** Bounds, traversal failures,
credential-link and name checks, type checks, project and session shape,
ownership, alias and the chmod itself all refused as `publish-shape` or
`publish-type`, so the export could say a run refused and not which question it
answered — the same "a bare code is not evidence" failure `unclassified` had one
layer down. Every refusal now names its check from a closed seventeen-name
vocabulary, with a closed errno category where an operation failed. **No path,
filename, prose, credential or configuration content is exported**, and an
unlabelled refusal degrades to `other` rather than leaking anything.

**A later failure discarded an observation already made.** `publish` ran *before*
`c.projection`, so a publication refusal threw away a provider exit and terminal
record that were already available — run183114 cannot say whether the provider's
answer was even well-formed. The observation is now made first and carried
through the refusal. **It is evidence, not a pass**: the arm still fails, no
second arm is admitted, no publication, shutdown or qualification gate is
bypassed, and a preserved observation is validated exactly like a real terminal
record, so a forged one cannot ride in on the failure path.

**What the next run could distinguish, and what stays unknown.** A future run
would name the exact publication branch and its errno, and would say what the
provider answered even when publication refuses. It would **not** explain
run183114: that export cannot identify the branch, and no synthetic reproduction
recovers its cause or its terminal response. The model stays unqualified and
unrecoverable for the earlier runs. **All three identities — 178579, 180078 and
183114 — are consumed**, and an old manifest is not rerunnable because the
diagnostics improved; a future live experiment needs its own justified selection.

Focused offline verification: **109 tests, OK**, exit 0, no timeout, owned
process group positively absent — receipt `evidence/corrected-183197.json`.
**Thirty-six reversal probes**, each failing exactly where it should, including
two that pass only because the real `worker.main` is now exercised directly
rather than simulated. R1 retained descriptors with alias/type/UID/GID checks, R2
complete bounded preflight before mutation, R3 causal diagnostics, turn-2
restored `0o660`, the strict model/artifact/continuity acceptance, the image and
the run limits are all unchanged.

## Correction 183267 — one validator, and the last unwrapped operation

Review183243 withheld the previous candidate on two findings, both mine.
Approved manifest: `157b7bb839ec5bcc5ee16bf5800c6d60600de377eb0bf956c3ee3f117ee5e8f0`.

**Two validators for one record.** The failure path carried a shorter copy of
the terminal check, so `type`, `subtype`, `is_error`, `session_matches`,
`unknown_member_hashes` and `api_error_status` went unverified **on that path
only** — a canary in any of the six was refused on the normal path and exported
on the failure path, six times out of six. The run still failed and no second arm
was admitted, so this was a closed-export defect rather than a false
qualification, but the export is the product. There is now **one**
`valid_terminal`, used by both paths, and each of the six fields is tested on
both — paired, because the defect was precisely that the two paths disagreed.

`valid_publication` also checked membership before type, so an unhashable
`check` or `errno` raised `TypeError` out of the validator instead of being
refused by it. Types are checked first now.

**The target's own metadata read had no wrapper.** An `EACCES`, `EIO` or `ENOENT`
from the `fstat` in `_mutable` escaped as `unclassified` with a null publication
diagnostic — the one operation in the publication path still able to lose its
own cause. It reports the `target-metadata` check now, and `home-open`,
child `open` and `chmod` each have their own actual-operation coverage.

Focused offline verification: **114 tests, OK**, exit 0, no timeout, owned
process group positively absent — receipt `evidence/corrected-183267.json`.
**Thirty-nine reversal probes**, each failing exactly where it should. Retained
descriptors, before-mutation refusal, turn-2 restored `0o660`, the strict
model/artifact/continuity acceptance, the image and the run limits are unchanged,
and a valid observation still survives on the failure path — the correction does
not throw the good case out with the bad.

**These probes do not recover run183114's cause.** That export cannot identify
the branch, and all three identities remain consumed.

## Correction 183316 — completing the shared total validation

Review183295 verified the six-field leak and the `target-metadata` diagnostics
fixed, and left one bounded continuation. Approved manifest:
`d101f1ec1c3dac410e0551cb5beaf2ed60cf0ecce21aca33674e3da233eba7fa`.

**The same fault, in the validator I did not look at.** `valid_terminal` built
sets from unvalidated `members` and `model_fields` elements, and `consistent`
compared untyped model diagnostics by membership. `set([{}])` raises `TypeError`
on an unhashable element, so `members=[{}]`, `model_fields=[{}]`,
`model_diagnostic=[...]` and `model_usage_diagnostic={...}` each raised **out of**
the validator and surfaced as `unclassified` — the normal path never said
`terminal-record-values` and the preserved path never said `worker-failure-shape`.

This is exactly the fault I fixed in `valid_publication` last turn and did not
carry across, which is the same "fix the case, not the class" mistake this review
cycle has now caught in me three times. Element and diagnostic types are checked
**before** any set construction or membership test, in both predicates.

No canary was exported and no second arm was admitted, so this was diagnostic
completeness rather than a renewed leak — but a failure the export cannot name is
precisely what this cycle exists to remove.

Focused offline verification: **116 tests, OK**, exit 0, no timeout, owned
process group positively absent — receipt `evidence/corrected-183316.json`.
**Forty-one reversal probes**, each failing exactly where it should. The verified
six-field refusal, the list/dict/null publication refusals, the actual
`worker.main` EACCES/EIO/ENOENT `target-metadata` causes, the surviving valid
observation, the failed-arm and no-second-turn gates, retained descriptors,
before-mutation refusal, turn-2 restored `0o660`, the strict
model/artifact/continuity acceptance, the image and the run limits are all
unchanged. **Run183114's cause is still not recoverable** and all three
identities remain consumed.

## Identity 183372 — the one diagnostic experiment

Owner183369, after review183339 accepted candidate183316 as complete for the
offline correction cycle. Approved manifest:
`cefaf7bfa518874a082d9867c464f3629819828ef940cad5e8db0a74afb91945`.

### The command

From the baton repository root, one line:

```sh
python3 work/records/2026/09/finding-v12-production-context-qualification-preparation/evidence/qualification-fixture.py --run --approved-manifest 91f2f687379f7bea3a00e954d07204586b975ef4b873816912949b575428d626
```

### The identity

**Three identities are consumed and none is reusable**: `178579` by the
initial-artifact failure, `180078` by the collection failure, `183114` by the
publication failure. All nine of their roots keep their timestamps, nothing
executable in the fixture, contract or worker names any of them, and none is
repaired. The fresh roots are:

```text
/tmp/baton-w177936-qualification-183372            run root (private)
/dev/shm/baton-w177936-qualification-183372        credential slot copies
/tmp/baton-w177936-qualification-183372-export     export root (shareable)
```

All three were confirmed free and **none was created** — this reserves nothing
and launches nothing. They are reserved exclusively before any controller,
credential or engine admission, and `audit` still requires the manifest's
declared identity to equal the roots this code would take.

### Two outcomes, and both are worth having

Run183114 refused at `publish-shape` and the export could not say which of
seventeen checks had answered. The accepted cycle fixed exactly that, so this run
either:

1. **Names the actual publication check**, with its closed errno where an
   operation failed, **and retains the validated terminal observation** — so for
   the first time a publication failure also says what the provider answered; or
2. **Publishes successfully and reaches restoration** — the first `--resume`
   turn this campaign has ever run, and the first evidence for **G2, G3 and G5**.

**A failure that names its branch is a result, not a wasted run.** That is what
the owner-confirmed cycle was for: stop rerunning until failures produce useful
information, then run once.

### What it cannot do

It **cannot recover run183114's cause** — that export cannot identify the branch,
and no later run explains an earlier one. It **cannot settle the model**:
run180078's `modelUsage` held exactly two keys including the expected one, and the
other is unrecoverable from a document that was never retained; the strict
predicate is unchanged and is not relaxed here. And the custody correction is
still **offline-verified only** — this run is the first thing that would exercise
it with two real identities rather than same-UID fixtures, which is also why a
publication failure here would be informative rather than disappointing.

Everything else is unchanged: the strict model, artifact and continuity
acceptance, the image, the two-turn shape, 180 s per invocation, the 600 s
envelope, retained descriptors, before-mutation refusal, the R3 collection
diagnostics and turn-2 restored `0o660`.

Focused offline verification: **116 tests, OK**, exit 0, no timeout, owned process
group positively absent — receipt `evidence/identity-183372.json`. **Forty-two
reversal probes**, each failing exactly where it should, including one per
consumed identity. No agent live execution, engine, model, credential use, image
work, consumed-root repair or production enabling; selecting the run, its executor
and the moment remains a separate baton.ops decision.

## Correction 183524 — publish traversal, not contents

Run 20260916T035035Z published its two objects, consumed shutdown, then refused
at `source-inventory` with `state-coverage-incomplete`, cause **EACCES**, as the
manager. Owner-selected `OFFLINE-CUSTODY-CORRECTION-20260916.md`. Approved
manifest: `91f2f687379f7bea3a00e954d07204586b975ef4b873816912949b575428d626`.

**The diagnostics paid for themselves.** Run183114 said `publish-shape` and
nothing else; this one named its step, its refusal and its errno, and carried the
provider's answer alongside. That is what made the real problem visible.

**The problem is structural.** Publication relaxed exactly two objects while
`inventory` demands **whole-HOME** name and type coverage under a different uid.
Those two rules cannot both hold over a home whose other directories the CLI
creates `0o700`. Each half was built against its own review; neither was checked
against the other.

**The resolution: publish traversal, not contents.** Name and type coverage needs
`r-x` on **directories** and `r` on **no file** — `scandir` needs read on the
directory, `entry.stat` needs search on it, and neither opens a file. So every
runtime-owned directory becomes `0o2750`, setgid kept and no world access, while
**every file keeps the mode the CLI gave it** except the one selected session at
`0o640`. The manager sees every name and type its rules are about and can read
exactly the one file it is entitled to copy.

**This is not the broad HOME chmod the selection forbids.** No file content
becomes readable that was not already: `.claude.json`, other sessions and every
cache file stay as the CLI left them. Nothing is skipped — an unreadable file is
still recorded `content: unreadable:<errno>` — nothing extra is copied, and no
model, artifact or continuity gate moves. Directories are published only if the
runtime owns them; one it does not own is left alone. All mode changes still
follow the **complete** preflight, on descriptors the survey opened, bounded by
the `directory-bound` check rather than by the file-descriptor limit.

**The model gap is untouched and unresolved.** `expected-plus-other` with two
keys was observed **again**, and the strict predicate refused it, as it should.
The other key is unknown and unrecoverable from a document never retained. This
is a custody correction, not model or production qualification.

Focused offline verification: **120 tests, OK**, exit 0, no timeout, owned
process group positively absent — receipt `evidence/corrected-183524.json`, which
includes the observed shape end to end: a runtime-private directory that used to
refuse now inventories, the subset copies, the second turn is reached, and the
private file inside it stays unreadable and recorded rather than skipped.
**Forty-six reversal probes**, each failing exactly where it should.

**Same-UID limits, labelled.** These fixtures run as one identity, so
"unreadable to the manager" is stood in for by mode `0o000` and "owned by someone
else" by a targeted `lstat` report. Both are named as stand-ins in the tests.
Same-UID mode assertions are not evidence of manager readability, and this packet
does not claim otherwise.
