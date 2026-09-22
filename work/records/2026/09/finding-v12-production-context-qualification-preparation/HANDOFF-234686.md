# Claim234686 — Opus packet ready for independent review

Owner234684 / FINDING2026-09-22T00:44:55Z. New standalone package at
opus-234686/; the accepted Fable packet remains byte-identical, including its
manifest and all bound files. No product source or historical evidence edits.

Pin model and expected terminal identity to **claude-opus-5**, without a moving
alias or an unnecessary extended-context suffix. Official model-config docs
name the selector and minimum CLI2.1.219; the retained image has package2.1.247
and the exact selector in its digest-recorded binary. MODEL-SELECTION-234686.json
contains source URLs, archive/member/package hashes, costs and limits. Static
compatibility is confirmed; account access and reported identity are not observed.
No image execution/rebuild/export, credential read, live model or production
change occurred. The same independently verified image is reused.

Only code changes versus the accepted packet: new run/manifest/owner bindings,
MODEL/REPORTED_MODEL, an additional manifest-bound model-evidence file, and the
contract copy's MODEL/ACTUAL_MODEL constants. Strict predicates and all two-turn
isolation/supervisor/cleanup behavior are unchanged. Eleven deterministic tests
pass in0.321 unittest seconds,0.4138612210517749 supervisor seconds; process group
absent, no harness timeout. Two additive tests pin concrete Opus operands and
exercise wrong/Fable/mixed-model/session/result refusals plus byte-for-byte Fable
preservation and contract logic equivalence. The inherited supervisor timeout
case emits the same expected InterruptedError traceback as the accepted packet.
Exact-digest offline audit and git diff --check pass. No broader test repeat.

Manifest SHA256:
80c797de553a52dd3d78c5d36e040f3c94c6dfb26a80e9b2bb2b23df6ac6dee3

The exact zero-placeholder owner command is
opus-234686/CANARY-COMMAND-234686.txt; operator instructions and all file hashes
are opus-234686/CANARY-OPERATOR-234686.md and EVIDENCE-234686.json. Fresh run roots
are absent and unconsumed. Two provider turns180s each/600s total/no retry remain.

Return through baton.bug for fresh independent packet review, then baton.decide
for the separate live-run selection. This remains the isolated provider canary,
not a production certification or fabricated v12 serving-receipt collection.
All prior author/reviewer measured costs and unknowns remain in their original
evidence. New test spending above; final archive inspection .21443418704438955s
and two earlier read-only probes separately labeled in EVIDENCE-234686.json.
