# W325695 successor proof packet — preparation only

Prepared by baton.codxpc under E377003/E376998. Independent review and a later exact owner execution selection are required. E376729 is spent; it does not authorize this successor. Do not execute historical preparation-376414 again. No rebuild is proposed.

Read-only verification (no engine):

```sh
python3 -B work/records/2026/10/finding-v12-verifier-descriptor-descendants/preparation-377003/packet.py check
```

Proposed command **only after independent review and later owner selection**:

```sh
python3 -B work/records/2026/10/finding-v12-verifier-descriptor-descendants/preparation-377003/packet.py run --owner-selected --selection-sha256 48bf5fc7a890c652f3a64f817b25279113e7617b85c3e2f59df812fe677753b2
```

Selection SHA256 `48bf5fc7a890c652f3a64f817b25279113e7617b85c3e2f59df812fe677753b2` binds image `sha256:47e733834bb690fd4601e102f81e527a08b6ffe55da8b8cb345f45edfcb1517e`, diagnostic UID/GID65532:65532, unchanged payload/layout and the successor runner digest. Fresh proof identity `w325695-proof-377003`; ENGINE-RECEIPT must not exist. Check verifies packet pins and all42 preserved input hashes, successful historical build identity, unchanged diagnostic parameters, selection bindings and unused receipt without invoking Docker. Runner creates that receipt exclusively and fsyncs intent/identity before effects. Interrupted or failed receipts stay spent; no retry, receipt deletion or arbitrary cleanup is selected.

One proposed no-provider diagnostic: 120s total including40s cleanup reserve;20s receipt window; bounded per-call timeouts;2GiB/1CPU/64PIDs;80MiB actual diagnostic tmpfs; no network, credential mounts or host binds; pull never. LAYOUT.json retains the original100663296-byte general total including the legacy decoy; this diagnostic vector omits that16MiB decoy exactly as the accepted original did. Diagnostic UID/GID is explicitly selected, not evidence of production group provisioning. Original vector and kernel payload are unchanged. No live latency, full-workload fit, installed-manager execution or kernel acceptance follows from these deterministic tests.

Changed harness behavior: exact closed absence at BOTH preflight and cleanup; status1 with empty/empty-array stdout and one complete supported error. Known diagnostic words may vary in case, identifiers cannot. Status0 empty array, foreign/prefix/suffix/mixed responses and malformed observations remain uncertain. Present inspection requires full ID and exact queried Name or ID; acquisition additionally requires exact proof Name, image, label, UID/GID and any saved ID. Occupied preflight objects are never acquired or removed. Lost create plus later absence stays uncertain; an independently observed owned object can be cleaned by full ID but cannot turn a failed execution into success. Remove failure still leads to independent final observation within the reserve.

Durable diagnostics contain status, exact known reference, phase, closed classification/reason, stream byte lengths and SHA256; arbitrary engine/child text is never copied to the receipt. Supported response parsing is limited to64KiB; subprocess capture itself retains the original in-memory capture behavior. This is bounded safe DURABLE evidence, not a streaming memory-limit claim. Successful payload receipt persists only fixed pass fields and validated capacity/PID metrics, omitting arbitrary extras. Original invocation streams remain unknown; no claim that the spent run saw an absence rather than socket denial is made. Original parser required EMPTY stdout, not nonempty.

Provenance: PROVENANCE.json includes original32 pinned members, build and engine receipts, historical selection and prior classifier preparation. LAYOUT.json and kernel-payload.py are exact copies; product source and both prior preparations are unchanged. The earlier accepted source checkpoint ef703336 remains valid history; current downstream edits are intentionally excluded by the frozen build inputs. No runtime image reinspection was performed this claim.

Verification: `python3 -B -m unittest discover -s work/records/2026/10/finding-v12-verifier-descriptor-descendants/preparation-377003 -p 'test_*.py' -v` exercises the actual successor packet entry and Proof with deterministic engine/clock boundaries. Test copies live only in disposable temporary directories; the retained ENGINE-RECEIPT stays absent. See focused.log/VERIFICATION.json. Required positive/adversarial/ownership/lost-create/removal/deadline cases are in test_successor.py plus preserved runner scenarios and test_packet.py. Kernel mount/descendant/ENOSPC outcomes remain unproved until a separately selected real probe, followed by independent review. W321776 acceptance gate remains unchanged.
