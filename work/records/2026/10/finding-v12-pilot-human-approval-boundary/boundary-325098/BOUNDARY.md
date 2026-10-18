# The supported human approval boundary — established

Claim 325098, 2026-10-18. Driven by `human_boundary.py`; every step has its own
JSON answer beside this file and `MANIFEST.json` binds them by SHA-256. One
run, 0.6s. **The reviewer's research was right and the path works end to end
from a clean pre-receipt state.**

What was NOT touched, which is what makes this the human path rather than the
automatic one: `_accepted_receipts` (private, and it bundles the approval),
`admit_accepted`/`continue_accepted` (automatic integration admission), and any
forged receipt, invented worker observation or product edit.

## The chain, as driven

| Step | Result |
| --- | --- |
| 1. clean native reviewed candidate | proposal `integration-driver.proposal:d4312ded…`, **all four receipts absent**, accepted checkpoint present, `ordinary_test_evidence` resolving |
| 2. deployment grants | verifier and reviewer distinct from the owner; the owner holds no `verify` or `review`; generation pinned after the grants |
| 3. independent judgments | `verify` `passed` by `baton.verifier-325034`, `review` `accepted` by `baton.reviewer-325034`, **approval still `null`** |
| 4. owner `pending` | **`approval-due`**, approval receipt absent, owner holds approve/integrate/close |
| 4b. dossier binding | `record bind` — the citation's prerequisite |
| 5. approval withheld | human integration refused, satisfying closure refused, `session.integrate` refused `integration requires explicit approval`, receipts unchanged |
| 6. owner's decision | stale candidate, wrong review receipt and wrong principal each refused; `approve` accepted as `baton.slaw`; exact replay replays |
| 7. closure and readback | `integrated` and `close satisfying` accepted; readback `closed` with the acceptance clause, the commit and `evidence_now: intact` |

Final receipts, each by its own actor: verification `passed`
(`baton.verifier-325034`), review `accepted` (`baton.reviewer-325034`),
approval `approved` (`baton.slaw`), integration `integrated` (`baton.slaw`).
The close decision records principal `principal:baton.slaw`, role `close`,
generation 15.

## So the suspected defect is NOT a product defect

My W321690 note reported that the native path pre-empts the owner's approval.
That observation stands for the path it measured — automatic integration
admission writes all three receipts, and the owner's later approve is then
refused as immutable — but it is **not** the selected human-integration path
and it is not the only way to reach an approvable candidate. On a clean native
reviewed candidate, verification and review can be published independently by
separately granted participants while the approval is withheld, and the owner's
own decision then lands through the installed command. No product change is
needed for single-human approval.

What a deployment must therefore DO, which belongs in the pilot packet:

1. Select single-human approval by **not** running automatic integration
   admission for that Work. The automatic path is a different selection.
2. Grant `verify` and `review` to participants distinct from the owner, and
   `approve`/`integrate`/`close` to the owner — which is exactly what
   `bootstrap`'s `owner_participant` member does for the owner half.
3. Bind the canonical dossier before the owner records a human integration;
   the citation refuses without it. This driver's first run was refused for
   exactly that reason, which is recorded rather than tidied away.

## What is simulated, labelled

The engine (no daemon) and the provider (injected) in the Job's own turns; the
verifier's and reviewer's JUDGEMENTS, made here on the basis of the exact
public observations the evidence files print; and the owner's approval, human
integration record and closure. The integration record's own bytes say
`SIMULATED` and carry forty zeroes for the commit so it cannot be mistaken for
one. No live model, live credential, deployment or Git mutation.
