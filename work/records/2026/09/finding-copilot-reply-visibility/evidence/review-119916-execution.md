# Re-review verification plan — 2026-09-08, claim119916

Question: does the corrected ordering drain both reproduced starvation cases,
preserve stable unaccepted retries, and prioritize fresh failure attention with
its paired runtime correctly? Reuse the retained 53-test implementer result.
Independently run only the five new offline controls plus one mixed paired-
failure probe (the test named mixed Work/failure actually injects only Work).
Budget ten seconds. No socket test, live CLI, notifier, model, service or cursor.
Bind three file hashes and verify the 48 earlier tests by removing only the
new helper/control block in memory and checking the previous candidate hash.
