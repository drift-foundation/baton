# Recall-only packet — claim235340

Prepared for independent baton.bug review, then baton.decide. Authority:
FINDING.md final owner-approved recall-only amendment (M235310/reroute235311),
claim235340 boundary/result entries, current PLAN.md and PROGRESS.md. Prior
independent review: review-2026-09-22T03-24-23Z.md. No live execution selected.

Candidate: recall-235340/CANARY-MANIFEST-235340.json, SHA256
`dfa75118e3110cc5c7346b4d2bc026c21b33b9931340db3d129ac596cf754e2a`.
Exact proposed invocation: recall-235340/CANARY-COMMAND-235340.txt.
Operator instructions: recall-235340/CANARY-OPERATOR-235340.md.
Evidence: recall-235340/EVIDENCE-235340.json, SHA256
`6af69b9487c90472bed0a9c16eec9993b432e7ba8e1365e2e2b4292272e3a47d`.

The new controller requires exactly the observed modelUsage keys claude-opus-5
and claude-haiku-4-5-20251001. Direct model is absent or exactly claude-opus-5;
missing/unknown usage and conflicting direct values refuse. Success, session,
READY and exact recall remain required. The original strict projection remains
unchanged, including actual_model null. It is nested in an explicitly separate
experimental envelope with mixed usage and unestablished model attribution.
No primary/exclusive/auxiliary attribution is made. Both controller observation
and independent review output include the scope; review recomputes from raw
provider results for each turn. Usage values are not used as attribution.

Only new recall-235340/ files plus parent FINDING/PLAN/PROGRESS and this handoff
were written. The sole test path is recall-235340/test_isolated_canary.py,
covering this selected experimental acceptance and preserving the old failure,
isolation and cleanup coverage. The strict contract copy is byte-identical to
opus-234686/evidence/qualification_contract.py. All old Opus/Fable packet and
supporting hashes verified unchanged; no product edits. Supporting model/image
facts are reused from their retained independent evidence, not re-probed live.

Verification:16 deterministic tests pass,0.5140488809993258 supervisor seconds,
exit0/no timeout/process group absent. Exact-digest offline audit and command
binding pass; git diff --check passes. Expected timeout-child interruption is
retained in the passing log. New /tmp/w177936-recall-235340 and
/dev/shm/w177936-recall-235340 roots are absent/unreserved. Two turns180s each,
420s active/600s total,no retry; original isolation/session-only transfer,
credential delivery and cleanup code unchanged. Failed opus-234686 stays failed,
consumed and unchanged. No protected old raw result/session/credential read.

Cumulative spending is preserved, not reset: this claim adds only the measured
0.5140488809993258s deterministic run. Prior Opus author0.4138612210517749s,
reviewer0.324s, failed-result review0.0050291449997530435s, operator live
4.933623595000427s, previous static inspection0.21443418704438955s and separately
labeled exploratory costs remain separate. EVIDENCE-235340.json links prior
Fable and all older known/unknown records; no historical upper bound inferred.
No live provider/engine/build/export/enabling/Git mutation this claim.

Remaining: independent packet acceptance, then separate owner live selection
and independent protected-result review. Deterministic results prove fixture
behavior only. They establish no new provider recall, kernel isolation, model
attribution, token/cache savings or production qualification.
