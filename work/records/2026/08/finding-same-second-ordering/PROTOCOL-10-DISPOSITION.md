> **NOTE — the digest below is superseded.** `342a2f6cf335…` was the
> candidate at the time of writing; PLAN 25 renumbered the successor to
> `10.2.0` and the current digest is `1ac97f1fda17…`. Everything this
> file says about the ORDERING ruling still stands.

---

# Protocol 10: documented and retained

Owner: `baton.implementer`. `FINDING.md` and `PLAN.md` are the reviewer's.

PLAN step 1 — "document and retain deterministic `(created_ts, id)` ordering;
no schema change for 1.2.0" — is done. Steps 2–4 are protocol 11 and untouched.

## Documented

`docs/AGENTS-MAILBOX-PROTO.md`, in `Working the channel`, now states the rule
and its limit in one place: ordering is `(created_ts, id)`; `created_ts` has
one-second resolution; across a second boundary that is chronological, inside
one second it is not, because ties break on a random 128-bit id. It says what
is NOT affected — nothing lost, nothing duplicated, every item present exactly
once, and coordinated use unaffected because the standing pattern is `wait`
then `claim --message-id` — and what the rule does not support: treating an
unqualified `claim`, or the top of a list, as "the next one I published". It
names protocol 11 as where the persisted publication sequence lands.

That document is hash-pinned by both distribution manifests, so the change
moves the release bytes. **The set digest is now `342a2f6c…`**, replacing the
`671ff9fb…` I reported earlier. Nothing was deployed at either digest — the
production root still holds only v1.1.0 — so no published release is affected,
but any build a human started before this message should be re-run.

## Retained, and pinned by tests

**`test_naming_the_message_defeats_the_same_second_ordering_limit`**
(`tests/core/test_core_api.py`) — five messages inside one timestamp second
(asserted, so the test cannot pass by accident on a slow machine), then each
claimed BY ID in an order deliberately unrelated to any listing. Every claim
returns the message it named, each is claimable exactly once, and `scan` is
empty at the end. This is the reason the limit is not a delivery defect, and
it is now a property rather than an argument.

`test_list_sent_is_newest_first_by_a_total_order` already pinned the
determinism half and already said, honestly, that it does not compare against
`scan`'s order. Unchanged.

**`test_the_protocol_document_states_the_ordering_limit`**
(`tests/core/test_core_conformance.py`) — the document must state the rule,
the one-second resolution, and the mitigation. A release that quietly dropped
that paragraph would ship a protocol document promising more than the code
does, and the manifests would happily pin it.

## Gate

    just build     candidate 1.2.0, set digest 342a2f6cf335…
    just test      2896 passed, 0 failed   (4m03s), bin/ absent

## Not done

No schema change, no ordering change, no `transitions.seq` work, nothing from
the protocol-11 acceptance boundary. No deployment, no production write, no
Git command that mutates state.
