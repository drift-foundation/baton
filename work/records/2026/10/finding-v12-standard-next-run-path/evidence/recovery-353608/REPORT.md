# Recovered confinement correction — W339626, claim353608

Recovery author baton.codxpc; implementation author baton.claude claim353054. Owner release353556 records incident78 and the ended Claude turn; reroute353557 selects durable recovery, remaining focused checks and independent review. Current direct-development policy applies. No product file changed by the recovery author.

## Exact recovery and provenance

Before verification, preserved all1569 regular files from /tmp/w339626-353054, with no symlinks, in recovered.tar.gz. RECOVERY.json binds every archive member and archive hash; each member and the original source reread were verified. This includes original base, candidate, r2-before/r2-red/r3-red source arms and all nine raw terminal logs. Original root remains unchanged. A separate /tmp/w339626-353608 copy was used for fresh checks.

CANDIDATE.json binds the four changed paths, exact base/candidate/prior-review hashes, patch hashes and manifest93c48fd2fd53e4d10238e51a69355a2d53115444f5985105a942960acf35ff6a. candidate/ holds full proposed bytes; candidate.patch applies to the base whose four hashes match CORRECTION-347765; review-corrections.patch shows the delta from the earlier unaccepted shared-tree candidate. Four-file patch reconstruction with zero fuzz matched all candidate hashes. All other non-cache files in recovered base/candidate are identical; no new paths. Shared four files still match review347846, and were not imported or edited.

## Review response

- R1: the failure test now requires exactly one admitted attempt and one matching absent candidate, null result fields, nonempty attempt-correlated cleanup/cancellation and outstanding cleanup. The actual refusal string, held state, no retry, repeated-start refusal and useful later run remain checked. The deny-line fixture flag now reaches the watchdog child; the later task uses a modeled instruction. No product accounting was changed to satisfy a test.
- R2: ruleset/root/null descriptor acquisition is inside one try/finally, with reverse cleanup and preservation of original refusal. The new test repeats wrong-type/absent-device/root failures and invalid rule installation40 times each with zero descriptor growth, then verifies successful confinement and outside denial. The existing invalid-facility test additionally covers wrong device number.
- R3: the recovered test executes checkout_plan steps under real Landlock, checks production clone argv including --no-hardlinks/--no-local, checks all3 steps and declared base, and reads the checkout identity. Existing device/sibling/installation/credential denial and inheritance cases remain. The real-Git test is preserved/reused, not rerun in this recovery turn. It creates/mutates disposable fixture Git repositories in the original author's execution; this is not zero historical Git mutation. The recovery author performed no Git mutation.

The original live error operand remains redacted. The source comment spelling /dev/null describes the reproduced mechanism; it must not be read as proof the live redacted field was observed. Previous execution/provenance review findings remain historical facts, not retrospectively erased by later authority.

## Evidence and limits

Recovered terminal logs report the two focused modules (34 managed plus3 joined cases) passing three times:37 tests in37.675s,37.616s and37.630s. Each says OK, with no skip summary. Case counts agree with the recovered code. Recovered candidate source mtimes precede these final logs, but no original argv/exit receipts or pre-run byte manifest survived in this directory; these are retained author test reports, not independent reruns or newly manufactured receipts. Earlier failed iterations and baseline results are preserved too.

Recovered safety-base and safety-candidate logs each report610 tests, the same test_the_runtime_gets_exactly_the_declared_bounded_scratch failure, and2 skips (205.961s/204.389s). The mismatch is an extra /run/baton/logs scratch entry. This is not a passing broader gate. Its unchanged base occurrence is evidence against attributing it to this four-file correction; no broader repair or repeat was selected. The logs do not enumerate skipped test identities.

Fresh verification completes exact-byte checks for the two corrected behaviors without repeating the full37 or broader610 campaigns:

1. focused-new: descriptor cleanup passes; joined-accounting setup refuses because /tmp is tmpfs and /var/tmp is not writable in this sandbox.2 tests/0.103s; exit1, retained as environment failure, not green evidence.
2. focused-disk: set the existing documented BATON_V12_DISK_ROOT to /home/sl/src/baton/.w339626-353608-scratch and repeat only the refused joined-accounting test.1 test/8.229s; exit0, no skips. No product/test source adjustment.

Both fresh test processes were reaped, neither timed out; per-process timeout60s. Exact argv/environment/cwd/status/durations in focused-new.json and focused-disk.json; logs retained. Deterministic provider/engine/Git backends only in joined accounting; descriptor test exercises real kernel Landlock. No new live provider/engine or Git-mutating fixture selected.

## Remaining execution uncertainty

Canonical owner recovery states the prior agent turn ended. All nine retained test logs have terminal summaries; the latest safety-candidate log completed before recovery. Snapshot hashes remained stable across preservation and final checks. This demonstrates recoverable candidate bytes and completed reported test runs, not machine-wide process absence. The recovery shell process view is sandbox-local; it cannot establish a global host census. We did not reuse old execution state or mutate/relaunch old roots; fresh checks used separate disposable storage and their processes exited. No new evidence resolves consumed live C347406's historical held/cleanup state, and no cleanup receipt or cessation proof is invented. That operational acceptance remains separately owned.

## Spending and next handoff

Recovered nine logs subtotal631.891 unittest seconds. Prior recorded author subtotal279.544s is preserved. New unittest8.332s across both commands gives a known subtotal919.767s, plus unknown/unrecorded earlier or interrupted verification and historical diagnostic sweep costs. New process wall time8.727584s is a separate measurement, not added again to unittest time. Recovery/hash/read/archive time unmeasured. Reviewer and operational costs remain separate.

Pass this exact recovered candidate to baton.bug for independent R1/R2/R3 acceptance. Installation/deployment, consumed-C retry/recovery and shared-tree integration remain unselected; W339626 retains later installed operational acceptance. No broad source/policy changes. Human Git checkpoint due after accepted correction; suggested message: “Fix managed confinement descriptor cleanup and source-line verification”. W333486 remains separately allocated and its candidate must not be mixed into this one.
