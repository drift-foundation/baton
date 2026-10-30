"""W333485: the bounded serving renewal pass, and the permission it may extend.

TOK-9 and section 19 policy 2 under `v12/DESIGN.md`: "The host MAY explicitly
renew a still-unexpired, unrevoked token for the same resource, generation,
operation and execution under the selected bounded policy." The grant authority
is `worker_manager.tokens` and it is unchanged by this module: `tokens.renew` is
the atomic conditional decision, it owns the deadline revision, the replay rule,
the renewal bound and the expiry/ambiguity judgements, and nothing here recomputes
any of them.

WHAT WAS MISSING WAS THE CALLER. Measured on this candidate's base before a line
was written: `grep -rn "tokens.renew" v12/python/src v12/python/tools`
finds the definition, the tests and no production invocation at all -- so every
granted permission in a serving deployment ran to its initial lifetime and then
became the expiry pass's problem, however healthy the execution was. This module
is that caller, and it is deliberately only a caller.

WHY IT LIVES IN THE JOB MANAGER. The decision needs facts from two owners at
once -- the Host Worker Manager's attempt rows and token records, and this
store's own episodes and ending obligations -- and the package that may import
both is this one (the Worker Manager may not import upwards). The DESIGN's
component table puts "eligibility" and "ending obligations" here and "token
ownership" there, which is exactly the split this file composes: this module
asks, `tokens.renew` decides.

THE SELECTED POLICY, PINNED. `SCAN_SECONDS`, `LEAD_SECONDS`, the requested
lifetime and the renewal bound are written down below with their consequences
derived rather than asserted -- see `schedule`. The two token constants are
CONSUMED, not raised: `RENEWAL_SECONDS is tokens.LIFETIME_SECONDS` and
`NOMINAL_RENEWALS is tokens.RENEWAL_LIMIT`.

WHAT THIS PASS WILL NOT DO, each because a requirement says so:

  * No external I/O, at all. Every act here is a read or one short write on one
    of the two stores -- no engine, no filesystem, no subprocess, no provider.
    That is what makes it safe to ask BETWEEN a reclaim's engine calls, which is
    how a 1440-second command allowance is kept from eating a 120-second lead
    (`tools/job_manager.py:_pumping`), and it is why DB-1 is satisfied by
    construction rather than by inspection.
  * No renewal on every scan. A scan that is not within the lead answers
    `not-due` and writes nothing; "renew early because we happen to be looking"
    is how a bounded four-renewal allowance is spent in the first two minutes.
  * No reset of anything on restart. A restarted pass holds no scan history and
    no cached token view: it reads committed state, so a renewal already
    committed is seen as committed and a Job's invocation ceilings are not
    touched by any path here (`execution_limits` is read by its own owner at
    launch preparation and this module writes nothing it reads).
  * No revival. An overdue generation is REFUSED and its expiry is enforced --
    see `_overdue` -- because no scheduling lead can compensate for an outage,
    and a pass that renewed whatever it found late would be exactly the
    "clock adjustment revives the token" TOK-9 forbids.
  * No release of an uncertain runtime, and no extension of a limit, when the
    four-renewal allowance is spent: `exhausted` leaves the existing final
    deadline standing and says so.
"""

from ..contracts import ContractRefusal
from ..contracts.errors import name_value
from ..worker_manager import attempts, boundaries, tokens
from . import ending, episodes, schema

__all__ = ["DECISIONS", "LEAD_SECONDS", "NOMINAL_RENEWALS", "RENEWAL_SECONDS",
           "SCAN_SECONDS", "ServingRenewal", "decide", "job_eligibility",
           "job_refusal", "schedule", "serving_renewal"]

# -- the pinned policy, with its consequences derived ------------------------
#
# SCAN_SECONDS   the floor between two inspections of the eligible set. A floor
#                rather than a cadence: the pass is asked more often than this
#                (every tick, and between a reclaim's engine calls) and answers
#                `scanned: False` until the floor has passed, so the DB cost of
#                being asked often is bounded while the LATENCY of a decision
#                stays small.
# LEAD_SECONDS   how much permission must remain before a renewal is due. It is
#                the budget for everything that can delay a decision: the scan
#                floor, one bounded engine command in the pass that interleaves
#                this one, and the database work around them.
# RENEWAL_SECONDS  what is requested from the host's trusted clock. The token
#                owner's own lifetime, unchanged -- a renewal asking for more
#                than an acquisition would be a token constant raised here.
# NOMINAL_RENEWALS the token owner's bound, consumed rather than restated.
SCAN_SECONDS = 30
LEAD_SECONDS = 120
RENEWAL_SECONDS = tokens.LIFETIME_SECONDS
NOMINAL_RENEWALS = tokens.RENEWAL_LIMIT

# What one candidate's visit can answer, as a closed vocabulary. A reader that
# cannot tell `not-due` from `held` cannot tell a healthy execution from one
# whose permission this manager has stopped being able to extend.
DECISIONS = ("renewed", "replayed", "not-due", "ineligible", "held",
             "exhausted", "expiry-enforced")


def schedule(*, lifetime=RENEWAL_SECONDS, lead=LEAD_SECONDS,
             renewals=NOMINAL_RENEWALS, scan=SCAN_SECONDS):
    """The ladder this policy produces, COMPUTED from the four numbers.

    The figures in the Work's proposal -- renewals due at 780, 1560, 2340 and
    3120 elapsed seconds and a final deadline at 4020 -- are consequences of
    (900, 120, 4), not independent facts to be maintained beside them. So they
    are derived here and asserted in the acceptance suite against the elapsed
    instants a controlled clock actually reaches, which is the difference
    between a pinned guarantee and a comment that used to be true.

    `final_deadline_seconds` is the elapsed second at which permission ends if
    every renewal is taken at the earliest instant the lead allows. It is not a
    promise of useful provider time and it is not a cumulative Job allowance:
    it is one resource permission's last deadline.
    """
    if type(lifetime) is not int or lifetime <= 0:
        raise ContractRefusal("integrity", "schema",
                              f"a renewal lifetime is a positive whole number "
                              f"of seconds; this is {name_value(lifetime)}")
    if type(lead) is not int or lead <= 0 or lead >= lifetime:
        raise ContractRefusal(
            "integrity", "schema",
            f"a renewal lead is a positive whole number of seconds inside the "
            f"lifetime it protects; this is {name_value(lead)} against a "
            f"lifetime of {name_value(lifetime)}")
    if type(renewals) is not int or renewals < 0:
        raise ContractRefusal("integrity", "schema",
                              f"a renewal bound is a whole number of "
                              f"extensions; this is {name_value(renewals)}")
    due, deadlines, deadline = [], [lifetime], lifetime
    for _ in range(renewals):
        due.append(deadline - lead)
        deadline = (deadline - lead) + lifetime
        deadlines.append(deadline)
    return {"lifetime_seconds": lifetime, "lead_seconds": lead,
            "scan_seconds": scan, "renewals": renewals,
            "renews_after_seconds": tuple(due),
            "deadlines_seconds": tuple(deadlines),
            "final_deadline_seconds": deadline}


def protected_seconds(*, engine_seconds, scan=SCAN_SECONDS, lead=LEAD_SECONDS):
    """The lead left over after the worst interleaved delay this composition has.

    THE HONEST ARITHMETIC, and it is the whole latency argument. A serving tick
    is NOT bounded by its interval -- `tools/job_manager.py:135` records a
    command allowance of 3 engine calls x 30 seconds x 16 candidates = 1440
    seconds for the reclaim pass alone -- so a renewal decision taken once per
    pass could not protect even the initial lease. What bounds this pass's
    latency instead is where it is ASKED: before every engine command the
    reclaim issues, with the scan floor as the only thing that can defer it.

    So between two inspections there is at most the floor plus ONE bounded
    engine command, and this answers what remains of the lead after both. It
    deliberately does not pretend to bound the database and ending work around
    those calls: that work is not measured by this module, the margin below is
    what absorbs it, and an outage longer than the whole lead is handled by
    refusing renewal and enforcing expiry rather than by arithmetic.
    """
    if type(engine_seconds) is not int or engine_seconds < 0:
        raise ContractRefusal(
            "integrity", "schema",
            f"a bounded engine command is a whole number of seconds; this is "
            f"{name_value(engine_seconds)}")
    return lead - scan - engine_seconds


# -- the JOB store's own half of eligibility ---------------------------------


def job_refusal(store, attempt_id):
    """None when THIS store's records permit continued permission, else why not.

    ASKED AT THE OWNER'S BOUNDARY. Whether a Job's episode is still the live one,
    whether it ended, and whether a composed ending has been registered for it
    are this store's facts; the Worker Manager cannot answer them and a renewal
    pass that guessed would renew permission for an execution this control plane
    has already finished with.

    UNKNOWN CORRESPONDENCE REFUSES. A control store legitimately carries attempts
    belonging to other Job stores, so "no episode here names this attempt" is an
    ordinary answer -- and it is a REFUSAL rather than a pass, because this
    deployment cannot establish that the execution is still wanted. The honest
    consequence is that the permission runs to its current deadline and the
    expiry path owns it, which is the same outcome as before any renewal existed.
    """
    boundaries.identity(attempt_id, "a runtime attempt id")
    found = [boundaries.row(record, "a persisted stage episode",
                            schema.EPISODE_COLUMNS)
             for record in store._connection.execute(
                 "SELECT * FROM episodes WHERE attempt_id = ? "
                 "ORDER BY stage_id, episode", (attempt_id,)).fetchall()]
    if not found:
        return (f"no episode of this Job store asked for attempt "
                f"{name_value(attempt_id)}; an execution whose correspondence "
                f"this control plane cannot establish is held at its current "
                f"deadline rather than extended")
    if len(found) > 1:
        return (f"{len(found)} episodes name attempt {name_value(attempt_id)}; "
                f"one episode asks for one attempt, and choosing between them "
                f"would be inventing which one this permission serves")
    episode = found[0]
    if episode["ended_state"] is not None:
        return (f"stage {name_value(episode['stage_id'])} episode "
                f"{episode['episode']} ended as "
                f"{name_value(episode['ended_state'])}; an ended episode's "
                f"execution is not extended")
    # AND IT MUST BE THE STAGE'S CURRENT EPISODE. `ended_state IS NULL` on this
    # row and a different live episode on the same stage is the supersession
    # case: a correction opens the successor, and the predecessor's permission
    # is the expiry path's business rather than this pass's.
    live = episodes.live_of(store, episode["stage_id"])
    if live is None or live["episode"] != episode["episode"]:
        return (f"stage {name_value(episode['stage_id'])} is now attempted by "
                f"episode {None if live is None else live['episode']} and this "
                f"attempt belongs to episode {episode['episode']}; a superseded "
                f"episode holds no current assignment generation")
    if ending.intent_of(store, episode["stage_id"],
                        episode["episode"]) is not None:
        return (f"stage {name_value(episode['stage_id'])} episode "
                f"{episode['episode']} has a registered composed ending; the "
                f"obligation to finish it is not a reason to extend it")
    return None


def job_eligibility(store):
    """`job_refusal` as the capability the pass is composed with.

    A capability rather than the store itself, for the reason
    `tools/job_manager.py` takes its reads by name: a pass handed a whole Job
    store could write to it, and this one has no business doing so.
    """
    def eligible(attempt_id):
        return job_refusal(store, attempt_id)

    return eligible


# -- the HOST's half of eligibility ------------------------------------------
#
# Every axis read here is a durable fact about the execution's lifecycle. ACTIVITY
# IS NOT AMONG THEM, deliberately: `activity_bytes`/`activity_at` are a liveness
# PROJECTION, and TOK-9's first sentence is that liveness does not extend a token.
# A busy cancelled attempt is refused below and a silent running one is renewed,
# which is the asymmetry that sentence asks for.
_LIFECYCLE = (("execution_runtime", "running"),
              ("worker_disposition", "none"),
              ("output", "open"),
              ("cleanup", "pending"))


def _attempt_refusal(control, row):
    """None when this attempt row may still hold renewable permission."""
    attempt_id = row["runtime_attempt_id"]
    if row["assignment_generation"] is None:
        return (f"attempt {name_value(attempt_id)} has fixed no assignment; "
                f"permission is extended for a current assignment generation "
                f"and an unactivated attempt names none")
    for axis, required in _LIFECYCLE:
        if row[axis] != required:
            return (f"attempt {name_value(attempt_id)} has {axis}="
                    f"{name_value(row[axis])} rather than "
                    f"{name_value(required)}; an ending, cancellation or "
                    f"settled execution is not renewed")
    if row["runtime_id"] is None:
        return (f"attempt {name_value(attempt_id)} has no attached runtime; "
                f"permission is extended for one uniquely bound current "
                f"execution")
    # SUPERSESSION, AT THE IDENTITY THE AUTHORITY MINTS. A later generation of
    # the same (authority, Work, participant) means this attempt's authority has
    # moved on even if its own axes have not been observed yet -- and extending
    # the older one would be renewing permission for a stale assignment.
    later = attempts._attempts(
        control,
        "WHERE authority_uuid = ? AND work_id = ? AND "
        "assignment_participant = ? AND assignment_generation > ? "
        "ORDER BY assignment_generation",
        (row["authority_uuid"], row["work_id"],
         row["assignment_participant"], row["assignment_generation"]))
    if later:
        return (f"attempt {name_value(attempt_id)} holds assignment generation "
                f"{row['assignment_generation']} and generation "
                f"{later[-1]['assignment_generation']} has since been fixed; a "
                f"superseded generation's permission is not extended")
    return None


def _token_refusal(control, row, state, *, operation):
    """None when this generation is the one renewable permission of its domain.

    The lifecycle facts are read from the token owner's own public reader, so
    this compares rather than decides -- and every comparison here is one the
    Work's eligibility list names: same domain and generation, same launch
    operation, uniquely bound current runtime, no return, revocation or timing
    ambiguity, and no unresolved activation.
    """
    attempt_id = row["runtime_attempt_id"]
    if state["returned"]:
        return (f"generation {state['generation']} of "
                f"{name_value(state['domain'])} has been returned")
    if state["revoked"]:
        return (f"generation {state['generation']} of "
                f"{name_value(state['domain'])} has been revoked; a withdrawn "
                f"entitlement is not extended")
    if state["timing_ambiguous"]:
        return (f"this manager's timing for generation {state['generation']} of "
                f"{name_value(state['domain'])} is AMBIGUOUS and held; "
                f"ambiguous timing is reconciled, never resolved by renewing")
    if state["launch"] != operation:
        return (f"generation {state['generation']} of "
                f"{name_value(state['domain'])} journalled launch "
                f"{name_value(state['launch'])} and this attempt's start "
                f"operation is {name_value(operation)}; a renewal is for the "
                f"same launch operation")
    if state["attempt"] != attempt_id:
        return (f"generation {state['generation']} of "
                f"{name_value(state['domain'])} was acquired for attempt "
                f"{name_value(state['attempt'])} and this row is "
                f"{name_value(attempt_id)}")
    if state["container"] is None:
        return (f"generation {state['generation']} of "
                f"{name_value(state['domain'])} has bound no container, so "
                f"whether its launch produced an execution is UNKNOWN")
    if state["container"] != row["runtime_id"]:
        return (f"generation {state['generation']} of "
                f"{name_value(state['domain'])} governs container "
                f"{name_value(state['container'])} and the attempt is attached "
                f"to {name_value(row['runtime_id'])}; the two names disagree "
                f"and the disagreement is held rather than resolved by picking "
                f"one")
    if state["activation_started"] is not True:
        return (f"the activation of container {name_value(state['container'])} "
                f"is not positively settled, so whether it is running is "
                f"UNKNOWN; an unresolved activation is held")
    held = tokens.outstanding(control, state["domain"])
    if [one["generation"] for one in held] != [state["generation"]]:
        return (f"{name_value(state['domain'])} has outstanding generations "
                f"{[one['generation'] for one in held]} and this renewal names "
                f"{state['generation']}; permission is extended only for the "
                f"one current generation of a domain")
    return None


# -- one candidate's visit ---------------------------------------------------


def _due(now, expires_at, *, lead):
    """Whether `now` is inside the lead before `expires_at`.

    Composed as `now + lead >= deadline` rather than `deadline - lead <= now`
    because the owned arithmetic this build has moves an instant FORWARD by a
    positive number of seconds, and instants are compared as text.
    """
    return boundaries.deadline(now, lead, "a renewal lead") >= expires_at


def _overdue(control, state, *, execution, operation, seconds):
    """Refuse a late renewal, and make the timing judgement DURABLE.

    The lead is a schedule and not a guarantee: an outage, a suspended process
    or an engine that would not answer can carry a generation past its deadline,
    and TOK-9 is explicit that nothing revives it. So this does not quietly skip
    an overdue generation -- it asks the public atomic API, which refuses and, on
    the way, records the expiry judgement that makes the fact un-arguable for
    every later act. The reclaim pass then owns revocation, stop and confirmed
    cessation; this pass owns refusing to extend.

    A generation already judged expired is not asked again: the record exists and
    a second request would answer the same refusal for nothing.
    """
    if state["expiry_judged_at"] is not None:
        return (f"generation {state['generation']} of "
                f"{name_value(state['domain'])} was judged expired at "
                f"{name_value(state['expiry_judged_at'])}; expiry has won and "
                f"no renewal revives it")
    try:
        tokens.renew(control, state, execution=execution, operation=operation,
                     expected_revision=state["revision"], seconds=seconds)
    except ContractRefusal as refusal:
        return refusal.message
    # A RENEWAL THAT SUCCEEDED AGAINST AN EXPIRED READ means the state moved
    # under this pass -- somebody renewed between the read and the request -- and
    # the honest answer is the committed one rather than this read's.
    return None


def decide(control, governance, row, *, now, eligible=None,
           lead=LEAD_SECONDS, seconds=RENEWAL_SECONDS):
    """Visit one attempt's permission and answer exactly what was decided.

    THE ORDER IS THE CONTRACT. The token's lifecycle is resolved first, because
    an overdue or settled generation is not a candidate for any amount of
    eligibility; then both owners' eligibility; then the lead; then one
    conditional write through `tokens.renew`, carrying the revision this pass
    OBSERVED. A caller that passed the revision it wished for rather than the one
    it read would be asking the token owner to skip the state it claims to have
    seen, and the owner refuses exactly that.

    THE CROSS-STORE READ HAPPENS BEFORE THE WRITE AND IS RE-ASKED AFTER IT. The
    two stores have two connections and no shared transaction, and DB-1 forbids
    reaching the second one from inside the first one's transaction -- so the
    Job-side gate cannot be a condition INSIDE the renewal. What fences the
    renewal is the token revision; what the re-ask adds is visibility: a
    cancellation that commits in the window is reported as
    `ineligible-after-renewal` on a permission whose deadline moved by at most
    one lifetime, and the ending it belongs to stops the container regardless.
    """
    attempt_id = row["runtime_attempt_id"]
    answer = {"attempt_id": attempt_id, "domain": None, "generation": None,
              "decision": None, "why": None, "expires_at": None,
              "revision": None, "renewals_remaining": None}
    domain = tokens.domain_of(governance.resource_kind,
                              governance.identity(row))
    operation = attempts._start_operation_id(row)
    answer["domain"] = domain
    generation = tokens.generation_of(control, domain, execution=attempt_id,
                                      operation=operation)
    if generation is None:
        return dict(answer, decision="ineligible",
                    why=f"no generation of {name_value(domain)} was reserved by "
                        f"attempt {name_value(attempt_id)} under its own start "
                        f"operation")
    state = tokens.token_of(control, domain, generation)
    answer.update(generation=generation, expires_at=state["expires_at"],
                  revision=state["revision"],
                  renewals_remaining=state["renewals_remaining"])
    if state["expired"]:
        return dict(answer, decision="expiry-enforced",
                    why=_overdue(control, state, execution=attempt_id,
                                 operation=operation, seconds=seconds))
    refusal = _token_refusal(control, row, state, operation=operation)
    if refusal is None:
        refusal = _attempt_refusal(control, row)
    if refusal is not None:
        # HELD RATHER THAN MERELY INELIGIBLE when what stands is an UNKNOWN this
        # manager must reconcile instead of an ordinary end: the two are
        # different operator actions and a reader cannot infer which from prose.
        decision = "held" if ("UNKNOWN" in refusal or "AMBIGUOUS" in refusal) \
            else "ineligible"
        return dict(answer, decision=decision, why=refusal)
    if eligible is not None:
        refusal = eligible(attempt_id)
        if refusal is not None:
            return dict(answer, decision="ineligible", why=refusal)
    if not _due(now, state["expires_at"], lead=lead):
        return dict(answer, decision="not-due",
                    why=f"permission stands until "
                        f"{name_value(state['expires_at'])} and the renewal "
                        f"lead is {lead} seconds")
    if state["renewals_remaining"] <= 0:
        # EXHAUSTION IS NOT AN EXTENSION AND NOT A RELEASE. The existing final
        # deadline is left exactly where the last renewal put it, the resource
        # stays held, and the holder finishes or is revoked.
        return dict(answer, decision="exhausted",
                    why=f"generation {generation} of {name_value(domain)} has "
                        f"taken its {state['renewals']} renewals and the "
                        f"bounded policy allows {NOMINAL_RENEWALS}; permission "
                        f"ends at {name_value(state['expires_at'])} and is not "
                        f"extended")
    committed = tokens.renew(control, state, execution=attempt_id,
                             operation=operation,
                             expected_revision=state["revision"],
                             seconds=seconds)
    fresh = tokens.token_of(control, domain, generation)
    answer.update(expires_at=fresh["expires_at"], revision=fresh["revision"],
                  renewals_remaining=fresh["renewals_remaining"])
    # REPLAYED, NOT RENEWED, when the committed record is not the revision this
    # request would have written: a lost reply's retry answers the extension that
    # already happened, and reporting that as a fresh renewal would double-count
    # an allowance nobody spent twice.
    decision = ("renewed" if committed["revision"] == state["revision"] + 1
                else "replayed")
    answer = dict(answer, decision=decision,
                  why=f"generation {generation} of {name_value(domain)} now "
                      f"stands at revision {committed['revision']} until "
                      f"{name_value(committed['expires_at'])}")
    if eligible is not None:
        after = eligible(attempt_id)
        if after is not None:
            answer["ineligible_after_renewal"] = after
    return answer


# -- the pass a serving deployment runs --------------------------------------


class ServingRenewal:
    """One inspection of every governed permission this manager may extend.

    ASKED OFTEN, SCANNING RARELY, DECIDING IMMEDIATELY. The serving loop asks
    this at every tick boundary and the reclaim composition asks it before every
    engine command; the scan floor turns most of those asks into a cheap
    `scanned: False`, and the ones that do scan reach a decision in database work
    alone. That is what separates a timely renewal decision from the blocking
    engine and sweep work around it -- see `protected_seconds` for the exact
    arithmetic and its stated limit.

    NO CAP AND NO ROTATION, which is the opposite of the reclaim pass's choice
    and for the opposite reason. A capped reclaim is fair because its cost is
    engine calls; a capped renewal would be a deadline nobody looked at before it
    passed. Every candidate is visited on every scan, each inside its own fault
    boundary, and the cost of that is database reads over this manager's own
    attempts.
    """

    def __init__(self, control, governance, *, eligible=None,
                 scan_seconds=SCAN_SECONDS, lead=LEAD_SECONDS,
                 seconds=RENEWAL_SECONDS):
        self.control = control
        self.governance = governance
        self.eligible = (None if eligible is None
                         else boundaries.capability(
                             eligible, "a Job-side renewal eligibility read"))
        self.scan_seconds = scan_seconds
        self.lead = lead
        self.seconds = seconds
        # CUMULATIVE COUNTERS, carried in every answer. A scan that happened
        # inside a reclaim's engine loop is reported nowhere else, so the counts
        # are how a tick's report accounts for renewals this process performed
        # between its own ticks.
        self.scans = 0
        self.renewals = 0
        self.scanned_at = None
        self.next_scan_at = None

    def _deferred(self, why, *, now):
        return {"scanned": False, "scanned_at": self.scanned_at,
                "asked_at": now, "next_scan_at": self.next_scan_at,
                "why": why, "scans": self.scans, "renewals": self.renewals,
                "decisions": [], "refused": []}

    def __call__(self, *, now):
        now = boundaries.instant(now, "a renewal scan instant")
        if self.scanned_at is not None and now < self.scanned_at:
            # THE CLOCK WENT BACKWARDS, AND THAT IS NOT A LICENCE TO LOOK AGAIN.
            # TOK-9: ambiguous timing is held and reconciled. A scan taken on a
            # clock this manager cannot trust would be deciding deadlines from
            # it; the per-generation ambiguity record is the durable half, and
            # it is written by the token owner when a renewal is actually asked.
            return self._deferred(
                f"this manager's clock read {name_value(now)} after a scan at "
                f"{name_value(self.scanned_at)}; a scan is not taken on a clock "
                f"that moved backwards", now=now)
        if self.next_scan_at is not None and now < self.next_scan_at:
            return self._deferred(
                f"the scan floor of {self.scan_seconds} seconds stands until "
                f"{name_value(self.next_scan_at)}", now=now)
        if self.control._connection.in_transaction:
            # ASKED FROM INSIDE A TRANSACTION, which is a caller defect and not
            # something to work around: this pass writes, and a write nested in
            # somebody else's transaction would be rolled back with it. Reported
            # rather than raised, because the caller that asked is usually an
            # engine-call seam whose own act must not fail for this.
            return self._deferred(
                "a transaction is open on this manager's control connection, so "
                "no renewal decision is taken inside it", now=now)
        self.scans += 1
        self.scanned_at = now
        self.next_scan_at = boundaries.deadline(now, self.scan_seconds,
                                                "the next renewal scan")
        decisions, refused = [], []
        for row in self._candidates():
            try:
                answer = decide(self.control, self.governance, row, now=now,
                                eligible=self.eligible, lead=self.lead,
                                seconds=self.seconds)
            except (KeyboardInterrupt, SystemExit):
                raise
            except ContractRefusal as refusal:
                refused.append({"attempt_id": row["runtime_attempt_id"],
                                "why": refusal.message})
                continue
            except Exception as fault:                     # noqa: BLE001
                # ONE PERMISSION'S FAULT DOES NOT END THE SCAN, for the reason
                # the reclaim pass collects its own: a scan that died on one
                # unreadable record would leave every other deadline unvisited.
                refused.append({"attempt_id": row["runtime_attempt_id"],
                                "why": f"the renewal decision faulted: "
                                       f"{fault!r}"})
                continue
            if answer["decision"] in ("renewed", "replayed"):
                self.renewals += 1 if answer["decision"] == "renewed" else 0
            decisions.append(answer)
        return {"scanned": True, "scanned_at": now, "asked_at": now,
                "next_scan_at": self.next_scan_at, "why": None,
                "scans": self.scans, "renewals": self.renewals,
                "decisions": decisions, "refused": refused}

    def _candidates(self):
        """Every attempt row with a pinned boundary object, by identity.

        THE SAME DISCOVERY THE RECLAIM PASS MAKES, and asked here rather than
        imported from the tool: a package may not import a tool, and the attempt
        table's own reader belongs to its owner. An attempt with no pinned
        workspace object names no governed resource, so `decide` refuses it at
        `governance.identity` and the fault boundary above records it.
        """
        return attempts._attempts(
            self.control,
            "WHERE workspace_device IS NOT NULL AND workspace_inode IS NOT NULL "
            "ORDER BY runtime_attempt_id")


def serving_renewal(control, store, *, governance=None,
                    scan_seconds=SCAN_SECONDS, lead=LEAD_SECONDS,
                    seconds=RENEWAL_SECONDS):
    """The production composition: both owners' stores, one pass.

    The one place a deployment's two stores meet for this decision. Composed by
    `tools/job_manager.py serve`, and handed to the serving loop AND to the
    reclaim pass -- the first for the tick boundary, the second so a long engine
    pass cannot sit on a lead.
    """
    return ServingRenewal(
        control, governance if governance is not None
        else tokens.workspace_governance(),
        eligible=job_eligibility(store), scan_seconds=scan_seconds, lead=lead,
        seconds=seconds)
