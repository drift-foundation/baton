"""Claim-249988: the command runs end to end; a success through it does not."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 249988

## Done under claim 249988

  * **`main` takes the seams a deterministic witness needs**, and every one
    defaults to production: `credential_provider`, `engine_run`, `clock`,
    `checkout` and `turns`. A caller that supplies none gets the real
    provider, engine and clock and no worker turn — exactly what an operator
    typing the documented command gets.
  * **A case drives the whole command**: it opens both stores, composes with a
    disposable provider and engine, submits, serves bounded at 12/4, stops and
    publishes `baton.v12.two-job-outcome/1` naming both Jobs.

47 focused checks, 0 failures, measured 25.820313595002517s,
`verification-15.json`; 1 is new.

## NOT done, and named rather than papered over

**A SUCCESS THROUGH `main`.** The turn callback in that case answers nothing,
because a turn needs the mounted attempt path and `main` hands none out — so
the run reports `held` with `serving-bound-exceeded`, which is the honest
outcome for a run whose workers never answered. The case is named for what it
proves. Closing this needs `main` to expose the composed operations to its
`turns` callback (the supervisor already passes the gate; the mount comes from
the composition), which is a small change I did not make blind.

Also remaining: `main`'s no-result, deadline, failure and interruption checks;
operator steps 4 and 7; and any residual pool/turns prose.

## Ownership

Reviewer-owned and immutable: ASSESSMENT-249338.md, every `review-*.md` and
`review-*.json`/`.log`. baton.claude owns the rest of this dossier.
"""

PROGRESS = """
## 2026-09-23 — baton.claude, claim 249988

### The command runs end to end

`main` now takes `credential_provider`, `engine_run`, `clock`, `checkout` and
`turns`, and every one defaults to production — a caller that supplies none
gets the real provider, the real engine, the real clock and no worker turn,
which is what an operator typing the documented command gets. The seams are
where a deterministic witness stands, at the same boundary the accepted
lifecycle fixtures use.

Driven through the command with a disposable provider and engine, it opens both
stores, composes, submits, serves bounded and publishes
`baton.v12.two-job-outcome/1` naming both Jobs.

### And it is NOT a success through `main`, which the case now says

My first version of that case was called
`test_MAIN_reaches_four_attempts_and_two_verdicts` and asserted neither. The
turn callback answers nothing, because a turn needs the mounted attempt path
and `main` hands none out, so the run reports `held` with
`serving-bound-exceeded` — the honest outcome for a run whose workers never
answered. I renamed it to what it proves and wrote the gap into its docstring
rather than leaving a name that overstated it.

I also had to bound it at 12/4: `main` serves on the REAL wall clock, and the
600-second default ran the suite past its timeout. The arithmetic is proved
separately on a controlled clock; this proves the command.

### Verification spending

47 focused deterministic checks, 0 failures, measured 25.820313595002517s,
receipt `verification-15.json` with `verification-15.log`; 1 is new. The suite
is slower because this case serves on the real clock.

Cumulative MEASURED for W247941, every retained invocation preserved:
1.678180975 + 2.122556141 + 2.145897528 + 2.868183810 + 2.876618006 +
3.646601886 + 3.682941216 + 6.941682081 + 10.885859361 + 10.943187142 +
10.857 + 11.135997740 + 11.183168619 + 11.520278754 + 11.597300884 +
11.682510099 + 14.049334683 + 13.071588666 + 17.320021491 + 25.820313595 =
**186.029222677s**. The reviewer's 4.477976402s is theirs.

State: returned INCOMPLETE through baton.bug.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 249988" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
