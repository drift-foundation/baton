# G1 progress — baton.claude

## 2026-09-26 claim 275681 — milestone-1 core implemented; INVENTORY FALLOUT MEASURED, NOT FIXED

Review 2026-09-26T13:29:00Z's four corrections accepted; three are implemented, one is
pinned and reported below.

**THE FOUR CORRECTIONS, and what I did with each.**

1. **Production ownership contradicting the connection — ACCEPTED, seam pinned, NOT yet
   wired.** My read-only declaration was author-imposed, as the reviewer said. The seam
   I select is `attempts.py:1454 request_runtime_start` for acquisition and
   `oci.py:2265 start` / `:3067 stop` for launch correlation and cessation, with
   `job_manager/manager.py:804 serve` for overdue enforcement. Those four are now mine
   under this Work. **I have not edited them, and the module is therefore still an
   unused helper — which the reviewer is right does not count as the milestone.**
2. **Conflict identity outliving an attempt — IMPLEMENTED and proved.** `domain_of`
   names the RESOURCE; my "attempt-derived" proposal is withdrawn in the module's own
   docstring as "an escape hatch dressed as an identity". Two distinct attempts
   competing for one resource, and an unrelated resource progressing, are both cases.
3. **Withholding effects until binding — IMPLEMENTED as a positive gate.**
   `effects_permitted` answers False until this generation is current, unreturned,
   unexpired AND has a bound container; the binding is typed to the journalled launch,
   so a container from another start cannot attach. The closed start/dispatch sequence
   at the production seam is the next step.
4. **First milestone bounded — RESPECTED.** Generation exclusion beyond gen2, renewal
   versus expiry, lost replies, restart reconciliation and engine-failure holds are NOT
   asserted and are not claimed; the selector says so at the top.

**PROFILE SEMANTICS RECORDED** as the reviewer required: `LIFETIME_SECONDS` 900,
`STOP_GRACE_SECONDS` 30 (after which an answer counts as UNKNOWN and is held, never
presumed stopped), `RENEWAL_LIMIT` 4 (exhaustion does not free the resource), and
`TOKEN_VERSION` 1 so a later shape change is a migration. Journal-only representation,
no schema change.

**EVIDENCE.** `test_shared_resource_token.py` 10 cases OK, 0.024s, on real disposable
`ControlStore` instances. **Seven mutations, all caught:** dropping the outstanding
check → 1 fails; dropping the effects gate → 2; dropping the cessation check → 3;
dropping ONLY the surviving-helper half → 2; dropping the launch-correlation check → 1;
skipping the eligibility predicate → 1; dropping the stale-owner check → 1.

**AND HERE IS WHAT I BROKE, measured rather than left for the reviewer to find.**

    tests.manager.test_boundary_inventory   41 failures   (its baseline on this tree is 28)
    tests.manager.test_dependencies        144 failures   (no baseline: never run in my Works)
    tests.manager.test_secrets               2 failures
    `tokens.py` is named 51 times across those three suites' output.

So `tokens.py` is implicated and I am not calling this milestone clean. The cause is the
same class as the 42-failure cascade I caused in W270664: a new module's public
parameters must appear in `test_dependencies`' declared OPERANDS set, and its
`boundaries.*` call sites become receiving entries the inventory requires declared and
probed. `domain`, `execution`, `eligible`, `cessation`, `launch`, `container`,
`resource_kind` and `generation` are the new names. **The fix is a declaration change in
those author-owned catalogs, and I could not verify it inside this claim's remaining
budget** — beginning it and handing over a half-declared catalog would be worse than
reporting the count.

**EXACT REMAINING SCOPE, in order.** (a) Declare the new operands and boundary entries
and re-measure all three suites against their baselines. (b) Wire the pinned seam so the
token governs a real runtime path, with the closed start/dispatch gate. (c) Generation
exclusion gen1/gen2/gen3 and late-binding refusal after revocation. (d) Renewal versus
expiry arbitration including the lost reply. (e) Restart reconciliation of overdue and
uncertain tokens; engine-failure holds; production overdue enforcement without a status
read or a fixture calling a helper. (f) The journal-walk measurement, and the projection
table only if it is needed, with its compatibility plan.

**PRESERVED:** W270664's evidence and probes, W257624's region, the accepted
no-implicit-reopen refusal. G2 and G3 untouched. No live Docker, provider, engine,
deployment, cleanup or version-control mutation.
