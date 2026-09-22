# Failure-diagnostic packet — claim235602

Prepared under owner235599/reroute235600 for independent baton.bug review,
then baton.decide for separate exact live selection. Authority: final owner
resumption FINDING entry, claim235602 boundary/result, current PLAN/PROGRESS,
review-2026-09-22T04-28-19Z.md and OWNER-SERIOUS-WORK-GATE-20260922.md.

Candidate diagnostic-235602/CANARY-MANIFEST-235602.json SHA256
`a9e1c97bd20c5cb85b556e91488f3c0e6ecc07fd6a2636d330666c144bee918e`. Exact proposed command:
diagnostic-235602/CANARY-COMMAND-235602.txt; operator instructions:
diagnostic-235602/CANARY-OPERATOR-235602.md. Evidence:
diagnostic-235602/EVIDENCE-235602.json SHA256 `d5a40450cab8aa840d56c45eb7170e90e672eeb9e247379be269bddeb3e6070a`.

Provider/version capture now drains both streams, preserving at most2MiB each,
exact exit status, closed reason, elapsed time and truncation flags. A bounded
base64 envelope transports these records across worker stdout even on nonzero
worker exit; Docker start/attach allows12MiB per stream solely for transport
overhead. Other engine outputs remain2MiB per stream. Both nested and outer
failures are retained privately. The controller saves wire/provider diagnostics
before interpreting status/JSON and captures obtainable post-runtime facts before
cleanup. Cleanup saves before/after-stop observations before exact owned removal.
Unobtainable post-state is explicit; cleanup uncertainty remains failure.

No nonzero process, malformed JSON, timeout, truncation or missing inspection
admits turn two. Independent review checks nested process statuses and equality
with retained raw provider results. Closed public outcomes never contain raw
stream text; private records are0600 under the0700 run root. Raw prefixes on
limits/timeout are not claimed complete. No authentication cause is inferred.

Only new diagnostic-235602 files and this handoff plus attributable parent
FINDING/PLAN/PROGRESS were written. Test path diagnostic-235602/test_isolated_canary.py
extends the16 existing cases with nested nonzero/version/engine failure, both
stream retention, malformed/empty JSON, missing inspection, real worker main,
status forgery, timeout/overflow and old-packet preservation coverage. Strict
contract and all historical recall/Opus/Fable files match original hashes.
No product files, credential/global settings or old consumed roots changed.

Final26 tests pass,1.4149330489999556s supervisor time; total new
3.1298126479996426s across two retained runs. First run exposed a duplicate exclusive
cleanup-before write (fixed with distinct post-stop record) and a newline mismatch
in the test fixture expectation. Both processes ended/no timeout/groups absent.
Exact-digest offline audit, command binding and git diff --check pass. Fresh
/tmp/w177936-diagnostic-235602 and /dev/shm/w177936-diagnostic-235602 are absent.
Previous reviewer0.0014763550007046433s/operator live1.5016096300005302s and all
older measured/unknown costs remain separately referenced in EVIDENCE-235602.
No invented historical total or reset of prior spending.

No live provider, actual engine, auth probe, credential/session read, image build,
export, enabling or Git mutation. Two turns180s each/420s active/600s total/no retry,
exact mixed-model acceptance and isolation/session-only transfer unchanged.
Remaining: independent packet review, exact separate live selection, independent
actual protected-result review. Deterministic fixture/transport proofs establish
no new live recall or production qualification. Normal manager serving/admission,
strict production model policy and certification remain distinct from this
isolated direct-Docker experiment; any further production-use selection belongs
to the owner, not this correction. Serious-work gate remains until disposition.
