"""Claim-240196 dossier entries: PROGRESS, FINDING, PLAN, OWNERSHIP."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PROGRESS = """
## 2026-09-22 -- baton.claude, claim 240196, R1 and R2 complete

Review 2026-09-22T15:32:51Z requested changes on two counts before the operator
command; owner reroute 240193 selects both within the existing baseline scope.
Both are done. No store was opened on any deployed instance, no container
started, no grant minted, no runtime cleaned, no live run, no mutating
version-control operation, and no file under `v12/` edited.

**Both findings were reproduced against the current tree before anything was
changed.** The composer really does fail with `ModuleNotFoundError: No module
named 'baton_v12'` in a child with no inherited `PYTHONPATH`; `job-a` really
was hard-coded at three sites; and `_attempts_of` really does filter the status
projection to the selected Job, so an older Job's runtime was never going to
appear in this run's accounting whatever the operator document claimed.

**R2 -- a fresh run name is not a fresh Job, and this run accounts for one Job.**

* The Job identity is composed. `baseline_bindings._job_identity` derives
  `job-<run_id>` by default, so a fresh run identity is a fresh Job identity
  without an operator having to know they are two different things. `job-a` is
  refused by name: it is the identity already recorded in the W236087
  instance's Job store.
* `baseline.survey` reads `job_rows` and `stage_rows` BEFORE any owner act and
  refuses a Job identity the store already records. The collision used to
  surface at `submit`, which is after `prepare` has configured storage,
  certified a profile and minted a one-run qualification grant -- so the old
  behaviour spent an exactly-once grant to discover a run it could not make.
  `main` returns exit 2 for it, with nothing spent and no outcome written.
* The admission gate is now scoped to one Job. This closed a defect the
  reviewer's finding implies but does not state: `serve` sweeps the STORE, and
  the caps are counted by KIND, so an unrelated Job's eligible implementation
  stage would have been admitted here, spent this run's single invocation and
  started a container against work nobody selected. A foreign stage is refused
  before it reaches the composed deployment, and recorded in
  `foreign_admissions` rather than `gate_refusals` -- a refusal ends this run,
  and a stranger in the store must not be able to do that.
  `test_another_jobs_stage_never_spends_this_runs_invocation` drives a real
  second submission through the public API and asserts the stranger reached the
  gate and was turned away while this run still settled.
* The accounting claim is withdrawn rather than reworded. The outcome carries
  `job_id`, `preexisting_jobs`, `preexisting_stages` and an `accounting_scope`
  sentence saying plainly that a runtime belonging to another Job is NOT
  covered by it and its absence is NOT established by it. W236087's outstanding
  runtime stays outstanding, separately, whichever arrangement is selected.

**R1 -- the commands are commands now, and they are exercised as such.**

* `test_entrypoints.py` is new. `TheDocumentedComposerRunsAsDocumented` runs
  the exact command `OPERATOR-239528.md` prints, in a CHILD PROCESS with
  `PYTHONPATH` removed from the environment and then set to the bound source
  alone, with `cwd` at the filesystem root so nothing resolves relative to a
  shell -- over a RELOCATED copy of the real `baton_v12` and `tools` made with
  `shutil.copytree`. The reviewer's own reproduction is kept as a regression:
  without the binding it fails at the first product import AND writes nothing.
* `TheDocumentedSupervisorRunsThroughMain` drives `baseline.main` itself, which
  no test reached before: exit 0 on a settled attributed run, exit 1 on an
  elapsed bound with the engine asked to stop, exit 2 on a source this process
  does not import, and exit 2 on a Job identity the store already holds. The
  refusal case is the sharp one -- the relocated copy is byte-identical, so
  every pinned digest verifies and only `verify_imported_sources` can catch it.
* The operator document binds the interpreter, the import path and absolute
  program paths; carries an actual Step 5a with the Authority calls; and states
  `preflight`'s real limits -- it is a helper neither CLI main calls, a missing
  capability name is conclusive while a present one is not, and it cannot
  verify route handlers at all. The previous revision claimed it supplied the
  route-handler list, which contradicted the helper's own docstring.
* `SELECTIONS-239528.json` now separates retained facts from open choices. The
  image, worker adapter digest, manager source and installed runtime were
  re-read from disk under this claim and match `PACKET-INPUTS-239485.json`
  exactly: image `sha256:2e9e84ff...7456bd`, adapter `abdf903d...bb4d`, 106
  flat manager-source files, `baton-v12-stack` `04aa459a...a58a`. What stays
  open is named and explained.

**One thing I could not establish, stated rather than assumed.** The reuse
alternative -- running on the W236087 instance -- is now possible because the
Job identity no longer collides, but its faulted attempt still holds an open
assignment in that Work's scope, and whether the manager admits a new
assignment for the same participant while one is open needs that deployment's
stores opened. This claim did not open them. The operator document recommends
the fresh isolated instance and records the reuse path with that caveat
attached rather than buried.

**A fixture defect the Job identity change exposed and fixed.** The test
harness prepared one packet and supervised another; the qualification grant
binds `packet["context"]["job_id"]`, so once the two packets stopped sharing
`job-a` the opening admission had no grant for the Job it was admitting. The
fixture now prepares the packet it drives, and the packet's Job identity is
read from the submission it writes.

Verification: 77 focused deterministic checks, measured 15.704004109s, receipt
`verification-2.json` with `verification-2.log`. It records the digests of the
five W236087 ancestor files, so the copy-rather-than-import derivation stays
checkable. Engine and provider subprocess are the two accepted seams; version
control, the adapter, the ending driver and the cleanup journal are real.

Cumulative measured for W239528, naming every run I actually timed:
7.146396201 + 7.149914038 + 7.138971223 (claim 239653) + 15.684039575 +
15.704004109 + 7.187 + 6.480 + 7.670 (claim 240196) = **74.160325146s**. Short
diagnostic runs during development were not individually retained and are not
in that figure; the reviewer is right that the earlier handoff quoted a rerun
that was not in PROGRESS's total, and this entry fixes that by listing the runs
rather than quoting one.

All ten inherited W236087 digests re-verified byte-identical. `git diff --check`
clean. State: awaiting independent review.
"""

FINDING = """
## 2026-09-22 -- claim 240196, the operator command corrected

Review 2026-09-22T15:32:51Z accepted the deterministic baseline and refused the
operator command, on two counts that were both correct and both reproduced
against the current tree before anything was changed.

**A run identity is not a Job identity.** Every packet this composer wrote
named `job-a`, so "select a fresh `run_id`" did not make the documented
instance reuse executable: two such packets collide in one Job store at
`submit`, which is AFTER `prepare` has spent an exactly-once qualification
grant. The Job identity is now derived from the run identity, and
`baseline.survey` refuses a collision before any owner act.

**And one run accounts for one Job.** `_attempts_of` filters the status
projection to the selected Job, so an older Job's outstanding runtime was never
going to appear in this run's attempt discovery, cancellation or cleanup. The
operator document had claimed it would. That claim is withdrawn rather than
reworded: the outcome now names every other Job the store holds and states
plainly that it covers none of them.

**A defect the finding implies and the correction closes.** `serve` sweeps the
STORE, and the admission caps are counted by KIND. An unrelated Job's eligible
implementation stage would therefore have been admitted by this run, spending
its single invocation and starting a container against work nobody selected
here. Admission is now scoped to one Job, and a foreign stage is recorded as
foreign rather than as a refusal -- because a refusal ends the run, and a
stranger in the store must not be able to end a correct one.

**A command that cannot be run is not a command.** The documented composer
invoked plain `python3` and fails at its first product import in any child
without an inherited `PYTHONPATH`. Both entrypoints now bind the interpreter,
the import path and absolute program paths, and `test_entrypoints.py` runs them
as commands -- the composer in a real child process over a relocated copy of
the real source, the supervisor through `baseline.main` itself, which nothing
had executed before. The reviewer's reproduction is kept as a regression, and
the sharpest case is the packet bound to that byte-identical relocated copy:
every pinned digest verifies, and only `verify_imported_sources` catches it.

The document also overstated its own preflight, claiming it supplies a
route-handler list the helper's own docstring says it cannot produce. Its real
limits are now stated where they are relied on, and the artifact operands that
W236087 already selected and accepted are bound rather than blanked.

What could NOT be established is recorded as such: reusing the W236087 instance
is now possible, but its faulted attempt still holds an open assignment in that
Work's scope, and whether a new assignment is admitted alongside it needs that
deployment's stores opened. This claim did not open them, so the fresh isolated
instance is the recommendation and the caveat travels with the alternative.

Verification: 77 focused deterministic checks, 15.704004109s measured.
"""

PLAN = """# Current action -- R1 and R2 corrected, awaiting independent review

## Active state -- claim 240196, baton.claude, returned for review

Owner reroute 240193 selected both corrections from
`review-2026-09-22T15-32-51Z.md` within the existing baseline scope. Both are
complete. No deployed store was opened, nothing was provisioned, no runtime was
recovered, no reviewer stage or resume was added, and no file under `v12/` was
edited.

### Done under this claim

1. **R2, the Job and store arrangement.** The Job identity is composed as
   `job-<run_id>`; `job-a` is refused by name. `baseline.survey` refuses a
   recorded Job identity BEFORE any owner act, so a one-run grant is never
   spent discovering a submission that cannot be made. The admission gate is
   scoped to one Job, so another Job's stage cannot spend this run's single
   invocation. The outcome carries `job_id`, `preexisting_jobs` and an
   `accounting_scope` sentence disclaiming every other Job.
2. **R2, the accounting claim.** Withdrawn, not reworded. W236087's outstanding
   runtime is preserved and is separately outstanding under every arrangement.
3. **R1, the commands.** Interpreter, import path and absolute program paths
   bound; an actual Step 5a; `preflight`'s real limits stated; retained
   artifact bindings restored and revalidated from disk.
4. **R1, the proof.** `test_entrypoints.py` runs the composer as a child
   process over a relocated real source tree and drives `baseline.main`
   through exit 0, exit 1, and two distinct exit-2 refusals.

Verification: 77 checks, 15.704004109s measured, receipt `verification-2.json`.

### Next, and whose

* **The reviewer's.** Independent validation of the corrected command, the Job
  scope and the entrypoint proof.
* **The owner's**, and none of it authorized by this preparation: the fresh
  instance and its step 5a provisioning; the selections still marked `<OWNER>`;
  whether to run the live command at all; W236087's faulted-attempt recovery.

## Open and explicitly not established here

Reusing the W236087 instance is now possible -- the Job identity no longer
collides -- but its faulted attempt holds an open assignment in that Work's
scope, and whether the manager admits a new assignment alongside it needs that
deployment's stores opened. This claim did not open them. The operator document
recommends the fresh isolated instance and attaches the caveat to the
alternative.

## Not in scope here, and not done

Any live execution, any deployed provisioning, any cleanup of W236087's
outstanding runtime, any reuse of its consumed grant, any destructive recovery,
any reviewer stage, any session resume, and any Work closure.

---

"""

OWNERSHIP = """
## Claim 240196 -- files added under this claim

    test_entrypoints.py           the two operator entrypoints, run as commands
    records_240196.py             this claim's dossier writer
    verification-2.json/.log      the 77-check receipt

`OPERATOR-239528.md`, `SELECTIONS-239528.json`, `baseline.py`,
`baseline_bindings.py`, `test_baseline.py`, `test_baseline_bindings.py`,
`verify.py`, `FINDING.md`, `PLAN.md` and `PROGRESS.md` were edited under this
claim and are this Job's own.

**The reviewer's files were not touched**: `review-2026-09-22T15-32-51Z.md`,
`review-evidence-239808.json`, `review-tests-239808.log`,
`review-probes-239808.py` and `review-probes-239808.json` belong to baton.rvpc
and are append-only history. `verification-1.json/.log` is claim 239653's
receipt and is kept beside the new one rather than replaced.

All ten inherited W236087 digests in that dossier's
`review-evidence-239589.json` were re-verified byte-identical again under this
claim.
"""


def main():
    progress = HERE / "PROGRESS.md"
    if "claim 240196" not in progress.read_text(encoding="utf-8"):
        progress.write_text(
            progress.read_text(encoding="utf-8").rstrip("\n") + "\n" + PROGRESS,
            encoding="utf-8")

    finding = HERE / "FINDING.md"
    if "claim 240196" not in finding.read_text(encoding="utf-8"):
        finding.write_text(
            finding.read_text(encoding="utf-8").rstrip("\n") + "\n" + FINDING,
            encoding="utf-8")

    plan = HERE / "PLAN.md"
    body = plan.read_text(encoding="utf-8")
    if "claim 240196" not in body:
        head = body.split("\n", 1)[0]
        plan.write_text(
            PLAN + body.replace(head, "# Historical action" + head.split("--", 1)[-1]
                                if "--" in head else "# Historical action", 1),
            encoding="utf-8")

    ownership = HERE / "OWNERSHIP-239528.md"
    if "Claim 240196" not in ownership.read_text(encoding="utf-8"):
        ownership.write_text(
            ownership.read_text(encoding="utf-8").rstrip("\n") + "\n"
            + OWNERSHIP, encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
