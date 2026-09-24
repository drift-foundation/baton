"""Claim-252472: one of four live findings corrected; three not yet diagnosed."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 252472; RETURNED INCOMPLETE

Owner 252468: the live two-Job run failed. Preserve
`/home/sl/baton-instances/two-jobs-251156`; diagnose the agent faults and the
failure settlement; correct the missing workspace-directory preparation and the
3600s-versus-180s timeout binding; deliver supported cleanup commands; return
exact operator recovery and fresh-run commands.

[DIAGNOSIS-252472.md](DIAGNOSIS-252472.md) is what this claim established, and
it is one of the four.

## DONE — the timeout binding, diagnosed and corrected

The launch document says why in one member: `execution_limits.requested` is
`{}`, so every boundary resolved to compatibility defaults. And one layer
deeper: `documents.SUBMISSION_LIMITS_SCHEMAS` is `/2` alone, so on the `/1`
submission this packet composed the per-Job `execution_limits` member is
REFUSED as unrecognised — the selected 180s could not be expressed at all.

`SUBMISSION_SCHEMA` is now `/2` and `requested_limits()` derives the ceilings
from `LIMITS["per_attempt_seconds"]`, so the declared bound and the submitted
operand are one number. A case asserts the member and asks the product what a
submitted Job resolves to: `provider_turn` 180, `origin: "job"`.

## NOT DONE — and each is named rather than guessed at

  1. **The agent faults.** Both workers answered `describe` and faulted during
     `work` with `fault_code: agent`; the harness ran and recorded its own
     ending, and the provider's own output is retained NOWHERE — `logs/*/native`
     is empty for both and Docker logs were empty. The next act is to establish
     where a faulted turn's provider output goes and who drops it, not to name
     a cause. The owner said explicitly not to infer authentication failure.
  2. **The failure settlement.** 12 sweeps, no committed cleanup, both
     outstanding, both stages still `starting`. A faulted terminal carries no
     `manifest_digest`, so no intake receipt exists and the ending cannot reach
     `authorize_cleanup` — that is the shape W236087 recorded, and a
     resemblance is not a diagnosis. This store's ending rows have not been
     read.
  3. **The workspace-directory preparation.** Both attempts have every
     directory I can name. I have NOT identified which one was missing, so
     nothing is corrected for it.
  4. **The cleanup commands.** Deliberately not printed: the ending must be
     settled before a destroy can be authorized, and item 2 is what has not
     established that path. `docker rm` is not the procedure — it would remove
     the runtime with no committed cleanup record.

## REMAINING SCOPE, exactly

Items 1–4 above, then the operator recovery and fresh-run commands, then
independent review. The preserved instance must stay preserved; no live rerun,
store reset or container deletion.

## Evidence

`verification-25.json` — 84 checks, 0 failures, 72.36727672899724s, pins agree.

## Ownership

Reviewer-owned and immutable: ASSESSMENT-249338.md, every `review-*.md` and
`review-*.json`/`.log`. The owner owns the FINDING entry of 2026-09-24T00:58Z.
baton.claude owns the rest of this dossier.
"""

PROGRESS = """
## 2026-09-24 — baton.claude, claim 252472

### The live run failed, and one of its four findings is mine to fix outright

The timeout binding. The owner saw 3600 compatibility seconds on a run this
packet declared at 180, and the launch document it delivered says why:
`execution_limits.requested` is `{}`. My submission asked the manager for
nothing, so every boundary fell to the frozen defaults.

The reason is one layer deeper than a forgotten member.
`documents.SUBMISSION_LIMITS_SCHEMAS` is `baton.v12.job-submission/2` alone, and
this packet composed `/1` — on which that member is refused as unrecognised.
The bound I had written into `LIMITS` and printed in ADOPTION's limits table
could not be expressed in the document I was composing. It was a claim in prose
with nothing behind it, which is the same defect as several earlier ones in this
dossier wearing a different hat.

Corrected: `/2`, and `requested_limits()` derives the asked-for ceilings from
`LIMITS["per_attempt_seconds"]` so the declared and the submitted are one
number by construction. The case asserts the member and then asks the PRODUCT
what a submitted Job resolves to — 180, `origin: "job"` — because a member
present and a ceiling effective are different facts and the live run had
neither.

**This does not explain the failure.** Both containers exited in about two
seconds; no ceiling of any size was reached. Correcting it removes a real
defect and diagnoses nothing.

### Three findings I did not diagnose, and I am not going to guess

**The agent faults.** Both workers answered `describe` and faulted during
`work`, `fault_code: agent`, `disposition: null`, `manifest_digest: null`. So
the harness ran and recorded its own ending; the agent inside it failed. And
the provider's own output is retained NOWHERE — `logs/attempt-*/native` is
empty for both attempts and the owner records empty Docker logs. I have nothing
that would distinguish a credential problem from a missing directory, a umask,
a refused network or a bad invocation, and the owner said explicitly not to
infer authentication failure. The next act is to establish where a faulted
turn's provider output goes and who drops it.

**The failure settlement.** Twelve sweeps, no committed cleanup, both attempts
outstanding, both stages still `starting` while both runtimes were quiescent. A
faulted terminal collects no intake receipt, so the ending cannot reach
`authorize_cleanup` — which is exactly the shape W236087 recorded for its own
stalled cleanup. That is a resemblance and I have written it down as one; I
have not read this store's ending rows.

**The workspace-directory preparation.** The owner names a missing one. Both
attempts have `scratch`, `credentials`, `custody`, `workspace`,
`credential-state` and `inputs`, and Job A's `workspace` holds its result
directory. I have not identified which directory was absent, so I have
corrected nothing for it — a change to a directory I cannot show was missing
would be a fix without a cause.

**The cleanup commands are deliberately not printed.** The ending has to be
settled before a destroy can be authorized, and that is precisely the item
above that is unfinished. `docker rm` is not the procedure: it would remove the
runtime while the manager's journal still asserts nothing was cleaned, which is
the opposite of an accounted stop.

The supervisor itself behaved correctly and reported honestly: admission closed
before cancellation, both assignments fenced, both runtimes confirmed quiescent,
`held`, every reason named.

### Verification spending

**`verification-25.json` — 84 checks, 0 failures, 72.36727672899724s**, pins
agree.

Named suite subtotal: 829.463197653s + 72.36727672899724s =
**901.830474382s**.

Also measured this claim and NOT in that subtotal: six suite runs at 72.162s,
72.521s, 72.123s, 72.597s and two that failed to load from the dossier rather
than the distribution; one receipt attempt that recorded 1 check and an error
for the same reason, discarded and re-taken; and several sub-second reads of the
preserved instance. Earlier disclosed costs and the ~120s timeout overlap stand
unchanged.

State: returned INCOMPLETE through baton.bug with the remaining scope named.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 252472" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
