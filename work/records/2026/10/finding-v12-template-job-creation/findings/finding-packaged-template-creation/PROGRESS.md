# Implementation progress

## claim366250 — the frozen command builds, installs and creates

Answers the bound `FINDING.md` and `PLAN.md` under thread366246. Baseline is
the parent's accepted `candidate-365848` (manifest
`7ad4b9381840836d13dd485fd08ce2e63bb5b5a200419f0987c6900ae1baa730`), whose 28
members I re-hashed to their recorded candidate digests and whose 28 `base`
digests I re-hashed against the current tree before touching anything: no
drift. The base has moved from `39e83746` to `18e771f0`, and `18e771f0` is a
`work/` checkpoint — `git diff --stat 39e83746 HEAD -- v12` is empty — so
every pinned decision still holds. This child's candidate is
`candidate-366250/`.

### The first question, and it is the one the FINDING asked first

**The build is available here, and the inability claim does not hold.** The
prepared environment at `/home/sl/.local/state/baton-v12-venv` already carries
`pyinstaller 6.16.0`, `pyinstaller-hooks-contrib 2026.7`, `altgraph 0.17.5`,
`packaging 26.3` and `setuptools 84.0.0` — every entry of
`requirements.build.lock`, at exactly the pinned version. I did not take that
as the answer either: `just build` was run as written, and its own first step
(`pip install --no-cache-dir --require-hashes --ignore-installed -r
requirements.build.lock`) downloaded and installed all five from the index
against their pinned hashes before PyInstaller ran. `evidence/build.log` is
the whole run, pip step included.

So nothing here is a revalidation by assertion. The supported recipe ran and
produced a bundle, and the rest of this section is what that bundle does.

### Where it was built, and why that location is the honest one

The bundle must carry the CANDIDATE bytes, and the candidate is the
repository at `18e771f0` plus the accepted overlay — which is not what is
checked out. So the build root is a disposable copy.

It is at `/home/sl/src/baton/.w366250-build`, **inside** the working tree, and
that is deliberate. `packaging/stack.spec` captures the build stamp through
`tools.build_stamp.capture()`, which finds the repository by walking up from
its own file looking for `v12/justfile` and then performs two READS —
`rev-parse HEAD` and `status --porcelain --untracked-files=normal`. From a
root under `/tmp` those reads find no repository, the stamp records
`commit: null`, and `--version` then answers `baton 12.0.0 (source commit
unknown)` — which `test_packaging` correctly refuses. Built where it was, the
stamp records what is true:

    commit 18e771f034d22fed40ae4c597aa606f50c169daa, dirty: true

A dirty build is allowed and says so; the exact bytes are pinned by this
candidate's own manifest rather than by the commit. **No Git mutation was
performed by anything in this claim** — `rev-parse` and `status` are the two
reads `build_stamp`'s own docstring names, and `git archive` (used to lay down
the disposable roots) writes nothing to the repository.

The build root was removed after the evidence was captured.

### What the bundle is

    files             81
    folder digest     25f1039e246a6906bfaa305f6a359a7f859029727de1cdb90140a2babc6791ff
    executable        ba962a2086310df238ff25cf282a3298f71ae9289594e6f7c83222ee8f4571ef
    version           baton 12.0.0 (18e771f0, dirty)
    python / platform 3.13.7 / Linux-6.17.0-41-generic-x86_64, x86_64
    schema assets     agent-session-1.0 48212, worker-control-1.0 51419
    native validator  _internal/rpds/rpds.cpython-313-x86_64-linux-gnu.so

`evidence/bundle-manifest.json` carries all 81 per-file digests.

**One observed fact, reported rather than corrected.** I built twice from
byte-identical source. The executable and 80 of the 81 files are identical
across the two builds; exactly one is not — `_internal/base_library.zip`,
whose zip metadata carries timestamps. So a one-folder build is reproducible
except for that archive. Nothing claims otherwise and nothing depends on it:
`instance.manifest` pins whichever bundle is installed and `instance.verify`
holds the installation to it, which `test_packaging` already proves over a
real bundle. Making the build bit-reproducible would be the packaging
redesign the FINDING excludes, so this is recorded and not acted on.

### The outcome: the frozen command creates ordinary Jobs

`tests/tools/test_packaged_creation.py`, **13 cases**, every one of them
running the built executable as a SUBPROCESS with nothing of this checkout
around it — no `PYTHONPATH`, no `BATON_V12_*`, no virtual environment, `HOME`
inside a disposable root, working directory `/`. That is
`test_packaging.Fixture.ran`'s own convention, borrowed rather than reinvented,
and `test_packaging.built()` stays the one rule for which bundle is examined.

- **The install is the bundle's own `bootstrap`**, with `--distro` naming the
  bundle itself. Nothing is patched — and that is the difference that matters,
  because `test_connected_creation` must patch `bootstrap._identity_of` to
  install a stand-in directory. Here `_identity_of` RUNS the real command and
  holds it to being frozen, to carrying both frozen schema assets and to
  naming a native validator that is one of the files the instance binds. Two
  cases then read the instance's own selector back: the runtime it recorded
  re-digests to what it copied, and the identity it kept is the command's own
  answer with the extension on disk inside what it binds.
- **The creation is the bundle's own `manager … create`**, with ordinary
  operands — a task name, a statement, an acceptance criterion and a work
  scope. There is no digest, manifest or launch packet among them, and the
  argument list has nowhere to put one, which is SCH-1a's "ordinary creation
  MUST NOT require operator-authored manifests or bespoke launch packets"
  asked of the DEPLOYED surface. The answer carries the derived work id, the
  derived input and policy digests, the resolved template with its origin,
  and `servable: {implementation: [impl-a], review: [review-a]}`.
- **The template came out of the bundle's packaged resources.** The inventory
  is not read from this process's own packages: it is read out of the sentence
  the COMMAND writes when asked for a version it does not hold — "this build
  carries the job templates 'baton.v12.job-template.implementation-review/1'"
  — and the created Job's version is in it.
- **What is durable afterwards**, read from the instance's own files: the Job
  store holds the Job's own task document, whose instructions carry the
  statement, the acceptance criterion, the selected scope path and the
  template version; the binding is published into the instance's
  `deployment.json` and additively into `install-inputs.json`; and the
  submission has the template's two stages.
- **Same-intent replay**: the identical request again answers the identical
  document, with one reservation in state `created`, one binding, one entry in
  the install document and two stage rows — not two of anything. A CHANGED
  intent under the same task is refused instead, naming both request digests
  and saying why a byte-identical submission is still two creations.
- **Truthful refusals**, each one the product's own: a template this build
  does not carry, and a source selection it does not serve. Both exit 1 with
  the refusal's own sentence, write nothing on stdout, and leave no
  reservation, no binding and no install-document entry behind.

### A false pass I wrote and then removed

One case asked for `--override terminal_policy=report-and-hold` and asserted
that `terminal_policy` appeared in the refusal. It passed — and it was
worthless: that string appears inside **argparse's** `unrecognized arguments`
line, so the template's permitted-override rule was never consulted. The
deployed command offers exactly the two operands the template permits
(`--provider-turn-seconds`, `--verification-command-seconds`) and no way to
ask for anything else, which IS the enforcement. It is now two honest cases:
an operand this command does not serve is refused by the parser with exit 2
and nothing created, and the PERMITTED override is carried end to end into the
Job's own boundary (`provider_turn` 120s, `origin: job`, default 3600 — every
other boundary still the deployment's `compatibility`).

`packaged_refusal` now also requires **exit 1 and a `ContractRefusal` on
stderr**, so an argparse exit 2 can never satisfy a case about a product
refusal again.

### The gate now covers this

`v12/justfile`'s `test-packaging` recipe built the bundle and ran
`tests.tools.test_packaging` alone, so the new proof would have been orphaned
— green only when somebody remembered it. The recipe now runs both suites
under the same `BATON_V12_STACK_PACKAGING_REQUIRED=1` bound to the bundle it
just built, with the timeout raised 600s → 900s for the longer run. Its skip
rule is inherited rather than re-decided: without a bundle the new suite skips
with the exact command to run, and under `REQUIRED` it fails instead, which
`evidence/no-bundle-skips.txt` and `evidence/no-bundle-required-fails.txt`
show as 13 skips and 13 failures respectively.

### What was NOT changed

**No product byte.** The packaged command, its resources and its wiring needed
no correction: `src/` and `tools/` are exactly the accepted candidate's. The
two changes are one new test file and the gate recipe.

### Verification

Candidate root `/tmp/w366250` (the tracked tree at `18e771f0` with the
accepted overlay; proved byte-identical to the build root over 330 files),
`PYTHONPATH=src:.`

- **`just test-packaging`, the supported gate, run as written: 24 OK, exit 0**
  — it built the bundle itself and then ran both suites against it.
- **`tests.tools.test_packaged_creation`: 13 OK**; 13 skipped with no bundle;
  13 failed with no bundle under `REQUIRED`.
- **Whole `tests/job_manager`: 1375 OK.**
- **Nine tools suites** (packaging, packaged_creation, connected_creation,
  creation_ports, job_task_delivery, retry_task_lineage,
  fresh_retry_line_recovery, bootstrap, instance): **453 OK**.

`evidence/claim-366250/` with `HOW-THESE-WERE-RUN.txt`, the full build log,
the gate log, the bundle identity and per-file manifest, and every run above.

### Cost

Reading `v12/justfile`'s `build` and `test-packaging`, `packaging/stack.spec`,
`requirements.build.lock`, `tools/build_stamp.py`, `tools/stack_command.py`,
`src/baton_v12/version.py`, `bootstrap.main`/`_identity_of`,
`tools/job_manager.py`'s `create` operands, `tests/tools/test_packaging.py`
and the connected-creation and bootstrap fixtures, plus the pilot instance
packet's `COMMANDS.md` (to establish that its real-repository install is the
production path and not this bounded proof's). Probes: four — the build
itself, the packaged install and create, the refusal messages (which is where
the false pass was caught), and the two-build comparison. Builds: three (one
unlogged, one logged, one by the gate). Test runs: the new suite six times
(two failing — the fixture's `created` helper shadowing the owning fixture's,
and the missing repository asset in the build root). No live provider, no
model, no container engine, no deployed-instance mutation, no migration, no
cutover.

### Boundaries

No Git mutation of any kind; the only version-control calls anywhere in this
claim are `rev-parse`, `status`, `log`, `diff` and `archive`, all reads.
`--no-repositories` was passed to every install, no Job was served, no runtime
started and no credential or provider reached. The canonical `v12` tree is
byte-unchanged; the disposable build root inside it was removed. The parent's
`candidate-365848` and every earlier candidate and evidence directory are
preserved and re-verified. The bound `FINDING.md` and `PLAN.md` are the
reviewer's and are unmodified; I wrote `candidate-366250/`,
`evidence/claim-366250/` and this file.
