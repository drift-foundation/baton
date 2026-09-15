# W71879 — committed final view and early refusal feedback, tuner153401

Owner153398 assigns the parent15:00:00Z final-view correction and14:55:17Z disk/preparation-failure fixes. All three are implemented and locally verified. Return directly to the operator, without a preparatory reviewer-model gate.

From `/home/sl/src/baton/v12/python`, run the same single command:

```sh
/usr/bin/env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. /usr/bin/python3 ../testing/standalone_ab/scenario.py
```

The corrected default creates a unique fresh `~/.local/state/baton/v12/synthetic-ab-*` root. Public filesystem preflight runs before image/Git preparation; this host reports ext4/accepted there and tmpfs/policy-denied for `/tmp`. An explicit `--root` still must name a fresh canonical disk-backed directory. The ordinary operator Docker/gid1001/initial `sudo chown` setup boundary is unchanged. No failed root is reused or repaired.

## Final output contract

Integration intentionally advances Git objects/reference without updating checkout/index. The runner now compares the selected `refs/heads/main` commit to `Authority.canonical_target()`, exports exactly that commit's supported regular blobs and modes through read-only Git reads into fresh `final-view/`, and records commit/tree/blob/content provenance in `evidence/final-view.json`. It runs `check_greeting.py`, `check_hours.py` and whole-view unittest discovery, then requires exact byte/mode cleanliness and an unchanged committed reference. Original source identity/cleanliness remains required.

The original target checkout and index are retained as diagnostic evidence; `final_target_status` remains recorded and `target_checkout_is_output=false` identifies the distinction. This explicitly supersedes the old assumption that the ref-only integration target checkout was the final verified output. The clean committed view is the output; no cleanliness test was simply removed, no old target reset, and no product integration behavior changed. Both actual A/B checks and all added B tests are required.

## Early failures

The failure observer opens the ControlStore read-only and uses public preparation/start-failure readers before requiring an exchange terminal. It correlates the record's exact attempt and fixed assignment with the stage, allocation, claimed receipt and current episode; stale/foreign evidence is not accepted. The full owner refusal remains in first-failure.json. Provider diagnostics are explicitly not applicable to these owner failures. Whole/per-attempt budgets, disk policy and containment remain unchanged.

## Validation and preservation

Twelve focused tests pass, including five new cases for stale checkout versus committed A+B output, foreign canonical commit refusal, verification mutation refusal, disk preflight ordering/failure persistence, and exact current preparation/start assignment correlation. Existing seven assertions/cases remain; the direct unittest entry was moved after the appended classes. Syntax, whitespace, CLI help and exact candidate/provenance checks pass. Six changed paths: scenario.py, run.py, failure_observation.py, README.md and new final_view.py under v12/testing/standalone_ab, plus v12/python/tests/tools/test_standalone_ab.py. Exact base/candidate bytes, patch and hashes are in evidence/synthetic-final-view-153401.

Read-only replay against retained actual evidence independently confirms:

- Synthetic1's current preparation refusal is reported immediately with no exchange required: policy/denied for tmpfs.
- Synthetic2's Authority canonical commit9a512c976e7715bdb37405e08d3ddddf16699126/treea74cd7ab445209bc0af14e592d4b587f9624aad5 exports to a clean view. Both behavior scripts and all seven tests pass, including test_hours and A's empty-name checks. The original target files and Git index/objects remain byte-identical after replay.

These are historical evidence replays, not a new full scenario or retroactive success. Both failed synthetic result files, run10's result, historical packages and the earlier observer source/tests remain unchanged. Synthetic2 still records its original stale-checkout failure; full corrected scenario success awaits the operator result.

## Cost

Current measured checks 0.847047775023s; cumulative recorded preparation/checks 122.825071286919s plus retained uncertainty. Current managed claim wall sample 594.669s since15:04:37Z includes reasoning/reads/edits/checks, not model billing time; final canonical pass adds handoff latency. Synthetic attempt totals246.9176634180185s and18.794468152016634s are kept separately, with execution241.82697641299455s and18.547138238005573s. Prior failed/interrupted live walls2945.872874202047s persist. No new model or container scenario was run here.

Return scenario-result.json, evidence/run-result.json, evidence/final-view.json and the three final test logs from the printed new root.
