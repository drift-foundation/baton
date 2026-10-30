# Joined operator preparation and remaining bootstrap decision

Custodian is already selected: owner347695, accepted child347718. Do not select custody again. Amendment345734 digest8a46facba604ad3c5e2c1c1b7d76eaf91b84ea1e2aad5e904f296c301a7c7394 is independently accepted; its task permits conditional use of retained three buffers. Original345625 remains unconsumed, but does not automatically select the amended bytes or override the later lease-before-launch boundary.

One helper is ready. Read-only mode:

```sh
python3 -B /home/sl/src/baton/work/records/2026/10/finding-v12-serving-token-renewal/prepare-operator-347720.py
```

After explicit selection of preparation for this exact amendment (no launch), the same helper performs stage, bootstrap and bind once, captures each status/stdout/stderr/duration and generated identities, then stops:

```sh
python3 -B /home/sl/src/baton/work/records/2026/10/finding-v12-serving-token-renewal/prepare-operator-347720.py --prepare-authorized
```

SHA256ff360808c78e3742297be354c42b4698a9d6c76d5957a9c05ccaee1925aad009. Run as sl, never sudo. Exact root serving-renewal-w333485-339444 must be absent; receipts operator-preparation-347720 must not exist. Any failure preserves state; no retry/cleanup. This helper has no launch command. Preparation selection is currently absent; do not execute its mutating mode yet. Preparing this unchanged host would still leave900s effective permission and may be wasteful before the correction below, so defer mutation until its inputs are settled.

## Concrete bootstrap boundary requiring owner disposition

Current host PreparedGovernance.reserve in worker_manager/workspaces.py:3972 omits seconds; tokens.acquire defaults900. Accepted amendment changes the worker task only. A worker implementing future host policy cannot retroactively fix the host grant governing its own first invocation. There is no verified operator-duration override; changing the constant or injecting a monkey patch is unreviewed product implementation. Existing authoring commands still use that host. Running them before correcting it contradicts the explicit347695/347548 lease-before-launch condition. General AGENTS v11-preparation/v12-execution policy forbids host product implementation absent an explicit bounded exception.

Recommended concrete disposition: authorize a one-time bootstrap exception for the configured implementer to produce the smallest prospective execution-envelope permission correction in an isolated candidate on the host, with deterministic focused verification and independent reviewer verification under that same exception. Outcome: derive bounded initial permission from populated execution/cleanup envelope or actual eligible renewal, no arbitrary replacement constant, no Job-limit reset, cancellation/expiry/no revival/restart/unknown-hold safety. Evidence must exercise real acquisition/serving boundary under controlled clock through the selected3600 interval and cleanup. Necessary files remain implementer-selected; coordinate actual overlap. No live provider/engine execution, deployment/install change, existing-token mutation or Git mutation under this proposed exception. It expires at independent acceptance of this bootstrap correction. Then bind exact accepted host bytes into one immutable successor and request only its concrete operator preparation/start selection.

This exception is a proposal, not granted authority. Alternative owner-supplied already accepted host capability can satisfy the same boundary. Do not merely select another900s run to hope it finishes. W341357 remains blocked on this accepted permission result. Current prepared packet, historical partials and all evidence remain immutable.
