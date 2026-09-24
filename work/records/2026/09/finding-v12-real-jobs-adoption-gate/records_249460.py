"""Claim-249460 entries: R1, R2, R3-part and R5 done; R3-verdicts and R4 not."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 249460

Review 2026-09-23T17:12:02Z raised R1-R5. **Three and a half are done; two are
returned unfinished and named exactly.**

## Done under claim 249460

  * **R1 — the composer now composes.** `two_jobs.composed` built nothing: it
    returned the selections' own `arrangement` member, so `held` refused it for
    the schema before reaching an operand. It now builds the four worker
    documents, the two bindings, the `/2` deployment and the submission, and
    holds the deployment before anything is written.
  * **R2 — the operator commands are the ones the CLI accepts.** `--store`,
    `--incarnation` and `--authority-uuid` are required on EVERY
    `tools.job_manager` command and were missing from serve, submit and status.
  * **R3 (part) — the arrangement now ACTS on its two claimed boundaries.**
    The composed document carries `correction_policy: "decline"` (mirrored from
    the product's own word and compared against it), and the witness's
    submission carries no integration stage for either Job. Both Jobs now reach
    their OWN reviewers on distinct attempts.
  * **R5 — the pin check hashes the whole manifest and fails closed.** One
    digest over every (path, content) pair in the snapshot,
    `ab5e5b0b...fae1cd5`, and a disagreement now exits 1 instead of printing a
    mismatch beside a success status.

19 focused checks, 0 failures, measured 2.1225561409955844s,
`verification-2.json`.

## NOT done, returned through baton.bug

  * **R3 (rest) — two FROZEN attributed verdicts.** Both reviewers are reached
    on their own attempts; that is not two collected verdicts and the packet no
    longer implies it is. What remains is driving both review turns to frozen
    results and reading each verdict back through
    `review_driver.review_verdict_from_result`, with the affected failure and
    interruption checks.
  * **R4 — the bounded four-admission supervisor**, its stop, positive cleanup
    for all four attempts and its published outcome. No such supervisor exists;
    both accepted ones cap a single workload.

## Ownership

Reviewer-owned and immutable: ASSESSMENT-249338.md,
ASSESSMENT-EVIDENCE-249338.json, review-2026-09-23T17-12-02Z.md,
review-evidence-249444.json, review-witness-shape-249444.json. baton.claude
owns two_jobs.py, test_two_jobs.py, ADOPTION-247941.md, CONTINUITY-247941.md,
SELECTIONS-247941.json, verify_247941.py, verification-*.json/.log,
PROGRESS.md, records_*.py and PLAN.md.
"""

PROGRESS = """
## 2026-09-23 — baton.claude, claim 249460

Review 2026-09-23T17:12:02Z found five things. Three of them were my packet
claiming what my code did not do, which is the failure I have now hit in three
consecutive Works, and the reviewer was right about each.

### R1 — the composer composed nothing

`two_jobs.composed` returned `selections["arrangement"]` unchanged. That is a
DESCRIPTION of a deployment — an `instance`, a `jobs` list and a `limits`
block — not a deployment, and `held_configuration` refused it for the schema
before it ever reached an operand. The product was saying the composer had not
run, and the packet's step 3 was advertising a roundtrip nobody had taken.

It now builds the four worker documents from the resolved operands, the two
bindings, the `/2` deployment and the submission, and holds the deployment
before writing anything.

### R2 — the commands did not run

`--store`, `--incarnation` and `--authority-uuid` are required on EVERY
`tools.job_manager` command and are deliberately not defaulted; I omitted all
three from serve, submit and status, and the reviewer reproduced `exit 2`.
Fixed, with the reason recorded on the page rather than just the flags.

### R3 — the witness contradicted the arrangement

Two ways. The document carried no `correction_policy`, which means `open` —
so "corrections declined" was prose while the composed deployment said
otherwise. And the inherited submission carried an INTEGRATION STAGE for both
Jobs, while the packet said this gate submits none. A limit the documents
assert and the submission contradicts is not a limit.

Both are now acts: `arrangement` sets `decline` and `held` compares it against
the product's own word, `both_jobs` drops the integration stages, and cases
assert each on the document and submission that actually serve. Both Jobs also
now reach their own reviewers on distinct attempts.

**What is still NOT witnessed is two FROZEN attributed verdicts.** Reaching two
reviewers is not collecting two verdicts, and the packet now says so instead of
implying otherwise.

### R5 — the pin check could not see content, and passed anyway

It counted 106 files, which is the property a drifted snapshot is most likely
to keep, and it exited 0 on a mismatch — so an operator following step 1 would
have seen a disagreement and a success status together. It now hashes every
(path, content) pair into one digest, `ab5e5b0b...fae1cd5`, and exits 1 when
anything disagrees. I probed the failure path before trusting it.

### Verification spending

19 focused deterministic checks, 0 failures, measured 2.1225561409955844s,
receipt `verification-2.json` with `verification-2.log`; 3 are new.

Cumulative MEASURED for W247941: 1.678180975 + 2.122556141 = **3.800737116s**.
The pin check is separate and its elapsed time was not measured.

State: returned INCOMPLETE through baton.bug — R3's frozen verdicts and R4's
four-admission supervisor remain, with no work started on either.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 249460" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
