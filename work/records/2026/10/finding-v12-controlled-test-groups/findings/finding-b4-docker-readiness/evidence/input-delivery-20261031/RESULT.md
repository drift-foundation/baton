# Input-delivery non-engine slice — W384944 / E384976

Partial correction ready for review; three concrete product cleanup errors remain.
Only `v12/python/tests/manager/test_input_delivery.py` changed. Candidate `af6fa9da8cc47c25b6848fd22491318f2bd019e1924b39c570eb795c2a62854c`; base `c4fdf626322b9296e2211aa5d3a6ee69b616c81deaf6d821a2746a45fcc0480e`. Exact candidate/base/diff retained and shared target matched base before transfer. All1133 snapshot files verified with three allocated overlays; both earlier accepted overlays unchanged. No Docker/image/build/provider execution or shared/product edits.

## Fixture correction and verification

Configure canonical workspace storage in the two frozen-root classes and trust-model fixture before custody removal. Each racing caller opens/closes its own ControlStore on its thread and reads its configured group; no cross-thread connection reuse or check_same_thread bypass. The original first-allocation case now synchronizes the actual mkdir seam instead of obsolete lexists. Every race asserts both callers reached that seam; all prior result assertions remain, including two successful reopen answers. No freeze/refusal/sibling/retry assertions weakened.

Focused six non-engine classes, all32 cases collected/started exactly once each run:
- Baseline:25 pass,4 failures,3 errors;0.320s body/0.564227s wall.
- Fixture correction:29 pass,0 failures,3 errors;0.511s body/0.764674s wall.
- Final with explicit seam-arrival proof:29 pass,0 failures,3 errors;0.550s body/0.764505s wall.
No skips/unaccounted cases/source drift. Total measured command wall 2.093406s.
Every fresh disk root was empty and removed. Exact case ledgers, logs and1133-path
before/after hashes retained. Prepared interpreter per run recorded in log header.

## Confirmed blocker for K/coordinator

The three original cleanup acceptance assertions now reach the intended product call
instead of refusing missing configuration. All fail PermissionError(13), inputs,
at workspaces.py:6904, _removed_through_handles -> os.rmdir(name, dir_fd=parent).
The algorithm admits all directories, then traverses in reverse and thaws only the
current child; its frozen0555 parent has not been thawed when unlinking that child.
Deleting an entry needs write access to its parent. This is a product operation
ordering defect, not permission to pre-thaw the test subject or weaken cleanup.
Function hash 7add4bb67afeb25d0ea541ff6f70e18b1ca6749bb424f47d310d22b923c667ed matches current shared tree at inspection.
Exact source excerpt retained in product-blocker-source.txt; final.log gives three
canonical reproductions. No speculative code patch or product mutation made.

Required coordinated repair: K owns workspaces.py. Preserve complete admission,
retained-handle/no-follow confinement, refusal before effects, ownership/hold rules,
and exact-attempt cleanup; make admitted frozen-home deletion possible in the
correct permission order. Review sibling modes/content, retry, replaced/symlink/mount
and foreign-owned refusal coverage. After an accepted product candidate is allocated,
rerun these32 cases on that stable candidate; current green29 do not waive the three.

## Remaining work

The four historical create-race failures are cleared on this snapshot. The three
cleanup cases remain open with the more specific product cause above. Other engine
identity/custody/ending/adoption cases and pure image/driver fixtures remain unchanged
from preflight. ENGINE-CONTINUATION.md records exact inherited build behavior and
proposed bounded image selection/build and two-class continuation; neither Docker
subclass ran. Earlier accepted integration-worker83/83 and initial-access4/4 proofs
remain intact. Independent review, joined current-tree and final B4 acceptance due.
