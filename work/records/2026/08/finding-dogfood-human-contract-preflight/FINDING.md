# Hold the human contract before dogfood side effects

Work: W51476
Follow-up of: W39358
Discovered by: W39364 pre-run invocation

## Observed

`tools/dogfood_operator.py::preflight` does not accept or validate
`human_contract`. A locator in the broader `artifactRef` spelling
`baton:<path>` passed the caller's preparation, then
`contracts.manifest.check_input_pair` refused it because the shared canonical
URI grammar requires the narrower `scheme://authority...` form.

That refusal arrived only after source staging, claim submission, assignment
activation and credential-slot materialization. No runtime or provider turn
started, but the exact no-side-effect interval `preflight` promises was open.

Evidence:
`work/records/2026/08/finding-v12-first-useful-dogfood-task/findings/finding-first-useful-task-acceptance/acceptance-2026-08-30T22-49Z.md`.

## Confirmed defect

The input composer copies `human_contract` into the manifest and relies on the
later whole-manifest validator. Preflight validates policies, bindings,
network, route and task, but not this explicit grant. Two locator grammars are
therefore applied at two lifecycle times, and the later one owns the real
contract.

## Required boundary

- Add `human_contract` to preflight and hold its exact closed artifact shape,
  sizes/digest/text values and locator before any staging or authority act.
- Reuse `contracts.manifest.check_uri` for the locator; do not create a second
  URI grammar.
- Reuse one pure human-contract hold at preflight and manifest composition so
  the two call sites cannot drift.
- Catch only typed contract refusals from grammar owners; unexpected owner
  faults remain implementation defects.
- Add an arc-level regression proving a malformed locator causes zero source,
  claim, activation, credential, runtime or provider acts, plus focused shape
  and owner-failure cases.

This is operator hardening and does not authorize another provider turn.

## Confirmed clarification — 2026-08-31

The earlier `scheme://authority...` description is superseded as a complete
description of the canonical locator grammar. The shared owner admits that
form for non-file schemes and separately admits `file:///absolute-path` with
no host. The operative decision was always to reuse
`contracts.manifest.check_uri`; no local grammar depends on the shorthand.
