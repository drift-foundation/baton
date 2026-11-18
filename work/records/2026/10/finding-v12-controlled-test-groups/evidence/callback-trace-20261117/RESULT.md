# Callback-tracing correction (review 2026-11-17T23-24-47Z P1, M385048)

K, copilot under owner claim E384905, no claim held. Review:
`review-2026-11-17T23-24-47Z.md`. Reproductions: `evidence/review-owner-selections-20261117/`
`callback-probes.py` / `.log` (both ACCEPTED before this correction).

## Defect

`StageCProtections._owned_construction` accepted an `ast.Lambda` as a value with no further proof,
and `map`/`filter` sit in `_COMPOSING_BUILTINS`, so a composing builtin that INVOKES a callback had
only its arguments traced: `list(map(lambda x: json.loads(x), texts))` owned its elements by the
lambda being a lambda. `_owned_module_value` accepted a module-level lambda the same way.

## Correction (test_boundary_inventory.py, StageCProtections only; no product change)

- A lambda as a value answers ITS BODY, traced at the site. Its parameters are what invokes it binds
  (`_owned_lambda_parameter`): a package callee's invocation (as before), `transact`'s connection
  (as before), or -- new -- a composing builtin that invokes the callback over a traced iterable:
  `map(f, xs, ys)` binds the i-th parameter to the i-th iterable, `filter(f, xs)` to `xs`,
  `sorted/min/max(xs, key=f)` and `xs.sort(key=f)` to `xs`. The iterable is traced; its elements are
  what the callback sees. Any other binder fails closed with the existing message.
- A NON-lambda callback handed to those builtins (`map(json.loads, texts)`, `sorted(rows, key=_decode)`,
  a module-level lambda) fails closed: "is a callback handed to map; what it answers is owned by
  nothing this trace follows" -- unless it is a composing builtin or composing package function
  (`map(str, values)`, `map(name_value, bad)`), which composes the traced elements.
- A module-level lambda that reads any of its parameters fails closed (bound only where invoked,
  which the module-level trace does not follow); one that reads none answers its traced body.
- `map`/`filter` stay in `_COMPOSING_BUILTINS` with the justification that the callback is now traced.

Two narrow rules the 28-operand audit then required, each from a concrete failure
(`operand-audit-before-real-rule.txt`):

- `check_no_durable_secret` (contracts.secrets; source not read by the inventory) joins
  `_COMPOSING_PACKAGE`: it walks the document it is handed for a live bearer value, refuses one, and
  returns THAT SAME document, introducing no content. Needed because `sealing.py:_staged` hands
  `copied_manifest` the callback `admits=lambda relative, content: check_no_durable_secret(content.decode(...), what=...)`,
  whose body is now traced.
- A PRIVATE helper that validates its own parameter under its own literal label
  (`workspaces.py:_real`: `boundaries.text(path, "a filesystem root")`, recorded in
  `owning_validators()` as `caller:path`) owns it there, the same rule `owner_of` applies at a public
  door, instead of fanning out to every caller. Without it the `admits` trace ran
  `relative -> _walk -> _open_directory -> _real#path -> every caller of _real -> custody._derived_root
  -> intake._output_root_places -> intake._output_root_identities`, a private function no package
  code calls (its callers are tests; intake.py:4493 records that its calls are gone), and failed there
  -- a fan-out through a shared path canonicaliser, not an ownership gap of the operand.
- `_owned_caller`'s "binds from no caller" message now carries the trail.

## Witnesses

`test_the_owned_input_trace_follows_a_callback_to_what_it_answers`: the reviewer's two universes
(map over a parser lambda, map over an environment lambda) plus map over `json.loads`, map over a
package function, `sorted` by a parser key, a lambda handed on as a value, a local lambda invoked,
a module-level lambda used as a key -- all rejected with the named gap and `owning_validators() == {}`;
callbacks over OWNED elements (`sorted`/`map`/`filter`/`.sort`/`min` over validated rows, `map(str, [value])`
over a validated value) accepted. The prior wrapper, trace, signature-member and composition witnesses
are unchanged and pass.

## Verification (focused; no scans/Docker/B4/full/live)

| run | result | log |
|---|---|---|
| reviewer callback probes | both REJECTED | reviewer-callback-probes-after.log |
| reviewer wrapper probes (M385032) | three REJECTED | reviewer-wrapper-probes-after.log |
| reviewer trace probes (2026-10-31) | three REJECTED, none accepted | reviewer-trace-probes-after.log |
| reviewer renewal probe | refuses (changed after decided) | reviewer-renewal-probe-after.log |
| operand audit: 28 stated operands (23 STAGE_C_INTERNAL + 5 STAGE_C_ADOPTED_ROW_DOORS) + LayoutDelivery's 3 | 31 of 31 traced, 0 failures, 51 s | operand-audit.txt (operand-audit.py) |
| StageCProtections | 25 run, OK, 87.1 s | stage-c-protections.log |
| ten inventory gate classes (StageCProtections, EveryReceivingEntryHasOneOwner, EveryProbeProvesItArrived, EveryStatedOwnerHasAWitness, HelperDeclarationsHaveExactAccounting, StatedRules, StoppedSettlementInventory, LanesHaveCompleteReceivingCoverage, CallerResolvedReadsClosuresAndReplays, DynamicTableReadsStayVisible) | 200 run, OK, 145.2 s (199 + the new witness) | gates.log |

No row of the 28 lost its proof; none was removed or restated. The audit header line names the rule.

## Candidate

`CANDIDATE-SHA256.txt` (same fourteen paths as owner-selections-20261117; only
test_boundary_inventory.py's digest changed). `candidate.diff` against committed 6477a8db.
RESULT.md of owner-selections-20261117 corrected in place (dated): PRODUCT_MODULES placeholder
-> 1396 run OK 38.5 s; "16 run" -> the selected 17 (3 StageCProtections + 9 + 5); intake.py added
to the touched-path summary.

Paths touched this round: v12/python/tests/manager/test_boundary_inventory.py only (plus this
evidence directory, the corrected RESULT.md, PLAN.md, PROGRESS.md). Codexpc's engine fixture modules
untouched. Not addressed here, per the review: the long-fixture-root diagnostic failures
(`review-owner-selections-20261117/regression.log`) are carried into B5.
