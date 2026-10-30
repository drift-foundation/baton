# Retained-native operational proposal — revision 2, claim356947

The proposal `review-2026-10-23T01-09-52Z.md` required, **corrected** for the
two findings in `review-2026-10-23T01-19-06Z.md`.

**Every command below is a PROPOSAL. Nothing in it was executed.** No live
instance was read — not even a directory listing of the retained destination —
no build or setup was run, nothing was downloaded, and no Git state was
mutated. All findings come from reading the integrated source at commit
`30245386`.

`PENDING(...)` is notation, not shell syntax.

## What revision 1 got wrong

**1. My proposed export would have produced a bundle that cannot say what it
was built from.** Revision 1 proposed `git archive … | tar -x`, a tree with no
repository metadata. `packaging/stack.spec:42` calls `build_stamp.capture()`;
`build_stamp.py:60` walks up from its own file for a directory containing
`v12/justfile` — which my export *does* contain, so it would be found — and
`:95` then runs `rev-parse HEAD` there. In a non-repository that read fails, so
`commit` stays `None` and `detail` reads *"the repository tool could not name a
commit for …"*. **Naming the commit in a proposal document does not put it in
the frozen identity.** Corrected in Part A.

To be precise about the severity: the stamp would **not lie** — it records null
plus a detail, by design. It would be a bundle that is honestly unable to
state its own provenance, which is still unusable as release provenance.
`capture()` takes no commit operand (`capture(source=None, runner=None)`, and
the spec calls it bare), so there is no way to supply provenance externally.
Fabricating a stamp is forbidden and is not proposed.

**2. I understated the missing update capability, and I contradicted my own
Part B doing it.** Revision 1 said only "a guarded `publish` caller" was
missing and that its risky half was already verified. That is wrong on two
counts, and `instance.py:255` is why: `verify` compares **every** path in a
selector against `layout(destination)` and refuses any disagreement, and
`layout` derives `distro` as `<destination>/distro` and `command` as
`<destination>/distro/baton-v12-stack`. So **an unchanged destination cannot
select an external bundle at all** — the new bytes must land at the
destination's own `distro`. The capability is therefore "replace a runtime
directory *and* its selector coherently", not "write one selector file".
`publish` atomically replaces **one file**; it says nothing about the
directory, and its temporary-symlink test proves that narrow primitive, not
upgrade safety. And a stopped supervisor with no live *recorded* runtime is not
exclusive writer/launch fencing nor fresh cessation evidence — **Part B's own
caveat says that recorded answer is not a fresh observation**, and revision 1
used that caveat to keep group 5 open while quietly treating "stopped" as
sufficient in Part C. Corrected in Part C.

Retained from revision 1 unchanged, as the review directed: the fresh
build-environment isolation, the named download effects, and the separate
operational selection boundaries.

---

## Part A — the proposed build, with truthful provenance

### A1. The source must be a real repository at the exact commit

Building from the shared checkout is wrong for a different reason than
revision 1 gave: it is dirty against `30245386` in five files
(`v12/DESIGN.md`, `v12/.dockerignore`, `v12/worker/Dockerfile.claude`,
`v12/python/tests/manager/test_claude_agent.py`, plus untracked
`v12/python/src/baton_v12/verification_context.py` and its test). The stamp
would record `commit 30245386` **with `dirty: true`** — honest, but a bundle
whose bytes are not the reviewed ones.

**Proposed, for Slawomir to run — Git-mutating preparation is his:**

    CLEAN=PENDING(new absolute path outside the checkout, e.g. /home/sl/baton-builds/30245386/src)
    test -e "$CLEAN" && { echo "refuse: $CLEAN already exists" >&2; exit 1; }
    git clone /home/sl/src/baton "$CLEAN"
    git -C "$CLEAN" rev-parse HEAD      # must print 302453869d07eb5579e79a6572586d3c3cf62a5c
    git -C "$CLEAN" status --porcelain --untracked-files=normal   # must print nothing

A plain clone lands on the default branch at its tip, and `30245386` **is**
that tip today — so this needs no `checkout`, which keeps it to operations that
write nothing to the source repository. **Both verification lines are
preconditions, not decoration**: if the tip has moved, the clone is not the
reviewed source and the build must not proceed from it. If it has moved,
Slawomir's alternative is a detached checkout at that exact commit — still his
act, still proposed only.

The two checks matter because they are exactly what `capture()` will observe:
`rev-parse HEAD` becomes `commit`, and `status --porcelain
--untracked-files=normal` becomes `dirty`. Verifying them beforehand is
verifying the provenance the bundle will carry.

### A2. A side effect of building inside a clean clone

`stack.spec:42` writes the captured stamp to
`v12/python/packaging/build-stamp.json` **inside the source tree**, so a build
dirties its own clone. That is anticipated: `build_stamp.GENERATED` excuses
exactly `v12/python/build/out/`, `v12/python/build/work/` and that one stamp
file from the dirty computation, *"only under `v12/python`"*, because *"a stamp
that says 'dirty' about its own output says nothing about the source it was
built from."* Ordinary untracked source anywhere still counts as dirty. So the
stamp written by the build does not corrupt the stamp's own answer — but the
clone is no longer pristine afterwards and should not be reused as a
"clean source" for a second build without re-checking A1's two lines.

### A3. Environment and output, with refusal on pre-existence

`mkdir -p` neither establishes freshness nor protects old output, which
revision 1 glossed. Proposed:

    export BATON_V12_VENV=PENDING(new absolute venv path, e.g. /home/sl/baton-builds/30245386/venv)
    OUT=PENDING(new absolute output path, e.g. /home/sl/baton-builds/30245386/build)
    test -e "$OUT" && { echo "refuse: $OUT already exists" >&2; exit 1; }
    cd "$CLEAN/v12" && just setup
    cd "$CLEAN/v12" && just build "$OUT"

- **`OUT` must be refused if it exists.** `just build` passes `--noconfirm
  --clean`, so it would overwrite an existing output without asking. It must
  not be the retained instance's `distro`, and must not be a path holding a
  historical bundle.
- **`BATON_V12_VENV` needs no hand-rolled check**: `just setup` is documented
  as *"REPEATABLE AND NEVER DESTRUCTIVE … Anything else at that path is refused
  with the path named, and is never deleted."* The refusal already exists; the
  fresh path is what makes it irrelevant.

### A4. The two side effects an owner must consent to — unchanged from revision 1

1. **It mutates the prepared virtual environment.** `v12/justfile:131` runs
   `"$PREPARED" -m pip install --no-cache-dir --disable-pip-version-check
   --require-hashes --ignore-installed -r requirements.build.lock`, installing
   the packaging tool with `--ignore-installed` so it overwrites a present
   version. The default environment is `$XDG_STATE_HOME/baton-v12-venv` —
   `/home/sl/.local/state/baton-v12-venv`, **the interpreter this campaign's
   accepted test evidence was produced with**. A fresh `BATON_V12_VENV`
   (`tools/environment.py:46`) keeps the build away from it, which also matches
   the distribution's own position that *"a deployed distribution never
   acquires a packaging tool."*
2. **It downloads.** No `--no-index` and no wheelhouse: build-tool artifacts
   come from the configured index, bounded only by `--require-hashes` against
   `requirements.build.lock`. `--no-cache-dir` means no pip cache is read or
   written.

### A5. Provenance known now, and outputs that cannot be

| Known | Value |
|---|---|
| Intended source commit | `302453869d07eb5579e79a6572586d3c3cf62a5c` |
| Build host platform | `Linux 6.17.0-41-generic x86_64` |
| Build interpreter | Python 3.13.7 |
| Runtime lock | `v12/python/requirements.lock`, `--require-hashes` |
| Build-tool lock | `v12/python/requirements.build.lock`, `--require-hashes` |
| Packaging spec | `v12/python/packaging/stack.spec` |

`PENDING` until the build is selected and run: the bundle's
`instance.manifest` file count and whole-folder digest, per-file digests, the
`identity` output, and the stamp's actual `commit`/`dirty` values. The bundle
is host-specific by construction, so **no value for any of these can be
derived from source, and stating one would be fabrication.**

---

## Part B — the supported read-only inspection commands

Unchanged from revision 1 and accepted by the review; restated in brief with
the qualification the review asked for.

    /home/sl/baton-instances/native-coordination-pilot-w321608-1/distro/baton-v12-stack identity
    /home/sl/baton-instances/native-coordination-pilot-w321608-1/distro/baton-v12-stack status \
        --instance /home/sl/baton-instances/native-coordination-pilot-w321608-1/instance.json

Served at `stack_command.py:264` and `:246`, generated at `bootstrap.py:2003`.
**Qualified by the retained bundle's own provenance**: these shapes match
*current* source, and what the retained bundle actually serves is whatever it
was built from. Its build predates `attempt-diagnostics`
(`stack_command.py:266`), so that subcommand is certainly absent there; no
current instance facts were established here, by me or by the review.

From `stack.py:1130` and `:866`, `status` answers: process health with pid or
an unknown detail and its record; snapshot freshness as absent/unreadable/state
with **both** observed and published ages; observed Job count and canonical
flag; the runtime boundary as open episodes, how many carry a recorded runtime,
and observation age — stating in its own words that *"stopping a supervisor
does not stop a runtime, and this is the last RECORDED answer rather than a
fresh one"*; and configuration state when not configured.

It **cannot** answer control/Job/authority store schema versions or
compatibility, token guard state, or per-attempt cessation facts. Group 3's
remaining store-schema pin is therefore not answerable by any supported
read-only command on this surface, and no private-store workaround is proposed.

---

## Part C — the retained update capability, assessed as acceptance questions

### C1. There is no supported in-place update. Four source facts, no readback.

1. `bootstrap.py:1877` — an existing runtime at the destination's `distro` is
   refused: *"nothing here upgrades a deployment in place. Stop that instance
   and prepare a new destination if you mean a different runtime."*
2. `instance.py:312` — every lifecycle command refuses when the installed
   bundle's whole-folder digest differs from the selector's record.
3. `instance.py:302` — a frozen command must drive the instance it names:
   *"one build must not dispatch children on behalf of another."*
4. `instance.py:255` with `layout()` — **every** path in a selector is compared
   to the destination's derivation and must resolve inside it. `distro` is
   `<destination>/distro`; `command` is `<destination>/distro/baton-v12-stack`.

Fact 4 is the one revision 1 missed, and it changes the shape of the problem:
**an unchanged destination cannot point at an external bundle.** New bytes must
be installed *at* `<destination>/distro`. Combined with fact 2, copying a new
bundle there without a matching selector **bricks** every lifecycle command;
with fact 1, `bootstrap` will not prepare over the destination at all; and
`instance.create` is exclusive by construction (`instance.py:386`).

### C2. The finite missing outcome, stated as acceptance questions

These are **capability acceptance questions, not a design and not an
implementation plan.** I am not proposing to build this and did not; the review
forbids inventing or implementing an updater, and exact design is separate
selected Work if the owner chooses retained adoption.

An operation that adopts a new runtime into the **retained** destination would
have to establish all six:

1. **Preservation** — the retained authority, stores, output, logs and
   prior-generation evidence survive unchanged, and the superseded selector and
   bundle identity are retained as evidence rather than discarded.
2. **Exclusion** — concurrent launches and writers are actually fenced for the
   duration, not merely believed absent. A stopped supervisor is not a fence.
3. **Cessation** — applicable cessation of anything still executing is
   *established*, on fresh evidence. `status`'s runtime line is explicitly the
   last recorded answer, so it cannot discharge this.
4. **Compatibility and candidate provenance** — the new bundle verifies as a
   bundle, carries truthful provenance (Part A), and is compatible with the
   retained stores' schemas. Nothing on the supported read-only surface answers
   the schema half today (Part B).
5. **Coherence** — the installed runtime bytes at `<destination>/distro` and
   the selector's `runtime.digest` change **together**, because facts 2 and 4
   make either alone a refusal.
6. **Interruption safety** — an interrupted replacement either recovers or
   refuses, and never leaves a mixed installation. This is the hard one: a
   directory replacement and a selector replacement are two mutations, and
   `publish`'s atomicity covers only the second. Interrupted between them, the
   deployment is bricked by fact 2 in either order.

**What already exists, stated without inflating it.** `instance.manifest`
digests a whole bundle folder and refuses a symlinked root or internal links
pointing outside it. `instance.emit` composes a selector. `instance.verify` is
the check that refuses the mismatch. `instance.publish` atomically replaces one
selector file and is proven by `tests/tools/test_instance.py:745` not to write
through a symlink planted at its temporary name — and it has no production
caller. **These are useful parts. They do not add up to questions 1, 2, 3, 5
or 6, and revision 1 was wrong to suggest the capability was mostly verified.**

### C3. The alternative, and what it does not do

Preparing a **new destination** from the new bundle is fully supported today —
it is what all four refusals point at — and leaves the retained pilot untouched
as evidence.

**It does not recover the old Job, and cannot silently be treated as if it
did.** The new deployment does not inherit the failed episode, so the retained
pilot's expired-token episode stays unrecovered. No revival and no
resubmission is proposed for it. If recovering *that* Job is part of the
acceptance, a new destination does not meet it.

---

## Still pending, honestly

- Every build output, including the stamp's actual `commit`/`dirty` values.
- All current retained-instance state. No readback was performed.
- Group 3's store schema compatibility — unanswerable on the supported
  read-only surface.
- Group 5's concrete current hold and recovery disposition.
- Group 7's post-execution receipts — future results, never fixture
  substitutes.

## Selection boundaries

Three owner selections, in order, none taken here: **(1)** source preparation
and the build, which is Slawomir's for the Git half and carries the download
and environment-mutation consent above; **(2)** the read-only readback of the
retained instance; **(3)** either a new destination, accepting C3's cost, or
retained adoption — which needs the C2 capability and its own bounded Work and
acceptance. W321608's gate remains. Git remains Slawomir's.
