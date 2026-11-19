# W385227 status UX candidate

Codexpc / baton.codxpc / impl; claim E385238. Base `85e646ba63ee70e932c989252b61558bc3a821f5`. Manifest SHA-256 `79b1ae6dd1fcb4faf70c8e129fc63dbe06f1842c0819d1c776a272186557c020`. Primary locator: `work/records/2026/11/finding-v12-status-job-outcomes`.

## Outcome

Installed status now leads with per-Job outcome, stage states, typed exchange fault/adapter cause when available and explicit closed dependency gates. Service health follows. Fresh/stale and canonical/noncanonical qualifications precede the Job statements. Absent/unreadable snapshots remain unknown; only fresh canonical zero-Job data says idle. Cancellation request and unresolved shutdown remain visible. Completion reports published stage completion, not acceptance. No proposal absence or active model work is inferred.

The original machine-readable observe result, status exit semantics, process ownership distinctions, serving acknowledgement, both freshness ages and detailed runtime boundary are preserved. One snapshot supplies both Job and runtime information. No new database reader or status mutation. Scope/decision: FINDING.md; exact ownership/current state: PLAN.md; author account: PROGRESS.md.

## Candidate and verification

Two paths only: `v12/python/tools/stack.py`, `v12/python/tests/tools/test_stack.py`. `candidate/manifest.json` binds base and final hashes and retained files; `candidate/candidate.patch` is the exact diff. Base bytes retained in `evidence/base-paths.json`. K's pool/single_worker correction is disjoint, coordinated in M385245/M385246; no accepted W385222 paths changed.

**133 tests OK, zero skips**, 26.134 seconds unittest, 26.337 seconds wall, 180-second timeout. Includes 11 new cases and existing lifecycle, installed monitor/recipe, serving, unknown ownership, malformed/stale snapshot, runtime boundary and disposable empty-stack composition checks. Commands/environment/status: `evidence/focused-final-run.json`; full output: `evidence/focused-final.log`; rerunnable focused selection: `evidence/run_focused.py`. Earlier focused selection: 32 tests OK in 0.167 seconds, `evidence/focused-1.log`. `git diff --check` passed.

`evidence/example-status.txt` demonstrates the retained native-labels-4 canonical fault publication with **simulated** fresh timing and service health; it is a deterministic display replay, not a live observation. It shows FAILED, agent fault with unknown cause, blocked review, then Services and retained runtime counts/warning.

## Review and limits

Ready for independent review by baton.decide, not self-accepted. Assess derived headings against stage/cancellation facts, qualifications before outcomes, no invented cause/proposal/coding, output ordering and preserved lifecycle/read-only behavior. Fault display uses closed published exchange codes; deeper diagnostics remain available through the detailed monitor/status evidence. No full suite/build/deployment, Docker/provider invocation, live instance mutation or Git mutation. Owner retains Git.
