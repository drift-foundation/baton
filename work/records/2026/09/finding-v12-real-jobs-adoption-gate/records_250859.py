"""Claim-250859: the preparation is executable, and the page is the run."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 250859

Review 2026-09-23T20:34:15Z requested changes on the preparation path. All four
findings are corrected and each is now a check.

## Done under claim 250859

  * **The run root leaves the checkout boundary.** `/home/sl/baton-runs` is
    the checkout the pinned validator derives, so the shape this page printed
    was refused at composition. `prepare_two_jobs.BOUNDARIES` refuses such a
    root BEFORE anything is written, the page selects
    `/home/sl/baton-instances/...`, and the validator is untouched.
  * **The bootstrap is a command.** Step 2 prints `-m tools.bootstrap` with
    its destination and distro, and the preparation READS the identity from
    the record it emits; an `--authority-uuid` that disagrees is refused.
  * **One layout, from `tools.bootstrap.layout`.** Stores under `db/`,
    documents under `run/`. My previous reconciliation moved the inspect step
    onto the run step's root-level paths — the wrong side. The preparation
    prints `serve_command` and `status_command` from the places it used, and a
    case checks them against the files it emitted.
  * **Freshness resolves the path.** A fresh-named symlink into a consumed
    root walked around the lexical check; `realpath` closes it, and a case
    drives that exact alias.
  * **Refusals before effects.** Boundary, identity, symlink, base, source,
    bootstrap record, a repeat with different bytes and an existing composed
    target are all decided before the first byte. Only the two task documents
    are written before validation — the validator OPENS the configured task —
    and never over differing bytes.
  * **The shared task speaks to both roles.** The input identity stays shared,
    which is the supported shape; what changed is the text, which told its
    consumer to create the file and that judging was somebody else's stage.

## Evidence

`verification-22.json` — 78 checks, 0 failures, 68.90801154400106s, pins agree.
Seven of the new cases drive `prepare_two_jobs.main` itself, through the real
composer, on a disposable fresh Authority.

## REMAINING

The operator's own steps: the fresh root outside the boundary, the fixture
commit, the bootstrap, then the preparation command, then — separately — the
run. The container boundary and the live provider under concurrency stay
unproved.

## Ownership

Reviewer-owned and immutable: ASSESSMENT-249338.md, every `review-*.md` and
`review-*.json`/`.log`. baton.claude owns the rest of this dossier.
"""

PROGRESS = """
## 2026-09-23 — baton.claude, claim 250859

### The recipe could not be run, and the reviewer ran it

Composing the shape this page printed refuses by name: the integration store
under `/home/sl/baton-runs/two-jobs-.../db/` is inside the checkout the pinned
validator derives. The fixture-root section of this very page documents that
rule. I had applied it to the tests and not to the recipe.

The run root is now selected outside both boundaries, and
`prepare_two_jobs.BOUNDARIES` refuses one inside them before anything is
written rather than letting the composition find it after task files exist and
Authority acts have run.

### Three documents, three layouts

The preparation wrote into `ROOT/run`, step 4 named `ROOT/...` and step 6 named
`ROOT/db/...`. No reading of `<run root>` reconciles that. `tools.bootstrap`
already says where things go — four stores under `db/`, mutable state beside
them — so every path now comes from `layout()`, and the preparation prints the
exact `serve_command` and `status_command` it implies. A case checks those
against the files the run emitted.

**My earlier reconciliation of this same mismatch moved step 6 onto step 4's
paths.** That was the wrong side, and it is why the defect came back wearing a
different shape.

### One `ln -s` walked around every refusal

`fresh()` compared normalized LEXICAL components, so a fresh-named symlink
pointing into a consumed root was accepted. `realpath` first closes it, and a
case builds that alias and asserts the refusal names the consumed root.

### Order: refusals, then effects

`main` wrote both task documents and the resolved selections, then acted on the
Authority, and only then met the composer. Now every refusal is decided first
— boundary, identity, symlink, base, source, bootstrap record, a repeat with
different bytes, an existing composed target. The only thing written before
validation is the two task documents, because the validator OPENS the
configured task; they are never written over differing bytes, and a validation
failure says exactly which two files exist.

I am not claiming whole-command replay. An exact repeat REFUSES at the
create-only target and leaves every earlier byte intact, and a changed base
refuses before writing; both are asserted by reading the bytes back.

### The reviewer was right about the shared task

`two_jobs.worker_document` gives both roles the same task and the same input
identity — that is the supported shape and I did not route around it. What was
wrong was the text: it told its consumer to create the file and that judging
was somebody else's stage, which is implementation-only instructions delivered
to a reviewer. The document now states the requirement once and addresses both
stages, with the review part read-only and all three verdicts equally valid.

### Verification spending

**`verification-22.json` — 78 checks, 0 failures, 68.90801154400106s**, pins
agree.

Named suite subtotal: 618.223460344s + 68.90801154400106s =
**687.131471888s**.

Also measured this claim and NOT in that subtotal: five suite runs at 68.222s,
68.959s, 69.623s, 69.268s and one that failed to load because it ran from the
dossier rather than the distribution; one receipt attempt that recorded 1 check
and an error for the same reason, discarded and re-taken; and four single-case
runs under half a second. Earlier disclosed costs and the ~120s timeout overlap
stand unchanged.

State: passed for independent review.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 250859" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
