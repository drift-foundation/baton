# W339626 input amendment: installed boundary cannot express it

2026-10-21, baton.codxpc, claim344532. Preparation only; awaiting independent review.

## Bound inputs

INPUT-BINDING-344532.json records exact current TASK-344516, DESIGN, install-once
and rapid-start owner-input hashes, together with installed entry/selection and
accepted installer source hashes. Binding SHA256:
90b2fad2102039ace7e77127137a0df9ffc2ddc516ad4dec25f7dd78cf77cb62.
This is an input inventory, not an executable packet or launch selection.
TASK-339833 and sealed v3 remain untouched. No authority-state or secret reads.

## Confirmed refusal seams

Read installed /opt/baton-managed-entry/entry.py and accepted installer source
/tmp/baton-managed-entry-340184/v12/python/tools/managed_entry_install.py.
The latter is evidence of the accepted installer, not a claim to have read its
root-private operator copy.

* Installer register(), lines59-87: destination mkdir refuses the existing
  selection; create() uses O_EXCL. main() offers only install/register/arm,
  prepare-storage and disable. There is no task amendment command.
* Installed entry selection(), lines153-229: exact protected inventory hashes,
  packet/deployment hashes and bound task_document paths exclude task overrides.
  main(), lines264-279 accepts only check/inspect/start plus selection name.
* operational(), lines70-114: storage must be STORAGE/selection and another
  selection cannot share its UID. A differently named registration therefore
  does not reuse provisioned v3 storage/identity through this interface.
* consume(), lines246-260 binds the exact armed selection digest and records
  consumption exclusively. Neither a new task argument nor an amended file is
  admitted by existing start. No start was attempted to demonstrate this.

Installed task.json still contains TASK-339833. Packet fixture hashes still name
old DESIGN and TASK-339833; submission/deployment input-manifest identities also
bind that old task. Updating only the external task file would leave both the
trusted inventory and execution input identities inconsistent. No change to
these installed bytes is authorized. Canonical child closure establishes v3
provisioning/check evidence, not permission to amend or execute it.

## Smallest concrete bootstrap proposal (NOT selected or implemented)

Use one newly bounded host-preparation exception to implement the TASK-344516
outcome in an isolated /tmp source copy, producing an independently reviewed
candidate. This avoids changing the trusted entry merely to make its own
replacement implementable. Expired exception340055 is not relied on.

Proposed authority is limited to source/test/document development for the bound
task, with an exact source baseline inventory captured before edits and final
candidate digest/path inventory. Reuse the current manager/controller owners;
deliver cohesive one-time installation, input-only launch/preflight and supported
failed-start recovery. Do not execute the installation against the host. Test
privileged operations through deterministic boundaries and temporary roots;
exercise the real affected configuration/controller owners. No provider, Docker
launch, account/credential/ACL/sudoers operation, installed-file change, authority
store mutation, consumed receipt reset, Git mutation or automatic integration.

Required verification outcomes remain TASK-344516: two distinct input-only tasks
using unchanged code after simulated installation; full routine startup timing
to substantive work, clearly labelled simulation; missing output parent creation
before consumption; invalid prerequisites refusing before consumption/dispatch;
collision/stale/foreign/incompatible inputs; recovery retaining uncertain or
consumed effects without replay and preserving separation and attribution.
Run focused next-run and authoring-enforcement tests with per-run timeouts;
record measured duration, changed test paths and limitations. No blanket live
proof is inferred. Deliver candidate and evidence through baton.bug for review,
then human integration and separately selected installation/execution as needed.

This is a concrete alternative execution-boundary selection for the reviewer/
owner to decide, not a request to prepare another bespoke v4 packet. If rejected,
the remaining decision is an explicitly selected trusted registration-amendment
capability; the present CLI cannot supply that capability. Do not bypass its
immutable inventory, exclusive UID or consumption checks. Existing v3 remains
preserved pending that decision; it must not run the old task.

## Verification and remaining work

Source inspection and SHA256 input binding only. Hash/read/write interval
0.000245576s; no product tests or launches this turn. Historical parent product
tests0s, author preparation0.954673s, reviewer preflight0.031483s internal/0.2221s
outer, initial failed start0.2174s, v2 failed start0.262026465s process/0.417s
call retained separately; child evidence/accounting remains in W343989 and
W339972. Nested clocks are not added. Reading/planning elapsed is unknown.

Remaining: independent review of this seam and explicit bootstrap-boundary
selection; implementation and deterministic acceptance; independent candidate
review; human integration; any separately selected installation/live acceptance.
There is no runnable amended packet and no product delivery claim.
