# Proposed qualification command — not executed

baton.tuner, claim178579, owner178575. Independent fixture review is next at
baton.feat; baton.ops then records whether to select this exact live run and
its execution claimant. This file makes that decision concrete. Supplying a
manifest hash verifies bytes; it is not evidence of owner authorization.

**The filename records this packet's origin, not the run identity.** It is
maintained in place, as it was through corrections178875, 179146 and 179295, so
each review's pinned digest names the bytes it actually read. The current run
identity is **180078** — see the final section; the 178579 identity is consumed.

From the baton repository root, the proposed command is:

```sh
python3 work/records/2026/09/finding-v12-production-context-qualification-preparation/evidence/qualification-fixture.py --run --approved-manifest 3b0020baf600335d6e7f2d999f6b01e70507e4c515a8c3c7ee4f8a3e24824bde
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
python3 work/records/2026/09/finding-v12-production-context-qualification-preparation/evidence/qualification-fixture.py --run --approved-manifest 3b0020baf600335d6e7f2d999f6b01e70507e4c515a8c3c7ee4f8a3e24824bde
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

Focused offline verification: **94 tests, OK**, exit 0, no timeout, owned process
group positively absent, including the eight-step × four-kind fault matrix
injected at the **real** collection operations and the real worker publication
exercised through the composed controller path. **Twenty-eight reversal probes**,
each failing exactly where it should.
