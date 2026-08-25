# Plan: reconcile ACP tool-call kind across prose and schema

1. [done 2026-08-23] Record the frozen §6.2 / `toolCallView` contradiction
   discovered during W4 and preserve the current implementation as a
   deliberate non-resolution.
2. [done 2026-08-23] Revalidate the pinned ACP SDK and captured provider evidence for
   the exact root-level `tool_call` and `tool_call_update` shapes.
3. [done 2026-08-23; approved] Rule ACP `kind` as portable, optional advisory
   evidence in agent-session 1.0. Copy a pinned-vocabulary value when present;
   omit the member when absent and never infer or synthesize a fallback. The
   field is presentation-only and carries no policy or outcome authority.
4. [queued for implementation] Append an explicit correction/supersession to the
   owning ACP finding and update SPEC, schema, examples, model, evidence
   interpretation, product schema copy and focused regressions atomically.
5. [queued] Re-review every consumer against the corrected single contract.
4. [done 2026-08-23] Implemented as one contract change across seven
   artefacts: the owning record's §6.2 row and a new §6.2.1 that QUOTES the
   superseded reading of both artefacts; `toolCallView.kind` and a new
   `toolKind` definition in the frozen schema, so schema and model cannot
   drift on the vocabulary; the correction appended to
   `finding-acp-agent-boundary/FINDING.md`; `normalize_tool_call` in the
   executable model with the trace-driven case routed through it; the
   byte-identical product schema copy; the v12 normalizer; and focused
   present/absent/invalid regressions in both the model and v12. Revalidated
   against the pinned SDK rather than inferred from either artefact —
   `kind?: ToolKind` and `kind?: ToolKind | null`, ten values, exactly as
   ruled. One v12 assertion that required a supplied kind to be DISCARDED is
   superseded and marked where it stood. The captured trace is unchanged and
   its interpretation corrected: no kind is now a positive absent example.
   Evidence: `evidence/implementation-2026-08-23.txt`.
5. [queued] Re-review every consumer against the corrected single contract.
   Not discharged by item 4.
6. [changes requested 2026-08-23; independent review round 1] Preserve the
   accepted seven-artifact correction, then distinguish initial `tool_call`
   from `tool_call_update`: omitted kind is absent on either; explicit null is
   absent only on the update and refuses on the initial call. Validate kind as
   a string before vocabulary membership in both executable consumers so
   every invalid value returns the closed schema error instead of a raw
   JavaScript or Python exception. Retain the four additive regressions and
   migrate the two existing null-absence fixtures under the review's explicit
   authority. Consumer sweep found no policy/outcome reader. Review:
   `review-2026-08-23T19-05-30Z.md`; evidence:
   `evidence/review-round1-2026-08-23.txt`.

6. [done 2026-08-23] Closed. The correction QUOTED the SDK's nullability
   distinction and then implemented one path; both consumers now carry their
   SOURCE and decide on it, with the whole table stated in SPEC §6.2.1 so
   prose and code finish in one state. And both refusals stopped running the
   value they were refusing — JavaScript no longer serializes it into the
   diagnostic, Python no longer hashes it into a frozenset — so every invalid
   value leaves as the closed pair. The four additive review regressions are
   retained and the two null-absence fixtures migrated on the review's
   explicit authority. Two more cases per consumer, each a TABLE OVER BOTH
   SOURCES rather than the corner that happened to fail. Ten mutations run;
   one JavaScript mutation is reported EQUIVALENT rather than counted, and one
   Python zero turned out to be my measuring instrument rather than the code.
   Separately found and fixed: this Work's own model test class sat BELOW the
   `if __name__ == "__main__"` guard, so running the file as a script never
   defined it — 57 tests instead of 64, with every W543 model case inert.
   Both runners now report 66.
   Evidence: `evidence/correction-round1-2026-08-23.txt`.
7. [queued] Re-review every consumer against the corrected single contract.
   The review's sweep and a repeat of it after this change both found no
   runtime reader of the advisory field beyond the executable model and the
   v12 normalizer, so what remains is confirmation at W4 composition rather
   than a search.
7. [done 2026-08-23; independent sign-off] Confirmed the corrected contract
   at the current W4 composition. The two executable consumers preserve the
   source-specific nullability table and the closed refusal taxonomy; direct
   and discovery model runners both execute 66 tests; frozen and product
   schema copies have the same SHA-256 digest; and no consumer reads portable
   tool-call kind as policy, authority, outcome, success, failure or
   disposition. Agent events are 52/52; full v12 is 650/654, with the four
   failures owned by W641 and W4. Review:
   `review-2026-08-23T20-00-57Z.md`; evidence:
   `evidence/signoff-round2-2026-08-23.txt`.
