# W385517 — E385529 correction for independent review

Outcome: bounded correction complete; independent acceptance and any owner full-suite rerun remain pending. No full-suite rerun, live provider, installed-instance change, main-source import or protected Git mutation performed.

## Root cause and deterministic evidence

The retained owner run at d1919f95 failed before its intended SIGKILL: test_manager_loss_retains_unknown_and_restart_does_not_repeat passed await_file(action.json), then json.loads raised at character 0. The real composed fixture first admits/reconciles, obtains the manager guard, and calls Path.write_text on action.json. write_text opens with mode=w, creating/truncating the visible pathname before writing and closing the JSON. await_file observes existence only. Thus the parent may read an empty ready marker between open and write. This is a fixture publication defect, not evidence of a product JSON/storage defect.

publication-probe.py extracts and executes the original write statement from the base fixture. Its Path.open hook takes the reader's turn immediately after the real open, before returning the stream to write_text. The path exists, bytes are empty, and the parser raises the exact character-0 JSONDecodeError. The same run injects the old publication primitive into the new invariant test and produces exactly one expected assertion failure. This is a deterministic schedule, not timing probability or a sleep. The diagnostic catches JSONDecodeError solely to establish and report the expected negative control; the fixture reader still parses strictly without catches or retries.

## Bounded correction

The fixture-only publish_action helper writes/closes retained partial output first, writes/closes JSON to a sibling temporary pathname, then atomically replaces action.json. The ready pathname is never published incomplete. The new test inspects the real post-open/pre-write boundary, requires the ready marker to be absent and partial output complete, then checks final JSON and temporary-file removal. Same-directory atomic rename establishes interprocess publication; no power-loss durability claim is made. Production manager/guard/enforcement code is unchanged. Existing manager-loss fault qualification, failing restart, action-byte no-repeat assertions, deadline/exclusion, parent-loss and operator-stop tests are unchanged.

Secondary display-only correction: present_accounting now states collected, passed, optional skips, failures, errors and unaccounted explicitly. Existing detailed required-skip/duplicate/fixture-anomaly lines remain. account(), machine JSON and exit-status computation are unchanged. New nine-scenario output matrix covers clean, all-accounted failure/error, missing, optional/required skip, duplicate, fixture error/skip and verifies ledger immutability. Three old expected human-summary strings are updated; no expectations weakened.

## Candidate and provenance

Base: d1919f951f919e0064386d131a9bfa457e9eaaec.
Tree identity: e467b92f20a73340835ed52ee84777cb3d5da0ba9050fe8d8ab04d0289d00f04.
manifest.json SHA256: 6644449db7d91d8ff50ebedbb07b78f269ce04e27bf45506d127addf3ceea319.
candidate.patch SHA256: be817d1bd402b2924ad14cc031bcc14cbee18974d9fbd25cf77109c2a36b1b04.
Tree identity hashes the compact sorted-key JSON file-entry list in manifest.json; each entry binds base and candidate bytes.

Exactly three changed paths, with complete base/ and candidate/ snapshots here:
- v12/python/tests/manager/test_authoring_manager_guard.py
- v12/python/tools/parallel_test.py
- v12/python/tests/tools/test_parallel_runner.py

The accepted original five-path correction is already in the pinned base and remains intact. Scratch implementation: work/scratch/w385517-385529/candidate. Reconstruct on another machine by copying the base source without Git metadata and overlaying candidate/; use the documented prepared interpreter and disk-backed fixture roots. Durable snapshots/patch are sufficient without retaining scratch. Main v12 diff empty; protected HEAD/index identities unchanged (protected-before.json, protected-after.json). Temporary test root empty after verification.

## Focused verification and accounting

Final candidate: just test-one tests.manager.test_authoring_manager_guard tests.tools.test_parallel_runner, 81 collected/executed/passed, 0 failures/errors/skips/duplicates/unaccounted, wall 28.187153s (unittest 27.929s). Includes all seven existing real manager-composition cases, new publication test, and all 73 runner tests. candidate-final.log/json retain exact command/cwd/time; accounting.json independently matches prepared-interpreter collection to every verbose outcome (not a claim of native parallel_test --account).

Deterministic legacy proof and expected negative control: publication-probe.log, 1 test with 1 expected failure, no errors, 0.007373s overall probe stopwatch. The exact legacy write also reproduces the original JSONDecodeError before finishing valid JSON.

Earlier candidate-focused run: 16 executed,15 passed,1 failure,0 errors/skips,21.080783s. Failure was in newly authored probe instrumentation: it inspected positional mode only while Path.write_text passes mode='w' by keyword. Corrected hook now accepts the real keyword form; the final 81-case run uses final source. The preliminary standalone probe hit the same instrumentation issue (publication-probe-instrumentation-error.log); its duration was not measured. Preserve these as development failures, not product failures. Measured verification total 49.275309s; preliminary probe time unknown, no fabricated aggregate bound.

## Remaining limitations / handoff

No unresolved product decision identified. This proves deterministic fixture publication and focused compatibility, not full-suite acceptance. Independent review must verify exact candidate/provenance, controlled negative evidence and retained manager-loss guarantees; reviewed import/checkpoint and owner full-suite acceptance remain separate. No broad rerun was requested or performed.
