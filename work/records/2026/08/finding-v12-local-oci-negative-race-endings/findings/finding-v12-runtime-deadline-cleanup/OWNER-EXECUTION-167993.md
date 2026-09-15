# W32577 — fresh corrected-supervisor owner execution

Prepared by baton.codex claim167993 under owner decision
2026-09-14T09:09:48Z and reroute167900. Execute once from the owner host terminal:

```sh
/home/sl/src/baton/.venv/bin/python3 /home/sl/src/baton/work/records/2026/08/finding-v12-local-oci-negative-race-endings/findings/finding-v12-runtime-deadline-cleanup/owner-execute-167993.py
```

The command works from any current directory. It refuses changed bound inputs,
interpreter/dependency mismatch, or an existing execution directory before
launch. It creates owner-execution-167993/ in this dossier, with guard.json,
stdout.log, stderr.log, receipt.json and the supervisor run/ evidence. The
wrapper has been parsed and source-inspected, not run. Do not reuse consumed
owner-execute-164414.py. No preparation engine run occurred.

## Exact candidate and execution boundary

Accepted candidate164779 SHA256
ea2cb3557d8ac87b8198ec5bd5cc9c35545a550c0c9a8e53b3b2da11323902e5,
accepted by review-2026-09-14T00-12-24Z.md. All11 candidate files and nine
additional input/provisioning files match. preflight-167993.json records the
20 comparisons; bindings additionally pin the candidate manifest itself.

| Artifact | SHA256 |
| --- | --- |
| owner-execute-167993.py | 15458d98811bee08c75f3cbbd3db730dfe9f720e4f2d513f0c3dcaa6086e84f4 |
| execution-bindings-167993.json | 3e3e2520cca28eeb13a46a7ee4ceab55b3b54ab26fd8b21c7ff27371da71ec91 |
| engine-gate.py (unchanged accepted correction) | 980911451d33acfae889a09c4ec519b355267e6466b0138e60575587bfb77a8e |

Interpreter: /home/sl/src/baton/.venv/bin/python3, Python3.13.7,
jsonschema4.26.0. Current metadata checked; wrapper also binds interpreter
binary bytes and exact version. No install or interpreter mutation.

Image: sha256:9b8c98820877e33d38d33352d86cc3810e5b72d4935a181b82b512b4d3291de8.
A standalone read-only image inspection in this claim confirms that exact ID,
entrypoint [python3, /opt/baton/baton_worker.py] and user65532:65532.
environment-observations-167993.json records selected observed fields. The
existing owner build/COPY-content evidence and matching bound source files
supply content provenance; no container/content probe, build or pull was run.
This direct metadata inspection does not establish managed Python-to-Docker
access. The selected launch boundary remains Slawomir's host terminal.

## Bounds, cleanup and evidence

One fresh180s per-run limit; the obsolete149.18984108400764s historical remainder
is not an admission gate. Supervisor retains120/5/50/5 phase limits for body,
process-group settlement, exact owned-container cleanup and accounting. Outer
timeout stays177s with1s kill grace and2s launch/termination margin. Expected30s
plus10s margin is an estimate. No limit or cleanup phase was shortened. The
outer watchdog may truncate late accounting; that yields failure/unresolved
evidence, never acceptance. No new supervisor behavior was implemented.

The wrapper records raw exit, monotonic elapsed, run_remaining_seconds and
historical_plus_run_seconds. Historical30.81015891599236s remains explicit
and is never reset or subtracted from the new run limit. A timeout, interruption,
overrun, missing receipt or nonzero exit is not a pass or proof of cleanup.
Provisional supervisor result/stdout is not authoritative completion: assess
its actual exit after output together with the underlying evidence. Every
receipt retains independent_acceptance=false until separate review.

Preserve all logs, exact names/creation intents, retained fixture artifacts,
output and custody evidence. Return actual receipt.json and run/ results to
baton.feat through W32577. The wrapper performs no retry or follow-up cleanup.
Do not use retained names as proof of current ownership or absence; report any
unresolved ending to ops without unrelated removal. Original44 evidence files
match preservation-164779.json; original exit1 and unresolved names remain
historical failure. The new execution directory does not yet exist.

The real-engine question is daemon stop/removal and actual provider endings,
partial-output custody, sibling preservation, lane release and distinct
Authority-gate discharge. Deterministic classifier replay cannot supply that
engine evidence. Agent/Authority fixtures remain deterministic; no live model.

## Remaining acceptance and ownership

After the owner run, independently assess the full result, then complete
remaining pinned product verification and deadline documentation. M165203
already handed DEPLOYMENT back to W32577; current hash matches
971fba687461bf4cc0c8899b5f692d086cad3af8cd794573b2004cee1f0a7f94. Preserve
W161230 reviewed sections and recheck any intervening edit before writing.
There is no renewed documentation handback approval gate. No docs edit here.

No test suite or runtime gate ran in preparation. Existing author68.89533569900784s,
reviewer5.649451640987536s and original engine30.81015891599236s records remain.
Metadata probes were not independently wall-timed; do not claim their duration
as zero. M166331 removes cumulative development-stopwatch gates; selected
per-run limits, focused scope, cleanup and actual-result review remain.
Obligation163303 is answered. W32577 and its parent remain open.
