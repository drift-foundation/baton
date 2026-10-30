# Implementer progress — W371295

## claim376473 — returned without starting; the accepted input mapped

Authorization: owner W371072 E371253. Blocker W371294 is CLOSED, so its
contract is the accepted input. Read at claim: this assignment and all four
thread messages (371295, 371454, 374197, 375563), none of which changes the
approved capability/1, deployment/3, derivation/1 or resolution/2 shapes.

**I did not start the source.** This slice is five carriers plus the
pre-effect predicate, the replay and dispatch fences and the common Job
projection — one connected admission contract whose whole point is that the
pieces agree. I did not have the room in this claim to build and verify that,
and a fragment of it would be the shape this team's reviews have repeatedly
and correctly refused. Nothing is half-wired: the tree is unchanged by this
claim.

### What the next claim starts from, as the author of the accepted input

`baton_v12.job_manager.role_contract` (accepted under W371294) already
provides, and should be consumed rather than re-derived:

* `CONTRACT_SCHEMA`, the closed member/constraint/role vocabularies, and
  `check_role_contract` / `role_contract_of_bytes` — the pure validator, with
  duplicate-key refusal and the 16 KiB encoded ceiling;
* `contract_digest` — canonical, over the whole document, with NO embedded
  digest member, so a resolution pins the contract by computing rather than
  by copying a claim;
* `baseline_document()` — a fresh detached copy per call, and
  `BASELINE_DIGEST` `sha256:21b78036…acdffdaf`, asserted at import;
* `TEMPLATE_CONTRACTS` / `contract_for(version)` — the binding table, where
  `None` is the explicitly legacy answer for `/1`;
* and `templates.IMPLEMENTATION_REVIEW_2`, registered and derived from `/1`
  so the two revisions differ only in their version.

The capability document is NOT implemented — deliberately, and a case in
`tests/job_manager/test_role_contract.py` asserts the descriptor mentions no
capability, adapter, image, profile or qualification digest at all. Its
approved shape and synthetic vector are in `PROPOSAL.md`
(`ad0f2171…`), whose digest reproduces, with
`CAPABILITY.synthetic.json` canonicalizing to
`sha256:4d6a3391facb990ac61090ab5e6b114203b27a27faeca1083458c7bd8f649601` —
verified under this tree's own `contracts.digest` during W371294.

### Coordination facts read this claim

W371073's revised plan (bootstrap/2, instance/2, launch/5) is **awaiting owner
selection** and changes none of the approved shapes; overlap is to be
coordinated only after selection. W371396's admission/timing plan is accepted
but awaiting disposition; one version meaning is to be agreed after owner
selection. W375517 waits canonically on this Work's accepted provenance and
schema, and this Work retains first Job-schema ownership.

Verification spending this claim: read-only reading of the assignment and
thread. No run, because nothing was changed. No provider, engine, deployment
or live execution; no Git mutation.
