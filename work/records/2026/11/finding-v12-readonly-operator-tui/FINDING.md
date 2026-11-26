# Read-only operator TUI — W386308

2026-11-25: Slawomir requested queueing a simple way to see what is happening and asked whether to use a TUI or a web page. The proposed first delivery is a terminal interface for the existing local monitoring workflow. DESIGN OBS-2 already specifies a shared published snapshot and read model for a future TUI. W167896 delivered the earlier read-only viewer; W385263 added human-facing headlines.

2026-11-25 owner decision: Slawomir selected the single-instance read-only TUI as the first operator interface for this Work. The first slice is the compact Job list, selected Job detail, and in-place refresh described in PLAN.

2026-11-26, preparation by K (`baton.prompt`): a bounded contract for the first slice is proposed in IMPLEMENTATION-CONTRACT-PROPOSED-2026-11-26.md. Observed while preparing: main is now `76b2f2b2`, which changes worker source, so the qualified worker images match source only up to `67fd60f8`; the retained A1 extract renders through `job_view` as DECISION NEEDED with `job-w385263-a1/implementation: model-attribution-missing; owner action needed`. Two owner questions are open and recorded in the contract: the launch baseline, and list order. No baseline is pinned and no packet exists.

## Owner baseline selection for M386340

Option C selected: pin the TUI field Job to the verified checkpoint after W386299 is imported on top of the MANUAL Jobs checkpoint. Qualify the two worker images against that combined source before native dispatch. List ordering remains a separate UX decision.

## Owner list-order selection for M386340

Keep the list in snapshot order and preserve the selected Job by identity across refreshes. A transition to DECISION NEEDED does not promote a row or change the selection. Pressing n jumps to the next Job needing an operator decision.

2026-11-26, owner decisions (terminal instruction to K): launch from the verified post-W386299 checkpoint; keep snapshot order in the Job list; `n` jumps to the next DECISION NEEDED Job. Recorded in IMPLEMENTATION-CONTRACT-2026-11-26-r1.md, which supersedes the proposed contract. Pseudo-terminal check by K: on the host, with an empty environment and `/dev/null` streams, a test can allocate its own pseudo-terminal and drive a curses program to a clean exit (evidence/pty-probe-K/). Whether the worker container allows the same was not run and is listed in the contract as a real-container check.

2026-11-26, review disposition recorded by K. The first-slice candidate (base `7961f8bd`, combined patch `f0cc2bd83ac98ddb8b7918f5d5bae1cfce13e8156363bc7bda86730ff9e0c4c6`, eight paths) was implemented by `baton.claude` by host workflow and reviewed by Codex in the owner-attached session: changes requested in review-2026-11-26T03-55-01Z.md (60×8 boundary in the real curses path; tail of a tall selected phase unreachable), both corrected by delta `00d4edcf…`, accepted in review-2026-11-26T04-05-35Z.md with no correction required. The reviewer states horizontal truncation is intentional under the contract and that packaged entry-point verification remains open. The reviews carry no ledger transition; the Work is still queued on the review route.
