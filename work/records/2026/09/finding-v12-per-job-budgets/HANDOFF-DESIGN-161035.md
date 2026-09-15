# Planning handoff — independent design review only

Owner-selected architecture: FINDING2026-09-13T13:47:40Z / M161029.
Prepared by baton.codex under claim161035 at2026-09-13T13:58:24Z.

Read the current FINDING/PLAN, unchanged implementer PROGRESS, prior independent
review-2026-09-13T12-21-26Z.md, and the complete new
MANAGED-INTEGRATION-DESIGN-2026-09-13.md. Research source hashes and candidate
comparison are in research-161035.json. The old RECOVERY-SCOPE-DISPOSITION is
explicitly superseded; do not review or implement it as the current remedy.

Task for baton.impl: independently review the proposed architecture, exact paths,
authority and tests. **Do not implement.** The owner ruling selects managed Docker
and relocation through ordinary input/output; it explicitly does not grant a
blanket implementation path set. The new design is authored by the reviewer and
must not be self-approved. Append a separate dated design-review record and return
to baton.feat with concrete accepted points, defects and necessary scope changes.

Priorities: (1) actual preparation Work/offer/claim/attempt mapping against
activate_assignment, with subordinate execution charged to the parent allocation;
(2) portable bounded input and collected result without shared coordinator paths;
(3) derived apply eligibility and target-owner live-grant/stop/CAS ordering;
(4) failed-phase ending that releases only the correct capacity without success,
retry or target repair; (5) exact first-slice schema/source/test authority. Check
the proposal's explicit open gates, especially the placement/publication boundary.

No runtime test is requested for a read-only design review. If a focused
deterministic probe is necessary to decide a concrete public API question, record
that question and its actual cost; no repeated broad suite, live model or image
installation. Current author246runs2530.5844189850177s plus4unknown activities;
reviewer147.73142127899519s. No reset or W103525 transfer. Candidate29paths unchanged;
W71879 provenance and existing-test authority stay in the prior packet. No
completion/import approval or dependent implementation is implied.
