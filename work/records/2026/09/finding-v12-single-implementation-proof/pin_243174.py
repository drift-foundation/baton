"""Record the findings and PIN the paths, BEFORE implementation.

Owner pass 243171: "Preserve /home/sl/baton-runs/single-implementation-success-
239528/run and record findings before implementation." This script is that
record; nothing is edited until it has run.
"""
import hashlib
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[4]

PINNED = ("work/records/2026/09/finding-v12-single-implementation-proof"
          "/baseline.py",)

FINDING = """
## 2026-09-23 -- the successful baseline run, and three findings

Owner pass 243171, recorded here BEFORE implementation as that pass requires.
`/home/sl/baton-runs/single-implementation-success-239528/run` is preserved and
was read only; no store belonging to it was opened. Copies of its outcome,
task, submission, context profile, provider and verification logs and a
recorded inventory of its context-home modes are in `live-success-243174/`.

### The result that matters, and it is good news

**The real provider followed the adapter's edit-only contract.** Five turns,
18.3 seconds, `is_error: false`, `terminal_reason: completed`, and its own
account:

> "`harness.py` now contains a single line, `print('READY')`... Exit code is 0.
> The change is left uncommitted in the working tree (`git status` shows
> ` M harness.py`); nothing else was touched."

The verification log reads `READY`. The retained outcome carries one proposal
attributed to `Baton worker <worker@baton.invalid>`, authored and committed by
the adapter, with exactly the declared base `842ec458...` as its single parent.
Runtime destroyed, cleanup `retained` with the engine's own absence sentence,
`outstanding_cleanup: []`.

That answers `PROVIDER-QUESTION-239528.md`'s first half: given
implementation-only requirements and an explicit instruction not to move HEAD,
this provider edited and did not commit. One run is one sample, and it is the
sample that was missing.

### Finding 1 -- the custody failure, established

`context_use` was held with reason `custody-invalid`, so the generation was
never sealed -- the context storage has no `generations/` directory at all.

**The cause is directory MODES inside the private context home.**
`context_delivery._private` refuses any custody directory whose mode carries
group or other bits:

    if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077 ...
        refuse("protected custody owner or mode changed")

Running the product's own `_state` measurement over the preserved home, with
the profile's `{conversation_id}` resolved, reproduces it exactly:

    snapshot=False  REFUSED -> protected custody owner or mode changed

**Seven directories the real CLI created carry `0o755`**: `.claude/backups`,
`.claude/projects`, `.claude/session-env`,
`.claude/session-env/<conversation>`, `.claude/shell-snapshots`,
`.claude/projects/-output` and `.claude/projects/-output/memory`. The CLI
created them with the ordinary process umask. `.claude` itself and
`.claude/sessions` are `0o700`, and the state file and the credential symlink
are exactly as the profile requires -- so nothing is wrong with the state; it
is the directories on the way to it.

**Why no deterministic test caught this.** The fixture's fake provider does

    for parent in (state.parent, state.parent.parent): parent.chmod(0o700)

-- it compensates for precisely this behaviour, which is why the harness has
always passed. And the compensation would not have been enough anyway: the
real CLI creates `memory/`, `session-env/`, `shell-snapshots/` and `backups/`,
which are not those two parents.

This is a real product/deployment gap. **It is diagnosed here and not fixed
here**: owner pass 243171 asks for the diagnosis and for the non-progressing
wait, and deciding whether the manager should tolerate a umask-created
directory, or the delivery should impose the mode, is a product decision with
its own security reasoning. It is recorded as the next selection.

### Finding 2 -- a terminal non-progressing condition still waits for the bound

Once the context use is held, `stage_execution`'s composed conclude returns
`outcome: "held"` with `provider-context-unproved` and never reaches
`settle_ending`, so the registered ending obligation stays owed and the stage
projects `answering` forever -- exactly the shape corrected under claim 242687
for the `unable` disposition, one branch over. Claim 242687 deliberately left
this branch alone; this run is the case that shows the same conflation reaches
a COMPLETED turn whose proposal was produced, published and cleaned up.

**Nothing can change after that point.** The runtime is destroyed, the cleanup
is committed, the proposal is retained, and the context hold is durable. The
supervisor nevertheless kept sweeping, and the owner interrupted it at 443
seconds of a 900-second bound.

The supervisor is where this Job can act: a run whose canonical state stops
changing while its stage cannot advance must stop and say so, rather than
spending its whole bound discovering that nothing is happening. A shorter
justified default bound is the backstop, not the mechanism.

### Finding 3 -- the interruption was reported as a traceback

**The outcome WAS retained.** `outcome.json` exists, written at 18:34 for a run
that began at 18:26, and it is complete and internally consistent: `stopped:
interrupted`, `interrupted: "KeyboardInterrupt: signal 2"`, the attribution,
the cleanup and `final_canonical_read: true`. This is read from the file rather
than inferred from the exception, as the owner asked.

What the operator saw was an uncaught `SupervisorInterrupted` traceback out of
`main`. `supervise` deliberately raises it after retaining the outcome -- an
operator who pressed Ctrl-C is owed both the outcome and the process exiting --
but `main` never catches it, so the one thing the operator needed, the path of
the retained outcome, was the one thing not printed.
"""

PLAN = """# Current action -- the successful-baseline stall and interruption report

## Active -- claim 243174, baton.claude

Owner pass 243171, after a run in which the real provider DID follow the
edit-only contract and produce an attributed proposal. Three findings are
recorded in FINDING before any implementation, as that pass requires.

`/home/sl/baton-runs/single-implementation-success-239528/run` is preserved and
was read only. Evidence copied to `live-success-243174/`.

## PINNED OWNERSHIP -- pinned BEFORE the first edit

%s

Only this dossier's own `baseline.py` is edited under this claim. **No file
under `v12/` is touched**: the custody failure is diagnosed, not fixed, and the
non-progressing wait is the supervisor's to correct.

## Selected under this claim

1. **Interruption reporting.** `main` catches `SupervisorInterrupted`, prints
   the retained outcome's path and state plainly, and exits non-zero without a
   traceback. The outcome is already retained; what was missing was saying so.
2. **A terminal non-progressing stop.** A run whose canonical state is
   unchanged across consecutive ticks while its stage cannot advance stops with
   a named reason instead of spending the overall bound. Conservative by
   construction: it requires the stage to be non-terminal AND every started
   runtime to be positively cleaned up AND the observed state to be identical,
   for several consecutive ticks.
3. **A shorter justified default bound**, as the backstop rather than the
   mechanism.
4. Deterministic regressions through the actual composition, preserving the
   context-integrity and no-false-success checks.
5. A successor packet and exact commands. Bound snapshots are NOT overwritten,
   and `snapshot_242687.py`'s destructive rebuild -- reviewer finding
   2026-09-23T00:06:24Z -- is corrected so it refuses an existing destination.

## NOT done here, and recorded as the next selection

The custody mode gap itself. Whether the manager should tolerate a
umask-created directory inside the context home, or the delivery should impose
the mode, is a product decision with its own security reasoning and its own
review. Finding 1 states the evidence and the exact refusing check.

## Not in scope

Any live rerun, recovery, destructive cleanup, reviewer stage, resume or
closure. Credential renewal is not this claim's concern either way.

---

"""


def sha(path):
    reading = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            reading.update(block)
    return reading.hexdigest()


def main():
    pins = "\n".join(f"    {one}\n        {sha(ROOT / one)}" for one in PINNED)
    finding = HERE / "FINDING.md"
    if "the successful baseline run" not in finding.read_text(encoding="utf-8"):
        finding.write_text(
            finding.read_text(encoding="utf-8").rstrip("\n") + "\n" + FINDING,
            encoding="utf-8")
    plan = HERE / "PLAN.md"
    body = plan.read_text(encoding="utf-8")
    if "claim 243174" not in body:
        head = body.split("\n", 1)[0]
        plan.write_text((PLAN % pins) + body.replace(
            head, "# Historical action" + head.split("action", 1)[-1], 1),
            encoding="utf-8")
    print(pins)
    print("recorded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
