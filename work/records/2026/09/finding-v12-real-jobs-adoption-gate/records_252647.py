"""Claim-252647: the settlement gate is read, and it is my supervisor's gap."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 252647; RETURNED INCOMPLETE

Review 2026-09-24T01:25:43Z accepted the workspace provisioning and the
per-invocation wording and asked for the four unstarted owner items. **One is
done, and it answers a question I had previously only resembled.**

## DONE — the settlement gate, read through the supported readers

`settlement_252647.py` opens the preserved instance read-only and asks the
public readers the review named — `ending.intent_of`, `settlement_of`,
`ending_of` — plus the attempt, intake and output readers. No SQL, no act.
`SETTLEMENT-252647.json` is the receipt; `SETTLEMENT-252647.md` is the finding.

**No composed-ending obligation was ever registered.** All four stages at
episode 1 answer `None` for intent, settlement and both, and
`pending_endings()` is empty — so nothing was owed and nothing was waiting. The
twelve cleanup sweeps had nothing to settle; they were not blocked.

**It is a missing RESULT, not withheld cleanup authority**, and the chain is
absent link by link: faulted terminal with no `manifest_digest` → no intake
receipt → no gate discharge → no cleanup authority. Nothing refused; nothing
was asked.

**And the defect is mine.** `intake.abandon_attempt` is the manager's FOURTH
ending, for exactly this case — an attempt whose runtime started and whose
worker never answered, with no receipt, no start failure and no refusal.
`two_job_supervisor.supervise` closes admission, cancels and sweeps, and has
**no abandonment step**, so a faulted receiptless attempt can never reach a
cleanup record however many sweeps run. The product has the door; this packet
does not use it.

The ordinary receipt path must not substitute: a stop ordered before the fence
recreates the boundary W44716 exists to close.

## NOT DONE

  1. **The executed image's diagnostic path.** Where provider stdout, stderr
     and exceptions go on a faulted turn, traced in the IMAGE's own source —
     the reviewer's caution stands: the checkout's `claude_agent._Captured`
     locators are not proven to match the image that ran.
  2. **A deterministic faulting provider** at the normal boundary, reproducing
     both diagnostic retention and the settlement gate above.
  3. **The supervisor's abandonment step**, which the finding above now
     identifies as the correction.
  4. **The runnable recovery invocation.** `SETTLEMENT-252647.md` states the
     operation, its preconditions (all four already established by the read)
     and the exact readback that means it worked, but does NOT print a command:
     `abandon_attempt` takes a live Authority port and an engine adapter, and
     the operand composition for this deployment has to be read out of
     `tools/dogfood_operator.py` and shown to compose against
     `run/deployment.json` first. Bounded, and next.
  5. **Corrected fresh-run commands**, after 3.

## Standing constraints

The preserved instance stays preserved and was opened read-only. No cleanup
executed, no store reset, no container deleted, no live rerun. `held` with no
committed cleanup and no verdict is the current outcome; W247941 does not close.

## Evidence

`verification-27.json` — 85 checks, 0 failures, 72.99730089001241s, pins agree.

## Ownership

Reviewer-owned and immutable: ASSESSMENT-249338.md, every `review-*.md` and
`review-*.json`/`.log`. The owner owns the FINDING entries of 2026-09-23 and
2026-09-24. baton.claude owns the rest of this dossier.
"""

PROGRESS = """
## 2026-09-24 — baton.claude, claim 252647

### The resemblance was wrong about which half was missing

Last claim I offered W236087's stalled cleanup as a resemblance and said so.
The reviewer pointed at the supported readers instead, and reading them changes
the answer.

Every one answers absence. No intake receipt, no gate discharge, no ABANDONED
gate discharge, no cleanup of either kind, no frozen output — and on the Job
side, for all four stages at episode 1, no ending intent, no settlement, and
`pending_endings()` empty.

**So nothing was owed.** I had been describing a manager that could not settle
an obligation; there was no obligation. The twelve cleanup sweeps were not
blocked by a missing authority, they had nothing to settle. That is a different
fact from the one I wrote down, and it is the one the readers give.

The chain is absent in order: faulted terminal with no `manifest_digest` → no
intake receipt → no gate discharge → no cleanup authority. Missing RESULT, not
withheld authority, which is exactly the distinction the review asked for.

### And the defect is mine

`intake.abandon_attempt` is the manager's fourth ending and it exists for this
case in as many words — "an attempt whose runtime started and whose worker
never answered has no receipt, no start failure and no refusal, and now has its
own public operation". It carries its own fence and its own removal order.

`two_job_supervisor.supervise` closes admission, cancels through
`_cancel_active`, drives sweeps and reads the journal. It never abandons. So a
faulted receiptless attempt cannot reach a cleanup record in this packet at
all, however long the reserve — which is why the live run reported outstanding
cleanup and why that report was honest.

I am not adding the step in this claim. It is a behaviour change to accepted
bounded-run machinery on the strength of a finding written an hour ago, and it
belongs in front of a reviewer as a named correction rather than inside the
claim that discovered the need for it.

### The recovery, prepared and deliberately not printed as a command

`SETTLEMENT-252647.md` states the operation, its four preconditions — every one
already established by this read — and the exact readback that means it worked:
an abandoned gate discharge, and an abandonment cleanup of `retained`.

It does not print a runnable invocation, and the reason is specific rather than
cautious: `abandon_attempt` takes a live Authority port and an engine adapter,
so the operand composition for THIS deployment has to be read out of
`tools/dogfood_operator.py` and shown to compose against the served
`run/deployment.json` before a command is printed. Printing one I have not
composed is how an operator ends up typing something nobody checked.

`docker rm` is still the wrong act, and now for a stated reason: it would remove
the runtime while the Authority still holds the assignment unfenced, which is
the boundary abandonment exists to close.

### Verification spending

**`verification-27.json` — 85 checks, 0 failures, 72.99730089001241s**, pins
agree.

Named suite subtotal: 974.871880096s + 72.99730089001241s =
**1047.869180986s**.

Also measured this claim and NOT in that subtotal: two read-only probes of the
preserved instance, the first of which failed on an import name that does not
exist in the pinned tree (`runtimes`) and was corrected to the supported
readers; both were sub-second. Earlier disclosed costs and the ~120s timeout
overlap stand unchanged.

State: returned INCOMPLETE through baton.bug with the remaining scope named.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 252647" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
