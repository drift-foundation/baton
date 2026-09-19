"""W197661 claim200930 — the acceptance predicate for THIS episode, on the
REAL contracts.

REPLACING instance-200254's verifier, which review200453 found to be a broken
instrument rather than a failing one. It called `status` without `--control` or
`--observe`, so the projection it judged answered `canonical=false` and said so
in its own document while the verifier never looked; and three of its final
predicates named members no contract has -- `episodes[].ended_state` on an
ordinarily completed stage, a `conclude` receipt where receipt acts are `admit`
and `claim`, and `job.status.outcome`, which does not exist. A check that can
never pass is not a finding.

TWO HALVES, AND THE SPLIT IS THE POINT.

  `judge` and everything it calls are PURE FUNCTIONS over documents. They open
  nothing, read no path and reach no deployment, so the predicates can be
  driven by POSITIVE AND NEGATIVE FIXTURES -- a successful shape this accepts
  and broken ones it must refuse -- without a live run. Review
  2026-09-18T06-19-15Z: "Contract-derived verifier and negative cases need not
  wait for successful live fixture."

  `main` is the thin shell that OBSERVES: it reads canonical status through
  the installed command with `--control`, opens the Authority READ-ONLY, seals
  or compares the immutable expected manifest, and writes a FRESH result named
  by this claim. It decides nothing the pure half does not.

FAIL-CLOSED, AND THIS TIME IT IS TRUE. Review 2026-09-18T06-19-15Z corrected a
claim of mine: `compose_lifecycle.policy_pin` only PREDICTS the approval pin,
and nothing executed the comparison. `check_policy_pin` is called here, its
answer is a required check, and a deployment whose configured pin is not the
Authority's current generation is refused before anything is called ready.

WHAT IT DOES NOT DO. It starts nothing, submits nothing, runs no container,
takes no provider turn, opens the Authority for writing and touches no version
control. It never overwrites a previous verification: each run writes its own
`verification-<claim>.json`.
"""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = Path("/home/sl/src/baton")

# THIS EPISODE'S IDENTITIES. Nothing here is inherited from an earlier one, and
# instance-200254's and instance-200000's image digests keep their own
# attribution.
DEST = Path("/home/sl/baton-v12-lifecycle-201492-run4")
AUTHORITY = "d8a042193ef54af182b1e3ee85240c5a"
WORK = "d8a04219-W1"
JOB = "w197661-lifecycle"
SUBMISSION = "w197661-lifecycle-201492"
TARGET_BASE = "e486652c4ddebfb696e030b4b867e914248db542"
CANDIDATE_FILE = "w197661-fixture.txt"
CANDIDATE_BYTES = "w197661 deterministic fixture candidate\n"
# ONE EPISODE, DECLARED. Review201853 [R1]: the verifier accepted
# `terminal.episode = 999` and accepted its removal, because nothing bound it.
# This proof is of a SINGLE-episode integration -- one offer, one attempt, no
# retry -- and that is a fact about the run being proved, so it is declared
# here and bound to BOTH the observation and the projection's own stage. The
# two observed operands are compared with each other as well as with this
# constant, so satisfying it by copying one number into both sides is not
# enough.
EXPECTED_EPISODE = 1

# THE ACCEPTED OBSERVATION SURFACE, BY THE NAME THE CLI USES.
# `tools/stage_execution.py:6198 observation_from` builds `StageObservation`
# from one already-read document; `observing_factory` at 6204 is the
# `status --observe` entry point named the way `factory` is. Neither opens a
# serving surface: `observe_integration` at 6173 opens the Authority with
# `open_readonly` and the IntegrationStore with `open_readonly`, holds both
# only for the read, and delegates to `Integration.observe` -> `account`.
OBSERVING_FACTORY = "tools.stage_execution:observing_factory"
DEPLOYMENT = DEST / "deployment.json"

CONTEXT = HERE / "context"
RECIPE = CONTEXT / "Dockerfile.fixture"
BUILT_DISTRO = HERE / "build/distro/out/distro"

# THE IMMUTABLE EXPECTED MANIFEST. Review 2026-09-18T05-14-53Z [R3]: the old
# verifier measured this episode's COPY inputs and compared them with -- this
# episode. Current-to-current is not provenance. This file is SEALED once, by
# an explicit act, and every later run compares against it; a build whose
# inputs moved afterwards is a failed check rather than a silently accepted
# one.
EXPECTED = HERE / "EXPECTED.json"


def sha_bytes(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def sha_file(place):
    return sha_bytes(Path(place).read_bytes())


def tree_manifest(root):
    """Every entry under one root: files by content, LINKS BY TARGET.

    Review [R3]: the old `tree_digest` skipped every symlink and every path
    containing `__pycache__`, so it did not bind the complete one-folder
    runtime -- a link repointed or a cached module replaced left the digest
    unchanged. A manifest that skips what it cannot hash is a manifest that
    says the skipped thing does not matter.
    """
    root = Path(root)
    held = {}
    for where, directories, names in os.walk(root, followlinks=False):
        directories.sort()
        for name in sorted(names) + sorted(
                one for one in directories
                if os.path.islink(os.path.join(where, one))):
            place = Path(where) / name
            relative = str(place.relative_to(root))
            if place.is_symlink():
                held[relative] = "link:" + os.readlink(place)
            elif place.is_file():
                held[relative] = sha_file(place)
            else:
                held[relative] = "other"
    return held


def manifest_digest(held):
    return sha_bytes(json.dumps(held, sort_keys=True).encode())


def copy_inputs(recipe=RECIPE, context=CONTEXT):
    """Every byte the image was built from, by the recipe's own COPY list."""
    if not Path(recipe).is_file():
        return None
    copied = [line.split()[1] for line in Path(recipe).read_text().splitlines()
              if line.startswith("COPY")]
    held = {}
    for one in copied:
        place = Path(context) / one
        if place.is_file():
            held[one] = sha_file(place)
        elif place.is_dir():
            held[one] = manifest_digest(tree_manifest(place))
        else:
            held[one] = "absent"
    return held


# -- the pure half -----------------------------------------------------------


class Checks:
    """Every answer, recorded whether it held or not.

    TWO QUESTIONS, ANSWERED APART. Review202028: "Explicitly separate historical
    completion acceptance from readiness to authorize another action."

      REQUIRED     did this run's integration COMPLETE, provably, on evidence
                   this episode owns? A failure here means the run is not a
                   completed lifecycle.
      READINESS    could this deployment authorize a NEW action right now? A
                   failure here says nothing about what already happened, and
                   it stays VISIBLE rather than being folded into the verdict
                   or dropped.

    WHY THIS EXISTS AT ALL, and it is not a convenience. The pin-equality check
    was an unconditional gate on historical acceptance, and review202028
    established from the code that a SUCCESSFUL integration necessarily breaks
    it: `authority/core.py integrate` takes its authorization decision and only
    then calls `set_policy("canonical_target", ...)`, which unconditionally
    bumps the generation -- so the receipt records generation N while the
    Authority ends at N+1. A gate that every success fails is not a gate.
    """

    def __init__(self):
        self.held = []

    def check(self, what, answer, detail=None):
        self.held.append({"check": what, "held": bool(answer),
                          "kind": "required",
                          "required": True, "detail": detail})
        return bool(answer)

    def readiness(self, what, answer, detail=None):
        """A CHECKED PRECONDITION for authorizing another action.

        NOT A SOFTENED CHECK. The standing direction was that the pin
        comparison must not be SILENTLY removed, and it is not: it still runs,
        its measured values are still recorded, and the result document still
        reports it. What changed is which question it answers.

        AND NOT A PROPHECY. Review202123: "Readiness means bounded checked
        preconditions, not proof every future action succeeds/fails."
        `ready: false` says one precondition this verifier checked does not
        hold right now. It does not say every possible new Job must fail, and
        the caller analysis behind it is explicitly incomplete.
        """
        self.held.append({"check": what, "held": bool(answer),
                          "kind": "readiness",
                          "required": False, "detail": detail})
        return bool(answer)

    def diagnostic(self, what, answer, detail=None):
        """A measured OBSERVATION that enters NEITHER verdict.

        WHY THIS THIRD CATEGORY EXISTS, and it is a defect review202123 found
        in my own instrument: I recorded BOTH "current == configured" and
        "current == configured + 1" as readiness requirements, and `ready` was
        `not readiness_failed`. Those are mutually exclusive for any consistent
        pair of readings, so `ready` could never be true -- their probes showed
        configured 23 / current 23 failing the advance and configured 23 /
        current 24 failing equality, with every required check passing in both.

        THE ONE-STEP SHAPE IS HISTORY, NOT A PRECONDITION. It describes what
        this completed integration did. A future action does not have to
        satisfy it, so it belongs in neither conjunction -- it is measured,
        reported, and carries its own caution that it proves no ownership.
        """
        self.held.append({"check": what, "held": bool(answer),
                          "kind": "diagnostic",
                          "required": False, "detail": detail})
        return bool(answer)

    @property
    def readiness_failed(self):
        """READINESS only. A diagnostic can never enter this list, which is
        what keeps the two verdicts independent of it."""
        return [one["check"] for one in self.held
                if not one["held"] and one.get("kind") == "readiness"]

    @property
    def diagnostics(self):
        return [{"observation": one["check"], "held": one["held"]}
                for one in self.held if one.get("kind") == "diagnostic"]

    def same(self, what, found, wanted):
        return self.check(what, found == wanted,
                          {"found": found, "wanted": wanted})

    def bound(self, what, found, wanted, kind="text"):
        """Equal, both there, AND both the shape their kind promises.

        Review 2026-09-18T06-41-32Z [R1]: two absences compared equal, so
        emptying both sides passed every check. Review 2026-09-18T07-01-24Z
        [R1]: presence alone still accepted `False` on both sides -- a
        comparison of two well-typed-looking nothings is the same defect
        wearing a scalar.
        """
        held = _well_formed(found, kind) and _well_formed(wanted, kind)
        return self.check(what, held and found == wanted,
                          {"found": found, "wanted": wanted,
                           "well_formed": held, "kind": kind})

    def binding(self, what, found, wanted, kind="identity"):
        """A REQUIRED two-sided reference, with no optional-operand escape.

        Review 2026-09-18T07-01-24Z [R1]: `named` treated `wanted=None` as
        "no binding requested", so REMOVING the verdict's `checkpoint_id` --
        the very identity the check exists to bind -- turned the check off and
        reported a pass. A required reference has two sides by definition;
        a missing counterpart is the failure, not an exemption.
        """
        return self.bound(what, found, wanted, kind)

    def present(self, what, found, kind="identity"):
        """One required value whose contract is that it EXISTS and is shaped.

        Used only where there is genuinely no counterpart to bind against.
        """
        return self.check(what, _well_formed(found, kind),
                          {"found": found, "kind": kind})

    @property
    def failed(self):
        """The REQUIRED failures only -- what makes a run not a completed one.

        A readiness failure is reported through `readiness_failed` and in the
        result document; it is not erased, and it is not a verdict on what
        already happened.
        """
        return [one["check"] for one in self.held
                if not one["held"] and one["required"]]


# WHAT EACH REQUIRED VALUE HAS TO LOOK LIKE. Review 2026-09-18T07-01-24Z [R1]:
# `_present` accepted every non-container scalar, so setting all five
# provenance members to `False` on BOTH sides passed every check -- presence is
# not validation, and the docstring claiming "well-formed" was describing an
# intention. Each kind is checked for the shape its own contract states.
_DIGEST = re.compile(r"\Asha256:[0-9a-f]{64}\Z")
_IDENTITY = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9._:%/-]{1,255}\Z")


def _well_formed(value, kind="text"):
    """Whether a required value is there AND is the shape its kind promises.

    `identity` an unpadded printable name, `digest` this campaign's own
    prefixed sha256, `document` a non-empty mapping, `manifest` a non-empty
    mapping of names to digests or nested manifests, `count` a non-negative
    integer, `text` any non-empty string. A boolean is never any of them,
    which is the probe that found this.

    `count` EXISTS BECAUSE TWO REAL VALUES ARE NUMBERS. A completion's `fence`
    and a receipt decision's `policy_generation` are integers, and asking
    `identity` of them answered not-well-formed while `found` and `wanted`
    were visibly the same number -- a check that failed over its own type
    vocabulary rather than over the run. Zero is a legitimate generation, so
    this is not `bool(value)`.
    """
    if isinstance(value, bool) or value is None:
        return False
    if kind == "count":
        return type(value) is int and value >= 0
    if kind == "identity":
        return type(value) is str and _IDENTITY.match(value) is not None
    if kind == "digest":
        return type(value) is str and _DIGEST.match(value) is not None
    if kind in ("document", "manifest"):
        if type(value) is not dict or not value:
            return False
        if kind == "manifest":
            return all(type(name) is str and name
                       and (_well_formed(held, "digest")
                            or _well_formed(held, "manifest"))
                       for name, held in value.items())
        return True
    if kind == "list":
        return type(value) is list and len(value) > 0
    return type(value) is str and value != ""


def _present(value):
    """The older, weaker question, kept only where any non-empty value will do.

    Every REQUIRED identity, digest and manifest goes through `_well_formed`
    now; this remains for values whose contract is only "something is here".
    """
    if isinstance(value, bool) or value is None:
        return False
    if isinstance(value, (str, bytes, dict, list, tuple, set)):
        return len(value) > 0
    return True


def authority_target(observed):
    """The canonical target the Authority answers, or None if it was unread."""
    return (observed.get("authority") or {}).get("canonical_target")


def _stages(job):
    return {one.get("kind"): one for one in (job or {}).get("stages", [])}


def judge(observed):
    """Every predicate, over documents this function did not fetch.

    `observed` is a closed dictionary of what the shell read:

      status      the Job projection, as the installed command answered it
      expected    the sealed manifest, or None when nothing is sealed yet
      measured    this run's own measurement of the same things
      authority   {"policy_generation", "canonical_target", "work_present"}
      pin         {"configured_pin", "authority_generation", "equal"}
      line        {"candidate", "custody"} read from the materialized line
      records     the accepted verdict, checkpoint, result and terminal

    EVERY MEMBER IS REQUIRED, and a missing one is a FAILED check rather than
    a skipped one: the shell reports what it could not read, and this refuses
    to call an unread thing acceptable.
    """
    checks = Checks()
    status = observed.get("status") or {}

    # -- the projection is CANONICAL, which is the defect this replaces ------
    checks.check("the status projection is CANONICAL",
                 status.get("canonical") is True,
                 {"canonical": status.get("canonical"),
                  "why": "an unobserved projection answers canonical=false and "
                         "says nothing about where a run stopped"})

    job = None
    for one in status.get("jobs", []):
        if one.get("job_id") == JOB:
            job = one
    checks.check("the projection names this Job", job is not None, JOB)
    checks.bound("it is the submission this episode recorded",
                 (job or {}).get("submission_id"), SUBMISSION, "identity")
    checks.bound("its terminal policy is report-and-hold",
                 (job or {}).get("terminal_policy"), "report-and-hold")

    stages = _stages(job)
    checks.same("it has the three stages", sorted(stages),
                ["implementation", "integration", "review"])
    for kind in ("implementation", "review", "integration"):
        checks.bound(f"the {kind} stage COMPLETED",
                     (stages.get(kind) or {}).get("state"), "completed")
        checks.present(f"the {kind} stage names an attempt",
                       (stages.get(kind) or {}).get("attempt_id"))

    # -- the real records, and not three members no contract has -------------
    records = observed.get("records") or {}
    verdict = records.get("verdict") or {}
    checkpoint = records.get("checkpoint") or {}
    result = records.get("result") or {}
    terminal = records.get("terminal") or {}
    # AN UNREAD RECORD IS NOT A MISSING ONE, and neither is acceptable -- but
    # they are different failures and an operator looks in different places
    # for them. Review [R4]: "distinguish missing records from
    # unread/unimplemented ones" and "do not conflate the unimplemented reader
    # with a lifecycle refusal".
    for name, held in (("verdict", verdict), ("checkpoint", checkpoint),
                       ("result", result), ("terminal", terminal)):
        checks.check(f"the {name} record was READ",
                     _present(held) and "unread" not in held,
                     held.get("unread") if isinstance(held, dict) else held)
    checks.bound("a review verdict was ACCEPTED",
                 verdict.get("disposition"), "accepted")
    checks.binding("the accepted verdict names this episode's review "
                   "attempt", verdict.get("attempt_id"),
                   (stages.get("review") or {}).get("attempt_id"))
    checks.bound("the verdict names this Work",
                 verdict.get("work_id"), WORK, "identity")
    checks.present("an integration CHECKPOINT was accepted",
                   checkpoint.get("checkpoint_id"))
    checks.binding("the accepted checkpoint is the one the verdict names",
                   checkpoint.get("checkpoint_id"),
                   verdict.get("checkpoint_id"))
    checks.bound("the checkpoint records the declared base",
                 (checkpoint.get("evidence") or {}).get("base"), TARGET_BASE,
                 "identity")
    checks.bound("the checkpoint holds the candidate path",
                 (checkpoint.get("evidence") or {}).get("paths"),
                 [CANDIDATE_FILE], "list")
    checks.bound("the producer's frozen RESULT is completed",
                 result.get("disposition"), "completed")
    checks.bound("the frozen result names this Work",
                 ((result.get("assignment_ref") or {}).get("work_ref") or {})
                 .get("work_id"), WORK, "identity")
    checks.binding("the frozen result is THIS implementation attempt's",
                   result.get("attempt_id"),
                   (stages.get("implementation") or {}).get("attempt_id"))
    # THE TERMINAL, FROM THE CONTRACT AND NOT FROM A SPELLING. Review
    # 2026-09-18T07-01-24Z: I asserted `state == "held"` and called it proof of
    # a successful report-and-hold. `tools/stage_execution.managed_account`
    # says otherwise -- it writes `held` for a HELD QUEUE ENTRY or an ending
    # that was not `answered`, `answered` for an imported and settled
    # execution, and `completed` only once the integration receipt is there.
    # So `held` is a HOLD, which is the opposite of what I read it as, and the
    # name of the Job's terminal POLICY is not a state its integration reaches.
    checks.bound("the integration account reached its COMPLETED state",
                 terminal.get("state"), "completed", "text")
    checks.check("and `held` is not mistaken for that",
                 terminal.get("state") != "held",
                 {"state": terminal.get("state"),
                  "why": "the ordinary account writes held for a held queue "
                         "entry or an ending that was not answered; it is a "
                         "hold rather than a successful terminal"})

    # -- THE COMPLETION'S REFERENCES, BOUND TO THIS EPISODE -------------------
    #
    # Review201732 [R1]: "bind its answer to this authority/Work/Job/stage/
    # episode/attempt/offer and required completion references, and fail on
    # missing, mismatched, held or unread evidence. A bare completed string or
    # provider result is not an equivalent proof."
    # -- THE OPENER THIS READ WENT THROUGH, NOW REQUIRED TO BE READ-ONLY ----
    #
    # WHAT THIS USED TO SAY, AND WHY THAT HAD TO GO. Review201853 [R2] found
    # the outer handle was `JobStore.open`, which is write-capable, and the
    # honest interim was to REPORT that -- so this check positively required
    # `opener_is_read_only: False`. Review201931 was right that such a check
    # describes an interim and must never become the acceptance contract: it
    # would refuse the fix. `JobStore.open_readonly` now exists, so the
    # requirement is inverted to what it should always have been.
    opener = terminal.get("_opener") or {}
    checks.check("the opener this read went through is REPORTED",
                 bool(opener) and opener.get("opener") is not None,
                 {"opener": opener.get("opener"),
                  "why": "an unreported opener is how a future reader composed "
                         "through a writable handle would go unnoticed"})
    checks.check("and it is a READ-ONLY owner",
                 opener.get("opener_is_read_only") is True,
                 {"opener": opener.get("opener"),
                  "why": "baton_v12.job_manager.JobStore.open_readonly: "
                         "mode=ro, no creation, no initialization, no "
                         "migration, no WAL request and no writable fallback"})
    checks.check("the owner itself refuses what must not be read",
                 opener.get("refusals_are_the_owners") is True,
                 {"why": "a missing, empty, foreign, wrong-Authority, "
                         "old-schema or future-schema store is the OPENER's "
                         "refusal; the interim header guard this replaced "
                         "could not stop a valid old store from being "
                         "migrated"})
    # THE STORE'S OWN DATA, WHICH MUST NOT MOVE. This is the check that says
    # the retained run is intact, and it is separate from the sidecar question
    # below because they are different facts and a reader needs them apart.
    checks.check("this read moved no byte of the store's DATA",
                 opener.get("data_unchanged") is True,
                 {"before": (opener.get("bytes_before") or {}).get("main"),
                  "after": (opener.get("bytes_after") or {}).get("main"),
                  "why": "an empirical measurement over an existing store, NOT "
                         "a substitute for the capability the opener lacks"})
    # AND THE SIDECAR QUESTION, WHICH IS NOT A DATABASE MUTATION. Review201931
    # asked for these to be distinguished and `tests/job_manager/
    # test_store_readonly.py` pins the distinction: a Job store an ordinary
    # manager has used is in WAL mode, SQLite needs `-shm`/`-wal` to READ such
    # a database, and a `mode=ro` connection can neither checkpoint nor remove
    # them. So a surviving sidecar is SQLite reading a WAL store, not this
    # verifier writing one -- the check above is the one that says the database
    # did not move, and this one is reported beside it rather than as proof of
    # a write.
    checks.check("the read created NOTHING BUT SQLite's own WAL machinery",
                 opener.get("only_sqlite_sidecars") is True,
                 {"before": opener.get("bytes_before"),
                  "after": opener.get("bytes_after"),
                  "created": opener.get("sidecars_created"),
                  "why": "-wal and -shm are what SQLite needs to READ a "
                         "WAL-mode database, and a mode=ro connection can "
                         "neither checkpoint nor remove them; anything else "
                         "appearing beside the store would be this verifier "
                         "writing",
                  "the_fact_about_the_database": "`this read moved no byte of "
                                                 "the store's DATA`, above"})

    checks.bound("the observation is the integration-stage-observation "
                 "contract", terminal.get("schema"),
                 "baton.v12.integration-stage-observation/1", "identity")
    checks.bound("the observation names THIS stage", terminal.get("stage_id"),
                 f"{JOB}/integration", "identity")
    checks.binding("the observed attempt is the stage's attempt",
                   terminal.get("attempt_id"),
                   (stages.get("integration") or {}).get("attempt_id"))
    checks.binding("the observed offer is the stage's offer",
                   terminal.get("offer_id"),
                   (stages.get("integration") or {}).get("offer_id"))
    # THE EPISODE, TYPED AND BOUND TWICE. Review201853 [R1] probed this exact
    # hole: `episode = 999` was accepted and so was removing it. It is bound to
    # the projection's own selected stage episode -- a SEPARATE observed
    # operand, read by a different reader -- and to this proof's declared
    # single episode, and it must be a non-negative integer, so a boolean or a
    # string cannot satisfy it.
    stage_episode = (stages.get("integration") or {}).get("episode")
    checks.check("the observed episode is a typed episode number",
                 _well_formed(terminal.get("episode"), "count"),
                 {"episode": terminal.get("episode"),
                  "why": "a missing episode, a boolean or a string is not an "
                         "episode; review201853 accepted all three"})
    checks.binding("the observed episode IS the stage's selected episode",
                   terminal.get("episode"), stage_episode, "count")
    checks.bound("this proof's integration ran ONE episode",
                 terminal.get("episode"), EXPECTED_EPISODE, "count")
    checks.bound("and the projection agrees it ran one", stage_episode,
                 EXPECTED_EPISODE, "count")
    assignment = terminal.get("assignment") or {}
    work_ref = assignment.get("work_ref") or {}
    checks.bound("the observed assignment names this Authority",
                 work_ref.get("authority_uuid"), AUTHORITY, "identity")
    checks.bound("the observed assignment names this Work",
                 work_ref.get("work_id"), WORK, "identity")
    completion = terminal.get("completion") or {}
    for member in ("proposal_id", "integration_receipt_id", "entry_id",
                   "lease_id", "handoff_operation_id", "runtime_id"):
        checks.present(f"the completion names its {member}",
                       completion.get(member))
    checks.bound("the completion's fence is this episode's", completion
                 .get("fence"), 1, "count")
    checks.bound("the completion routes to integration",
                 completion.get("to_route"), "integration", "identity")
    checks.bound("the completion's execution runtime is quiescent",
                 completion.get("execution_runtime"), "quiescent", "identity")
    checks.binding("the completion's source proposal IS its proposal",
                   completion.get("source_proposal_id"),
                   completion.get("proposal_id"))

    # -- THE OWNED BASE -> RESULT -> TARGET CHAIN ----------------------------
    #
    # Review201732 [R3]: "A completed import can advance canonical target: base
    # equality is wrong after completion. Ancestry alone is too weak (an
    # unrelated later descendant passes). Bind initial base, owned settlement/
    # result revision, final target and imported candidate/test evidence
    # through the accepted completion contract."
    #
    # THE CHAIN, AND WHY EACH LINK IS LOAD-BEARING. The proposal was made FROM
    # the declared base; it PRODUCED one candidate revision; the Authority's
    # canonical target is now that same revision; and the receipt that settled
    # it names that same proposal with disposition `integrated`. An unrelated
    # descendant of the base satisfies ancestry and fails the middle link,
    # because it is not what THIS proposal produced.
    owned = observed.get("owned") or {}
    checks.check("the owned proposal was READ",
                 _present(owned) and "unread" not in owned,
                 owned.get("unread") if isinstance(owned, dict) else owned)
    proposal = owned.get("proposal") or {}
    receipt = owned.get("receipt") or {}
    checks.binding("the owned proposal is the one the completion names",
                   proposal.get("proposal_id"), completion.get("proposal_id"))
    checks.bound("the owned proposal was made FROM the declared base",
                 proposal.get("target"), TARGET_BASE, "identity")
    proposal_ref = (proposal.get("assignment_ref") or {}).get("work_ref") or {}
    checks.bound("the owned proposal names this Work",
                 proposal_ref.get("work_id"), WORK, "identity")
    # THE PROPOSAL'S AUTHORITY, which review201853 [R1] showed was unbound: it
    # changed this to 32 `f` characters and the run was still accepted. A
    # proposal from another Authority can carry this Work's local id, so the
    # Work binding alone does not cover it.
    checks.bound("the owned proposal names this Authority",
                 proposal_ref.get("authority_uuid"), AUTHORITY, "identity")
    checks.binding("its Authority is the one the OBSERVATION names",
                   proposal_ref.get("authority_uuid"),
                   ((terminal.get("assignment") or {}).get("work_ref") or {})
                   .get("authority_uuid"))
    checks.binding("the owned proposal is THIS episode's frozen result",
                   proposal.get("result_id"), result.get("result_id"))
    checks.present("the owned proposal produced a candidate revision",
                   proposal.get("candidate_digest"))
    checks.binding("the canonical target IS the revision this proposal "
                   "produced", authority_target(observed),
                   proposal.get("candidate_digest"))
    checks.check("and the target actually ADVANCED from the base",
                 _well_formed(proposal.get("candidate_digest"), "identity")
                 and proposal.get("candidate_digest") != TARGET_BASE,
                 {"base": TARGET_BASE,
                  "candidate": proposal.get("candidate_digest"),
                  "why": "a completed import advances the target, so base "
                         "equality is wrong after completion; ancestry alone "
                         "is too weak because an unrelated later descendant "
                         "satisfies it"})
    checks.binding("the integration receipt is the completion's",
                   receipt.get("receipt_id"),
                   completion.get("integration_receipt_id"))
    checks.binding("the receipt settles the owned proposal",
                   receipt.get("proposal_id"), proposal.get("proposal_id"))
    checks.bound("the receipt's disposition is INTEGRATED",
                 receipt.get("disposition"), "integrated", "identity")
    checks.binding("the receipt settled the same candidate",
                   receipt.get("candidate_digest"),
                   proposal.get("candidate_digest"))
    checks.bound("the receipt names the declared base as its target",
                 receipt.get("target"), TARGET_BASE, "identity")

    # -- the candidate, proved from the line the manager materialized --------
    line = observed.get("line") or {}
    checks.bound("the candidate file carries exactly the declared bytes",
                 line.get("candidate"), CANDIDATE_BYTES)
    # THE ATTEMPT IS BOUND, NOT COUNTED. Review [R3]: the old verifier asserted
    # `len(attempts) == 1` and never compared the identity, so any one attempt
    # satisfied it.
    checks.binding("custody holds THIS implementation attempt",
                   line.get("custody"),
                   (stages.get("implementation") or {}).get("attempt_id"))

    # -- the Authority, read-only --------------------------------------------
    authority = observed.get("authority") or {}
    # THE CANONICAL TARGET IS BOUND ABOVE, THROUGH THE OWNED PROPOSAL, and the
    # equality that used to live here was simply wrong: a completed import
    # advances the target, so demanding it still equal the declared base fails
    # every successful run. What stays here is that the target is READABLE and
    # well formed; whose revision it is, is the chain's business.
    checks.check("the Authority answers a well-formed canonical target",
                 _well_formed(authority.get("canonical_target"), "identity"),
                 {"canonical_target": authority.get("canonical_target"),
                  "why": "base equality is wrong after a completed import; "
                         "the owned base->result->target chain above is what "
                         "proves whose revision this is"})
    checks.check("the Job's Work exists on this Authority",
                 authority.get("work_present") is True, WORK)

    # -- the approval pin, MEASURED against the Authority ---------------------
    pin = observed.get("pin") or {}
    # KEPT, MEASURED, AND MOVED TO THE QUESTION IT ACTUALLY ANSWERS.
    #
    # WHAT IT USED TO BE: an unconditional REQUIRED gate on historical
    # completion. Review202028 established from the code why that is wrong, and
    # `authority/core.py integrate` was re-read against the current tree to
    # confirm it: the authorization decision is taken FIRST, then
    # `set_policy("canonical_target", proposal["candidate_digest"])` runs, and
    # `set_policy` unconditionally calls `_bump_policy_generation`. The receipt
    # then records the EARLIER decision. So a successful integration always
    # ends with the Authority one generation past the receipt's, and a gate
    # requiring equality is one every success fails.
    #
    # IT IS NOT REMOVED AND NOT SOFTENED. It runs, its measured values are
    # recorded, and the result document reports it under `readiness`. What it
    # says is that this deployment cannot authorize a NEW action while its
    # configured pin and its Authority disagree -- `driver._accepted_receipts`
    # refuses on exactly that comparison, at driver.py:1111-1115, before its
    # `issue=False` branch too.
    checks.readiness("the deployment could authorize a NEW action",
                 pin.get("equal") is True,
                 {"configured_pin": pin.get("configured_pin"),
                  "authority_generation": pin.get("authority_generation"),
                  "bears_on": "FUTURE authorization only; this says nothing "
                              "about the completed integration above, which is "
                              "proved from owned evidence",
                  "what_a_false_here_means": "ONE checked precondition does "
                         "not hold right now. It is not a prediction that "
                         "every possible new Job must fail: the callers that "
                         "reach driver._accepted_receipts are not all traced, "
                         "and that analysis stays incomplete",
                  "the_mechanism": "authority/core.py integrate decides, then "
                         "set_policy(canonical_target) bumps the generation "
                         "unconditionally, so a SUCCESSFUL integration leaves "
                         "the Authority at receipt_generation + 1",
                  "corroborated_in_product_source": "tools/stage_execution.py"
                         ":3103 already says _accepted_receipts 'checks the "
                         "deployment pin against the Authority's CURRENT "
                         "generation before it issues anything, so issuing at "
                         "reconciliation time -- after the first Job's "
                         "integration bumped that generation -- can only ever "
                         "refuse'",
                  "observed_for_a_COMPLETED_job": "this destination was "
                         "restarted at generation 10 with pin 9 during "
                         "claim201770 and all three stages reported completed "
                         "with one episode each; reading a completed stage "
                         "does not reach _accepted_receipts, so the earlier "
                         "claim that a resume would defer is WITHDRAWN as to "
                         "completed work",
                  "not_established_here": "whether a deployment with NEW work "
                         "to integrate reaches that guard through any "
                         "particular caller; the callee's own comparison is "
                         "read, the callers are not all traced"})
    # AND THE ONE-STEP ADVANCE IS NOT ITSELF A PROOF OF ANYTHING. Review202028:
    # "Do not ... infer acceptance from merely current == configured+1." This
    # records the shape without letting it stand in for the owned evidence.
    checks.diagnostic("the advance is the ONE STEP a single integration makes",
                 _well_formed(pin.get("authority_generation"), "count")
                 and _well_formed(pin.get("configured_pin"), "count")
                 and pin.get("authority_generation")
                 == pin.get("configured_pin") + 1,
                 {"configured_pin": pin.get("configured_pin"),
                  "authority_generation": pin.get("authority_generation"),
                  "why_this_is_not_acceptance": "a one-step advance is what "
                         "this mechanism produces, not evidence that THIS "
                         "episode produced it; the owned proposal, result, "
                         "target and receipt bindings above are what prove "
                         "that, and they fail independently of this",
                  "why_it_is_not_a_readiness_precondition": "it describes what "
                         "this COMPLETED integration did; a future action does "
                         "not have to satisfy it. Recording it beside pin "
                         "equality made `ready` unsatisfiable, because the two "
                         "cannot both hold for consistent readings"})
    # ACCEPTANCE-TIME IS A DIFFERENT QUESTION FROM READINESS-TO-AUTHORIZE, and
    # review201732 asked for both to be preserved rather than merged: the
    # receipt that settled this episode records the generation it was ACCEPTED
    # under, and that historical fact is unaffected by a later advance.
    # AND THIS ONE IS REQUIRED, because it is a fact about what HAPPENED: the
    # receipt records the generation it was accepted under, and a later advance
    # cannot un-accept it. Review202028: "Preserve ... acceptance-time receipt
    # generation" and "a mismatched/unowned receipt or terminal still fails."
    accepted_under = ((owned.get("receipt") or {}).get("decision") or {}) \
        .get("policy_generation")
    checks.bound("the integration receipt was accepted under the configured "
                 "pin", accepted_under, pin.get("configured_pin"), "count")

    # -- provenance, against an IMMUTABLE expectation -------------------------
    expected, measured = observed.get("expected"), observed.get("measured") or {}
    checks.check("an immutable expected manifest is SEALED",
                 bool(expected), EXPECTED.name)
    # WHAT THE SEAL IS WORTH, CLASSIFIED RATHER THAN ASSUMED. The image digest
    # has an independent build-time record; the inputs do not. Both are stated,
    # and the second is a READINESS-style fact about the evidence rather than a
    # failure of the run -- the run happened, and this is how well it is
    # attested.
    provenance = observed.get("provenance") or {}
    checks.check("the sealed image is corroborated by the BUILD's own record",
                 (provenance.get("image_identity") or {}).get("corroborated")
                 is True, provenance.get("image_identity"))
    # EVIDENCE QUALITY, WHICH IS ITS OWN THING. Review202123: "Input
    # attestation is separately documented evidence quality." It is not a
    # precondition for authorizing another action -- a deployment with a
    # perfectly attested build and a stale pin is unready, and one with a
    # matching pin and an unattested build is ready to act while its build
    # remains less well evidenced. Putting it in the readiness conjunction
    # conflated two unrelated facts.
    checks.diagnostic("the sealed image INPUTS are independently attested",
                 (provenance.get("image_inputs") or {}).get("corroborated")
                 is True,
                 {**(provenance.get("image_inputs") or {}),
                  "bears_on": "how well this episode's build is EVIDENCED; not "
                              "whether its lifecycle completed, and not "
                              "whether this deployment could act again",
                  "the_standing_limitation": "the seal was written after the "
                         "build, so it proves only that nothing moved since. "
                         "Accepted historical fixture completion is NOT "
                         "approval to deploy the claimed source bytes."})
    for name, kind in (("image", "identity"), ("image_inputs", "manifest"),
                       ("built_runtime", "digest"),
                       ("installed_runtime", "digest"),
                       ("configuration", "digest")):
        checks.bound(f"the {name} matches the sealed expectation",
                     measured.get(name), (expected or {}).get(name), kind)
    return checks


# -- the observing half ------------------------------------------------------


def classify_provenance():
    """What the seal proves, what the build records corroborate, and what
    neither does.

    Review202028: "Preserve the post-build seal limitation: historical source
    equality is not a prospective build-input attestation. Final evidence must
    state that limitation and classify whether the existing immutable image/
    build records corroborate inputs, without rewriting the seal."

    THE SEAL IS NOT REWRITTEN. `EXPECTED.json` stays exactly as it was written,
    and `main` still refuses to reseal. This only CLASSIFIES it.

    THE THREE ANSWERS, and they are genuinely different:

      the IMAGE identity IS corroborated. `build/fixture.iid` is written by the
      build itself, at build time, and it carries the same digest the seal
      carries. It predates the seal, so it is not the seal's own measurement
      read back.

      the IMAGE INPUTS are NOT corroborated. The build log names the COPY lines
      but records no content digest for each input, so the sealed
      `image_inputs` manifest was measured at seal time -- AFTER the build --
      and nothing independent attests what the build actually consumed. This is
      the post-build seal limitation, stated rather than papered over: the seal
      proves nothing MOVED after it, and does not attest what went in before.

      the RECIPE's recorded digests are attribution, not attestation. The
      Dockerfile names W198667's three reviewed bytes by digest, which says
      what the author intended to carry; it is not a build-time measurement.
    """
    image = None
    place = HERE / "build/fixture.iid"
    if place.is_file():
        image = place.read_text().strip()
    sealed = json.loads(EXPECTED.read_text()) if EXPECTED.is_file() else {}
    built_at = place.stat().st_mtime if place.is_file() else None
    sealed_at = EXPECTED.stat().st_mtime if EXPECTED.is_file() else None
    return {
        "seal": {"file": EXPECTED.name, "rewritten": False,
                 "what_it_proves": "that nothing measured has MOVED since it "
                                   "was written",
                 "what_it_does_not_prove": "what the build consumed, because "
                                           "it was written after the build"},
        "image_identity": {
            "corroborated": bool(image) and image == sealed.get("image"),
            "by": "build/fixture.iid, written by the build itself",
            "build_record": image, "sealed": sealed.get("image"),
            "record_predates_the_seal": (
                None if built_at is None or sealed_at is None
                else built_at < sealed_at)},
        "image_inputs": {
            "corroborated": False,
            "why_not": "the build log names the COPY lines but records no "
                       "content digest per input, so the sealed manifest was "
                       "measured at seal time and nothing independent attests "
                       "what the build consumed"},
        "recipe_attribution": {
            "is_attestation": False,
            "what_it_is": "the Dockerfile names W198667's three reviewed "
                          "digests, which records what the author intended to "
                          "carry rather than what the build measured"},
    }

def read_status(run=None, observe=True):
    """The Job projection, through the INSTALLED command, WITH the control
    store AND WITH `--observe` -- which is the whole of review201732's R2.

    WHY `--observe` IS NOT OPTIONAL HERE, and my own F1 was wrong without it.
    `tools/job_manager.py` composes `_ReadOnly(control)` when `--observe` is
    absent and `_Observing(control, observed)` when it is present, and
    `_Observing` is the only one that contributes `observe_integration`. The
    projection consults that account BEFORE its generic worker rules, so an
    integration whose completion only the account knows reads `starting`
    without the operand and `completed` with it. IDENTICAL STORES ARE NOT
    IDENTICAL OBSERVATION CAPABILITY, and the difference is this flag rather
    than the incarnation I first blamed.

    `observe=False` EXISTS SO THE COMPARISON CAN BE RUN, not as a fallback: it
    is how `measure_observation_gap` obtains the unobserved answer to set
    beside the observed one, which is the controlled comparison review201732
    required before attributing anything to a product defect.

    THE CONFIGURATION IS NAMED BECAUSE `observing_factory` DEMANDS IT.
    `stage_execution._configuration` refuses unless
    BATON_V12_STAGE_EXECUTION_CONFIG is set, and this deployment's document is
    its own `deployment.json`. Passing it in the child environment keeps this
    process's environment untouched.
    """
    runner = run or (lambda argv, env=None: subprocess.run(
        argv, capture_output=True, text=True, timeout=180, env=env))
    argv = [str(DEST / "distro/baton-v12-stack"), "manager",
            "--store", str(DEST / "db/jobs.sqlite3"),
            "--incarnation", "c200930-verify",
            "--authority-uuid", AUTHORITY, "status",
            "--control", str(DEST / "db/control.sqlite3")]
    environment = dict(os.environ)
    if observe:
        argv += ["--observe", OBSERVING_FACTORY]
        environment["BATON_V12_STAGE_EXECUTION_CONFIG"] = str(DEPLOYMENT)
    try:
        found = runner(argv, environment)
    except TypeError:
        # A TEST RUNNER THAT TAKES ONLY THE ARGV still works, because the
        # environment it would have been given is this process's own.
        found = runner(argv)
    if found.returncode != 0:
        return None
    try:
        return json.loads(found.stdout)
    except ValueError:
        return None


def measure_observation_gap(run=None):
    """Both answers, side by side, with ONLY the operand differing.

    Review201732 [R2]: "confirm the exact recorded command/factory and compare
    using tools.stage_execution:observing_factory with the same configuration.
    Do not label new incarnation the cause without a controlled comparison."
    This IS that comparison -- same destination, same store, same incarnation,
    same authority, one flag -- and it is what turned my F1 from a claimed
    product contradiction into a defect in how I invoked the command.
    """
    observed = read_status(run=run, observe=True)
    unobserved = read_status(run=run, observe=False)

    def integration_of(document):
        for job in (document or {}).get("jobs", []):
            if job.get("job_id") != JOB:
                continue
            for stage in job.get("stages", []):
                if stage.get("kind") == "integration":
                    return stage.get("state")
        return None

    return {"with_observe": integration_of(observed),
            "without_observe": integration_of(unobserved),
            "factory": OBSERVING_FACTORY,
            "only_difference": "the --observe operand and the configuration "
                               "it requires; store, incarnation, authority "
                               "and control store are identical",
            "explains_the_gap": (integration_of(observed) == "completed"
                                 and integration_of(unobserved) != "completed")}


def read_authority():
    """Policy generation, canonical target and the Work, READ-ONLY.

    `Authority.open_readonly` exists for exactly this: `open` takes a write
    lock, applies the schema and sets a persistent journal mode, which is
    right for a serving deployment and wrong for a verifier. The old one used
    `open` while its docstring called itself read-only.
    """
    sys.path.insert(0, str(REPO / "v12/python"))
    sys.path.insert(0, str(REPO / "v12/python/src"))
    from baton_v12.authority import Authority

    authority = Authority.open_readonly(str(DEST / "db/authority.sqlite3"),
                                        expected_authority_uuid=AUTHORITY)
    try:
        return {"policy_generation": authority.policy_generation(),
                "canonical_target": authority.canonical_target(),
                "work_present": authority.project_work(WORK) is not None}
    finally:
        dispose = getattr(authority, "dispose", None)
        if dispose is not None:
            dispose()


def read_line():
    """The candidate bytes and the ONE custody attempt, from the line."""
    lines = DEST / "storage/.baton-review-lines"
    if not lines.is_dir():
        return {}
    held = sorted(os.listdir(lines))
    if len(held) != 1:
        return {"candidate": None, "custody": None, "lines": held}
    line = lines / held[0]
    candidate = line / "checkout" / CANDIDATE_FILE
    custody = line / "custody"
    attempts = sorted(os.listdir(custody)) if custody.is_dir() else []
    return {"candidate": candidate.read_text() if candidate.is_file() else None,
            "custody": attempts[0] if len(attempts) == 1 else None}


def measure():
    """This run's own measurement of everything the seal pins."""
    iid = HERE / "build/fixture.iid"
    configured = DEST / "deployment.json"
    return {
        "image": iid.read_text().strip() if iid.is_file() else None,
        "image_inputs": copy_inputs(),
        "built_runtime": manifest_digest(tree_manifest(BUILT_DISTRO))
        if BUILT_DISTRO.is_dir() else None,
        "installed_runtime": manifest_digest(tree_manifest(DEST / "distro"))
        if (DEST / "distro").is_dir() else None,
        "configuration": sha_file(configured) if configured.is_file() else None,
    }


def main(argv=None, run=None):
    parser = argparse.ArgumentParser(prog="verify_lifecycle")
    parser.add_argument("--seal", action="store_true",
                        help="write EXPECTED.json from this measurement; "
                             "refused when one already exists, because an "
                             "expectation a failing run may rewrite is not one")
    # NO DEFAULT THAT CAN COLLIDE SILENTLY. A reusable name plus an
    # overwriting write is how the previous run's evidence disappeared.
    parser.add_argument("--claim", required=True,
                        help="this run's own identity; the result is created "
                             "exclusively under it and a collision is refused")
    # SYS.ARGV WHEN NOBODY PASSED ONE. The first form of this parsed an
    # EMPTY list on `argv is None`, so `--seal` typed at a terminal was
    # silently dropped and the seal step ran a verification instead.
    taken = parser.parse_args(sys.argv[1:] if argv is None else argv)

    measured = measure()
    if taken.seal:
        if EXPECTED.is_file():
            print("refused: an expectation is already sealed; a verifier that "
                  "reseals is a verifier that always passes", file=sys.stderr)
            return 2
        EXPECTED.write_text(json.dumps(measured, indent=2, sort_keys=True)
                            + "\n")
        print(json.dumps({"sealed": str(EXPECTED)}, indent=1))
        return 0

    sys.path.insert(0, str(HERE))
    import compose_lifecycle

    observed = {
        "status": read_status(run=run),
        "expected": json.loads(EXPECTED.read_text())
        if EXPECTED.is_file() else None,
        "measured": measured,
        "authority": read_authority(),
        "pin": compose_lifecycle.check_policy_pin(),
        "line": read_line(),
        "records": read_records(),
        "owned": read_owned_proposal(),
        "provenance": classify_provenance(),
        "observation_gap": measure_observation_gap(run=run),
    }
    # THE TERMINAL IS READ THROUGH ITS OWN OWNER and set beside the other
    # records, so `judge` keeps one vocabulary for "missing" and "unread".
    observed["records"]["terminal"] = read_terminal(run=run)
    checks = judge(observed)
    found = {"schema": "baton.w197661.verification/2", "claim": taken.claim,
             "destination": str(DEST), "authority_uuid": AUTHORITY,
             "work_id": WORK, "job_id": JOB, "submission_id": SUBMISSION,
             "measured": measured, "pin": observed["pin"],
             "provenance": observed["provenance"],
             "observation_gap": observed["observation_gap"],
             "checks": checks.held, "failed": checks.failed,
             # TWO VERDICTS, NEITHER HIDING THE OTHER. `accepted` is about the
             # completed run; `ready` is about what this deployment could do
             # next. Review202028: "Keep readiness mismatch visible even when
             # historical completion passes."
             "accepted": not checks.failed,
             "readiness_failed": checks.readiness_failed,
             "ready": not checks.readiness_failed,
             # THREE CATEGORIES, AND THE THIRD ENTERS NEITHER VERDICT.
             # Review202123: keep the one-step observation "outside BOTH
             # historical acceptance and future-readiness conjunctions".
             "diagnostics": checks.diagnostics}
    # A FRESH RESULT EVERY TIME, AND THE FILESYSTEM ENFORCES IT. Review
    # 2026-09-18T06-41-32Z [R3]: this used `write_text` with a reusable
    # default claim, so a second run REPLACED the evidence of the first and
    # returned zero -- "do not overwrite" written as a comment rather than as
    # a rule. `O_EXCL` is the rule; a collision is refused and the previous
    # bytes are untouched.
    place = HERE / f"verification-{taken.claim}.json"
    try:
        handle = os.open(place, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError:
        print(f"refused: {place.name} already exists; a verification that "
              f"overwrites the previous one destroys the evidence somebody "
              f"would compare against. Name this run with --claim.",
              file=sys.stderr)
        return 2
    with os.fdopen(handle, "w") as writing:
        writing.write(json.dumps(found, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"accepted": found["accepted"],
                      "failed": found["failed"],
                      "ready": found["ready"],
                      "readiness_failed": found["readiness_failed"],
                      "diagnostics": found["diagnostics"],
                      "checks": len(checks.held)}, indent=1))
    if checks.readiness_failed:
        print("READINESS: a checked precondition for authorizing a NEW "
              "action does not hold. That is separate from whether the "
              "retained run completed, and it is not a prediction that every "
              "new Job must fail.", file=sys.stderr)
    if checks.failed:
        print("NOT ACCEPTED: a required check did not hold; this run is NOT a "
              "completed lifecycle", file=sys.stderr)
        return 1
    return 0


def read_records(control=None, line_id=None, implementation_attempt=None):
    """The accepted verdict, checkpoint, frozen result and terminal, READ.

    Review 2026-09-18T06-41-32Z [R4], and the correction is mine: this was an
    unconditional stub that asserted "this episode has no accepted verdict or
    checkpoint yet". THAT WAS WRONG, and the reviewer said exactly why -- the
    retained episode's implementation and review both COMPLETED, so those
    records exist and I confused an unimplemented reader with a lifecycle
    refusal. Reading them proves it: the line is `accepted`, the verdict's
    disposition is `accepted`, and the checkpoint names the candidate path.

    READ-ONLY, THROUGH THE OWNING CONTRACTS. `ControlStore.open_readonly`
    opens the store `mode=ro`, and every record comes from its own module's
    public reader -- `review_cycles.integration_checkpoint`,
    `review_cycles.verdict_of`, `output.frozen_output_of` -- rather than from
    a shape this file invents.

    THE TERMINAL IS READ HERE TOO, by `read_terminal`, and my claim that it
    could not be was WRONG. Review201732 [R1]: `managed_account` is not this
    episode's reader. `StageObservation.observe_integration` is, it opens both
    owners with `open_readonly`, and `observation_from` builds it without any
    serving operation. That correction is the whole of this turn's R1.
    """
    sys.path.insert(0, str(REPO / "v12/python"))
    sys.path.insert(0, str(REPO / "v12/python/src"))
    from baton_v12.worker_manager import ControlStore, review_cycles
    from baton_v12.worker_manager import output as output_records

    found = {"verdict": {"unread": "the control store was not opened"},
             "checkpoint": {"unread": "the control store was not opened"},
             "result": {"unread": "the control store was not opened"},
             "terminal": {"unread": "read_terminal was not called"}}
    if line_id is None:
        line_id = _one_line()
    if line_id is None:
        for name in ("verdict", "checkpoint", "result"):
            found[name] = {"unread": "this destination holds no single "
                                     "review line to read records from"}
        return found
    opened = control or ControlStore.open_readonly(
        str(DEST / "db/control.sqlite3"), incarnation="c201089-verify",
        clock=lambda: "2026-09-18T00:00:00.000Z")
    try:
        accepted = review_cycles.integration_checkpoint(opened, line_id)
        if accepted is None:
            found["checkpoint"] = {"missing": "this line has no accepted "
                                              "integration checkpoint"}
            found["verdict"] = {"missing": "no accepted checkpoint names a "
                                           "verdict on this line"}
        else:
            found["checkpoint"] = {
                "checkpoint_id": accepted.get("checkpoint_id"),
                "evidence": accepted.get("evidence") or {}}
            verdict_id = accepted.get("verdict_id")
            held = (review_cycles.verdict_of(opened, verdict_id)
                    if verdict_id else None)
            if held is None:
                found["verdict"] = {"missing": "the accepted checkpoint names "
                                               "no readable verdict"}
            else:
                # THE REVIEWING ATTEMPT IS THE ATTACHMENT'S, not a member the
                # verdict carries: the verdict names its attachment and the
                # attachment is what a reviewing attempt produced.
                found["verdict"] = {
                    "verdict_id": held.get("verdict_id"),
                    "disposition": held.get("disposition"),
                    "checkpoint_id": held.get("checkpoint_id"),
                    "work_id": held.get("work_id"),
                    "attempt_id": _reviewing_attempt(opened, held)}
        if implementation_attempt is None:
            implementation_attempt = _custody_attempt(line_id)
        if implementation_attempt is None:
            found["result"] = {"missing": "no single implementation attempt "
                                          "holds custody on this line"}
        else:
            frozen = output_records.frozen_output_of(opened,
                                                     implementation_attempt)
            found["result"] = ({"missing": "this implementation attempt has "
                                           "no frozen result"}
                               if frozen is None else
                               {"attempt_id": implementation_attempt,
                                "disposition": frozen.get("disposition"),
                                "result_id": frozen.get("result_id"),
                                "manifest_digest": frozen.get(
                                    "manifest_digest"),
                                # THE ASSIGNMENT LIVES IN THE RETAINED RESULT
                                # MANIFEST, not on the frozen row -- which
                                # answers `assignment_ref: null` and had this
                                # predicate failing over my reader rather than
                                # over the run. `load_manifest` is the owner.
                                "assignment_ref": _result_assignment(
                                    opened, frozen.get("manifest_digest"))})
    finally:
        if control is None:
            close = getattr(opened, "close", None)
            if close is not None:
                close()
    return found


def read_terminal(run=None):
    """The integration stage's own completion account, through read-only owners.

    THROUGH THE EXISTING OWNER, WHICH IS THE CORRECTION. claim201492 said no
    read-only path existed and pointed at `managed_account`. Review201732 [R1]
    named the actual one and it checks out against this tree:

      tools/stage_execution.py:6173  StageObservation.observe_integration
          opens `Authority.open_readonly` and `IntegrationStore.open_readonly`,
          holds both only for the read -- "handles are local to the read,
          including all refusal paths, so the observation object carries no
          serving capability or disposal obligation" -- and delegates to
          `Integration(context).observe(stage)`.
      tools/stage_execution.py:6198  observation_from
          builds that surface from one already-read document.

    NOTHING HERE REIMPLEMENTS ITS PREDICATES. This function fetches; `judge`
    binds what it fetched to this episode's identities. `operations_from` and
    `factory` are never called, and the composition below is the one
    `tools/job_manager.py:145` itself uses -- `_Observing(control, observed)`
    around the same object -- so the projection consulted here is the projection
    the CLI answers.

    WHAT IT ANSWERS is `baton.v12.integration-stage-observation/1`: the stage,
    episode, attempt, offer, the assignment's work_ref and participant, the
    `state`, and a `completion` naming the proposal, the source proposal, the
    result, the Authority integration receipt, the entry, the lease, the fence,
    the outgoing handoff operation, the route, the runtime and the execution
    runtime. A bare `completed` string is not that, which is why `judge` binds
    the references rather than the word.
    """
    sys.path.insert(0, str(REPO / "v12/python"))
    sys.path.insert(0, str(REPO / "v12/python/src"))
    if not DEPLOYMENT.is_file():
        return {"unread": f"this destination has no {DEPLOYMENT.name}, so the "
                          f"observation surface has no configuration to be "
                          f"built from"}
    # THE OWNER REFUSES NOW, AND THIS FILE NO LONGER GUESSES AT BYTES.
    # `JobStore.open_readonly` exists as of W197661 claim201954, so the
    # interim header guard is gone: a missing, empty, foreign, wrong-Authority,
    # old-schema or future-schema store is the OWNER's refusal, which is where
    # that decision belongs. The fingerprints stay, because historical evidence
    # comparing against them should keep comparing.
    store = DEST / "db/jobs.sqlite3"
    before = _store_fingerprint(store)
    # THE CONFIGURATION IS PASSED AS A DOCUMENT, not through the environment:
    # `observation_from` takes one already-read document, so nothing here needs
    # BATON_V12_STAGE_EXECUTION_CONFIG and this process's environment is
    # untouched. `observing_factory` is the flag's entry point and reads the
    # variable; the verifier uses the document form of the same surface.
    from baton_v12.job_manager import JobStore
    from baton_v12.worker_manager import ControlStore
    from tools import job_manager as manager_tool
    from tools import stage_execution

    when = lambda: "2026-09-18T00:00:00.000Z"                  # noqa: E731
    document = json.loads(DEPLOYMENT.read_text())
    try:
        with JobStore.open_readonly(str(store), authority_uuid=AUTHORITY,
                                    incarnation="c201954-verify",
                                    clock=when) as jobs:
            with ControlStore.open_readonly(
                    str(DEST / "db/control.sqlite3"),
                    incarnation="c201770-verify", clock=when) as control:
                observed = stage_execution.observation_from(document, jobs,
                                                            control)
                projected = manager_tool.status(
                    jobs, manager_tool._Observing(control, observed),
                    observed_at=when())
                stage = None
                for job in projected.get("jobs", []):
                    if job.get("job_id") != JOB:
                        continue
                    for one in job.get("stages", []):
                        if one.get("kind") == "integration":
                            stage = one
                if stage is None:
                    return {"missing": "this projection has no integration "
                                       "stage to observe",
                            "_opener": None}
                answer = observed.observe_integration(stage)
                if answer is None:
                    return {"missing": "the integration account answered "
                                       "nothing for this stage",
                            "_opener": None}
                # THE EMPIRICAL HALF, and it is NOT a substitute for the
                # capability the opener lacks. Review201853 [R2] framed the
                # finding as static capability rather than an allegation that
                # run4 was mutated, and this is the corresponding measurement:
                # the store's own bytes, before and after. A change is carried
                # out as a FAILED check rather than swallowed.
                held = dict(answer)
    except Exception as why:                                   # noqa: BLE001
        # A REFUSAL IS REPORTED, NEVER SWALLOWED INTO A PASS. `judge` fails an
        # unread terminal, so an exception here cannot be mistaken for
        # acceptance -- and its text is kept because that text is the finding.
        return {"unread": f"{type(why).__name__}: {why}",
                "_opener": _opener_report(store, before)}
    # MEASURED AFTER EVERY HANDLE IS CLOSED, which is the honest question. A
    # fingerprint taken while the connection is still open reports SQLite's
    # working files rather than what this verifier LEFT BEHIND, and "did the
    # destination end up changed" is the thing a reader cares about.
    held["_opener"] = _opener_report(store, before)
    return held



def _store_fingerprint(store):
    """Every byte SQLite owns for this store, digested, or None when absent.

    THE SIDECARS ARE PART OF IT. `JobStore.open` requests WAL, and a WAL switch
    is a change to `-wal` and `-shm` rather than to the main file, so digesting
    only `jobs.sqlite3` would report "nothing moved" about the very thing the
    capability gap is.
    """
    found = {}
    for suffix in ("", "-wal", "-shm"):
        place = Path(str(store) + suffix)
        if not place.is_file():
            found[suffix or "main"] = None
            continue
        digest = hashlib.sha256()
        with open(place, "rb") as handle:
            for block in iter(lambda: handle.read(1 << 16), b""):
                digest.update(block)
        found[suffix or "main"] = digest.hexdigest()
    return found


def _opener_report(store, before):
    """Which opener this read went through, and what moved.

    THE GAP F5 RECORDED IS CLOSED. `baton_v12.job_manager.JobStore.open_readonly`
    exists as of W197661 claim201954: a `mode=ro` URI, a refusal for a path
    that is not an existing regular store, a refusal for an empty one rather
    than initializing it, the current schema exactly and no migration, no WAL
    request and no write-capable fallback on a read failure. The Job store now
    has the counterpart `ControlStore`, `Authority` and `IntegrationStore`
    already had, so every handle `read_terminal` opens is a read-only owner.

    THE REFUSALS ARE THE OWNER'S, which is the substantive change rather than a
    relabelling. The interim was a header check in this file, and review201931
    named exactly what it could not do: a VALID OLD Job store passes a file
    header and then reaches `_adopt` -> `_migrate`. The opener refuses it at
    the version instead.

    THE FINGERPRINTS STAY, as evidence rather than as the argument. They are a
    measurement over one read; what makes this read-only is the opener's
    capability, not its observed effect.
    """
    after = _store_fingerprint(store)
    return {"opener": "baton_v12.job_manager.JobStore.open_readonly",
            "opener_is_read_only": True,
            "what_it_refuses": ["a path that is not an existing regular store",
                                "an empty store, rather than initializing one",
                                "any schema but this build's, rather than "
                                "migrating",
                                "a store bound to another Authority",
                                "a foreign database",
                                "a read failure, with no writable fallback"],
            "refusals_are_the_owners": True,
            "read_only_opener_available": True,
            "covered_by": "v12/python/tests/job_manager/test_store_readonly.py",
            "bytes_before": before, "bytes_after": after,
            "bytes_unchanged": before == after,
            "data_unchanged": before.get("main") == after.get("main"),
            "sidecars_unchanged": all(before.get(one) == after.get(one)
                                      for one in ("-wal", "-shm")),
            "sidecars_created": [one for one in ("-wal", "-shm")
                                 if before.get(one) is None
                                 and after.get(one) is not None],
            # WHAT APPEARED, AND WHETHER IT IS SQLITE'S. The previous framing
            # required NOTHING to appear, which was right while the outer
            # opener was write-capable and a created `-wal` WAS the gap. With
            # `JobStore.open_readonly` it is the opposite: SQLite creates these
            # to READ a WAL database and cannot remove them from a read-only
            # connection, so requiring their absence would refuse the fix.
            # What must still hold is that nothing ELSE appeared.
            "only_sqlite_sidecars": all(
                before.get(one) == after.get(one)
                for one in after if one not in ("-wal", "-shm")),
            "sidecars_are_sqlite_managed": (
                "SQLite needs -shm/-wal to READ a WAL-mode database and a "
                "mode=ro connection can neither checkpoint nor remove them, so "
                "a surviving sidecar is not a mutation of the database; "
                "`data_unchanged` is the fact that bears on that")}


def read_owned_proposal(receipt_kind="integration"):
    """The proposal and integration receipt this episode OWNS, read-only.

    THIS IS REVIEW201732's R3 BINDING, and it is what replaces both the wrong
    equality check and the too-weak ancestry one. The Authority holds, for this
    episode's own proposal:

      target            the revision the proposal was made FROM -- the
                        declared base
      candidate_digest  the revision this proposal PRODUCED
      result_id         the frozen result it was published from
      assignment_ref    the authority_uuid and work_id that own it

    and, for the integration receipt the completion names, the same
    `candidate_digest` and `target` plus a `disposition` and the
    `decision.policy_generation` the receipt was ACCEPTED under.

    SO THE BINDING IS A CHAIN, not a comparison: the proposal's `target` is the
    declared base, the proposal's `candidate_digest` is what the Authority now
    answers as the canonical target, and the receipt names that same proposal.
    An unrelated later descendant of the base fails the middle link, which is
    exactly the negative ancestry could not reject.
    """
    sys.path.insert(0, str(REPO / "v12/python"))
    sys.path.insert(0, str(REPO / "v12/python/src"))
    from baton_v12.authority import Authority

    terminal = read_terminal()
    completion = (terminal or {}).get("completion") or {}
    proposal_id = completion.get("proposal_id")
    if not proposal_id:
        return {"unread": "the integration observation names no proposal, so "
                          "there is nothing owned to bind the target to"}
    authority = Authority.open_readonly(str(DEST / "db/authority.sqlite3"),
                                        expected_authority_uuid=AUTHORITY)
    try:
        return {"proposal": authority.proposal(proposal_id),
                "receipt": authority.receipt(proposal_id, receipt_kind),
                "proposal_id": proposal_id}
    except Exception as why:                                   # noqa: BLE001
        return {"unread": f"{type(why).__name__}: {why}"}
    finally:
        dispose = getattr(authority, "dispose", None)
        if dispose is not None:
            dispose()


def _one_line():
    """The one review line this destination materialized, or None."""
    lines = DEST / "storage/.baton-review-lines"
    if not lines.is_dir():
        return None
    held = sorted(os.listdir(lines))
    return held[0] if len(held) == 1 else None


def _custody_attempt(line_id):
    """The one attempt holding custody on that line, or None."""
    custody = DEST / "storage/.baton-review-lines" / line_id / "custody"
    held = sorted(os.listdir(custody)) if custody.is_dir() else []
    return held[0] if len(held) == 1 else None


def _result_assignment(control, manifest_digest):
    """The assignment a frozen result names, from its RETAINED MANIFEST."""
    from baton_v12.worker_manager.manifests import load_manifest

    if not manifest_digest:
        return None
    try:
        held = load_manifest(control, manifest_digest, "resultManifest")
    except Exception:                                      # noqa: BLE001
        return None
    return (held or {}).get("assignment_ref")


def _reviewing_attempt(control, verdict):
    """The attempt whose review produced this verdict, through its owner.

    The verdict names its ATTACHMENT; the attachment is the record a reviewing
    attempt made. Answered as `None` when this build's reader cannot resolve
    it, which `judge` treats as a missing identity rather than a match.
    """
    from baton_v12.worker_manager import review_cycles

    try:
        held = review_cycles.review_of(control, verdict.get("attachment_id"))
    except Exception:                                      # noqa: BLE001
        return None
    # `runtime_attempt_id` IS THE MEMBER ITS OWNER ANSWERS WITH, and reading
    # `attempt_id` -- which this file guessed at first -- answered None for a
    # record that carries the identity perfectly well.
    return (held or {}).get("runtime_attempt_id")


if __name__ == "__main__":
    sys.exit(main())
