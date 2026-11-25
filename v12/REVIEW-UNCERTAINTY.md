# Ordinary review uncertainty and owner recovery

A reviewer may substantiate one existing `baton.review-report/1` verdict, or
write a separate `baton.review-uncertainty/1` object with exactly `schema` and
nonempty `findings`. A retained recovery review also supplies its required
`recovery_digest`. Uncertainty carries no `verdict`. Mixed, duplicate, malformed,
missing, failed-provider and foreign-candidate reports do not create an owner
item by inference and never create acceptance.

The worker preserves the report and findings and publishes a separate
`baton.checkpoint-review-uncertainty/1` claim containing `outcome: uncertain`
and its observed base/head/tree. The host validates the exact attempt,
assignment generation, attachment, checkpoint, retained result and optional
recovery evidence through the same custody and attribution owners as ordinary
review. Claude's contributor requirement remains mandatory; uncertainty does not
bypass it. The three verdicts and historical claim namespace are unchanged.

The serving composition delivers one durable Job owner item addressed to the
existing Authority `native_handoff_routing.decision_recipient` (Slawomir in the
selected deployment), only when that routing names this reviewer. Missing or
conflicting routing explicitly holds rather than guessing a recipient. The
owner item references exact retained report/candidate evidence without copying
model prose into the public queue. Restart and duplicate ending delivery replay
one item; changed binding refuses. Review stays held, with no verdict, acceptance,
correction, integration or automatic retry. The runtime is positively quiesced
and retained custody remains available; the unresolved ending is not settled or
cleaned up merely because an owner item exists. A later owner decision needs a
separately authorized continuation against that evidence.

Read the delivered queue through the installed manager:

```
manager review-uncertainty-items --jobs /absolute/job-store --authority-uuid AUTHORITY_UUID
```

This is read-only and loads no serving factory, engine or credential provider.
The ordinary operator must consume this queue; it is durable owner delivery, not
an email, a provider call or a fabricated Authority handoff response. The existing
clarification response/escalation channel remains separate and refuses a mixed
response plus uncertainty/verdict.

## Failed first-initialization withdrawal

The trusted host owner can invoke the existing D1 operation through:

```
manager credential-recovery-withdraw --control /absolute/control-store --attempt ATTEMPT_ID --receipt RECEIPT_ID --decision OWNER_DECISION_ID
```

The command resolves the exact retained provider selection/home mapping; it does
not accept a guessed home or credential source path. The existing home owner
requires proof initialization never succeeded, unchanged home, and a durably
fenced never-started holder. A successful initialization, changed home, uncertain
or started runtime, wrong receipt or missing binding retains the hold. The
original receipt and decision remain in audit history. Duplicate identical
withdrawal replays that audit. Refusals expose only a closed cause.

Withdrawal does not reseed, authorize a future copy, clear other holds, edit
credential bytes or contact the engine/provider. A separate explicit recovery
selection is still needed before the existing retry-authorization API or a new
execution may be used; the command deliberately offers neither. It provides the
bounded D1 operator surface, not general credential replacement or resume.
