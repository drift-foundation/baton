# Plan

Queued as a cross-cutting v11 correction discovered by the first human trial.

1. Inventory every canonical `discussion` schema, projection, transition,
   JSON, CLI, fixture, workflow, and TUI surface.
2. Replace it coherently with subject-bearing `thread`; do not ship dual
   canonical terms or compatibility aliases in the clean v11 authority.
3. Require a concise non-empty subject when creating a Thread. Messages retain
   bodies and never duplicate the subject.
4. Render the bottom pane as `Msgs`, identify the selected Thread compactly,
   and show its subject.
5. Update workflow and parity tests, then exercise several Threads labelled to
   one Work and one Thread labelled to several Work items.
6. Apply only to a new immutable v11 distribution and fresh trial authority.
7. [changes requested] Resolve review R1/R2 in
   `review-2026-08-15T22-35-13Z.md`: subject must participate in the
   effectively-once fingerprint, and every stored Thread—including the one
   born with Work—must obey one subject contract. Append accurate final-return
   evidence per R3, rerun focused W31 coverage, then run `just test-v11`.
8. [approved] Apply the same normalized, non-empty, single-line, at-most-80
   UTF-8-byte contract to Work titles and Thread subjects; store the normalized
   Work title as the born Thread subject without truncation or a second input.
9. [done] W31 revision 3 signed off in
   `review-2026-08-15T22-45-22Z.md`: focused 7/7, full v11 549+3, diff check
   clean. Close satisfying and unblock W17/W23 through authority state.
