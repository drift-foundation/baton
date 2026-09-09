### Concise reporting is mandatory

Every agent role, including the interactive copilot, follows these rules.
Write each technical explanation once in its canonical dossier or evidence
file, then reference it. Preserve decision history and prior reviews; apply
this rule to new reporting without rewriting immutable evidence.

- **Progress:** one attributable delta per meaningful result, normally at most
  200 words: what changed, verification outcome, remaining limitation and next
  action. Put detailed commands, logs, hashes and investigations in linked
  evidence. Do not retell the assignment, earlier reviews or unchanged design.
- **Discussion handoff:** at most100 words stating result, material blocker or
  limitation, requested next action and exact evidence locator. A human handoff
  must include the decision needed and recommendation. Do not copy the progress
  report into Messages.
- **Pass comment:** one sentence, at most40 words, naming the destination's
  action and linking the handoff or exact record. The pass is the authoritative
  transfer; the discussion carries its concise explanation.
- **Review:** lead with a verdict, blockers and next action in at most100 words.
  Record each new technical finding once beneath it with sufficient evidence;
  cite applicable prior findings and results instead of reproducing them.
- **Operator update:** at most100 words for a routine status or decision recap.
  Supply exact commands separately when action is needed. User-requested deeper
  discussion and substantive design analysis may use the detail they require.

These prose limits do not truncate required commands, typed references, exact
path sets or digest-bound approvals. Put bulky technical material at one linked
location and keep every decision-relevant limitation visible in the summary.
Progress may exceed its normal limit only for necessary new technical material
whose reason is stated briefly; length is never justified by repeating context.

**Before publishing, the author checks:** does every sentence add a new fact,
decision, limitation or action; is repeated detail replaced by a locator; and
can the recipient act without reconstructing Events? Remove duplication first.
Recipients, especially reviewers and the copilot, flag noncompliance in the next
existing handoff and require subsequent reporting to comply. Do not create a
separate approval cycle, delay a necessary transfer or rewrite prior evidence
merely to shorten a report. This is a mandatory agent operating rule; Baton does
not enforce prose length in the CLI.

    $BATON say thread=T2 body="Quoted and unquoted destinations are fixed; focused checks pass. Review the candidate in product:work/records/2026/09/finding-escapes/PROGRESS.md."
    $BATON pass work=W2 to=app.rview comment="Review the escape fix and evidence in product:work/records/2026/09/finding-escapes/PROGRESS.md."
