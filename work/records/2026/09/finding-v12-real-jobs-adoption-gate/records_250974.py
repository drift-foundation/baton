"""Claim-250974: the bootstrap step is a command, and the preflight is whole."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 250974

Review 2026-09-23T20:52:13Z accepted the root, role and layout corrections and
named three remaining items. All three are done.

## Done under claim 250974

  * **The bootstrap input is derived, not asked for.**
    `--emit-bootstrap-inputs` prints the `tools.bootstrap --inputs` document
    from the same accepted configuration as everything else. It runs before
    the instance exists, needs no record, performs no act, and still refuses a
    root inside a checkout boundary or under a consumed instance.
  * **The real tool is exercised.** A case emits the inputs, runs
    `tools.bootstrap` on a disposable destination with the pinned distro, and
    then runs the preparation against the receipt it actually wrote — through
    the real composer, to emitted documents.
  * **The Works are reconciled by running the tool rather than reasoning.**
    A fresh install prints `job   none; no Work, grant or placeholder was
    created`, and the case asserts that line. The preparation's two Works are
    therefore its own.
  * **The runtime install is named as the seam.** `tools.bootstrap` refuses
    without `--distro` and copies the pinned distribution; that copy is the
    only part of step 2 these checks perform rather than reason about.
  * **The create-only preflight matches the composer.** Any existing target
    path is refused — empty, occupied, symlink or not a directory — before the
    task documents, the selections or the Authority are touched, and a case
    asserts nothing was written.
  * **The provenance check runs before the effects**, and says only what it
    can: the in-process `baton_v12` that VALIDATES the packet must be the
    pinned one, which is a refusal; `tools` is imported by the composer
    subprocess, which binds its own path and runs the same check, so this
    process's resolution is recorded in the receipt rather than refused.
  * **The page distinguishes the two replays.** The Authority act replays
    under its own identity; the COMMAND refuses an exact repeat early, before
    any effect. It used to claim only the first.

## Evidence

`verification-23.json` — 80 checks, 0 failures, 70.19959550499334s, pins agree.

## REMAINING

The operator's own steps: the fresh root outside the boundary, the fixture
commit, the two step-2 commands, the preparation, then — separately — the run.
The container boundary and the live provider under concurrency stay unproved.

## Ownership

Reviewer-owned and immutable: ASSESSMENT-249338.md, every `review-*.md` and
`review-*.json`/`.log`. baton.claude owns the rest of this dossier.
"""

PROGRESS = """
## 2026-09-23 — baton.claude, claim 250974

### The bootstrap step still had a hole in it

The page named `tools.bootstrap` and left its required `--inputs` as
`<see v12/STACK.md>` — which is the open configuration task the owner had just
asked me to remove, one layer further down. `--emit-bootstrap-inputs` now
derives that document from the same accepted configuration as everything else,
and step 2 prints both commands.

I ran the tool before writing anything that claimed to know what it does. It
needs a built runtime — *"installing into … needs a built runtime; name it with
`--distro`"* — and with the pinned one it emits the record, the identity, the
empty-capacity configuration and the four stores, and prints:

> `job   none; no Work, grant or placeholder was created`

That is the reconciliation the reviewer asked for: a fresh install creates no
Work, so the preparation's two are its own and nothing competes. A case asserts
that exact line rather than my paraphrase of it, then feeds the receipt the
tool wrote into the preparation and checks the emitted packet.

The runtime copy is the seam, and the page says so: it is the only part of step
2 these checks perform rather than reason about.

### An empty directory walked through the preflight

The target check looked for `deployment.json` or `submission.json`, so an empty
`run/` passed it and the composer — which is create-only about the PATH —
refused afterwards, after the task documents, the selections and the Authority
acts. It now refuses any existing target, including a symlink or a
non-directory, and a case with an empty target asserts nothing was written.

### What the provenance check can honestly refuse

The reviewer asked for the composer's pins/import check to run before the
mutations. It does now, and it says only what it can: the `baton_v12` that
VALIDATES the packet in this process must be the pinned one, and that is a
refusal. `tools` is imported by the composer, which runs as a subprocess with
its path bound explicitly and runs this same check itself — so this process
resolving `tools` from a checkout it happens to be sitting in says nothing
about the artifact. Refusing on it would have failed callers for a condition
that never reaches the packet, so it is recorded in the receipt instead. The
suite found that immediately: bound as the tests bind it, `tools` is the
checkout's and `baton_v12` is the snapshot's.

### Replay, described as two things

The page said running it twice replays the same Works. That is true of the
Authority act and false of the command: a completed run has a composed target,
and the create-only rule refuses a second invocation before anything is
touched. Both are now stated, and the page says plainly that there is no
in-place re-preparation — select a fresh root.

### Verification spending

**`verification-23.json` — 80 checks, 0 failures, 70.19959550499334s**, pins
agree.

Named suite subtotal: 687.131471888s + 70.19959550499334s =
**757.331067393s**.

Also measured this claim and NOT in that subtotal: three suite runs at 68.695s,
70.220s and one that failed to load from the dossier rather than the
distribution; three receipt runs at 69.9201890520053s, 70.34040969400667s and
70.06803670999943s taken while line lengths were being corrected, so only the
last is the receipt; one single-case run; and two throwaway bootstrap probes,
whose temporary destinations were removed. Earlier disclosed costs and the
~120s timeout overlap stand unchanged.

State: passed for independent review.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 250974" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
