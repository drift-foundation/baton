# Ship the execution-policy generator in the v11 distribution

## Observed — 2026-08-20

During the schema-26 deployment of commit `d46ab1e`, the shipped
`conf/codex-event-bridge.template.json` instructed the operator to generate the
required exact Baton rules with
`tools/codex-event-bridge/src/exec_policy.mjs`. The deployed distribution did
not contain that source module or an equivalent installed command. It carried
only a subset of the bridge library under `lib/codex-event-bridge/`.

The committed source checkout contains the reviewed generator, so this rollout
can use that exact commit as an explicit stopgap. A standalone deployment,
however, cannot follow its own instructions and would force the operator to
hand-author security-sensitive rules.

## Acceptance boundary

- The immutable distribution contains an installed, documented way to emit
  exact `claim`, `say`, `pass`, and `close` rules for a named executable,
  config, and participant.
- The shipped dispatcher template references only installed resources.
- Generated output is byte-identical to the reviewed source helper and remains
  covered by the exact/broad/extra policy regressions.
- No schema or authority change is introduced.

## Deployment stopgap

For release `d46ab1e`, invoke the reviewed helper from the source checkout at
the same commit, install its output as the deployment-owned policy file, and
retain the W415 preflight plus live boundary verification. This is not the
packaging fix.

## Reviewer revalidation — 2026-08-20

**Observed.** The immutable `d46ab1e` release contains exactly these shared
bridge modules under `lib/codex-event-bridge/src/`:
`codex_baton_bridge.mjs`, `config.mjs`, `role_instructions.mjs`,
`runtime_publisher.mjs`, and `send_event.mjs`. It does not contain
`exec_policy.mjs`. Its `conf/codex-event-bridge.template.json` is byte-equal to
the source template (SHA-256
`1931c5cda2e6df6269ad72457c46e3e5f635e4275f2c6ac40f0a5a2ff1bb0576`)
and tells the operator to use the checkout-only
`tools/codex-event-bridge/src/exec_policy.mjs` path.

**Confirmed.** `tools/deploy_work.py:_stage_bridge()` copies only the modules
listed in `SOURCE_SHARED_GATE`; `exec_policy.mjs` is absent from that tuple.
The release therefore behaves exactly as its manifest predicts. Running the
source helper's `rulesFor()` for `/opt/baton/bin/baton`,
`/srv/baton/baton.json`, and `baton.codex` emits four newline-separated exact
allow rules, in the approved order `claim`, `say`, `pass`, `close`.

**Confirmed.** The installed `bin/` surface is separately pinned by
`tests/work/test_deploy_v11.py:test_the_deployed_layout_is_the_ruled_release_shape`
to exactly `baton` and `acp-baton-bridge`. This packaging follow-up does not
need to reopen that product-entry-point decision: the release already has the
private `lib/codex-event-bridge/src/` location for shared Node modules.

**Proposed patch boundary.** Preserve `rulesFor()`, `auditRules()`, and the
exact four-verb capability unchanged. Make `exec_policy.mjs` usable directly
as a strict stdout-only generator when Node executes it, accepting one
absolute Baton executable, one absolute accepted config, and one participant.
It must print only the four rules plus a final newline; it must not create,
overwrite, or install the deployment-owned policy file. Add that exact module
to `SOURCE_SHARED_GATE`, and update the dispatcher template to show an
invocation of the installed
`<release>/lib/codex-event-bridge/src/exec_policy.mjs` rather than any checkout
path. Keeping the CLI in the reviewed module makes the deployed bytes and the
imported preflight implementation one artifact instead of introducing a
second generator that could drift.

**Proposed strict CLI boundary.** Prefer explicit operands such as
`binary=/absolute/...`, `config=/absolute/...`, and
`participant=team.member`; refuse missing, duplicate, or unknown operands and
reuse `rulesFor()` validation for empty or relative paths. Errors go to stderr
with a nonzero status. The module's existing import behavior remains
side-effect-free, so bridge startup and the current test fixtures do not emit
policy text.

**Required regressions.** Extend the actual deployer lane, not a synthetic
copy list:

- assert the deployed module exists and is byte-equal to the reviewed source;
- execute it from the immutable target with no checkout `PYTHONPATH`, and
  compare stdout byte-for-byte with the source helper's approved four lines;
- assert the shipped template contains the installed `lib/` path and no
  `tools/codex-event-bridge/src/exec_policy.mjs` checkout locator;
- import the deployed artifact and retain the exact-only success,
  exact-plus-broad refusal, broad-only refusal, same-participant extra-verb
  refusal, and other-participant independence checks already owned by W415;
- cover missing/duplicate/unknown operands, relative binary/config, and the
  no-output-on-import boundary.

**Focused verification.** Run the W415 Node regression containing the
exact/broad/extra matrix, the v11 deployer tests, the W163 standalone-release
tests (to preserve the two-entry product and offline bridge), and
`git diff --check`. No schema, authority, config grammar, or runtime dispatch
change belongs in this Work.

**Baseline verification.**
`npm test -- --test-name-pattern=W415` in `tools/codex-event-bridge` passes all
22 selected tests on the pre-patch tree, confirming that the source helper's
exact/broad/extra behavior is green while the missing deployed artifact
remains the isolated defect.

**Open.** Operand spelling is an implementation-interface choice, not a
security ruling. If the implementer finds that a separate installed wrapper
is materially simpler, stop and obtain an explicit supersession of the pinned
two-entry `bin/` distribution boundary before adding a third executable.

## Implementer revalidation and interface resolution — 2026-08-20

**Confirmed against the current tree.** Every recorded claim still holds:
`SOURCE_SHARED_GATE` listed five modules and not `exec_policy.mjs`; the
shipped template named the checkout-only
`tools/codex-event-bridge/src/exec_policy.mjs`; the baseline
`npm test -- --test-name-pattern=W415` passed 22/22 before any change. No
supersession was needed.

**Resolved (the recorded Open item).** The generator's operand spelling is
`binary=`, `config=`, `participant=`, given in any order, all three required,
and nothing else accepted. Unknown, repeated, and value-less operands are
refused by name; empty and relative paths are refused by `rulesFor()`'s
existing validation rather than by a second copy of it. Refusals print the
message and the usage on stderr, exit nonzero, and emit NOTHING on stdout — a
truncated rules file is a broken boundary, not a warning.

**Resolved (no third entry point).** A separate installed wrapper was not
materially simpler, so the pinned two-entry `bin/` distribution boundary
needed no supersession. The CLI lives in the reviewed module, which keeps the
bytes that emit the rules and the bytes that audit them one artifact.

**Confirmed unchanged.** `RULED_VERBS`, `rulesFor()`, `auditRules()`,
`parseRules()`, `auditRulesFile()`, and `assertPolicyProvisioned()` are
byte-for-byte as reviewed; the direct invocation is additive and the module
stays side-effect-free on import, which the dispatcher's startup preflight
depends on.

## Review round 2 — accepted corrections, 2026-08-21

`review-2026-08-21T04-26-31Z.md` requested three changes. All three were
confirmed against the current tree and are now recorded rulings.

**P1 (confirmed defect in the shipped instruction).**
`EventBridge.start()` iterates EVERY `targets.*.identity` and calls
`assertPolicyProvisioned()` for each against the single nominated
`execPolicyFile` (`tools/codex-event-bridge/src/event_bridge.mjs:147-155`),
and the shipped template configures both `baton.codex` and `baton.tuner`. The
round-1 instruction showed one invocation redirected with `>`, so following it
once leaves the other identity with no rules and startup refuses; running it
twice truncates the first identity's rules.

**Ruled.** The generator interface stays SINGULAR — one executable, one
accepted config, one participant — and the instruction carries the
composition: run it once per configured participant, APPEND each run into a
staged file, and install that staged file. Staging is part of the ruling, not
style: a redirect onto the live nominated file truncates it before the
generator has validated an operand, which turns a typo into a dispatcher that
will not start.

**P2 (confirmed).** The round-1 overwrite regression asserted only that a
file of the same NAME survived, which an in-place rewrite would also satisfy.
The creates-and-overwrites-nothing boundary is asserted on the BYTES.

**P2 (confirmed, and this supersedes the round-1 phrasing).** Round 1
described the deployed module as "the same artifact the dispatcher imports".
It is not. `conf/infra.example.json` runs the dispatcher from
`<baton source>/tools/codex-event-bridge/bin/codex-event-bridge`, and the v11
distribution ships no `bin/codex-event-bridge`. What the release carries is a
BYTE-EQUAL IMMUTABLE COPY of the reviewed source helper, and the deployer's
byte-parity regression is the whole guarantee that the generator an operator
runs and the auditor a dispatcher runs are one implementation. This Work does
not co-deploy the generic dispatcher and must not imply that it does.
