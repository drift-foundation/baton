# Labels capacity recovery correction

K: bounded continuation under owner-held W321608, same isolated candidate arrangement. Read work/records/2026/11/finding-v12-retained-labels-candidate-review/review-2026-11-20T01-53-26Z.md. M385311 resolves R1 and confirms the earlier two fixes; only R2 capacity-order recovery remains.

- Outcome: correct the restoration instruction order and its regression coverage. No redesign or reopening resolved findings.
- Confirmed blocker: creation._own_work_changed appends additions before removals and says “and then”. At32labels with one missing/one extra, the first addition is refused. Reviewer real-Authority probe proves removing the extra then restoring the missing label works; current under-capacity test pins the wrong order.
- Required: emit capacity-respecting restoring steps (remove extras before adding missing labels), preserve authorization/per-label replay and reserved-intent protection. Correct the existing expectation and prove following the actual emitted steps at capacity restores the exact original set and permits original-request continuation. Preserve ordinary/race recovery, bounded Job-ID identity and original replay/reuse fixes.
- Verification: focused affected tests and the reviewer capacity probe; reuse unchanged accepted evidence rather than a broad rerun. Distinguish the real fixture reaching its original binding boundary from a complete submission. No full suite, engine/provider/deployment/live retry, host source import or Git mutation.
- Handoff: NEW immutable correction packet/delta/manifest against M385307, full candidate inventory and focused results, prior evidence preserved. Post to T321608 for W385292 independent delta review. Start now without another approval. Host monitoring checkpoint stays untouched.

The fresh_attempt raw-ID observation is confirmed pre-existing and outside this labels path; preserve for separate coordinator classification, do not expand this correction to it.
