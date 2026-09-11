# Remaining Job journal ownership boundary

Resolved by independent review-2026-09-09T17-26-15Z.md. The following records
the diagnosis that led to the accepted candidate; it is no longer queued work.

Review129555, current diagnosis, not new source authority. Scope stays the
existing four files; accepted behavior is still CONTRACT.md.

Confirmed cause: the patch adopted the missing provider fields but left the
consumer's own Job/episode evidence unbound. The correction reader likewise
uses its recorded signature as both actual and expected. Generic replay owns
operation selectors and JSON decoding, not these domain relationships.

Proposed bounded structure for revalidation by the implementer:

1. Derive the immutable selected Job/stage/Work/Authority and original attempt
   and generation. The receipt must agree with all of them, including job_id.
2. Own this Job's correction journal against its canonical CORRECT_KIND
   signature. Recompose the original operands used by advance_correction
   (Job, Work, line, checkpoint, verdict and attachment) from the adopted
   correction and public verdict owner. Validate closed nested documents before
   indexing. A row's own signature is never its expected signature.
3. Correlate the correction's opened implementation episode with the selected
   attempt and its historical episode row, including episode number and stored
   offer identity. The original row remains the locator after a successor.
4. Own the restart receipt against that original row's committed exclusion
   ending and against A/B historical owners. Do not use today's live episode,
   current line state or later writer as predicates for completed replay.
5. Route every successful exit through this ownership check, including the
   result returned by store.transact when a competing caller committed first.
   Keep the fresh path's preparation/allocation revalidation before its guarded
   update, and non-durable refusal for failed guards.

Focused proof: retained foreign Job/episode result, missing historical ending,
foreign correction signature, plus a valid ordinary successor/later replay.
Make the concurrent test's hold occur inside the first transaction action and
prove the second call arrives there; pausing before BEGIN does not establish
the claimed lock overlap. Reuse the already passing provider and broader
evidence. Author budget15.191/20s used,4.809s remaining; no reset.
