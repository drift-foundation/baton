"""Durable pooled worker selection for Job stage episodes.

W71877.  A logical worker is scheduler capacity, not a process or provider
session.  This module records the immutable pool generation and reserves that
capacity before the Worker Manager is asked to issue an offer.  Runtime,
offer, claim, output and cleanup state remain owned by the Worker Manager.
"""

import json

from ..contracts import ContractRefusal, canonical_text, digest
from ..contracts.errors import name_value
from ..worker_manager import boundaries
from .store import job_signature

__all__ = ["ALLOCATION_STATES", "LANES", "POOL_SCHEMA",
           "SEPARATION_CLASSES", "PooledManagerOperations", "activate_pool",
           "active_generation", "allocation_of", "allocation_refusal_of", "allocation_rows",
           "own_pool", "pool_workers", "reconcile_allocations", "release",
           "require_recovery", "reserve"]

POOL_SCHEMA = "baton.v12.worker-pool/1"
LANES = ("implementation", "review")
SEPARATION_CLASSES = ("provider-diverse", "same-provider/different-model",
                      "same-provider/same-model-fresh-context")
ALLOCATION_STATES = ("reserved", "recovery-required", "released")
POOL_MEMBERS = ("schema", "variant", "separation_class", "workers")
WORKER_MEMBERS = ("worker_id", "lane", "participant", "profile_name",
                  "profile_digest", "eligible_kinds")
SELECTION_OUTCOMES = ("initial", "preferred", "fallback")
LIVE_STATES = ("reserved", "recovery-required")
RELEASE_ENDINGS = frozenset({"abandoned-after-restart", "declined", "expired",
                             "claim-refused", "settlement-expired"})


def _refuse(message, *, durable=False):
    raise ContractRefusal("integrity", "schema", message, durable=durable)


def _unique(values, what):
    if len(set(values)) != len(values):
        _refuse(f"a worker pool names one {what} per worker; duplicate "
                f"{what} values are not distinct capacity")


def own_pool(document):
    """Own one closed pool document; principals arrive from deployment."""
    taken = boundaries.document(document, "a worker pool",
                                required=POOL_MEMBERS)
    if taken["schema"] != POOL_SCHEMA:
        _refuse(f"a worker pool is {name_value(POOL_SCHEMA)}; this is "
                f"{name_value(taken['schema'])}")
    variant = boundaries.text(taken["variant"], "a pool variant")
    separation = taken["separation_class"]
    if separation not in SEPARATION_CLASSES:
        _refuse(f"a pool separation class is one of "
                f"{', '.join(SEPARATION_CLASSES)}; this is "
                f"{name_value(separation)}")
    workers = taken["workers"]
    if type(workers) is not list or not workers:
        _refuse("a worker pool carries a non-empty workers list")
    owned = []
    for entry in workers:
        worker = boundaries.document(entry, "a configured worker",
                                     required=WORKER_MEMBERS)
        worker_id = boundaries.identity(worker["worker_id"], "a worker id")
        lane = worker["lane"]
        if lane not in LANES:
            _refuse(f"worker {name_value(worker_id)} names lane "
                    f"{name_value(lane)}; a lane is implementation or review")
        participant = boundaries.text(worker["participant"],
                                      "a worker participant")
        profile_name = boundaries.text(worker["profile_name"],
                                       "a worker profile name")
        profile_digest = boundaries.text(worker["profile_digest"],
                                         "a worker profile digest")
        kinds = worker["eligible_kinds"]
        if type(kinds) is not list or not kinds:
            _refuse(f"worker {name_value(worker_id)} needs at least one "
                    f"eligible stage kind")
        allowed = []
        for kind in kinds:
            if kind not in ("implementation", "review", "integration"):
                _refuse(f"worker {name_value(worker_id)} names unknown stage "
                        f"kind {name_value(kind)}")
            expected_lane = "review" if kind == "review" else "implementation"
            if lane != expected_lane:
                _refuse(f"worker {name_value(worker_id)} is in {lane} lane but "
                        f"names {kind} eligibility; lanes are immutable")
            if kind in allowed:
                _refuse(f"worker {name_value(worker_id)} repeats eligible kind "
                        f"{name_value(kind)}")
            allowed.append(kind)
        owned.append({"worker_id": worker_id, "lane": lane,
                      "participant": participant,
                      "profile_name": profile_name,
                      "profile_digest": profile_digest,
                      "eligible_kinds": sorted(allowed)})
    _unique([one["worker_id"] for one in owned], "worker id")
    _unique([one["participant"] for one in owned], "participant")
    return {"schema": POOL_SCHEMA, "variant": variant,
            "separation_class": separation,
            "workers": sorted(owned, key=lambda one: one["worker_id"])}


def _principals(principals, workers):
    if type(principals) is not dict:
        _refuse("pool activation needs deployment-resolved principals keyed "
                "by configured participant")
    wanted = {one["participant"] for one in workers}
    if set(principals) != wanted:
        _refuse("pool activation's resolved-principal keys must exactly match "
                "the configured participants")
    return {participant: boundaries.text(principals[participant],
                                          "a canonical principal")
            for participant in sorted(wanted)}


def active_generation(store):
    row = store._connection.execute(
        "SELECT * FROM pool_generations ORDER BY generation DESC LIMIT 1"
    ).fetchone()
    return dict(row) if row is not None else None


def pool_workers(store, generation=None):
    if generation is None:
        active = active_generation(store)
        if active is None:
            return []
        generation = active["generation"]
    return [dict(row) for row in store._connection.execute(
        "SELECT * FROM pool_workers WHERE generation = ? ORDER BY worker_id",
        (generation,))]


def _required_workers(store):
    active = active_generation(store)
    if active is None:
        return []
    rows = {(row["generation"], row["worker_id"]): row
            for row in pool_workers(store, active["generation"])}
    for allocation in store._connection.execute(
            "SELECT DISTINCT generation, worker_id FROM stage_allocations "
            "WHERE allocation_state IN ('reserved', 'recovery-required')"):
        key = (allocation["generation"], allocation["worker_id"])
        if key not in rows:
            row = store._connection.execute(
                "SELECT * FROM pool_workers WHERE generation = ? "
                "AND worker_id = ?", key).fetchone()
            if row is None:
                _refuse(f"live allocation names missing pool worker "
                        f"{name_value(key[1])} in generation {key[0]}")
            rows[key] = dict(row)
    return [rows[key] for key in sorted(rows)]


def activate_pool(store, document, resolved_principals):
    """Activate or reattach one immutable generation.

    Repeating the ACTIVE document revalidates every Authority-resolved
    principal and returns the same generation.  A different document creates
    the next generation; live allocations remain bound to their old rows.

    RETURNING DELIBERATELY TO A HISTORICAL VARIANT CREATES A NEW GENERATION,
    and W71877's review [P2] is why.  The digest identifies the immutable
    CONFIGURATION; it is not the identity of the act of activating it.  While
    it was also the operation identity, activating the primary document again
    after a fallback answered generation 1 and left generation 2 active --
    which reads as "the primary is back" while every new reservation still
    goes to the fallback.

    The two questions are separated here.  The operation identity counts how
    many generations already carry this digest, minus the live one when the
    live one IS this document.  An exact retry of the activation that is
    currently active therefore replays, and a deliberate return to a
    configuration that is not active is a new act with a new identity and a
    new generation.
    """
    pool = own_pool(document)
    principals = _principals(resolved_principals, pool["workers"])
    pool_digest = digest(pool)
    active = active_generation(store)
    live_is_this = active is not None and active["digest"] == pool_digest
    carried = store._connection.execute(
        "SELECT COUNT(*) FROM pool_generations WHERE digest = ?",
        (pool_digest,)).fetchone()[0]
    operation_id = ("pool.activate:" + pool_digest[7:] + ":"
                    + str(carried - (1 if live_is_this else 0)))
    signature = job_signature(
        "pool.activate", {"pool": pool, "resolved_principals": principals})
    if live_is_this:
        rows = list(store._connection.execute(
            "SELECT participant, canonical_principal FROM pool_workers "
            "WHERE generation = ? ORDER BY participant",
            (active["generation"],)))
        held = {row["participant"]: row["canonical_principal"] for row in rows}
        if held != principals:
            _refuse("the persisted pool generation resolves a participant to "
                    "another canonical principal; attachment refuses rather "
                    "than rewriting capacity identity")

    def perform(connection):
        # RE-READ UNDER THE LOCK, because the selection above is a pre-lock
        # observation: another manager may have activated something between
        # that read and this transaction, and the ACTIVE generation is what
        # decides whether this call is a revalidation or a new act.
        found = connection.execute(
            "SELECT * FROM pool_generations ORDER BY generation DESC LIMIT 1"
        ).fetchone()
        if found is not None and found["digest"] == pool_digest:
            generation = found["generation"]
            rows = list(connection.execute(
                "SELECT participant, canonical_principal FROM pool_workers "
                "WHERE generation = ? ORDER BY participant", (generation,)))
            held = {row["participant"]: row["canonical_principal"]
                    for row in rows}
            if held != principals:
                _refuse("the persisted pool generation resolves a participant "
                        "to another canonical principal; attachment refuses "
                        "rather than rewriting capacity identity")
            return _generation_document(found)
        generation = connection.execute(
            "SELECT COALESCE(MAX(generation), 0) + 1 FROM pool_generations"
        ).fetchone()[0]
        activated_at = store._now()
        connection.execute(
            "INSERT INTO pool_generations (generation, variant, "
            "separation_class, document, digest, activated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (generation, pool["variant"], pool["separation_class"],
             canonical_text(pool), pool_digest, activated_at))
        for worker in pool["workers"]:
            connection.execute(
                "INSERT INTO pool_workers (generation, worker_id, lane, "
                "participant, canonical_principal, profile_name, "
                "profile_digest, eligible_kinds) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (generation, worker["worker_id"], worker["lane"],
                 worker["participant"], principals[worker["participant"]],
                 worker["profile_name"], worker["profile_digest"],
                 canonical_text(worker["eligible_kinds"])))
        return {"generation": generation, "variant": pool["variant"],
                "separation_class": pool["separation_class"],
                "digest": pool_digest, "activated_at": activated_at}

    return store.transact(operation_id, "pool.activate", signature, perform)


def _generation_document(row):
    return {member: row[member] for member in
            ("generation", "variant", "separation_class", "digest",
             "activated_at")}


def allocation_rows(store, stage_id=None):
    sql = ("SELECT allocation.*, generation.variant, "
           "generation.separation_class, generation.digest AS generation_digest, "
           "worker.profile_name AS worker_profile_name, "
           "worker.profile_digest AS worker_profile_digest "
           "FROM stage_allocations allocation "
           "JOIN pool_generations generation USING (generation) "
           "JOIN pool_workers worker ON worker.generation = allocation.generation "
           "AND worker.worker_id = allocation.worker_id")
    operands = ()
    if stage_id is not None:
        sql += " WHERE allocation.stage_id = ?"
        operands = (stage_id,)
    sql += " ORDER BY allocation.reserved_at, allocation.assignment_id"
    return [dict(row) for row in store._connection.execute(sql, operands)]


def allocation_of(store, assignment_id):
    row = store._connection.execute(
        "SELECT allocation.*, generation.variant, "
        "generation.separation_class, generation.digest AS generation_digest, "
        "worker.profile_name AS worker_profile_name, "
        "worker.profile_digest AS worker_profile_digest "
        "FROM stage_allocations allocation "
        "JOIN pool_generations generation USING (generation) "
        "JOIN pool_workers worker ON worker.generation = allocation.generation "
        "AND worker.worker_id = allocation.worker_id "
        "WHERE allocation.assignment_id = ?",
        (assignment_id,)).fetchone()
    return dict(row) if row is not None else None


def allocation_refusal_of(store, assignment_id):
    row = store._connection.execute(
        "SELECT state, refusal FROM operations WHERE operation_id = ?",
        ("allocation.reserve:" + assignment_id,)).fetchone()
    return (None if row is None or row["state"] != "refused"
            else json.loads(row["refusal"]))


def _lane(kind):
    return "review" if kind == "review" else "implementation"


def _exclusions(connection, stage, excluded):
    excluded = excluded or {}
    worker_ids = set(excluded.get("worker_ids", ()))
    participants = set(excluded.get("participants", ()))
    principals = set(excluded.get("principals", ()))
    if stage["kind"] == "review":
        for row in connection.execute(
                "SELECT allocation.* FROM stage_allocations allocation "
                "JOIN stages producer ON producer.stage_id = allocation.stage_id "
                "WHERE producer.job_id = ? AND producer.kind = 'implementation'",
                (stage["job_id"],)):
            worker_ids.add(row["worker_id"])
            participants.add(row["participant"])
            principals.add(row["canonical_principal"])
    return worker_ids, participants, principals


def reserve(store, stage, *, excluded=None):
    """Reserve one eligible worker before the offer side effect."""
    assignment_id = boundaries.identity(stage["attempt_id"],
                                        "a stage assignment id")
    existing = allocation_of(store, assignment_id)
    if existing is not None:
        if existing["allocation_state"] == "released":
            _refuse(f"stage assignment {name_value(assignment_id)} already "
                    "has a released allocation and cannot be reserved again",
                    durable=True)
        return existing
    operation_id = "allocation.reserve:" + assignment_id
    signature = job_signature(
        "allocation.reserve", {"assignment_id": assignment_id,
                               "stage_id": stage["stage_id"],
                               "episode": stage["episode"]})

    def perform(connection):
        generation = connection.execute(
            "SELECT generation FROM pool_generations ORDER BY generation DESC "
            "LIMIT 1").fetchone()
        if generation is None:
            raise ContractRefusal("refused", "precondition",
                                  "no worker pool generation is active")
        generation = generation["generation"]
        lane = _lane(stage["kind"])
        workers = [dict(row) for row in connection.execute(
            "SELECT * FROM pool_workers WHERE generation = ? AND lane = ? "
            "AND profile_name = ? AND profile_digest = ? ORDER BY worker_id",
            (generation, lane, stage["profile_name"], stage["profile_digest"]))
            if stage["kind"] in json.loads(row["eligible_kinds"])]
        excluded_workers, excluded_participants, excluded_principals = \
            _exclusions(connection, stage, excluded)
        eligible = [worker for worker in workers
                    if worker["worker_id"] not in excluded_workers
                    and worker["participant"] not in excluded_participants
                    and worker["canonical_principal"] not in excluded_principals]
        if not eligible:
            raise ContractRefusal(
                "policy", "profile-uncertified",
                f"stage {name_value(stage['stage_id'])} has no eligible "
                f"{lane} worker for profile "
                f"{name_value(stage['profile_name'])}/"
                f"{name_value(stage['profile_digest'])} after hard "
                f"independence exclusions", durable=True)
        live = list(connection.execute(
            "SELECT worker_id, canonical_principal FROM stage_allocations "
            "WHERE allocation_state IN ('reserved', 'recovery-required')"))
        occupied_workers = {row["worker_id"] for row in live}
        occupied_principals = {row["canonical_principal"] for row in live}
        available = [worker for worker in eligible
                     if worker["worker_id"] not in occupied_workers
                     and worker["canonical_principal"] not in occupied_principals]
        if not available:
            raise ContractRefusal(
                "refused", "precondition",
                f"stage {name_value(stage['stage_id'])} has eligible {lane} "
                f"workers but every effective worker/principal capacity is "
                f"reserved or recovery-required")
        affinity = connection.execute(
            "SELECT worker_id FROM worker_affinity WHERE development_line = ? "
            "AND lane = ?", (stage["work_id"], lane)).fetchone()
        preferred = affinity["worker_id"] if affinity is not None else None
        selected = next((worker for worker in available
                         if worker["worker_id"] == preferred), available[0])
        outcome = ("initial" if preferred is None else
                   ("preferred" if selected["worker_id"] == preferred
                    else "fallback"))
        reserved_at = store._now()
        connection.execute(
            "INSERT INTO stage_allocations (assignment_id, stage_id, episode, "
            "generation, worker_id, lane, participant, canonical_principal, "
            "preferred_worker_id, selection_outcome, allocation_state, "
            "reserved_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'reserved', ?)",
            (assignment_id, stage["stage_id"], stage["episode"], generation,
             selected["worker_id"], lane, selected["participant"],
             selected["canonical_principal"], preferred, outcome, reserved_at))
        if affinity is None:
            connection.execute(
                "INSERT INTO worker_affinity (development_line, lane, worker_id, "
                "recorded_at) VALUES (?, ?, ?, ?)",
                (stage["work_id"], lane, selected["worker_id"], reserved_at))
        return allocation_of(store, assignment_id)

    return store.transact(operation_id, "allocation.reserve", signature,
                          perform)


def _move(store, assignment_id, state, reason):
    """One settlement act, always through the journal.

    W71877 review [P2]: this returned early whenever the allocation was
    already in the requested state or already released, BEFORE it built the
    operation signature -- so releasing twice with two different reasons
    answered the first row instead of refusing the changed operand, even
    though `reason` is part of the signature by construction.  A settled
    allocation is exactly where a replay has to be told from a second,
    different act; short-circuiting in front of the journal removed the only
    place that could tell them apart.

    Absence is still absence: there is nothing to move and nothing to record
    when no allocation exists.  Everything else goes to `JobStore.transact`,
    which replays an exact repeat and refuses a changed one.
    """
    allocation = allocation_of(store, assignment_id)
    if allocation is None:
        return None
    operation_id = f"allocation.{state}:{assignment_id}"
    signature = job_signature(
        f"allocation.{state}", {"assignment_id": assignment_id,
                                "reason": reason})

    def perform(connection):
        current = connection.execute(
            "SELECT allocation_state FROM stage_allocations "
            "WHERE assignment_id = ?", (assignment_id,)).fetchone()
        if current is None:
            return allocation_of(store, assignment_id)
        if current["allocation_state"] == "released":
            if state == "released":
                # The same terminal state this act asks for. Reaching here
                # means the journal did not hold this operation, so another
                # act released it: answer the settled row rather than
                # recording a second release of one allocation.
                return allocation_of(store, assignment_id)
            _refuse(f"allocation {name_value(assignment_id)} is released; a "
                    f"released allocation is not quarantined again, and its "
                    f"capacity is already back in circulation")
        if current["allocation_state"] == state:
            return allocation_of(store, assignment_id)
        now = store._now()
        if state == "released":
            connection.execute(
                "UPDATE stage_allocations SET allocation_state = 'released', "
                "released_at = ?, release_reason = ? WHERE assignment_id = ?",
                (now, reason, assignment_id))
        else:
            connection.execute(
                "UPDATE stage_allocations SET allocation_state = "
                "'recovery-required', recovery_required_at = ? "
                "WHERE assignment_id = ?", (now, assignment_id))
        return allocation_of(store, assignment_id)

    return store.transact(operation_id, f"allocation.{state}", signature,
                          perform)


def release(store, assignment_id, reason):
    return _move(store, assignment_id, "released",
                 boundaries.text(reason, "an allocation release reason"))


def require_recovery(store, assignment_id):
    return _move(store, assignment_id, "recovery-required", None)


def reconcile_allocations(store, held=None):
    """Settle scheduler capacity only from canonical episode/runtime facts."""
    moved = []
    held = held or {}
    for allocation in allocation_rows(store):
        if allocation["allocation_state"] not in LIVE_STATES:
            continue
        episode = store._connection.execute(
            "SELECT ended_state FROM episodes WHERE stage_id = ? AND episode = ?",
            (allocation["stage_id"], allocation["episode"])).fetchone()
        if episode is not None and episode["ended_state"] in RELEASE_ENDINGS:
            moved.append(release(store, allocation["assignment_id"],
                                episode["ended_state"]))
            continue
        entry = held.get(allocation["stage_id"])
        if entry is None or entry.get("attempt") is None:
            continue
        observed = entry["observed"]
        runtime = observed.get("runtime") or {}
        cleanup = runtime.get("cleanup")
        if cleanup in ("complete", "retained"):
            moved.append(release(store, allocation["assignment_id"],
                                f"cleanup-{cleanup}"))
        elif cleanup == "failed" or runtime.get("execution_runtime") == "uncertain":
            moved.append(require_recovery(store, allocation["assignment_id"]))
        elif observed.get("start_failure") is not None or \
                observed.get("preparation_failure") is not None:
            moved.append(release(store, allocation["assignment_id"],
                                "launch-failed-before-runtime"))
    return moved


class PooledManagerOperations:
    """The existing manager surface, selecting one participant per allocation."""

    canonical = True

    def __init__(self, store, workers, *, resolved_principals,
                 independence=None):
        """Attach to every worker this store still needs, and prove each one.

        `resolved_principals` IS REQUIRED AND COVERS LIVE PRIOR GENERATIONS,
        which is W71877's review [P1].  `activate_pool` revalidates the ONE
        generation whose document it is handed, and `_required_workers` then
        adds workers from older generations that still hold live allocations.
        Nothing revalidated those.  A claimed allocation from an old
        generation could therefore be launched, dispatched, concluded or
        observed after its endpoint had come to mean another principal, and
        the claim-answer comparison cannot help: that claim was taken before
        the restart.

        So attachment is where every required worker is proved, active or
        not, against the principal the deployment resolves NOW -- and it
        refuses before any stage operation rather than at the first one that
        happens to compare.
        """
        self.store = store
        if type(workers) is not dict or not workers:
            _refuse("pooled operations need worker operations keyed by "
                    "(generation, worker id)")
        self.workers = dict(workers)
        self._independence = independence
        rows = _required_workers(store)
        configured = {(row["generation"], row["worker_id"]) for row in rows}
        if set(self.workers) != configured:
            _refuse("pooled operations must provide exactly the active "
                    "generation and live prior generations' configured "
                    "(generation, worker id) pairs")
        resolved = _principals(
            resolved_principals,
            [{"participant": row["participant"]} for row in rows])
        for row in rows:
            key = (row["generation"], row["worker_id"])
            operation = self.workers[key]
            participant = getattr(getattr(operation, "port", None),
                                  "participant", None)
            if participant != row["participant"]:
                _refuse(f"worker {name_value(row['worker_id'])} is configured "
                        f"for {name_value(row['participant'])} but its "
                        f"participant-bound operations act for "
                        f"{name_value(participant)}")
            if resolved[row["participant"]] != row["canonical_principal"]:
                _refuse(f"worker {name_value(row['worker_id'])} in generation "
                        f"{row['generation']} was reserved under canonical "
                        f"principal {name_value(row['canonical_principal'])} "
                        f"and {name_value(row['participant'])} now resolves to "
                        f"{name_value(resolved[row['participant']])}; "
                        f"attachment refuses before any stage operation "
                        f"rather than acting for another principal")

    def _any(self):
        """Any attached worker, for an answer that is not stage-specific.

        `canonical_operation` derives an operation IDENTITY from an act and an
        offer id, and `receipt_of` asks every attached store.  Neither routes
        work, so neither needs an allocation -- which is exactly the thing
        `_worker` below must not do.
        """
        return self.workers[sorted(self.workers)[0]]

    def _offer_exists(self, stage):
        """Whether the canonical offer for this stage was already issued.

        The same question `binding_intent` already asks, at the same owner:
        the admit receipt is recorded by the Worker Manager when the offer
        commits, so its presence is canonical evidence rather than an
        inference from how a refusal was shaped.
        """
        return self.receipt_of(
            self.canonical_operation("admit", stage["offer_id"])) is not None

    def _allocation(self, stage, *, create=False):
        allocation = allocation_of(self.store, stage["attempt_id"])
        if allocation is None and create:
            excluded = (None if self._independence is None else
                        self._independence(stage))
            allocation = reserve(self.store, stage, excluded=excluded)
        return allocation

    def _reader(self, stage):
        """The worker that can ANSWER ABOUT this stage, or a refusal.

        `observe` and `refresh_runtime` are read-only and one tick asks them
        about every live stage -- including a stage that has not been admitted
        yet, which is how the manager learns that it owes an `admit` at all.
        A stage with no offer has no runtime for any worker to hold, so every
        attached store answers the same not-started document and choosing one
        decides nothing.

        THE MOMENT AN OFFER EXISTS WITHOUT AN ALLOCATION THAT STOPS BEING
        TRUE, and that is exactly the migrated in-flight stage W71877's
        review [P1] names: real work is running somewhere and answering about
        it from an arbitrary store would report another worker's silence as
        this stage's state. That refuses here, with the same words the acting
        operations use.
        """
        allocation = allocation_of(self.store, stage["attempt_id"])
        if allocation is not None:
            return self.workers[(allocation["generation"],
                                 allocation["worker_id"])]
        if self._offer_exists(stage):
            _refuse(self._unallocated(stage))
        return self._any()

    def _unallocated(self, stage):
        return (f"stage {name_value(stage['stage_id'])} has no scheduler "
                f"allocation, so no pooled worker owns it. A stage admitted "
                f"before the scheduler relations existed is recovered or "
                f"stopped through the participant-bound operations that hold "
                f"its offer; this boundary will not choose an endpoint for it")

    def _worker(self, stage):
        """The one worker this stage is reserved on, or a refusal.

        W71877 review [P1]: this fell back to whichever worker sorted first
        when no allocation existed, and `launch`, `dispatch`, `conclude`,
        `observe` and `refresh_runtime` all used it.  That erased
        reserve-before-offer and the participant/generation binding at the
        one seam where they decide which endpoint acts -- and the reviewer's
        reproduction launched an unallocated attempt through that worker.

        IT IS NOT AN ACADEMIC CALLER ERROR.  The 3 -> 4 migration deliberately
        creates EMPTY scheduler relations, so a store carrying an already
        admitted or claimed schema-3 stage arrives here with no allocation at
        all.  The refusal names that case and what to do with it, because a
        migrated in-flight stage has to be stopped or recovered through the
        Worker Manager operations that own its offer -- never run through
        whichever worker this dictionary happens to sort first.
        """
        allocation = allocation_of(self.store, stage["attempt_id"])
        if allocation is None:
            _refuse(self._unallocated(stage))
        return self.workers[(allocation["generation"],
                             allocation["worker_id"])]

    def canonical_operation(self, act, offer_id):
        return self._any().canonical_operation(act, offer_id)

    def receipt_of(self, operation_id):
        answers = [worker.receipt_of(operation_id)
                   for worker in self.workers.values()]
        answers = [answer for answer in answers if answer is not None]
        if not answers:
            return None
        first = answers[0]
        if any(answer != first for answer in answers[1:]):
            _refuse(f"worker control stores disagree about operation "
                    f"{name_value(operation_id)}")
        return first

    def recover(self, *, now):
        reports = [worker.recover(now=now)
                   for _, worker in sorted(self.workers.items())]
        abandoned = sorted({offer_id for report in reports
                            for offer_id in report["abandoned"]})
        recoverable = {}
        for report in reports:
            for offer in report["recoverable"]:
                recoverable[offer["offer_id"]] = offer
        return {"abandoned": abandoned,
                "recoverable": [recoverable[offer_id]
                                for offer_id in sorted(recoverable)]}

    def attach(self, offer_ids):
        attached = []
        for worker in self.workers.values():
            attached.extend(worker.attach(offer_ids))
        return attached

    def drain(self, handlers, *, quiescent=()):
        return sum(worker.drain(handlers, quiescent=quiescent)
                   for worker in self.workers.values())

    def binding_intent(self, stage, job):
        from .delegation import stage_intent
        intent = stage_intent(stage, job)
        allocation = self._allocation(stage)
        if allocation is None:
            operation_id = self.canonical_operation("admit", stage["offer_id"])
            if self.receipt_of(operation_id) is not None:
                raise ContractRefusal(
                    "refused", "operation-collision",
                    f"stage {name_value(stage['stage_id'])} has a canonical "
                    "offer but no scheduler allocation; adopting it would "
                    "erase the reserve-before-offer and participant binding",
                    durable=True)
            return intent
        intent["participant"] = allocation["participant"]
        return intent

    def admit(self, stage, job):
        allocation = self._allocation(stage, create=True)
        worker = self.workers[(allocation["generation"],
                               allocation["worker_id"])]
        try:
            return worker.admit(stage, job)
        except ContractRefusal as refusal:
            if refusal.durable and not self._offer_exists(stage):
                # DURABLE IS NOT "NO OFFER EXISTS", which is W71877's review
                # [P1].  Durability says the refusal is a recorded outcome;
                # `ManagerOperations.admit` commits `issue_offer` BEFORE it
                # invokes the injected bearer delivery, so a durable delivery
                # refusal can arrive with the canonical offer already there.
                # Releasing then lets unrelated work reserve the same logical
                # worker and principal while that offer may still be accepted.
                #
                # The settlement table permits release only on evidence that
                # no assignment exists.  The canonical admit receipt is that
                # evidence read at its owner: absent, no offer was issued and
                # the reservation is safe to return; present, this is the
                # uncertain case below.
                release(self.store, stage["attempt_id"],
                        "offer-durably-refused-before-any-offer")
            elif refusal.durable:
                require_recovery(self.store, stage["attempt_id"])
            raise
        except BaseException:
            # A fault after reserve but before a canonical offer is uncertain,
            # not absence.  Keep it out of circulation until positive recovery
            # evidence decides whether another stage may use this capacity.
            require_recovery(self.store, stage["attempt_id"])
            raise

    def claim(self, stage):
        allocation = self._allocation(stage)
        if allocation is None:
            _refuse(f"stage {name_value(stage['stage_id'])} has an offer but "
                    "no scheduler allocation")
        answer = self.workers[(allocation["generation"],
                               allocation["worker_id"])].claim(stage)
        principal = ((answer or {}).get("decision") or {}).get("principal")
        if principal != allocation["canonical_principal"]:
            require_recovery(self.store, stage["attempt_id"])
            raise ContractRefusal(
                "runtime-observation", "identity-mismatch",
                f"stage {name_value(stage['stage_id'])} reserved principal "
                f"{name_value(allocation['canonical_principal'])} but the "
                f"claim returned {name_value(principal)}; the allocation "
                f"requires explicit recovery", durable=True)
        return answer

    def launch(self, stage, job):
        return self._worker(stage).launch(stage, job)

    def dispatch(self, stage, job):
        return self._worker(stage).dispatch(stage, job)

    def conclude(self, stage, job):
        return self._worker(stage).conclude(stage, job)

    def observe(self, stage):
        return self._reader(stage).observe(stage)

    def refresh_runtime(self, stage):
        return self._reader(stage).refresh_runtime(stage)

    def close(self):
        closed = set()
        for worker in self.workers.values():
            if id(worker) in closed:
                continue
            closed.add(id(worker))
            close = getattr(worker, "close", None)
            if close is not None:
                close()
