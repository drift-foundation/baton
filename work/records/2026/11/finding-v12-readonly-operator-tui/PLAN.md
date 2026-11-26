# First field slice

Queued for owner selection after W386299 dispatch. Proposed scope is one instance, a compact refresh-in-place list of Jobs, headlines and reasons, with keyboard selection opening phase details and recorded activity. Keep selection stable across refresh, show stale or missing observations explicitly, and leave the Job running when the operator quits. Reuse the shared interpretation used by status and monitor. Verify with a multi-Job snapshot, a transition to DECISION NEEDED, stale evidence, and navigation/exit. Recheck overlap with W386295 and W386299 before assignment.

The owner approved the TUI choice and first-slice scope. Next milestone after W386299 dispatch: check current file ownership and prepare the bounded field assignment.

2026-11-26 (K, preparation only): contract proposed in IMPLEMENTATION-CONTRACT-PROPOSED-2026-11-26.md, with example screens from the retained A1 case, 16 deterministic cases, likely files and the overlap with W386299. Blockers before a launch packet: the owner's baseline choice (it decides whether worker images must be rebuilt), the list-order answer, the OBS-2 text in DESIGN, and whether worker containers provide a pseudo-terminal for the exit tests. Next milestone: owner answers, then the launch packet on the chosen baseline. W386308 is unclaimed.

Baseline sequencing selected: wait for the verified W386299 import before pinning the TUI launch source. The exact commit and image identities are pending.

List order settled: keep snapshot order and selection by Job identity, with n for the next DECISION NEEDED Job. Include a refresh where another Job enters that state while the operator reads the selected row.

2026-11-26 (K, preparation only): contract revision 1 written with the owner's baseline and list-order decisions. Remaining before a launch packet: W386299 imported and checkpointed; both worker images rebuilt and requalified from that commit, with a pseudo-terminal and curses inventory assertion; OBS-2 text in DESIGN. W386308 is unclaimed.

Option C baseline is now 7961f8bd4f5aae1209c72f796acb693d5ba65b76: verified W386299 joined onto the MANUAL checkpoint. Use it to prepare both image qualifications and the pseudo-terminal, curses and terminfo checks for W386308.

2026-11-26 (K, preparation only): baseline set by the owner to `7961f8bd4f5aae1209c72f796acb693d5ba65b76`. Image qualification packet prepared at `evidence/image-qualification-packet/`, payload `b842f002d3b4b2e02b0493698ce6f37096f54e956cfdd56c897ef91d1823fff9`: rebuild of both worker images from that commit, the earlier identity gates, and a new terminal gate under the worker posture and identity (curses import, terminfo, pseudo-terminal and slave, one clean curses session). 19 of 19 fake-engine scenarios pass. Next: review by someone other than K, the owner's selection of the image phase, then the TUI launch packet on the resulting image digests. W386308 is unclaimed.

2026-11-26, implementation (baton.claude, claim E386352): the first slice is implemented by host workflow on baseline `7961f8bd`. Candidate, case-to-test map, verification and open choices: `evidence/candidate-386352/REPORT.md`; patch SHA-256 `92d60ea9b4db2d07ea6d3ba47a6b7bfd183c74aef462d7c86b0d392057738c4a`. Next milestone: independent review of that exact patch, then the owner's Git checkpoint. Suggested commit message: "Add a read-only terminal interface for watching v12 Jobs". The native dispatch packet for this contract stays preparation only.

2026-11-26 (baton.claude, claim E386357): review 2026-11-26T03-55-01Z requested two corrections; both are in delta `00d4edcf4ad5728e232fee1626d97ba027d59ffddf91e5877b72b3c8a2e77e11` (`evidence/correction-386357/REPORT.md`). Next milestone: re-review of that delta, then the owner's checkpoint of base `7961f8bd` plus both patches (eight paths).

## 2026-11-26 — accepted; owner checkpoint pending (K)

Accepted by independent review (FINDING, same date). Pending human Git checkpoint of eight paths, with the reviewed `DESIGN.md` hunk staged apart from unrelated working-tree edits: commands and a read-only staged-bytes check are in `evidence/checkpoint-386358/CHECKPOINT.md`. Commit message: "Add a read-only terminal interface for watching v12 Jobs". Open after the checkpoint: the first packaged build and run of `baton-v12-stack tui` (command in the same file), then recording the commit identity here.
