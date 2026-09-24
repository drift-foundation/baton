"""Claim-252571: the workspace gap corrected; the fault trace still open."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 252571; RETURNED INCOMPLETE

Review 2026-09-24T01:14:08Z accepted the timeout correction within its actual
scope and returned three things. Two are done; the rest of the owner's
investigation is not.

## Done under claim 252571

  * **180 seconds is PER INVOCATION, and the packet said per attempt.** It
    bounds one provider turn and one verification command; nothing in
    `execution_limits` bounds an attempt's whole life and this packet has no
    other mechanism that does. `LIMITS["per_invocation_seconds"]` is the name
    now, and ADOPTION says what the number bounds and what it does not. The
    total this packet DOES bound is the RUN, at 600s including the 60s
    reserve, which is `supervise`'s arithmetic.
  * **The workspace gap was already identified and I recorded it as
    unknown.** The owner's 2026-09-23 startup entry — one entry above the one
    I worked from — says `worker_preflight` refused because the configured
    `run/workspaces` did not exist, and `operations_from` raised before
    `submit`. The attempt directories I read were made by the LATER
    invocation, after the operator's stopgap; I was reading the wrong
    invocation's leftovers. DIAGNOSIS-252472.md carries both corrections.
  * **The preparation now provisions what it declares.**
    `prepare_two_jobs.PROVISIONED` names the four owned roots the composed
    deployment declares and `provision()` creates them 0o700 after the
    composer has made `run/`, then reads the workspace store back through
    `workspaces.check_workspace_storage` — the same judgment
    `worker_preflight` makes. A case drives that check over the composed path
    before and after preparation: absent refuses by name, provisioned is
    held, and the composed deployment names the provisioned path.

## NOT DONE — the owner's investigation, item by item

  1. **The faulted work-turn diagnostic path**, traced in the pinned
     worker/image source: where provider/agent stdout, stderr and exceptions
     are captured, and which paths persist them when the terminal carries
     `fault_code: agent` and no result manifest. Not begun. Empty logs
     establish nothing about whether another diagnostic exists.
  2. **A deterministic faulting provider at the normal boundary**, to
     reproduce diagnostic retention and failure settlement. Not begun.
  3. **This instance's ending/settlement/intake/runtime facts through
     supported read-only APIs** — no SQL — to identify the actual gate,
     distinguishing a missing result from missing cleanup authority. Not
     begun; the W236087 resemblance remains context, not cause.
  4. **The exact supported cleanup/recovery commands** with preconditions and
     readback, and corrected fresh-run commands. Not delivered, because item 3
     is what would justify them.

## Standing constraints

The preserved instance stays preserved. No cleanup execution, store reset,
container deletion or live rerun. `held` with no committed cleanup and no
verdict is the current outcome; W247941 does not close.

## Evidence

`verification-26.json` — 85 checks, 0 failures, 73.04140571400058s, pins agree.

## Ownership

Reviewer-owned and immutable: ASSESSMENT-249338.md, every `review-*.md` and
`review-*.json`/`.log`. The owner owns the FINDING entries of 2026-09-23 and
2026-09-24. baton.claude owns the rest of this dossier.
"""

PROGRESS = """
## 2026-09-24 — baton.claude, claim 252571

### I recorded an unknown where a finding already existed

My diagnosis said the missing workspace directory was unidentified. The owner
had identified it precisely, one FINDING entry above the one I was working
from: `worker_preflight` refused because the configured `run/workspaces` did
not exist, and `operations_from` raised before `submit` and before
`supervise`.

What misled me was my own evidence. The attempt directories I inspected were
made by the LATER invocation — the one that ran after the operator's stopgap
`mkdir` — so I was reading leftovers from after the directory existed and
concluding it had never been missing. Reading a run's artifacts without
establishing WHICH invocation wrote them is how that happens.

The correction is in the packet as well as the record: `PROVISIONED` names the
four owned roots the composed deployment declares, `provision()` creates them
0o700 once the composer has made `run/`, and the workspace store is read back
through `workspaces.check_workspace_storage` — the same judgment the live
preflight makes, so a provisioning that satisfies this file but not the manager
is a refusal here rather than at the operator's next command. The case drives
that check over the composed path before and after: absent refuses by name,
provisioned is held, and the composed deployment names the provisioned path
rather than one beside it.

### 180 seconds bounds an invocation, not an attempt

The reviewer accepted the ceilings and narrowed what they mean.
`execution_limits` bounds one provider turn and one verification command;
nothing in it bounds an attempt's whole life, and this packet has no other
mechanism that does. `per_attempt_seconds` was the wrong name and ADOPTION's
table repeated it as a guarantee. Both say what the number is now, and the page
says plainly what it does NOT give. The total this packet bounds is the RUN.

### What I did not do

The owner's actual investigation. The faulted work-turn diagnostic path is not
traced in the pinned worker source; no deterministic faulting provider
reproduces the retention and settlement; this instance's ending, intake and
runtime facts are not read through the supported read-only APIs; and no cleanup
or recovery commands are delivered, because item 3 is what would justify them.
Each is named in PLAN.md rather than left as a gesture at remaining work.

### Verification spending

**`verification-26.json` — 85 checks, 0 failures, 73.04140571400058s**, pins
agree.

Named suite subtotal: 901.830474382s + 73.04140571400058s =
**974.871880096s**.

Also measured this claim and NOT in that subtotal: three suite runs at 73.295s,
73.143s and one 72.56113253100193s receipt run that FAILED its own page-count
check — the count update had been short-circuited by an earlier refusal, which
the guard caught; it was corrected and the receipt re-taken. Plus several
sub-second read-only reads of the preserved instance and the pinned source.
Earlier disclosed costs and the ~120s timeout overlap stand unchanged.

State: returned INCOMPLETE through baton.bug with the remaining scope named.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 252571" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
