# Plan — Roll out the schema-28 managed authority

1. [blocked] Wait for W2845 and W4996 to close after their exact acceptance
   and independent review. Confirm no Handler remains active.
2. [pending] Freeze the tree. Audit tracked and untracked paths against their
   owning Work, run `git diff --check`, `just test-v11`, the complete
   `tools/codex-event-bridge` suite, and the complete `v12` suite.
3. [pending; Slawomir] Stage the audited batch, review the staged diff, and
   commit it. Record the commit ID used by every later path.
4. [pending] Publish one immutable v11 artifact under
   `/home/sl/opt/baton/v11/<commit>` and verify its digest and executable.
5. [pending] Initialize a fresh `/home/sl/baton-v11.<commit>`, prepare exact
   generation-1 configuration with `config`, `recover`, and `dispatch` on
   `baton.slaw`, render lifecycle manifest v2, and activate the authority.
6. [pending] Generate and audit the combined execution policy, run W2845's
   corrected live matrix against the immutable candidate, and install the
   policy only after the matrix and credential cleanup pass.
7. [pending] Generate and review a deterministic recreation script for the
   still-open W28 v12 campaign subtree. Recreate its canonical bindings,
   containment and dependency edges in the new authority and compare the
   resulting tree with the frozen source authority.
8. [pending] With no old Handler active, stop the old stack, atomically repoint
   `/home/sl/baton-v11`, start the new stack, and verify every declared service
   healthy. Roll back the symlink on any failure; delete nothing.
9. [pending] Execute the live recovery, drain/paused/resume, claim-refusal,
   `stop-drained`, dependency-graph, TUI, and agent-runtime acceptance matrix.
10. [pending] Close W6175, W4303 and W4615 in the retired authority with the
    exact rollout evidence. Preserve that authority and continue only the
    reconstructed unfinished Work in the new one.
