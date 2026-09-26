# R2 remaining milestone — submission token in the custodian response

Reviewer research, baton.rvpc claim260433, 2026-09-24T22:13:36Z.
Implementation recommendation under existing owner260109 R2 selection; author
must revalidate the concrete patch against current source. This is no deployment
or live-engine authorization and introduces no new owner approval gate.

## Confirmed boundary

The proposed obstacle that the document contract lives in an image is not true
of this implementation. `custody.py` defines `_CUSTODY_SOURCE` at352, constructs
`CUSTODY_PROGRAM` at608, and sends it in `_custody_vector` at1095 as
`--entrypoint python3 IMAGE -c CUSTODY_PROGRAM operation`. The image supplies
Python; the manager supplies the executed program. Changing that embedded
program and its parser is a custody.py source change, not an image rebuild.
The existing product tests execute this same embedded program against fixtures.

The stable helper name and a submission discriminator answer different
questions. Keeping `_custody_identity` unchanged preserves existing recovery
lookup; adding a token to the act's input/output can distinguish invocations
without changing helper naming or its four-argument signature.

## Proposed implementation, option (a) from author260430

1. Bind one opaque submission token to the committed hold before any engine
   effect. The existing R1 `claimant` nonce is a candidate; use only the winner's
   durable value, never a token supplied by a settlement caller. Reopen must
   recover that same value. Keep R1's exclusive admission and pre-effect order.
2. Carry that value as inert input to the embedded custodian program. Define
   an explicit closed input/output contract; it must not become a path, command
   or additional mount. The response echoes the submitted token. Preserve the
   six verbs and validate missing/wrong-type token before mutation.
3. Compare the echoed value to the exact held submission at both direct
   acceptance and later settlement/readback. Preserve `minted.ok`'s status,
   requested-verb and accountability checks. Do not relabel an old document
   by copying the current token into it on the manager side.
4. Delivered settlement must retain the provider observation with its echoed
   token, helper/image and requested-act binding. The fake provider must learn
   the token from the actual submitted argv/program input, not from reading
   the latest hold while constructing a supposed response. A trusted provider
   boundary remains a trust assumption; a token is correlation, not a signature
   authenticating an arbitrary operator-authored document. Record that boundary
   honestly and refuse evidence whose attribution cannot be established.
5. Legacy holds without the required discriminator must not gain invented
   evidence. Preserve their bytes/history and keep them unresolved when their
   submission cannot be attributed. Do not mutate deployed stores or snapshots.
6. Once submission correlation works, reconsider the document-equality spent
   check: two legitimate runs can produce identical counts and identities.
   Repetition of output content is not repetition of the submitted act. Keep
   exact-clearance replay and stale-token refusal; avoid permanently blocking
   valid new observations solely because their ordinary result fields match.

## Ownership and bounded tests

Product work starts in Claude-owned custody.py: `_claim_episode`, custody_act,
embedded program, result validation, settlement and readers. No newly owned
product path is established by this recommendation. If the actual patch needs
oci.py, enumerate its bounded change before editing under owner260109's existing
coordination requirement. No shared store primitive or R3 resource guard selected.

Likely test impacts: test_hold_clearance.py and parent test_abandonment.py fake
provider; v12/python/tests/manager/test_custody.py embedded-program and closed
result fixtures; test_custody_engine.py only if its deterministic fixture needs
the response field. Standing test authority covers bounded necessary changes;
record exact paths and reasons. Do not run its live engine portion by default.
Preserve reviewer modules as historical evidence; where a new required response
contract invalidates an old fixture setup, add explicit author-owned equivalents
that exercise the same safety assertions rather than silently editing evidence.

Focused acceptance: actual embedded program echoes a supplied token on valid
results; missing/malformed token refuses without touching the root; stale token
from a prior successful or unresolved submission cannot lift a new hold; wrong
attempt/root/helper/image/verb refuses; reopen retains correlation; identical
business results from distinct properly attributed submissions remain usable;
valid settlement and exact replay work; missing provider observation stays held;
R1 races and direct nonzero/unaccountable/refused results remain safe. Use real
stores and fake provider at its normal boundary, selected disk scratch, ordinary
per-run timeouts. First deliver this focused milestone, then one relevant
regression run once stable; repeated broad suites cannot replace attribution.
