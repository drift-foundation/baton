"""The supported Work-label surface: label and unlabel one Work, read one
Work's live set and its journal, and list the Work a label filter selects.

W29401 CLI exposure, slice 1, over W29400's accepted authority label API.

WHAT WAS MISSING. `Authority.create_work(labels=...)`, `Session.label_work`,
`Session.unlabel_work`, `Authority.labels_of`, `Authority.work_label_events`
and `Authority.works_with_labels` have all been accepted behaviour since
W29400, and `stack_command.COMMANDS` exposed none of them. So every one of
them was reachable only by somebody willing to write Python against the
package -- which is the same gap `record` and `disposition` were registered to
close one Work-level verb at a time, and the reason W29401 was parked as "v12
has no CLI".

THIS IS A WRAPPER AND IT OWNS NO LABEL SEMANTICS. The grammar, the
cardinality, the convergent `changed:false`, the scope-resolved
`manage-work-labels` decision, the replay and the all-of/none-of predicate are
the authority's, reached through its own public faces. There is no normalizing
helper here, no second grammar, no cached set and no label the command can
write without a participant-bound session deciding it may.

WHY THE VERBS ARE SPELLED `label-work` AND `unlabel-work`. v11's `baton label`
and `baton unlabel` BIND A THREAD TO A WORK -- a relation between two records,
with an `--work` operand and a thread of its own. A v12 Work label is one
opaque value carried BY a Work. Reusing `label` here would have given one word
two meanings across the two hosts an operator runs side by side, so the Work
noun is in the verb and the dispatch is by COMMAND NAME and never by how an
operand is spelled: nothing in this file reads a label to decide which code
path it takes.

AND THE WORKER MANAGER'S `labels` ARE NOT THESE. Those are OCI runtime labels
-- execution identity a container is discovered and fenced by
(`worker_manager/documents.py`, `runtime.labels`) -- and the authority port
that consumes a Work projection names `labels` among the members it
deliberately does NOT read. Neither vocabulary is reachable from this command:
it imports neither module.

WHAT IT WILL NOT DO. It creates no Work -- `manager create --label` is where a
Work's create-time labels are stated, because that is the one act that makes
one. It reads no repository file, opens no Job or control store, and starts
nothing. The read verbs take the read-only authority handle, so asking a
serving deployment what it carries takes no write lock on it.
"""
import argparse
import json
import sys

__all__ = ["main"]

# The command operation identity's bound, and the one place this file states
# it. The frozen opaque grammar is 160 characters; a derived identity longer
# than that is refused HERE, naming the bound, rather than arriving at the
# journal as a malformed key.
MAX_OPERATION_ID = 160


def _say(value):
    """One answer, key-sorted and indented: the same input renders the same
    bytes twice, which is what makes this output comparable rather than merely
    readable."""
    print(json.dumps(value, indent=2, sort_keys=True))


def _refused(message):
    print("refused: " + message, file=sys.stderr)
    return 2


def _authority(taken, *, writable):
    """Open the named authority; read-only unless this verb writes.

    `labels` and `list` only read, and a read verb that opened the store
    writably would take a write lock on a deployment somebody is serving
    from -- the rule `tools/dossier_command.py` and
    `tools/disposition_command.py` already follow, for the same reason.
    """
    from baton_v12.authority import Authority

    if writable:
        return Authority.open(taken.authority_store,
                              expected_authority_uuid=taken.authority_uuid)
    return Authority.open_readonly(
        taken.authority_store, expected_authority_uuid=taken.authority_uuid)


def _canonical(values):
    """The `--label` operands, as the authority's own canonical set.

    THE AUTHORITY'S HELPER AND NOT A SECOND GRAMMAR. `canonical_label_set`
    lowers, validates the opaque-key alphabet, refuses two operands that
    normalize to one key, and sorts -- so `--label Release-Foo` and `--label
    release-foo` are one key, `--label a=b` and `--label a,b` are refused as
    keys this grammar does not have, and the acts below run in one determined
    order whatever order the operator wrote them in.
    """
    from baton_v12.authority.labels import canonical_label_set

    return canonical_label_set(list(values), what="the --label operand set")


def _derived(operation_id, suffix):
    """One authority act's operation identity, DERIVED from the command's.

    `label-work --label a --label b` is TWO authority acts: the accepted
    transition adds one label, which is what makes each addition separately
    replayable and separately attributable. The operator holds one handle on
    the whole request and each act needs its own, so each is derived -- which
    means an exact retry derives exactly the same ones and the authority
    replays each committed act.

    DERIVED FROM THE LABEL, not from its position in the argument list, so the
    identity an act gets does not depend on the order the operator typed the
    operands in.
    """
    from baton_v12.authority.errors import Refusal

    held = operation_id + ":" + suffix
    if len(held) > MAX_OPERATION_ID:
        raise Refusal(
            f"this command derives the operation identity {held!r} for its "
            f"{suffix} act, and a durable identity is at most "
            f"{MAX_OPERATION_ID} characters; supply a shorter --operation-id")
    return held


def _request(taken, verb, wanted):
    """The canonical request this invocation IS, as one comparable document.

    WHAT GOES IN IT: every operand that decides what is being asked -- the
    verb, the actor, the Work and the complete canonical label set. Not the
    store path, which is WHERE the authority is, and not the derived act
    identities, which are computed from the members already here.
    """
    return {"verb": verb, "participant": taken.participant,
            "work": taken.work, "labels": list(wanted)}


def _bind(authority, taken, request):
    """THE ONE ARBITER of whether this invocation is the same act as before.

    A mutation under one `--operation-id` carries operands no single
    transition takes: a label SET, where each act's own signature is one
    label. So two different requests could otherwise share an identity and
    each act would replay or commit on its own -- `label-work --label a` and
    then `label-work --label a --label b` under one identity would quietly
    perform half a new request.

    So the complete canonical request is journalled under the command's own
    operation identity by `Authority.bind_request`, and the AUTHORITY decides:
    an exact retry replays the binding, and a request that differs in any
    member collides as "reused for different operands" BEFORE this command
    performs anything at all. This is `tools/disposition_command.py`'s
    mechanism, used here for the same reason it exists.
    """
    from baton_v12.authority.errors import Refusal

    try:
        return authority.bind_request(taken.work, request,
                                      operation_id=taken.operation_id)
    except Refusal as refusal:
        # AND THE ANSWER SHOWS WHAT THE IDENTITY ALREADY MEANS. A collision is
        # the one refusal an operator cannot diagnose from their own command
        # line: they have to see the request this identity already carries to
        # know whether to correct the call or to use a new identity.
        held = None
        try:
            held = authority.operation_result(taken.operation_id)
        except Refusal:
            pass
        _say({"work_id": taken.work, "verb": request["verb"],
              "operation_id": taken.operation_id, "replayed": False,
              "already_carries": held, "this_request": request,
              "performed": "nothing"})
        raise Refusal(
            f"this {request['verb']} request is not the one operation "
            f"{taken.operation_id!r} already carries: {refusal}. The answer "
            f"above shows both; a retry under one identity is the same "
            f"request or it is refused, and nothing was done") from None


# -- the verbs ---------------------------------------------------------------

def _mutate(taken, *, adding):
    """Add or remove the named labels on one Work, as attributable acts.

    THE ACTOR IS THE BINDING. The session is minted for `--participant` and
    the authority takes the decision's principal from that binding, so there
    is no `--actor` here and that absence is the point -- a caller that could
    name the actor would be choosing an identity the authority then treated as
    authorized.

    PERMITTED WHATEVER THE WORK'S PHASE, AND AFTER CLOSURE, because the
    accepted contract says so and gives the reason: a label change is archive
    metadata and reopens, reschedules and re-authorizes nothing. There is
    deliberately no status check here; adding one would be this command
    inventing a rule the authority settled the other way.
    """
    verb = "label-work" if adding else "unlabel-work"
    # THE OPERANDS FIRST, before the store is opened at all: a malformed
    # label, two operands that are one key, or an `--operation-id` too long to
    # derive from are all facts about the REQUEST, and a correctable mistake
    # must not reach the journal.
    wanted = _canonical(taken.label)
    acts = [(one, _derived(taken.operation_id, verb + ":" + one))
            for one in wanted]
    with _authority(taken, writable=True) as authority:
        bound = _bind(authority, taken, _request(taken, verb, wanted))
        session = authority.session(taken.participant)
        performed = []
        committed = None
        for label, operation_id in acts:
            said = (session.label_work if adding else session.unlabel_work)(
                {"work_id": taken.work, "label": label,
                 "operation_id": operation_id})
            # THE AUTHORITY'S OWN ANSWER, minus its intermediate set. `said`
            # carries the labels AS OF THAT ACT, committed with the act and
            # replayed with it, and reporting a set observed between two acts
            # beside the one after all of them would be two answers to "what
            # does this Work carry" -- so the last act's set is the request's.
            performed.append({"label": said["label"], "action": said["action"],
                              "changed": said["changed"],
                              "operation_id": operation_id,
                              "decision": said["decision"]})
            committed = list(said["labels"])
        _say({"authority_uuid": authority.authority_uuid,
              "work_id": taken.work, "verb": verb, "actor": taken.participant,
              "operation_id": taken.operation_id, "request": bound,
              "acts": performed,
              # WHICH LABELS ACTUALLY MOVED, as its own member. A convergent
              # no-op succeeds, and an operator reading this needs to see that
              # the Work is in the asked-for state WITHOUT being told a change
              # happened that did not.
              "changed": sorted(one["label"] for one in performed
                                if one["changed"]),
              # THE SET THIS REQUEST LEFT, AS ITS LAST ACT COMMITTED IT -- not
              # a fresh read. W385292 review: the first cut read the live set
              # here, so an exact replay after an intervening act printed the
              # original acts beside somebody else's labels, which is neither
              # the committed outcome nor the byte-identical replay promised.
              # The committed results replay as they were; what the Work
              # carries NOW is `work labels`'s answer, as itself.
              "labels": committed})
    return 0


def _labels(taken):
    """One Work's live set and the journal that produced it. READ-ONLY.

    BOTH, because either alone is half an answer: the set says what the Work
    carries and the events say who added or removed what, under which
    authorization, and when. A create-time addition is attributed to the
    creation act rather than to a `manage-work-labels` grant, which is why
    each event carries `decision` or `creation` and not both.
    """
    with _authority(taken, writable=False) as authority:
        _say({"authority_uuid": authority.authority_uuid,
              "work_id": taken.work,
              "labels": authority.labels_of(taken.work),
              "events": authority.work_label_events(taken.work)})
    return 0


def _list(taken):
    """Every Work carrying ALL of one set and NONE of another. READ-ONLY.

    REPEATED `--label` INTERSECTS and repeated `--without-label` excludes, and
    the two compose. That is the accepted predicate's rule and deliberately
    not an implicit OR: a disjunction would get its own named operand rather
    than silently changing what a repeated filter has always meant. An empty
    filter is every Work, which is what this verb answered before any label
    existed and still answers.

    THE OPERANDS GO TO `works_with_labels` AS GIVEN, so the normalization, the
    duplicate refusal and the "cannot both carry and not carry" contradiction
    are decided once, by the authority, with its own sentences.

    AND NO LABEL SET IS JOINED ONTO THE ANSWER. The predicate decides both
    halves from ONE read view; reading each matched Work's labels afterwards
    would be a second instant reported as though it were part of the first.
    `work labels --work <id>` answers that question about one Work, as itself.
    """
    with _authority(taken, writable=False) as authority:
        matched = authority.works_with_labels(
            all_of=list(taken.label or ()),
            none_of=list(taken.without_label or ()))
        _say({"authority_uuid": authority.authority_uuid,
              "filter": {"all_of": list(taken.label or ()),
                         "none_of": list(taken.without_label or ())},
              "work": matched, "matched": len(matched)})
    return 0


VERBS = {"label-work": lambda taken: _mutate(taken, adding=True),
         "unlabel-work": lambda taken: _mutate(taken, adding=False),
         "labels": _labels,
         "list": _list}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(
        prog="baton-v12-stack work",
        description="This deployment's Work labels: plain cross-cutting "
                    "values carried by a Work. A label is one opaque key, "
                    "never a name=value tag; these verbs are not v11's "
                    "thread label/unlabel and not the Worker Manager's OCI "
                    "runtime labels.")
    verbs = parser.add_subparsers(dest="verb", required=True)

    def store_operands(one):
        one.add_argument("--authority-store", required=True)
        one.add_argument("--authority-uuid", required=True)

    def acting(one):
        """The operands every durable act takes.

        `--participant` AND NO `--actor`, as `disposition` takes them: the
        session is minted for this participant and the authority resolves the
        decision's principal from that binding, so there is nothing for a
        caller to name. `--operation-id` makes the request replayable -- the
        same identity with the same operands replays, and with different
        operands it collides.
        """
        store_operands(one)
        one.add_argument("--participant", required=True)
        one.add_argument("--work", required=True)
        one.add_argument("--operation-id", required=True)
        one.add_argument(
            "--label", required=True, action="append", metavar="LABEL",
            help="one plain label value, repeatable. 1 to 64 characters, "
                 "starting with an ASCII letter or digit and continuing with "
                 "ASCII letters, digits, dots, underscores or hyphens; "
                 "normalized to lower case. A key=value tag, a comma-joined "
                 "list and any other OR-like spelling are refused, because a "
                 "label is one opaque key and nothing here takes one apart")

    labelling = verbs.add_parser(
        "label-work", help="add labels to one Work")
    acting(labelling)
    unlabelling = verbs.add_parser(
        "unlabel-work", help="remove labels from one Work")
    acting(unlabelling)

    reading = verbs.add_parser(
        "labels", help="one Work's live labels and their mutation history")
    store_operands(reading)
    reading.add_argument("--work", required=True)

    listing = verbs.add_parser(
        "list", help="the Work a label filter selects")
    store_operands(listing)
    listing.add_argument("--label", action="append", default=None,
                         metavar="LABEL",
                         help="require this label; repeatable, and repeated "
                              "operands are ALL-OF, never OR")
    listing.add_argument("--without-label", action="append", default=None,
                         metavar="LABEL",
                         help="exclude this label; repeatable, and repeated "
                              "operands are NONE-OF")

    taken = parser.parse_args(argv)
    from baton_v12.authority.errors import Refusal

    try:
        return VERBS[taken.verb](taken)
    except Refusal as refusal:
        # THE AUTHORITY'S OWN SENTENCE, not a traceback. Every refusal this
        # command can reach is a contract answer an operator is meant to read.
        return _refused(str(refusal))
    except OSError as failure:
        return _refused(f"{type(failure).__name__}: {failure}")


if __name__ == "__main__":                                  # pragma: no cover
    raise SystemExit(main())
