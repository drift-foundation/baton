# Register check_input_pair receiver ownership

Date: 2026-08-27
Parent discovery: W6636, `work/records/2026/08/finding-v12-local-oci-lifecycle-composition/`
Follow-up to: W19784, `work/records/2026/08/finding-v12-assignment-identity-delivery/`

## Finding

**Observed:** The canonical boundary inventory does not register receiver ownership for the three parameters of `check_input_pair` in `v12/python/src/baton_v12/contracts/manifest.py`: `input_manifest`, `assignment_manifest`, and `what`.

**Confirmed:** The omission adds seven full-tree boundary-inventory failures beyond the accepted six-failure baseline recorded by the W6636 diagnostic review. W6636's approver authorized a correction follow-up to W19784.

**Confirmed boundary:** This Work registers the three receiving parameters and their witnesses in `v12/python/tests/manager/test_boundary_inventory.py`. It does not alter `check_input_pair` behavior, assignment identity, manifest semantics, or the accepted unrelated baseline.

**Proposed:** Revalidate the current canonical inventory and baseline first, then make the smallest additive ownership registration consistent with neighboring manifest receivers.

## Acceptance

- All three `check_input_pair` parameters have explicit canonical receiver-owner entries and witnesses.
- The focused inventory check no longer reports these omissions.
- The full-tree inventory returns to the revalidated accepted baseline without weakening assertions or masking unrelated failures.
- No runtime or manifest behavior changes.

## Open

- The accepted six-failure baseline must be revalidated at implementation time because independently queued work may have reduced it.
