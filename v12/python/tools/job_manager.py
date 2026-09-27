"""The one entry point onto the v12 Job manager: submit, status, serve.

W71875. THREE SUBCOMMANDS AND NO FOURTH. `submit` records one bounded
multi-Job submission; `status` prints the read-only projection; `serve` runs
the long-lived control loop. Everything else an operator used to do by hand --
issuing an offer, taking a claim, deciding what is next -- is what `serve`
derives, which is the point of the leaf.

WHAT THIS TOOL WILL NOT CONSTRUCT. It does not mint an authority session and
it does not mint bearers. `baton_v12.worker_manager` states its own rule --
the manager consumes an already-minted, participant-bound session that trusted
deployment supplies -- and a command-line tool that built one would be a way
to obtain authority by running a script in the checkout. So `serve` takes
`--operations module:attribute`, imports exactly that name, and calls it with
the two open stores; supplying the port, the mint and the bearer delivery is
the deployment's business and remains visible in the deployment's own code.

`submit` and `status` need no such capability. A submission is recorded in the
Job store alone, and a status assembled without the manager's control store
says so in its own `canonical` member rather than reporting an empty pipeline
as a quiet one.

JSON ON STDOUT, ONE DOCUMENT PER RUN. The output is the versioned document the
package answers with, so a program consuming this tool and a program calling
the package read the same thing.

THE TWO STORES ARE SEPARATE OPERANDS AND ARE NOT ASSUMED TO BELONG TOGETHER.
Review [P1]: `--store` and `--control` are chosen independently, so pointing a
second Job store at a control store another one is already driving is a typo
away. Nothing here pairs them by configuration; the package proves each
canonical act against the persisted Job/stage intent instead, and a control
store holding somebody else's offer under this store's derived identity refuses
rather than being adopted or projected.
"""

import importlib
import json
import sys

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import (JobStore, ManagerOperations, Unobserved,
                                   read_submission, reconcile, serve, status,
                                   submit)
from baton_v12.worker_manager import ControlStore
from baton_v12.worker_manager import attempts, boundaries, intake, oci, tokens

__all__ = ["main"]


def _utc_clock():
    """The one instant source this tool builds, when a caller supplies none.

    Built once and threaded through, because a tool that called
    `datetime.now()` in three places would have three clocks and a fixture
    pinning one would silently not pin the others.
    """
    from datetime import datetime, timezone

    def now():
        moment = datetime.now(timezone.utc)
        return (moment.strftime("%Y-%m-%dT%H:%M:%S.")
                + f"{moment.microsecond // 1000:03d}Z")

    return now


def _job_store(taken, clock):
    """The one place every command opens its Job store.

    W83781: AND THE AUTHORITY BINDING IS THREADED THROUGH IT, for all three
    commands. It is a stable public identity rather than a capability, so
    `submit` and read-only `status` still construct no Authority, open no
    Authority store and hold no session -- they name the Authority their Job
    store belongs to, and a store that says it belongs to another one refuses
    without being touched.
    """
    return JobStore.open(taken.store, authority_uuid=taken.authority_uuid,
                         incarnation=taken.incarnation, clock=clock)


def _read(path):
    if path == "-":
        return sys.stdin.read()
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


# -- W275774: THE OVERDUE-RESOURCE PASS THIS DEPLOYMENT SERVES ----------------
#
# Review 17:17:15Z: an optional hook `serve` never receives is not a production
# connection. So the pass is composed HERE, where a deployment tool belongs, and
# handed to `serve` on every serving run.
#
# THE ADAPTER IS LEAN ON PURPOSE. Reclaiming needs exactly two engine acts -- stop
# the exact container and ask what that identity now is -- and neither needs mounts,
# deliveries or an assignment. So this composes `oci.stop_vector` and
# `oci.inspect_vector` directly instead of building a full runtime adapter, which
# would require roots a reclaim has no business naming.


# W275774: THE TWO BOUNDS A TICK'S EXPIRY WORK HAS, stated exactly.
#
# A reclaim's engine calls are short by nature -- stop one container, describe one
# identity -- so the 600-second default this tool uses elsewhere is the wrong bound
# for them, and the number of resources one tick visits is capped so a backlog is
# worked through ACROSS ticks rather than inside one.
#
# WHAT THE ARITHMETIC ACTUALLY SAYS, restated as the reclaim grew a third act. A
# reclaim now makes at most THREE engine calls -- stop, remove, inspect -- each bounded
# by `_RECLAIM_SECONDS`, for each of at most `_RECLAIM_CANDIDATES` resources. That is a
# COMMAND ALLOWANCE of 3 * 30 * 16 = 1440 seconds, and the 960 in earlier records is
# historical. It is an upper bound on time spent waiting for THOSE calls and NOT a
# whole-loop latency: the ending's own observation and custody acts are additional, and
# nothing here bounds the database work.
_RECLAIM_SECONDS = 30
_RECLAIM_CANDIDATES = 16


def _engine_runner(argv, *, seconds=None):
    """One engine invocation, as a subprocess. The same shape `single_worker` uses."""
    import subprocess

    finished = subprocess.run(argv, capture_output=True,
                              timeout=600 if seconds is None else seconds)
    return {"status": finished.returncode,
            "stdout": finished.stdout.decode("utf-8", "replace"),
            "stderr": finished.stderr.decode("utf-8", "replace")}


class _ReclaimAdapter:
    """The two verbs a reclaim performs, over one engine.

    W275774 review 17:27:42Z found three defects here and all three were the same
    mistake in different clothes: reading a POSITIVE fact out of evidence that did
    not carry it.

      * A missing engine socket answers "no such file or directory", and a substring
        test for "no such" turned an UNREACHABLE ENGINE into a gone container. So
        absence is now recognised only from an exact missing-CONTAINER answer that
        NAMES the identity that was asked about.
      * An inspection that described some other container was accepted for the one
        requested. The body's own identity is now compared.
      * `Running: null` is not `false`. A non-boolean is not a state, so it answers
        uncertain rather than quiescent.

    Everything unrecognised answers `uncertain`, which the reclaim treats as a hold.
    That is the only safe default: a resource whose writer may still exist stays
    held, and nothing here converts a fault into a licence.
    """

    def __init__(self, engine, run, custodian_image_digest=None):
        self._engine = engine
        self._run = run
        # W275774 review 18:02:47Z: THE CUSTODIAN, when the deployment configures one.
        #
        # I claimed both P1s closed last claim and that was wrong: this adapter never
        # had `normalize_directory`, so the conditional ending ALWAYS took the
        # awaits-normalizing branch and no production path ever completed a
        # revoked-resource ending. The reviewer was right to keep the finding open.
        #
        # What the custodian act actually needs is small -- the engine, the runner and
        # a custodian image digest, exactly as `oci.OciAdapter.normalize_directory`
        # uses them. It needs no roots and no deliveries, which is why this lean
        # adapter can carry it without becoming the full runtime adapter.
        self.custodian_image_digest = custodian_image_digest

    def _asked(self, argv):
        """One engine invocation whose FAULTS are answers rather than escapes.

        `subprocess` raises `TimeoutExpired` and an unreachable binary raises
        `OSError`; neither is a `ContractRefusal`, so before this they escaped the
        reclaim's own catch and ended the whole serving pass. An engine that could
        not be asked is an UNKNOWN, which is a hold.
        """
        try:
            return self._run(argv, seconds=_RECLAIM_SECONDS)
        except (ContractRefusal, KeyboardInterrupt, SystemExit):
            # W275774 review 17:35:44Z: NARROWED. A `BaseException` catch swallowed
            # `KeyboardInterrupt` and `SystemExit`, so an operator stopping this
            # process was reported as an engine that could not be asked. A refusal is
            # the caller's to handle and an interruption is the operator's; neither is
            # an observation.
            raise
        except Exception as fault:                         # noqa: BLE001
            return {"status": -1, "stdout": "",
                    "stderr": f"the engine could not be asked: {fault!r}"}

    def stop_expired(self, command):
        # W275774 review 2026-09-26T20-07-17Z: NAMED FOR THE ACT IT PERFORMS. This
        # adapter exists for the expiry sweep alone; offering the cancellation's
        # `stop` name was what gave that capability a second crossing owner.
        taken = boundaries.document(command, "a reclaim stop command",
                                    required=("runtime_id", "operation_id"))
        answer = self._asked(oci.stop_vector(self._engine,
                                             runtime_id=taken["runtime_id"]))
        if answer["status"] != 0:
            raise ContractRefusal(
                "runtime-observation", "quiescence-unknown",
                f"the engine did not stop {taken['runtime_id']!r}: "
                f"{answer['stderr'][:240]!r}")
        return {"runtime_id": taken["runtime_id"],
                "operation_id": taken["operation_id"]}

    def remove(self, command):
        """The removal that makes absence REACHABLE, correlated to the reclaim.

        W275774 review 17:54:31Z: a stop-only reclaim left the container present, so no
        later observation could report `absent` and the revoked-resource ending could
        never run. Stopping and removing are separate facts and stay separate verbs: a
        container that stopped but could not be removed is still holding its mounts.
        """
        taken = boundaries.document(command, "a reclaim remove command",
                                    required=("runtime_id", "operation_id"))
        answer = self._asked(oci.destroy_vector(self._engine,
                                                runtime_id=taken["runtime_id"]))
        if answer["status"] != 0 and self._missing(
                taken["runtime_id"], answer["stderr"]) != "absent":
            # A REMOVAL OF SOMETHING ALREADY GONE IS NOT A FAILURE, and that is the one
            # non-zero answer this accepts -- exactly, by the same parsed identity rule
            # as the observation.
            raise ContractRefusal(
                "runtime-observation", "quiescence-unknown",
                f"the engine did not remove {taken['runtime_id']!r}: "
                f"{answer['stderr'][:240]!r}")
        return {"runtime_id": taken["runtime_id"],
                "operation_id": taken["operation_id"]}

    def normalize_directory(self, store, *, assignment_id, which, seconds=None,
                            reclaim=None):
        """One custody act, delegated to the normalization owner.

        Present only when a custodian image is configured: `_reclaiming` composes this
        adapter WITHOUT the capability otherwise, so the ending's own capability check
        refuses rather than this method pretending to normalize.

        W275774 review 18:11:15Z: THE SUPPLIED ALLOWANCES ARE HONOURED, not dropped.
        My first cut did `del seconds, reclaim`, which silently discarded the caller's
        budget -- so a caller that bounded an ending's remaining time got an unbounded
        custody act instead. The wrapper below is `oci.OciAdapter.normalize_directory`'s
        established pattern, reused rather than reinvented: each vector keeps its own
        maximum, an allowance can only LOWER it, and the ACTING vector spends the work
        budget while every other vector spends the total.
        """
        from baton_v12.worker_manager import custody as _custody

        run = self._run
        if seconds is not None:
            def bounded(argv, *, seconds=None, _run=self._run, _work=seconds,
                        _total=reclaim if reclaim is not None else seconds):
                most = (_custody.CUSTODY_ACT_SECONDS if seconds is None
                        else seconds)
                acting = len(argv) > 1 and argv[1] == "run"
                return _run(argv, seconds=_custody.allowed(
                    _work if acting else _total, most))

            run = bounded
        return _custody.custody_act(
            self._engine, run,
            image_digest=self.custodian_image_digest, store=store,
            assignment_id=assignment_id, operation="normalize", which=which)

    def observe(self, runtime_id):
        answer = self._asked(oci.inspect_vector(self._engine,
                                                runtime_id=runtime_id))
        if answer["status"] != 0:
            return {"runtime_id": runtime_id,
                    "state": self._missing(runtime_id, answer["stderr"]),
                    "why": f"the engine answered {answer['stderr'][:240]!r}"}
        described = self._described(runtime_id, answer["stdout"])
        if described is None:
            return {"runtime_id": runtime_id, "state": "uncertain",
                    "why": "the engine's description could not be read as this "
                           "exact identity's state"}
        return described

    @staticmethod
    def _missing(runtime_id, stderr):
        """`absent` ONLY for an exact missing-container answer about THIS identity.

        W275774 review 17:35:44Z: a substring test accepted
        "No such container: container-a-other" as the absence of `container-a`. So the
        identity is PARSED OUT of the message and compared exactly -- an answer about
        a neighbouring name says nothing about this one, and freeing a resource on it
        would be the worst possible misreading.
        """
        said = (stderr or "")
        for marker in ("No such container:", "No such object:"):
            at = said.find(marker)
            if at < 0:
                continue
            named = said[at + len(marker):].strip().split()[0:1]
            if named and named[0] == runtime_id:
                return "absent"
        return "uncertain"

    @staticmethod
    def _described(runtime_id, stdout):
        """The exact identity's own state, or `None` when that is not what arrived."""
        try:
            body = json.loads(stdout)
        except (TypeError, ValueError):
            return None
        if isinstance(body, list):
            if len(body) != 1:
                return None
            body = body[0]
        if not isinstance(body, dict):
            return None
        named = body.get("Id")
        if not isinstance(named, str) or named != runtime_id:
            # EXACT, AND NOTHING LOOSER. Review 17:35:44Z: my bidirectional prefix
            # rule accepted an EMPTY `Id` for every identity (everything starts with
            # "") and accepted `container-a-other` for `container-a`. A prefix is not
            # an identity. If short-id resolution is ever needed it will be an
            # explicit, validated canonicalisation with its own cases, not a
            # comparison that happens to be lenient.
            return None
        state = body.get("State")
        if not isinstance(state, dict):
            return None
        running = state.get("Running")
        if running is not True and running is not False:
            return None
        return {"runtime_id": runtime_id,
                "state": "running" if running else "quiescent",
                "why": "the engine described this exact identity"}


class _Reclaiming:
    """The lean adapter WITHOUT the custody verb, for a deployment that configured
    no custodian image. Composed explicitly rather than by omission so the reason is
    readable at the seam that decides it."""

    def __init__(self, adapter):
        self.stop_expired = adapter.stop_expired
        self.remove = adapter.remove
        self.observe = adapter.observe


def _reclaiming(control, engine, run, custodian=None):
    """One expiry pass over every attempt that has a runtime to reclaim.

    BOUNDED, which review 17:17:15Z asked for by name: it walks the attempts this
    manager itself recorded with an attached runtime, so the work per tick is the
    number of live attempts rather than the whole journal, and each attempt's own
    reclaim decides in its own transactions whether anything is overdue at all.

    ONE ATTEMPT'S REFUSAL DOES NOT END THE PASS, and this is the visible policy
    `manager.serve` deliberately does not choose: a sweep that died on one unreachable
    engine would leave every OTHER overdue resource held. The refusals are collected
    and answered, never swallowed.
    """
    governance = tokens.workspace_governance()
    # THE CAPABILITY IS COMPOSED ONLY WHEN IT CAN BE HONOURED. Without a configured
    # custodian image there is no normalization this pass can perform, and an adapter
    # advertising the verb anyway would turn the ending's refusal into a false start.
    adapter = _ReclaimAdapter(engine, run, custodian_image_digest=custodian)
    if custodian is None:
        adapter = _Reclaiming(adapter)
    # W275774 review 17:40:10Z [P1]: THE CAP WAS NOT FAIR, only bounded.
    #
    # A capped pass that always started at the beginning visited the SAME first
    # sixteen held resources on every tick, so a seventeenth was never reached at
    # all -- a bound that starves is worse than the unbounded sweep it replaced,
    # because the starved resource is held forever with nothing ever looking at it.
    #
    # So the pass remembers where it stopped and the next one CONTINUES AFTER IT,
    # wrapping around. Eligibility is still decided per attempt in its own
    # transactions, so rotation changes only the ORDER in which candidates are
    # visited -- never whether one qualifies -- and unknown holds are untouched.
    resumed = [None]
    # W275776 (Child C): THE UNCERTAIN HALF HAS ITS OWN CURSOR, for the same fairness
    # reason the overdue half does. The two sets overlap only by accident -- an
    # unresolved launch is usually NOT overdue -- so sharing one cursor would let a
    # long run of overdue candidates starve the unresolved ones and vice versa.
    resumed_unresolved = [None]

    def pass_over_attempts(*, now):
        del now
        reclaimed, refused = [], []
        # W275776, TOK-10: "Restart recovery processes overdue AND UNCERTAIN tokens
        # before admitting conflicts." The uncertain visit runs FIRST and separately.
        #
        # MEASURED BEFORE IT WAS WRITTEN: `_governed_candidates` selects on
        # `governance.overdue(...)`, so an outstanding token whose LAUNCH nobody settled
        # was no candidate at all until its lifetime ran out -- and the reviewer's probe
        # showed this pass making ZERO engine calls for exactly that state. The token
        # record already knew the container it had bound; nothing was looking at it.
        unresolved = _observing_unresolved(control, governance, adapter,
                                          resumed_unresolved)
        chosen = _after(_governed_candidates(control, governance),
                        resumed[0])[:_RECLAIM_CANDIDATES]
        if chosen:
            resumed[0] = chosen[-1]["runtime_attempt_id"]
        for row in chosen:
            try:
                outcome = intake.reclaim_expired_resource(
                    control, adapter,
                    attempt_id=row["runtime_attempt_id"], govern=governance)
                # W275774 review 17:54:31Z: AND THE ENDING RUNS IN THE SAME PASS.
                #
                # There was no production caller of `settle_revoked_resource` at all,
                # so a revoked resource was never normalized or returned by anything.
                # The reclaim withdraws and removes; the ending accounts for the roots
                # and returns. Running them in one pass is what makes the lifecycle
                # actually close -- and the ending refuses on its own preconditions
                # (revoked, absent now, no activation in flight) rather than trusting
                # what the reclaim just did.
                # AND THE ENDING ONLY IF THIS ADAPTER CAN NORMALIZE, which the lean
                # one cannot. Measured rather than assumed: wiring the ending in
                # unconditionally refused with "the runtime adapter's
                # directory-custody act is a capability this manager calls; this is
                # none". The ending accounts for the governed ROOTS, which means
                # custody acts, which means the full custodian composition -- more
                # than the two verbs a reclaim needs. Pretending otherwise would have
                # turned every tick into a refusal.
                if outcome.get("reclaimed") in ("held", "returned") \
                        and getattr(adapter, "normalize_directory", None) is not None:
                    outcome = dict(outcome, ending=intake.settle_revoked_resource(
                        control, adapter,
                        attempt_id=row["runtime_attempt_id"], govern=governance))
                elif outcome.get("reclaimed") == "held":
                    outcome = dict(
                        outcome,
                        ending="awaits-normalizing-ending",
                        ending_why="this pass's adapter performs no custody acts, so "
                                   "the roots are not accounted for here and the "
                                   "resource stays held")
                reclaimed.append(outcome)
            except ContractRefusal as refusal:
                refused.append({"attempt_id": row["runtime_attempt_id"],
                                "why": refusal.message})
            except (KeyboardInterrupt, SystemExit):
                # THE OPERATOR'S, NOT THIS PASS'S. Stopping the process is not an
                # attempt-level fault and must not be recorded as one.
                raise
            except Exception as fault:                     # noqa: BLE001
                # W275774 review 17:27:42Z: A FAULT IS NOT A LICENCE AND NOT AN END.
                # `TimeoutExpired` and `OSError` are not `ContractRefusal`s, so before
                # this they escaped and ended the whole pass -- leaving every OTHER
                # overdue resource unreclaimed because one engine hung. The resource
                # for this attempt stays held, because nothing was confirmed.
                refused.append({"attempt_id": row["runtime_attempt_id"],
                                "why": f"the reclaim faulted: {fault!r}"})
        return {"reclaimed": reclaimed, "refused": refused,
                "resumes_after": resumed[0],
                # W275776: THE EXACT UNRESOLVED EXECUTIONS, reported rather than acted on
                # -- see `_observing_unresolved` for why this pass observes and holds
                # rather than attaching.
                "unresolved": unresolved,
                "unresolved_resumes_after": resumed_unresolved[0]}

    return pass_over_attempts


def _observing_unresolved(control, governance, adapter, resumed):
    """Visit each persisted UNCERTAIN token, ask the engine about it, and report.

    W275776 (Child C), TOK-10 and HOST-2. A restart reconciles "the recorded attempt,
    token, launch operation, engine object, command receipt and custody state", and the
    uncertain half of that had no visitor: the expiry scan selects overdue tokens, and an
    interrupted launch leaves an outstanding token whose activation was admitted and never
    settled, usually well inside its deadline.

    WHAT THIS DOES, and the boundary is deliberately narrow:

      * `tokens.unresolved` answers the set, with the execution, operation, launch,
        container and deadline the token itself recorded. That is the exact reference
        REC-4 requires an unknown to carry.
      * For each one, the engine is asked ONE bounded question -- does the container this
        generation bound still exist, and what is it -- through the same `observe` verb
        the reclaim already uses. Outside every transaction.
      * The answer is REPORTED and the hold is RETAINED. Nothing here attaches, returns,
        revokes, stops or dispatches.

    WHY IT DOES NOT ATTACH, which is the part worth stating rather than discovering.
    `attempts.reconcile_runtime` is the accepted act that attaches an execution, and it
    requires a DELIVERY-SCOPED adapter: its `list` compares the engine's reported image
    against the exact image that delivery resolved, which this lean reclaim adapter has no
    way to know. Handing it an adapter that skipped that comparison would be a second,
    weaker spelling of a boundary that exists to stop a stale image being adopted on
    matching labels alone. So the observation stays here and the ATTACHMENT stays with the
    worker path that holds the delivery -- `tools/single_worker.py`'s own restart branch,
    which already reconciles from `start-requested`. This pass makes that path's work
    discoverable and keeps the resource held until then.

    AND POSITIVE ATTACHMENT WOULD NOT BE A SETTLEMENT ANYWAY. Finding the container alive
    says nothing about whether the launch this manager never saw return completed, and it
    is not permission to dispatch again; the activation stays unsettled, which is what
    keeps the resource held. An `absent` answer is likewise not an ending: the accepted
    ending for a proved non-launch is `intake.authorize_failed_start_cleanup`, which needs
    the failed-start record this cut may never have written. Both are reported.

    BOUNDED AND FAIR, with its own rotation cursor, and per-attempt fault isolation: an
    engine that cannot be asked about one execution leaves the others visited.
    """
    found = []
    visited = set()
    for row in _after(_governed_rows(control, governance),
                      resumed[0])[:_RECLAIM_CANDIDATES]:
        resumed[0] = row["runtime_attempt_id"]
        try:
            domain = tokens.domain_of("workspace", governance.identity(row))
        except ContractRefusal:
            continue
        # ONE DOMAIN IS REPORTED ONCE. W275776 review 2026-09-27T11-52-29Z: serial attempts
        # over one retained resource share a domain, so the discovery can reach the same
        # generation through several rows -- and reporting it once per row would be the same
        # unknown said several times.
        if domain in visited:
            continue
        visited.add(domain)
        for held in tokens.unresolved(control, domain):
            report = {"domain": held["domain"], "generation": held["generation"],
                      "execution": held["execution"],
                      "operation": held["operation"], "launch": held["launch"],
                      "container": held["container"],
                      "expires_at": held["expires_at"],
                      "expired": held["expired"],
                      # W275776 R2: WHICH CUT THIS IS, carried from the token's own record.
                      # `bound-not-admitted` and `admitted-unsettled` are different unknowns
                      # -- an inert created container against one that may be running -- and
                      # an operator reading this report needs to be told which.
                      "cut": held["cut"], "held": True}
            if held["container"] is None:
                # NOTHING TO ASK ABOUT BY ID. The launch is journalled and no container
                # identity was ever bound, so there is no engine object to observe -- the
                # hold is the whole answer.
                found.append(dict(report, observation="no-container-bound"))
                continue
            try:
                answered = adapter.observe(held["container"])
            except (KeyboardInterrupt, SystemExit):
                raise
            except ContractRefusal as refusal:
                # `uncertain` IS THIS MODULE'S EXISTING WORD for "this manager could not
                # establish what exists", and `_ReclaimAdapter` already answers it for
                # everything unrecognised. Measured while writing the cases: an
                # unreachable engine never reaches these branches at all because the
                # adapter converts the fault into that answer itself -- so inventing a
                # second word here would have described the same state two ways.
                found.append(dict(report, observation="uncertain",
                                  why=refusal.message))
                continue
            except Exception as fault:                     # noqa: BLE001
                found.append(dict(report, observation="uncertain",
                                  why=f"the engine could not be asked: {fault!r}"))
                continue
            observed = dict(report, observation=answered.get("state", "uncertain"),
                            why=answered.get("why"))
            # W275776 R2: AND A CONTRADICTION IS SAID OUT LOUD RATHER THAN AVERAGED AWAY.
            #
            # The attempt row may name a DIFFERENT runtime than the one this generation's
            # token authorized. OBSERVED, AND DELIBERATELY NOT ENDORSED HERE:
            # `reconcile_runtime` today attaches whichever container carries the attempt's
            # complete label set, which a probe of mine measured after expecting a refusal.
            # W275776 reviews 2026-09-27T11-52-29Z and 12-00-40Z are explicit that measuring
            # that behaviour is NOT authority to substitute a container bound to another token
            # identity, and no predecessor acceptance covers such a substitution. So this code
            # takes no position on whether the attachment is right; it only reports that the
            # two names disagree.
            #
            # Either way the two names disagree, and the disagreement matters: the resource's
            # stop and expiry path acts on the BOUND container while the attempt's own
            # ending acts on the attached one. So it is reported, and the hold stands. The
            # review's instruction is exactly this -- a contradictory observation is held,
            # never resolved by picking one.
            # AND THE ATTACHMENT IS THE TOKEN OWNER'S OWN, not the discovery row's.
            #
            # W275776 review 2026-09-27T11-52-29Z [P2], reproduced and confirmed: this read
            # `row["runtime_id"]`, and a row is only how the DOMAIN was discovered. A
            # historical attempt over the same retained resource carries its own old runtime,
            # so the report named the current execution and its correct bound container while
            # claiming a contradiction taken from somebody else's row -- a false actionable
            # contradiction, which is worse than none. The owner is the execution the TOKEN
            # names, and it is read here rather than assumed to be the row in hand.
            try:
                owner = attempts._require_attempt(control, held["execution"])
            except ContractRefusal as refusal:
                observed["attachment"] = "unreadable"
                observed["attachment_why"] = refusal.message
                found.append(observed)
                continue
            attached = owner["runtime_id"]
            if attached is not None and attached != held["container"]:
                observed["contradicts_binding"] = attached
            found.append(observed)
    return found


def _after(candidates, attempt_id):
    """The candidates in order, ROTATED to continue after the last one visited.

    Ordered by attempt identity so the rotation is stable across ticks and across
    restarts -- a fresh process begins at the start again, which is a sweep beginning
    at the start rather than a resource being skipped.
    """
    if attempt_id is None:
        return candidates
    for index, row in enumerate(candidates):
        if row["runtime_attempt_id"] > attempt_id:
            return candidates[index:] + candidates[:index]
    # EVERY CANDIDATE SORTS AT OR BEFORE THE LAST ONE VISITED, so the rotation has
    # come round: the next tick starts from the beginning again.
    return candidates


def _governed_rows(control, governance):
    """Every attempt row this manager recorded with a pinned boundary object.

    W275776: the ROW DISCOVERY both halves of recovery share, split out of
    `_governed_candidates` so the overdue half keeps its own eligibility question and the
    uncertain half can ask a different one over the same rows. The query is unchanged and
    the ordering is still by identity, which is what makes both rotations stable.
    """
    del governance
    return list(attempts._attempts(
        control,
        "WHERE workspace_device IS NOT NULL AND workspace_inode IS NOT NULL "
        "ORDER BY runtime_attempt_id"))


def _governed_candidates(control, governance):
    """The attempts whose GOVERNED TOKEN is still outstanding, and only those.

    Review 17:27:42Z corrected the query twice over. `WHERE runtime_id IS NOT NULL`
    was wrong in both directions: it swept every historically attached attempt,
    including ones whose resource was returned long ago, and it SKIPPED an attempt
    whose launch is unresolved precisely because no container was ever attached --
    which is the case an expiry sweep most needs to reach, since an unresolved launch
    may be writing right now.

    So the candidates are chosen by the TOKEN rather than by the runtime column: an
    attempt is a candidate when its own generation is outstanding and unreturned. The
    pinned boundary identity is required, because an attempt with no workspace object
    names no resource; that is a refusal inside `workspace_identity` rather than a
    silent skip, so it is asked here where the answer is a candidacy decision.
    """
    candidates = []
    for row in _governed_rows(control, governance):
        # W275774 review 17:35:44Z: ONLY THE ABSENCE OF A RESOURCE IDENTITY IS
        # SWALLOWED HERE. `overdue` already answers `None` when this attempt reserved
        # no generation, so catching every refusal as "no reservation" was hiding
        # INTEGRITY failures -- a signature that no longer verifies, a record whose
        # owner changed -- behind a candidacy decision. Those must reach the caller.
        try:
            identity = governance.identity(row)
        except ContractRefusal:
            # No pinned workspace object: this attempt names no resource, so it is
            # not a candidate and nothing is wrong.
            continue
        del identity
        outstanding = governance.overdue(
            control, row, operation=attempts._start_operation_id(row))
        if outstanding is not None:
            candidates.append(row)
    # EVERY CANDIDATE IS LISTED, and the CAP IS APPLIED AFTER ROTATION rather than by
    # stopping this scan. Listing is database reads over this manager's own attempts;
    # the expensive part of a tick is the engine, and that is what the cap bounds.
    return candidates


def _emit(document, stream):
    json.dump(document, stream, indent=2, sort_keys=False, ensure_ascii=False)
    stream.write("\n")
    return 0


def _submit(taken, clock, stream):
    with _job_store(taken, clock) as store:
        return _emit(submit(store, read_submission(_read(taken.document))),
                     stream)


def _status(taken, clock, stream):
    # W85500 review 2026-09-04T14-27-54Z [P1]: AN EXPLICIT REQUEST IS NEVER
    # SILENTLY DOWNGRADED.
    #
    # `--observe` reconstructs this attempt's launch and exchange files, and
    # `launch.adopt` needs the workspace group the CONTROL STORE holds -- so
    # there is nothing an observation factory can read without one. The earlier
    # form returned `Unobserved()` before it looked at the operand at all, so
    # an operator who asked for observation got a successful run, `exchange:
    # null`, and no indication whatever that the request had not been
    # performed. That is the same shape as the defect this Work exists to
    # correct: a surface reporting an absence it never went to look for.
    #
    # REFUSED RATHER THAN QUIETLY HONOURED SOME OTHER WAY. The operand names a
    # deployment factory; making it work without a control store would mean
    # inventing a second composition nobody reviewed.
    if taken.observe is not None and taken.control is None:
        raise SystemExit(
            "--observe reconstructs this attempt's durable launch and "
            "exchange files and needs --control to do it: the workspace group "
            "it adopts against lives in the Worker Manager control store. "
            "Rerun with --control, or drop --observe and accept "
            "`exchange: null`, which means nobody looked.")
    with _job_store(taken, clock) as store:
        if taken.control is None:
            # NO CONTROL STORE IS A LEGITIMATE ANSWER, and the projection
            # marks itself as unobserved rather than reporting a pipeline
            # nobody looked at.
            return _emit(status(store, Unobserved(), observed_at=clock()),
                         stream)
        with ControlStore.open(taken.control, incarnation=taken.incarnation,
                               clock=clock) as control:
            if taken.observe is None:
                return _emit(status(store, _ReadOnly(control),
                                    observed_at=clock()), stream)
            # W85500: THE DURABLE EXCHANGE READER, AND NOTHING ELSE.
            #
            # `_ReadOnly` always answered `exchange: null` because it had no
            # way to look, and the terminal a worker wrote was therefore
            # invisible to the one command an operator runs. The file is on
            # disk; the reader was never supplied.
            #
            # THE FACTORY IS RELEASED WHATEVER HAPPENS, exactly as `serve`
            # releases its own. An observation factory opens far less than a
            # serving one, but "far less" is not "nothing" and this tool does
            # not go looking for what it was.
            observed = _observation_from(taken.observe, store, control)
            try:
                return _emit(status(store, _Observing(control, observed),
                                    observed_at=clock()), stream)
            finally:
                _release(observed, stream)


class _Observing:
    """`_ReadOnly` plus ONE durable-file read, and still no act.

    W85500. THE ONE THING IT ADDS is the exchange observation, which is a read
    of files a worker wrote and this manager's launch delivery named. It
    remains read-only in the sense that matters: it issues no offer, takes no
    claim, applies no canonical ending, and -- the one this Work had to be
    careful about -- performs NO RUNTIME REFRESH.

    WHY THE RUNTIME AXIS IS DELIBERATELY LEFT STALE HERE. Refreshing it means
    `reconcile_runtime`, which RECORDS what it saw; a status command that did
    that would be a read that mutates the control store. So the runtime axis
    in a status document is exactly as fresh as the serving loop that last
    advanced the store, and a store nobody is advancing reports what nobody
    advanced. That is the honest answer, and it is why this class inherits
    `refresh_runtime` answering `None` rather than being given a capability.
    """

    canonical = True

    def __init__(self, control, observed):
        self._operations = ManagerOperations(
            control, None, mint_bearer=_refuses, deliver_bearer=_refuses,
            observe_exchange=_exchange_read(observed),
            # W126558: AND THE OTHER READ, BY NAME AND ONLY IF IT IS THERE.
            # An observation factory composed before this member existed is
            # still a complete one -- an integration read it does not have is
            # a deployment with no integration to observe, which is exactly
            # what `None` says. Taken by name for `_exchange_read`'s reason:
            # passing the object would hand this composition whatever else it
            # happened to carry.
            observe_integration=_integration_read(observed))

    def canonical_operation(self, act, offer_id):
        return self._operations.canonical_operation(act, offer_id)

    def receipt_of(self, operation_id):
        return self._operations.receipt_of(operation_id)

    def observe(self, stage):
        return self._operations.observe(stage)

    def refresh_runtime(self, stage):
        """Never. See the class docstring: this one would WRITE."""
        return None


def _exchange_read(observed):
    """The one member an observation factory is allowed to contribute.

    Taken by NAME from the object rather than accepting the object itself as a
    capability: a factory that also carried a dispatch or an ending would hand
    those to `ManagerOperations` if the whole object were passed through, and
    the point of this composition is that it cannot.
    """
    read = getattr(observed, "observe_exchange", None)
    if read is None:
        raise SystemExit(
            "--observe names a factory whose object has no observe_exchange; "
            "an observation surface that cannot read the exchange is the "
            "default this operand exists to replace")
    return read


def _integration_read(observed):
    """The optional second member an observation factory may contribute.

    OPTIONAL WHERE THE EXCHANGE READ IS REQUIRED, and the difference is the
    whole compatibility rule: `--observe` exists to read the exchange, so a
    factory that cannot is the default this operand replaces; an integration
    read is a later capability, and a factory composed without one keeps its
    exact previous behaviour rather than becoming invalid.

    IT GAINS NOTHING ELSE. This surface still performs no refresh and no
    serving act; what it adds is one more read of what a deployment already
    knows.
    """
    return getattr(observed, "observe_integration", None)


def _observation_from(name, store, control):
    """Import exactly the observation factory the operator named.

    Separate from `_operations_from` because the two are different authorities
    and reusing one name for both would let a `status --observe` be handed a
    serving factory -- which opens an Authority session and carries mint,
    dispatch, ending and pass capabilities that a read must not hold.
    """
    if ":" not in name:
        raise SystemExit(
            f"--observe names an observation factory as module:attribute; "
            f"this is {name!r}")
    where, _, attribute = name.partition(":")
    factory = getattr(importlib.import_module(where), attribute)
    return factory(store, control)


class _ReadOnly:
    """The manager's public READS, with every act refused.

    `status` is a read-only surface and this is what makes that a mechanism
    rather than a promise: the object it is handed cannot issue an offer, take
    a claim, or apply a canonical ending, because it has no method that does.

    WHAT THAT COSTS, STATED RATHER THAN HIDDEN. A status run reports the
    pipeline as this store has RECORDED it, plus the canonical observation of
    each stage's current episode. An offer that ended after the last sweep is
    canonically over and not yet recorded here, so the stage still reads
    `offered` until a serving reconciler attaches and applies it. A serving
    deployment is therefore at most one tick behind; a store nobody is
    advancing is exactly as behind as "nobody looked", which is the honest
    answer for a read-only view of it.
    """

    canonical = True

    def __init__(self, control):
        # NO PORT, because none of the three members below reaches one: the
        # authority is spoken to by acts, and this object has none. Handing it
        # a real session would put a capability inside a read-only surface for
        # nothing to use.
        self._operations = ManagerOperations(
            control, None, mint_bearer=_refuses, deliver_bearer=_refuses)

    def canonical_operation(self, act, offer_id):
        return self._operations.canonical_operation(act, offer_id)

    def receipt_of(self, operation_id):
        return self._operations.receipt_of(operation_id)

    def observe(self, stage):
        return self._operations.observe(stage)

    # NO `attach` AND NO `drain`, and review [P2, 2026-09-03] is why the
    # earlier draft's were removed rather than wired up. Attaching asks the
    # manager to republish canonical state; APPLYING what comes back ends an
    # episode, which is a durable act. A read-only surface performs none, so a
    # status run that attached would either write -- and stop being read-only
    # -- or drain assertions into a handler that ignored them, which is an
    # operator being told a fact was consumed when it was discarded. This
    # object has exactly the members `status` calls, and the serving
    # reconciler is the one consumer that attaches.


def _refuses(*ignored):
    raise ContractRefusal(
        "refused", "capability",
        "the status surface holds no authority capability; reading a status "
        "never mints, delivers or spends one")


def _operations_from(name, store, control):
    """Import exactly the deployment factory the operator named.

    `module:attribute`, and nothing is searched for. A tool that guessed at a
    factory would be choosing which authority the manager acts under.
    """
    if ":" not in name:
        raise SystemExit(
            f"--operations names a deployment factory as module:attribute; "
            f"this is {name!r}")
    where, _, attribute = name.partition(":")
    factory = getattr(importlib.import_module(where), attribute)
    return factory(store, control)


def _release(operations, stream):
    """Give a factory-owned object back whatever it opened, exactly once.

    W76207: a production factory opens an Authority, a credential home and a
    launch home that the two stores' context managers know nothing about, so
    a serve that returned or failed simply leaked them. The factory owns those
    handles, so the factory's object is asked to close them -- this tool does
    not go looking for what they were.

    OPTIONAL BY DESIGN AND SILENT WHEN ABSENT. Most operations objects hold
    nothing to release; requiring the member would make every deployment
    declare a teardown it does not need. A failure while releasing is reported
    and not raised: it must not replace the outcome the run already reached,
    and it must not stop the remaining handles from being released.
    """
    close = getattr(operations, "close", None)
    if close is None:
        return None
    try:
        close()
    except BaseException as failure:
        print(f"the deployment's operations did not release cleanly: "
              f"{type(failure).__name__}: {failure}", file=stream)
    return None


def _serve(taken, clock, stream):
    import signal
    import time

    with _job_store(taken, clock) as store:
        with ControlStore.open(taken.control, incarnation=taken.incarnation,
                               clock=clock) as control:
            # CONSTRUCTION IS INSIDE THE RELEASE, and review [P1] is why the
            # earlier version's comment was a claim the code did not keep: the
            # call sat in FRONT of the `try`, so a factory that opened an
            # Authority and then failed on its next operand returned nothing
            # for `_release` to close.
            #
            # WHAT THIS CAN AND CANNOT DO, stated because the difference
            # matters. It guarantees that an object the factory RETURNED is
            # always released, however this block leaves. It cannot release
            # handles a factory took and then abandoned by raising -- nothing
            # here ever saw them -- so a factory that acquires more than one
            # resource owns cleaning up its own partial construction, and this
            # tool holds it to that rather than pretending to do it for it.
            operations = None
            try:
                operations = _operations_from(taken.operations, store,
                                              control)
                # W183883 REVIEW 2026-09-16T06-00-07Z [C3]: THE SERVING
                # ACKNOWLEDGEMENT, and this is the only place that can give
                # one. `stage_execution.observation_from` builds a reader out
                # of a held configuration; `operations_from` opens the
                # Authority, mints and authorizes five sessions, runs three
                # worker preflights, opens the integration store and activates
                # the pool. So a status document published by the OBSERVER
                # says nothing about whether a serving process initialized --
                # a manager stopped before initialization coexists happily
                # with an observer reading a valid empty store, which is
                # exactly what a stopped process proved. The loop therefore
                # says so itself, once, after initialization and before it
                # serves anything.
                #
                # ON STDERR. Stdout is this tool's machine-readable report, and
                # a diagnostic line in front of it would not be one. Nothing
                # else about this command changes.
                print(f"serving initialization complete: "
                      f"incarnation={taken.incarnation!r} "
                      f"operations={taken.operations!r}",
                      file=sys.stderr, flush=True)
                running = [True]

                def stop(number, frame):
                    # POLITE, AND ONCE. The tick in flight finishes and its
                    # receipts are written; a loop that died mid-act would
                    # leave exactly the performed-but-unrecorded window
                    # reconciliation exists to close, for no reason.
                    running[0] = False

                signal.signal(signal.SIGINT, stop)
                signal.signal(signal.SIGTERM, stop)
                if taken.once:
                    return _emit(reconcile(store, operations, now=clock()),
                                 stream)
                # W275774: AND THE EXPIRY PASS IS SUPPLIED, not defaulted away.
                # A deployment whose factory composes its own pass wins, because it
                # may know more about its adapters than this tool does; otherwise
                # this tool's own lean pass is used.
                return _emit(serve(store, operations, clock=clock,
                                   sleep=time.sleep,
                                   should_continue=lambda: running[0],
                                   interval=taken.interval,
                                   reclaim=getattr(operations, "reclaim", None)
                                   or _reclaiming(control, taken.engine,
                                                  _engine_runner,
                                                  taken.custodian_image)), stream)
            finally:
                if operations is not None:
                    _release(operations, stream)


def main(argv, *, clock=None, stream=None):
    import argparse

    parser = argparse.ArgumentParser(
        prog="job_manager",
        description="Submit Jobs to the v12 Job manager, read its status, or "
                    "run its control loop.")
    parser.add_argument("--store", required=True,
                        help="the Job store's path; there is no default, and "
                             "one inside the checkout is what the external "
                             "state root exists to prevent")
    parser.add_argument("--incarnation", required=True,
                        help="this process's incarnation, which is what "
                             "restart recovery distinguishes managers by")
    # W83781: REQUIRED ON EVERY COMMAND, and deliberately not defaulted. Every
    # episode identity this store ever opens is derived in this Authority's
    # namespace; a default would be one operator's store deriving identities
    # in a namespace nobody chose, which is the collision this operand exists
    # to remove.
    parser.add_argument("--authority-uuid", required=True,
                        help="the 32-lowercase-hex Authority this Job store "
                             "belongs to; it namespaces every episode "
                             "identity the store derives, is persisted on "
                             "first open, and a later open naming another one "
                             "refuses without changing the store")
    commands = parser.add_subparsers(dest="command", required=True)

    submitting = commands.add_parser(
        "submit", help="record one versioned multi-Job submission")
    submitting.add_argument("--document", required=True,
                            help="the submission JSON, or - for stdin")
    submitting.set_defaults(run=_submit)

    reading = commands.add_parser(
        "status", help="print the read-only status projection")
    reading.add_argument("--control", default=None,
                         help="the Worker Manager control store; without it "
                              "the projection reports canonical=false rather "
                              "than an empty pipeline, and with one that is "
                              "driving another Job store it refuses rather "
                              "than projecting that store's offers as these "
                              "Jobs'")
    reading.add_argument("--observe", default=None,
                         help="an observation-only deployment factory as "
                              "module:attribute, which reconstructs this "
                              "attempt's durable launch and exchange files so "
                              "the projection can report a worker's terminal; "
                              "without it the exchange is reported as null, "
                              "which is 'nobody looked' rather than 'nothing "
                              "happened'. It opens no Authority and carries "
                              "no act, and it does not refresh the runtime "
                              "axis -- that is the serving loop's, because "
                              "reconciling records what it saw")
    reading.set_defaults(run=_status)

    serving = commands.add_parser(
        "serve", help="run the persistent control loop")
    serving.add_argument("--control", required=True,
                         help="the Worker Manager control store; each act is "
                              "proved against this Job store's own intent, so "
                              "one already driving another Job store refuses "
                              "instead of being adopted")
    serving.add_argument("--operations", required=True,
                         help="module:attribute of the deployment factory "
                              "called with (job_store, control_store)")
    serving.add_argument("--interval", type=int, default=5,
                         help="seconds between ticks")
    serving.add_argument("--once", action="store_true",
                         help="recover and sweep exactly once, then stop")
    serving.add_argument("--engine", default="docker",
                         help="the OCI engine this deployment's expiry pass asks "
                              "to stop and inspect an overdue runtime")
    serving.add_argument("--custodian-image", default=None,
                         help="the custodian image digest the expiry pass normalizes "
                              "a reclaimed attempt's roots with; without it a "
                              "reclaimed resource is revoked and stopped but its "
                              "roots are not accounted for, so it stays held")
    serving.set_defaults(run=_serve)

    taken = parser.parse_args(argv)
    return taken.run(taken, clock or _utc_clock(),
                     stream if stream is not None else sys.stdout)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
