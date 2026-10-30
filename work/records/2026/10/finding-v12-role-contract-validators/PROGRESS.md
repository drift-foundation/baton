# Implementer progress — W371294

## claim375825 — the closed descriptor, the /2 registry and its vectors

Authorization: owner W371072 E371253, decomposition E371293. Route
`baton.impl`, returning to `baton.bug`. This is the FIRST finite slice named in
the thread: *"closed development-role-contract/1, implementation-review/2
registry and canonical validators with frozen positive and refusal vectors.
Preserve legacy/default behavior. No qualification grants, deployment or live
execution."*

### Revalidated at claim, read-only, before any edit

    HEAD                            f36bcd75ed22430355efe1b274b8f236cb591f6b
    PROPOSAL.md                     ad0f2171f06f8da9e6e3c2784e50cab91d27f94c4d0727014e4520b00aa0b339  MATCHES the FINDING's pin
    INVENTORY-371102.json           59eac72bce391142a6d05734bb6a910eb88a5f011a87ff534a8e0c2226a66a4c  MATCHES E371253's approval
    ROLE-CONTRACT.proposed.json     1c0809092a5798bbff6e2b0425a5cbdcb363cbdc8d2c72e78ff9d18ad56a557c
    CAPABILITY.synthetic.json       3ac58bc32180c4362cd005664a7de4b8ae00c18081a787de406f04e439226b1d

**The two pinned canonical digests reproduce exactly** under this tree's own
`baton_v12.contracts.digest`, which is the first thing worth knowing because
the whole slice is an identity:

    ROLE-CONTRACT.proposed.json  -> sha256:21b78036947430e3ae073a04fd5237b10a844471207a52cba9ea6186acdffdaf  (proposal says the same)
    CAPABILITY.synthetic.json    -> sha256:4d6a3391facb990ac61090ab5e6b114203b27a27faeca1083458c7bd8f649601  (proposal says the same)

So the approved bounds are implementable as written and I am not reinterpreting
a digest the proposal computed with something else. Canonical bytes of the
descriptor: 1247, well inside the approved 16384 ceiling, and
`contracts.canonical.MAX_DEPTH` is already 8 — the depth the proposal names —
so that bound is the package's and not a second one of mine.

**Every pinned literal exists in this tree with an owner**, checked at the line
rather than taken from the proposal's prose:

| Proposal literal | Current owner |
| --- | --- |
| the task schema `/2` | `verification_context.LEGACY_TASK_SCHEMA` (and the worker's own `TASK_SCHEMA`) |
| the line source profile | `source_profiles.checkout.GIT_LINE_PROFILE` |
| the proposal output name | `templates.CANDIDATE_OUTPUT` |
| findings, logs | `review_driver.FINDINGS_OUTPUT`, `LOGS_OUTPUT` |
| both output types | `worker_manager.schema.OUTPUT_TYPES` |
| name/type/path/required/constraints | `worker_manager.sealing.DECLARED_OUTPUT_MEMBERS` |
| max_bytes/max_entries/allowed_media_types/link_policy/validator_digest | `sealing._ENFORCED + _DECLARED`, and the frozen `outputConstraints` |
| the proposal consumer id | suffix of `integration.driver.CLAIM_NAMESPACE` |
| the review consumer id | suffix of `review_driver.REVIEW_CLAIM_NAMESPACE` |

One thing the proposal does NOT say and the tree does: `verification_context`
already carries a task schema `/3`. That is consistent with the approved bounds
rather than a conflict — the proposal pins `/2` and says a task `/3` workload
"continues its explicit legacy path; this descriptor refuses new `/2`
qualification until its distinct contract is approved" — and a case drives
exactly that refusal against the real `/3` constant.

### Path ownership for this claim

Mine: `src/baton_v12/job_manager/role_contract.py` (new),
`src/baton_v12/job_manager/templates.py`, `tests/manager/test_role_contract.py`
(new). No `job_manager` file is dirty at claim and nothing else is editing
`templates.py`.

**Concurrent foreign work in the same tree, read-only dependencies named:**
another owner (W375444) holds uncommitted `worker_manager/schema.py`,
`tokens.py`, `workspaces.py`, `stopped_settlement.py` and
`tests/manager/test_boundary_inventory.py`; `v12/DESIGN.md` carries the
owner-approved SCH-1a delta uncommitted under the fragility-assessment record.
I depend on `schema.OUTPUT_TYPES` read-only and read that diff: it moves
`SCHEMA_VERSION` 18 to 19 and nothing else, so the constant I consume is
untouched. My own W325695 candidate (eight paths) is a separate reviewed
checkpoint held by `baton.rvpc` and is not edited here.

### Boundaries

No qualification document, capability registry, deployment/derivation/
resolution carrier or admission predicate — those are W371295's
"Compose qualified role contract admission and provenance" and the proposal's
later steps. `/1` and the configured default are preserved. Focused
deterministic tests only; no provider, engine, deployment or live execution. No
Git mutation. `FINDING.md` and `PLAN.md` are the reviewer's.
