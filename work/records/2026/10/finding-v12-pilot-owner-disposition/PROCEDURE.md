# The supported owner disposition procedure — W321689

The packaged command, in the order one delivery reaches it. Written for the
operator who holds the deployed bundle, which is the surface the pilot
assessment found had no owner verb at all. Every invocation below is
`<distro>/baton-v12-stack` (or `python3 -m tools.stack_command` from the
checkout — the same code, as `tools/stack_command.py` states).

`$STORE` is the instance's authority store, `$UUID` its authority identity,
both as `tools/instance.py` records them. `$WORK` is the Work id. `$ROOT` is
the materialization root the dossier's evidence references resolve against —
the repository checkout for this pilot.

## 0. Where the record is (W321688, already delivered)

    baton-v12-stack record read --authority-store "$STORE" \
        --authority-uuid "$UUID" --locator operator-quickstart-<suffix>

Answers the Work id from the dossier locator, or the locator from the Work.
Read-only.

## 1. What is due, and whether you can do it

    baton-v12-stack disposition pending --authority-store "$STORE" \
        --authority-uuid "$UUID" --work "$WORK" --participant "$OWNER"

Read-only; takes no write lock on a serving deployment. `owner_action` is one
of `no-candidate`, `awaiting-verification`, `awaiting-review`,
`review-not-accepted`, `approval-due`, `denied`, `integration-due`,
`closure-due`, `closed`, with `due` saying what that means in one sentence.
`holds` says whether `--participant` holds `approve`, `integrate` and `close`
in this Work's own scope.

Read from the answer, for the next step: `latest_proposal`, that proposal's
`candidate_digest`, its `receipts.review.receipt_id`, and `policy_generation`.

For a Work that is already closed it also answers `closure_acceptance` — the
selected acceptance the closure recorded, with the candidate, the four receipt
identities, the cited integration record and the commit — plus
`close_decision`, the principal and scope the close was authorized under, and
`rationale`, the operator's own prose. Add `--root "$ROOT"` and it resolves the
accepted integration record and reports its state now (`intact`, `changed` or
`unusable`) as a separate fact: a closure that committed is not undone by a
later edit, and an auditor wants to know about the edit anyway.

## 2. Approve or deny the exact reviewed candidate

    baton-v12-stack disposition approve --authority-store "$STORE" \
        --authority-uuid "$UUID" --participant "$OWNER" --work "$WORK" \
        --proposal "$PROPOSAL" --expect-candidate-digest "$CANDIDATE" \
        --expect-review "$REVIEW" --policy-generation "$GENERATION" \
        --approval-id "$APPROVAL" --operation-id "$OPERATION"

`deny` takes exactly the same operands. There is no `--actor`: the receipt's
actor comes from the session minted for `--participant`.

It refuses, writing nothing, when the proposal belongs to another Work, when
the candidate digest is not the one named, when verification did not pass, when
there is no accepted independent review or it is not the review named, when the
policy generation is not the one in force, and when the participant holds no
`approve` grant in this Work's scope. The same `--operation-id` with the same
operands replays the committed answer; with different operands it collides.

## 3. Record the human integration

A person imports the approved bytes, verifies them and commits — Slawomir owns
every Git operation — and writes an integration record beside the dossier's
other evidence, under `$ROOT`:

    {
      "schema": "baton.v12.human-integration-record/1",
      "authority_uuid": "<UUID>",
      "work_id": "<WORK>",
      "proposal_id": "<PROPOSAL>",
      "candidate_digest": "sha256:<...>",
      "commit": "<the commit the human made>",
      "integrated_by": "Slawomir",
      "integrated_at": "<UTC instant>",
      "notes": "optional: what was imported and what was checked",
      "paths": "optional"
    }

Then:

    baton-v12-stack disposition integrated --authority-store "$STORE" \
        --authority-uuid "$UUID" --participant "$OWNER" --work "$WORK" \
        --proposal "$PROPOSAL" --expect-candidate-digest "$CANDIDATE" \
        --root "$ROOT" --reference "$REFERENCE" --commit "$COMMIT" \
        --integration-id "$INTEGRATION" --operation-id "$OPERATION" \
        --evidence-operation-id "$CITATION"

Two durable acts, in this order: the record is digested and cited in the
dossier through W321688's provider, then the authority's immutable integration
receipt is written by the session's own actor. The command moves no bytes,
writes no repository file and runs no Git command.

It refuses, citing nothing, when the candidate is not approved, when the
participant holds no `integrate` grant, when the reference escapes `$ROOT` or
resolves through a symbolic link, when the record is missing, unreadable,
oversized, not JSON, not one document, missing or carrying an unknown member,
or when it names another authority, Work, proposal, candidate or commit.

If the citation commits and the receipt is then refused, the answer says so and
reports `durable`: a stale canonical target journals its attempt, so that
refusal is the committed outcome of those identities and the integration must
be recorded under new ones once the cause is resolved.

**Retrying it.** `--operation-id` is the COMMAND's operation identity. The
command journals its complete canonical request under it — verb, participant,
Work, proposal, candidate digest, reference, commit, integration identity,
citation operation, and the DIGEST of the record it read and validated — and
the authority decides what a retry is:

- the same request replays. The answer carries `replayed: true`, the receipt,
  the citation and `evidence_now`: the state of the cited record at this
  moment, reported separately, so a record edited or deleted after the
  integration does not turn a recovery into a reported failure.
- a different request refuses, cites nothing and records nothing. The answer
  shows both the request this identity already carries and the one just
  supplied, so the operator can see whether to correct the call or use a new
  identity. This holds whatever has happened to the files since: the
  comparison is against the journalled request, never against bytes on disk.

The two authority acts take operation identities derived from this one
(`<operation-id>:integrate` for the receipt, `--evidence-operation-id` for the
citation), so a partially completed act — bound but not cited, or cited but
not receipted — continues from where it stopped on the next identical
invocation. Because the validated digest is in the binding, that continuation
cites exactly the bytes the first attempt validated and needs no file at all:
a record edited or deleted in between cannot strand it, and the answer reports
the drift as `evidence_now`.

Each of those identities must also be this act's own. A citation at
`--evidence-operation-id` that names another Work, another reference or OTHER
BYTES than this request validated is refused — every time it is retried, and
before anything is written — as is a derived receipt identity already carrying
another integration. The honest recovery from a conflicting citation is the one
the authority's own sentence names: cite the record under its own reference, as
its own request with a fresh `--operation-id`.

## 3a. Reading an integration back

The two acts are two durable facts and both are read back by `record` and
`disposition`:

    baton-v12-stack record verify --authority-store "$STORE" \
        --authority-uuid "$UUID" --work "$WORK" --root "$ROOT"

resolves every citation against the root, and `disposition pending` reports the
integration receipt among the proposal's receipts.

## 4. Close on the selected acceptance

    baton-v12-stack disposition close --authority-store "$STORE" \
        --authority-uuid "$UUID" --participant "$OWNER" --work "$WORK" \
        --outcome satisfying --rationale "<why>" \
        --proposal "$PROPOSAL" --expect-candidate-digest "$CANDIDATE" \
        --root "$ROOT" --operation-id "$OPERATION" \
        [--expect-assignment "$FILE"]

A `satisfying` closure requires the whole selected acceptance: passed
verification, accepted independent review, the owner's approval, the owner's
integration receipt, and the human's integration record still intact where the
dossier cites it. It refuses otherwise and names which is missing — a passing
verification or a finished Job closes nothing.

Any other outcome (`non-satisfying`, `rejected`, `cancelled`) is an ordinary
ending, requires no acceptance, and takes none of `--proposal`,
`--expect-candidate-digest` or `--root`. Either way the answer reports every
proposal, receipt and citation that existed at closure; nothing here deletes or
rewrites evidence.

`--expect-assignment` names a JSON file holding the exact assignment identity
the close ends, which the authority requires when a Handler still holds the
Work. `pending` reports that identity under `work.assignment`.

**What a satisfying closure records.** The selected acceptance is composed into
the close's own durable rationale as one canonical
`owner-closure-acceptance: {...}` line after the operator's prose. That is what
makes it survive a restart, what puts it in the close operation's signature —
so a retry naming a different candidate collides instead of replaying this
decision — and what `pending` reads back. A `--rationale` that itself contains
that marker is refused: the command composes the clause from the receipts and
evidence it verified, and a hand-written one would be a claim nothing checked.

**Retrying it.** As with `integrated`, the command journals its complete
canonical request — verb, participant, Work, outcome, rationale, proposal,
candidate digest and the exact assignment precondition (including its absence)
— under `--operation-id`, and performs the close under the derived identity
`<operation-id>:close`. The same request replays the committed closure and
reports `replayed: true` with the stored acceptance and `evidence_now`; this is
the lost-response case, where the close committed, the answer never arrived and
the record may have changed since. On that path the acceptance is read from the
Work's own rationale rather than re-derived from the filesystem.

A request differing in any member — another outcome, actor, rationale,
proposal, candidate, or an assignment precondition added or dropped — is
refused, and the answer shows both requests. A close under a NEW operation
identity against an already-closed Work is refused by the authority itself
("Work is already closed").

Two refusals come BEFORE the request is bound, so a correctable mistake does
not consume the command identity: a participant holding no `close` capability,
and a Work with a live assignment where `--expect-assignment` was omitted. Add
the operand and rerun the same command.

## 5. Read it back

    baton-v12-stack disposition pending --authority-store "$STORE" \
        --authority-uuid "$UUID" --work "$WORK"

A closed Work answers `closed`, with its outcome, rationale and the decision
the close was authorized under. That readback — after a restart, from a fresh
open — is the acceptance.

## Configuring the owner

The grants are made at setup, in each bound Work's own scope, by naming one
optional member in the bootstrap input document:

    "owner_participant": "baton.slaw"

That grants `approve`, `integrate` and `close`. It deliberately does not grant
`verify` or `review`: owner capability and human integration are distinct from
technical review. Omitting the member changes nothing, and before this Work
nothing in a composed deployment held `close` at all.
