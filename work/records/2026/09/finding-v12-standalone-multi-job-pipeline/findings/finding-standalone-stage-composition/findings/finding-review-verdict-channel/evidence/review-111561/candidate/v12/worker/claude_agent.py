"""The REAL Claude provider adapter, injected into `baton_worker.main(agent=)`.

W39357, under `work/records/2026/08/finding-v12-first-useful-dogfood-task/
findings/finding-real-claude-adapter-image/`.

WHAT THIS IS. One agent object with the two methods `baton_worker` calls. It
runs a real provider against a private copy of the staged source and writes the
declared proposal tree. It is the first thing in this campaign that makes an
actual model turn happen inside a worker container.

WHAT IT IS EMPHATICALLY NOT, and each line is a boundary somebody could
reasonably have crossed:

  NOT THE WORKER. It does not frame, correlate, measure bytes, or publish
  `/output/output.json`. `baton_worker` does all of that, and it does it AFTER
  this returns -- which is what keeps a provider's output from ever becoming
  protocol framing or success identity.
  NOT W17110's SPIKE. Its pinned INSTALLATION facts are reused -- the base
  image, the exact CLI version, the trust store, the pre-owned home. Its
  `trial.mjs`, its `w17110-ping-pong` result shape and its direct Docker
  lifecycle are not.
  NOT A CREDENTIAL READER. It never opens, reads, hashes, prints, copies or
  inspects a bearer. It links the provider's expected path at the fixed slot
  and lets the provider do its own authentication.
  NOT A TRANSCRIBER OF ITS CHILDREN. It starts two processes that can read the
  attempt's credential, and it publishes NEITHER ONE'S OUTPUT. Both children
  run with both streams on `/dev/null`, so no byte a child wrote exists in
  this program to be interpolated into the proposal by accident or by a later
  edit. The evidence is the exit status and the frozen command, which this
  adapter and the operator authored.
  NOT A SETTLEMENT. A disposition is a CLAIM about what happened; the manager
  freezes, collects and settles. Nothing here can report `completed` for a turn
  that produced no candidate.

THE FOUR THINGS IT ACTUALLY DOES, in order, and every one of them in bounded
container-private space:

  1. read the frozen task at `/input/task.json`;
  2. copy `/input/source` into a private directory under the `/tmp` tmpfs --
     the staged source stays read-only and is never the copy destination;
  3. run the provider there, once, over a closed argv;
  4. author `proposal/{candidate,change.patch,result.json,verification.txt}`
     under the one declared output path.

WHY NO CHILD'S OUTPUT IS PUBLISHED. The provider holds the attempt's bearer,
and the task's own verification command is code out of the candidate the
provider has just edited, running as the same uid with the same mount still
readable. Their stream bytes are therefore exactly the class this proposal must
not carry, and no rule available here can tell one of those bytes from another
without reading the bearer -- which the confirmed boundary forbids, and forbids
for a good reason. So the bytes are not read at all. See the module-level
comment above `_ran`.

ONE STREAM IS NOW READ, AND ONLY TO CHOOSE ONE OF THIS FILE'S OWN WORDS.
W55360, approver ruling event 55479, narrowly supersedes the rule above for
PROVIDER STDOUT and nothing else: the adapter asks the CLI for a structured
JSON record, drains that stream through a bounded anonymous pipe, matches one
member against a closed map, and throws the bytes away. Provider stderr and
both verification streams are untouched and remain on `subprocess.DEVNULL`.
What crosses into `result.json` and the worker's recap is `api-error` or
`unclassified` -- words spelled in THIS file, never the provider's spelling of
them, never the document, never a parser's complaint about it.

`api-error` IS DESCRIPTIVE AND IS NOT A CAUSE. It says the provider's own
terminal record called the ending an API error. It is NOT evidence of an
expired credential, a limited or suspended account, a missing scope, or a
network fault, and no prose here, in the proposal, or in any operator
documentation may present it as one. Two supervised rounds under W51487 wanted
exactly that causal answer; this signal cannot give it, and saying otherwise
would make a supervised pilot act on a diagnosis nobody made.

WHY THE HOME IS PRIVATE AND THE CREDENTIAL IS A LINK. The runtime posture fixes
`--read-only` with tmpfs only at `/tmp` and `/dev/shm`, and the manager mounts
the bearer at `/run/baton/credentials/<slot>` rather than at the provider's own
path. A provider that writes anywhere under its home therefore cannot start at
all from an image-owned link. So the home is made at run time under `/tmp` and
the provider's credential path is a SYMLINK to the slot: the bytes are never
read by this program and never leave the mount, and the link dies with the
container.
"""

import json
import os
import re
import select
import shutil
import stat
import subprocess
import tempfile
import threading
import time

__all__ = ["ClaudeAgent"]

# -- the fixed paths, all constants of the DOGFOOD WORKLOAD --------------------
#
# Named here rather than taken as operands for the reason the worker names its
# own: a path a payload can vary is a path a runtime can be pointed at wrongly.
# These are the workload's convention and NOT worker-control protocol
# vocabulary -- the same boundary the parent finding draws for Git.

INPUT_ROOT = "/input"
OUTPUT_ROOT = "/output"

# The frozen task, and the staged tree it is about.
TASK_DOCUMENT = "task.json"
SOURCE_ROOT = "source"

# WHAT A TASK DOCUMENT IS, exactly. Closed, and versioned in the name, so a
# document from another generation is refused by an equality test rather than
# by parsing a version member and deciding what to do about it -- the same rule
# the launch document is under.
TASK_SCHEMA = "baton.dogfood-task/2"
TASK_MEMBERS = ("schema", "task_id", "instructions", "verification",
                "source_root", "source_profile", "declared_base")

# W71917: THE PROFILE PACKAGE, UNDER WHICHEVER NAME IT ARRIVED.
#
# `Dockerfile.claude` copies `source_profiles` in as a TOP-LEVEL package, not
# as `baton_v12.source_profiles`, and that is the image's pinned rule being
# kept rather than bent: nothing from `baton_v12` travels, because a worker
# that can import the manager is a worker one bug away from holding the
# manager's capabilities. The profile package is not the manager -- it imports
# nothing from `baton_v12`, and `baton_v12.worker_manager` imports nothing from
# it, which `tests/manager/test_source_boundary` holds both ways -- so it
# travels under its own name and the `baton_v12` namespace still does not exist
# in the image.
#
# ONE SPELLING, AND `baton_v12` IS NOT IT. An import naming that package --
# even in a fallback for the distribution's own test run -- would be this
# module able to spell the manager's namespace, which is the property
# `test_this_module_imports_nothing_from_the_manager` holds as a fact about
# this source rather than as a comment. The suites that drive this module put
# the package's directory on `sys.path` under this same top-level name, which
# is reproducing the image's layout rather than relaxing the rule.
import source_profiles as _profiles

# Where the checkout and the editable copy live. BOTH ARE IN THE WORKSPACE,
# which is W71917's whole subject: the workspace is disk-backed and the tmpfs
# is 64 MiB, so a real build or test pass cannot happen anywhere else.
CANDIDATE_NAME = "candidate"

# Version-control metadata, skipped by the copy and by the diff.
#
# NOT AN INFERENCE ABOUT THE TREE. This is applied only when the assignment
# DECLARED the git profile, so no tree is examined to decide whether it looks
# version-controlled; a generic profile carrying a directory of this name is
# ordinary material and is copied and diffed like any other.
VCS_METADATA = ".git"

# The private scratch root. `/tmp` is the adapter's tmpfs: `rw,noexec,nosuid,
# nodev,size=64m`, private to this container and gone when it ends.
PRIVATE_ROOT = "/tmp"

# -- the provider ------------------------------------------------------------

# WHERE THE MANAGER PUTS THE BEARER, and the slot this workload asks for. The
# root is the credential contract's; the slot name is this workload's request.
CREDENTIAL_ROOT = "/run/baton/credentials"
CREDENTIAL_SLOT = "claude"

# WHERE THE PROVIDER LOOKS FOR IT, relative to its own HOME. W17110 measured
# this: a FILE-shaped provider mount at `$HOME/.claude/.credentials.json`
# leaves the state directory writable, which the runtime needs.
PROVIDER_HOME_STATE = ".claude"
PROVIDER_CREDENTIAL = ".credentials.json"

# THE CLOSED ARGV, and the one place it departs from W17110.
#
# The spike ran `--print --permission-mode plan`, which is right for a
# ping-pong that must touch nothing and wrong for a task whose whole point is
# to edit files. W39364 then ran `--permission-mode acceptEdits`, and live
# dogfood measured what that actually was: an inner COMMAND allowlist. The
# agent could edit its private candidate but was refused the task's own Python
# verification, which the outer worker then ran itself -- proving the command
# belonged inside the container and was never a host-authority request.
#
# W64268 ruled that the container IS the boundary. Inside an accepted trusted
# worker runtime the agent may run the image's tools without per-command
# approval, so this tuple names the CLI's bypass ACTIVATION flag. Two nearby
# spellings are deliberately NOT used: `--allow-dangerously-skip-permissions`
# only permits bypass to be selected later, and `--permission-mode
# bypassPermissions` reintroduces the mode operand this Work removed.
#
# This is inner policy only. The external boundary -- read-only inputs, one
# private writable scratch, dropped capabilities, no host socket, no privilege,
# manager-owned lifecycle -- is `worker_manager.oci`'s and is UNCHANGED.
#
# `--print` is the non-interactive mode: one prompt, one answer, no terminal.
# `--output-format json` is W55360's operand and is the whole of that Work's
# departure from W39357. It asks the CLI for a STRUCTURED terminal record on
# stdout instead of prose, which is what makes reading that one stream a
# bounded, closed-vocabulary act rather than a diagnostic passthrough.
PROVIDER_PROGRAM = "claude"
PROVIDER_ARGUMENTS = ("--print", "--dangerously-skip-permissions",
                      "--output-format", "json")

# HOW MUCH OF THE PROVIDER'S STRUCTURED STDOUT IS EVER HELD, and W39357's
# deleted ceilings are NOT back: those bounded a window onto prose that was
# then published, and this one bounds a document that is parsed and thrown
# away. Nothing derived from these bytes leaves this module except one word
# chosen from `PROVIDER_FAILURE_REASONS` below.
#
# The stream is drained to EOF whatever its size -- the ceiling bounds what is
# RETAINED, never what is read -- so a verbose provider can neither block on a
# full pipe nor make this process allocate without limit. Output past the
# ceiling makes the record `unclassified` rather than being reassembled.
MAX_PROVIDER_RECORD = 1 << 16

# HOW LONG THE DRAIN MAY OUTLIVE THE PROVIDER PROCESS ITSELF, and this bound
# is W55360 review (2026-09-01T03:35:56Z) [P1]. EOF on the read end arrives
# when the LAST writer closes it, not when the provider exits -- and a child
# the provider started inherits that descriptor. A provider that spawns a
# long-lived descendant and exits therefore left a reader waiting on an EOF
# nobody was going to send, which wedged the worker AFTER the turn was over
# and made `PROVIDER_SECONDS` not a bound at all.
#
# So completion is bounded independently of EOF. Once the provider process is
# gone, whatever it wrote is already in the pipe and readable at once; this is
# the grace for reading it, not for waiting on anybody else's descriptor. When
# it runs out the record is PARTIAL -- the stream was never proved finished --
# and a partial record is `unclassified` exactly as an over-ceiling one is.
PROVIDER_DRAIN_SECONDS = 2

# The drain's wait slice. It only decides how promptly the reader notices that
# the provider has ended; the reader is never idle-waiting on anything else.
PROVIDER_DRAIN_SLICE = 0.05

# THE CLOSED MAP, AND IT HAS ONE ENTRY ON PURPOSE. W55360's approver ruling:
# `api_error` is the single value the evidence has actually observed, so it is
# the single value that earns a word. Every other spelling -- unknown, absent,
# duplicated, malformed, over-ceiling, not a string, not an object -- becomes
# `UNCLASSIFIED`, and adding a second entry requires its own observed evidence
# and its own case.
#
# SUBSTRING AND PATTERN MATCHING ARE FORBIDDEN HERE. The value is compared by
# equality and nothing else: a regex over provider-authored text is the wider
# classifier W55360 explicitly declined to become.
PROVIDER_FAILURE_REASONS = {"api_error": "api-error"}

# The words this adapter publishes when it did not get one from the map. Each
# is THIS module's own vocabulary, not the provider's.
UNCLASSIFIED = "unclassified"
PROVIDER_TIMED_OUT = "timeout"
PROVIDER_START_ERROR = "start-error"

# How long one provider turn is given. A real turn is minutes; a bound that
# cannot be reached turns ordinary work into a failure, and a bound that does
# not exist turns a wedged provider into a wedged container.
PROVIDER_SECONDS = 3600

# How long the task's own verification command is given. Bounded separately
# because it is the WORKLOAD's command rather than the provider's, and the two
# have nothing to do with each other.
VERIFICATION_SECONDS = 900

# How long ONE source-checkout step is given. W71917. Bounded separately again,
# and smaller than either of the two above: a local clone from a mounted
# directory is seconds of disk copying with no network in the container and
# nothing to wait on, so a step still running after this is wedged rather than
# busy.
CHECKOUT_SECONDS = 900

# -- what this adapter writes ------------------------------------------------

CANDIDATE = "candidate"

# W85497: WHERE A CHILD'S EPHEMERA GO, and the reason they are named here.
#
# Both children run WITH `candidate` AS THEIR WORKING DIRECTORY, and the
# candidate is the tree this adapter walks, diffs, revalidates and publishes.
# Anything an interpreter drops beside the source it is reading therefore
# becomes a PROPOSED CHANGE. The first ordinary self-hosted W71917 retry is
# the measurement: `python3 -m compileall -q src tests tools` wrote 149
# `__pycache__` entries into the candidate and the resulting patch was
# 10,779,527 bytes for ten real paths.
#
# THE PROVIDER'S CACHES ARRIVE BEFORE THE WALK, which is why this is not only
# the verifier's problem. The provider is prompted to run the verification
# command itself before returning, and `work` diffs the tree AFTER that turn --
# so a provider that does as it is asked contaminates the proposal even if the
# adapter's own verification writes nothing at all.
#
# EACH NAME IS A DIRECTORY UNDER THE PRIVATE SCRATCH, never under `candidate`
# and never the ambient default: `TMPDIR` unset would put temporary files in
# `/tmp` (harmless but unbounded across turns), and `XDG_CACHE_HOME` unset
# resolves under `HOME` -- which for the provider is the directory holding its
# credential link.
PROVIDER_EPHEMERA = "provider-ephemera"
VERIFICATION_EPHEMERA = "verification-ephemera"
VERIFICATION_HOME = "verification-home"
PATCH = "change.patch"
RESULT = "result.json"
VERIFICATION = "verification.txt"

# -- W105575: the prepared private line --------------------------------------
#
# Under the `git-line` profile the workspace IS the manager's durable private
# repository, already detached at the declared base, and this adapter's job
# gains exactly one act: COMMIT. Everything below exists to make that commit
# an account somebody can check rather than a claim.

# The durable object transport, inside the declared output. INCREMENTAL, over
# the immutable base to the new head: the recipient of a proposal already holds
# the base -- it is the canonical target -- so shipping its history again would
# be a second copy of the thing the private line exists to avoid.
BUNDLE = "objects.bundle"

# The line workload's own result document. A SECOND GENERATION, because its
# declared output no longer carries a `candidate` tree: the candidate is a
# commit now. The existing readers of `/1` consume that tree, so the version is
# what keeps them reading the shape they were written for.
LINE_RESULT_SCHEMA = "baton.dogfood-proposal/2"

# THE WORKER-OWNED CLAIM, and its namespace. `result_metadata` is the frozen
# schema's opaque per-output extension point; `baton_worker` carries it without
# reading it and the generic manager never branches on it. What travels is
# WORKER-OWNED FACT ONLY -- what this turn was built on, what it produced, and
# where its objects are inside its own declared output.
#
# WHAT MAY NEVER TRAVEL HERE: an artifact id, media type, byte count, content
# digest or custody locator; any manifest, result, input, policy or profile
# digest; any assignment reference, generation or operation identity. Those are
# the manager's measurements and identities, and a worker that minted one would
# be certifying its own output.
CLAIM_NAMESPACE = "baton.git-proposal/1"
CLAIM_MEMBERS = ("base", "head", "transport", "recap")
MAX_TRANSPORT = 128

# -- W110772: the review turn ------------------------------------------------
#
# THE SAME CONTAINER, THE SAME IMAGE, THE SAME PROVIDER, AND A DIFFERENT JOB.
# A review reads a frozen checkpoint and decides about it; it edits nothing,
# commits nothing and proposes nothing. What selects the branch is the launch
# document's `role`, which `baton_worker` has already validated and which the
# manager fills from the worker's configured launch role -- so the workload is
# chosen by an operand this container was launched under rather than by
# inspecting the filesystem for a shape that looks reviewable.
REVIEW_ROLE = "review"

# WHICH DECLARED OUTPUTS A SHARED JOB CARRIES, and why they are common rather
# than per-stage. `single_worker._matches` compares every stage of a Job
# against that Job's ONE input manifest digest, so an implementation manifest
# and a review manifest cannot both satisfy it. The declaration set is
# therefore the union and each role produces its own half, answering the other
# half `missing-optional`. The assembly owns constructing that manifest; this
# adapter owns knowing which half is its.
COMMON_OUTPUTS = ("proposal", "findings", "logs")
IMPLEMENTATION_OUTPUTS = ("proposal",)
REVIEW_OUTPUTS = ("findings", "logs")

# WHERE THE PROVIDER WRITES ITS REPORT, and it is deliberately NOT under
# `/output`. Every declared output directory is measured, sealed and collected
# by the manager, so a provider-authored file inside one would be adopted
# custody material before this adapter had looked at it. The report lands in a
# fresh private directory under the tmpfs, is validated here, and the findings
# output is then AUTHORED from it.
REVIEW_ROOM = "review-room"
REVIEW_REPORT = "review-report.json"

# THE REPORT'S CLOSED CONTRACT. Versioned in the name, like every other
# document this workload reads, so one from another generation is refused by an
# equality test rather than read for the parts that look familiar.
REVIEW_REPORT_SCHEMA = "baton.review-report/1"
REVIEW_REPORT_MEMBERS = ("schema", "verdict", "findings")

# The reviewer's closed answer. THE SAME THREE WORDS THE MANAGER RECORDS, and
# they are spelled here rather than imported because nothing from `baton_v12`
# travels into this image -- `test_claude_agent` holds the two against each
# other so they cannot drift.
REVIEW_VERDICTS = ("accepted", "changes-requested", "rejected")

# How many bytes of report this adapter will read. A document written by the
# provider is input from outside this program, so the bound is this program's.
MAX_REPORT_BYTES = 1 << 20
MAX_FINDINGS = 1 << 16

# WHAT THE FINDINGS OUTPUT CARRIES, both authored by this adapter from the
# validated report. `report.json` is the closed document and `findings.txt` is
# its prose, because a human opening the findings of a review wants the words
# and a consumer wants the structure.
REVIEW_RESULT = "report.json"
REVIEW_FINDINGS = "findings.txt"

# AND WHAT THE LOGS OUTPUT CARRIES. Adapter-authored status and check
# summaries, and nothing a child wrote: the provider holds this attempt's
# bearer, so its streams are exactly the bytes W39357's boundary keeps out of
# published material. The findings are a deliberately authored artifact
# adopted from a validated document; they are NOT a diagnostic-stream
# exemption, and no raw stdout, stderr or credential content reaches either.
REVIEW_LOG = "review.json"
REVIEW_LOG_SCHEMA = "baton.review-log/1"

# THE WORKER-OWNED CHECKPOINT-REVIEW CLAIM, and its namespace. The same shape
# `CLAIM_NAMESPACE` establishes for a proposal, one layer over: what this turn
# decided, and what it observed about the source it decided over.
#
# WHAT MAY NEVER TRAVEL HERE, exactly as for the proposal claim: an artifact
# id, media type, byte count, content digest or custody locator; any manifest,
# result, input, policy or profile digest; any attachment, checkpoint,
# assignment reference, generation or operation identity. Those are the
# manager's, and it re-reads every one of them from its own owner.
REVIEW_CLAIM_NAMESPACE = "baton.checkpoint-review/1"
REVIEW_CLAIM_MEMBERS = ("base", "head", "tree", "verdict")

# THE COMMIT'S AUTHOR, spelled here and composed onto the argv. The container
# is `--read-only` with a private HOME under the tmpfs and no Git configuration
# at all, so an identity that is not on the command line is not an identity;
# and one taken from the environment would be whatever the image happened to
# leave behind.
COMMIT_NAME = "Baton worker"
COMMIT_EMAIL = "worker@baton.invalid"

# WHY EVERY VECTOR CARRIES `safe.directory`. The runtime posture pins
# `--user 65532:65532` while the line and the mount are the manager's, so Git's
# dubious-ownership check applies to a repository this worker was deliberately
# given. Composed as ONE per-command override: nothing writes a configuration
# file, and no global state outlives the vector it was composed for.
#
# AND WHY THE COMMIT ALSO CARRIES `core.hooksPath`. W105575 review 2026-09-07:
# `--no-verify` skips `pre-commit` and `commit-msg` and leaves
# `prepare-commit-msg` enabled, so it is not the no-hook guarantee it looks
# like. Pointing the hook path at a name that is not a directory is what makes
# "no hook runs" true for every hook rather than for the two that were named.
NO_HOOKS = "/dev/null"

# The worker's reserved names inside the workspace, which are NOT candidate
# material and must not become one.
#
# `output.json` is `baton_worker`'s completion envelope and `.publishing` is
# the name it stages that document under. BOTH ARRIVE AFTER THIS ADAPTER
# RETURNS -- the worker measures the declared outputs and publishes the
# envelope once `work` has answered -- so an adapter that excluded only what it
# writes itself would leave the line permanently dirty and the manager's own
# checkpoint freeze would refuse it. They are named here, and
# `test_claude_agent` holds them against `baton_worker`'s own literals so the
# two cannot drift.
COMPLETION_MANIFEST = "output.json"
COMPLETION_STAGING = COMPLETION_MANIFEST + ".publishing"

# The manager's per-attempt result root, whose exact name carries a runtime
# attempt id this adapter is never told. A deliberate ONE-GLOB reservation of
# that namespace rather than an exact name, and it is the only pattern here
# that is not literal.
RESULT_ROOT_PATTERN = "result-*"

# What a declared output path may not contain if it is to be written as an
# exact ignore pattern. A declared path is a PATH; an ignore entry is a
# PATTERN, and the characters below are the ones that make the two differ. A
# declared path carrying any of them is refused rather than escaped, because
# guessing at an escaping is how a reserved name silently stops being reserved.
IGNORE_METACHARACTERS = "*?[]!#\\"

# The two tree entry modes a candidate file may have. Everything else Git can
# put in a tree -- a symlink at `120000`, a gitlink at `160000`, a subtree --
# is the committed half of the walk's own type boundary, and is refused on the
# side a recipient actually resolves rather than only on the side this adapter
# happened to walk.
TREE_FILE_MODES = ("100644", "100755")

# The one remaining ceiling, and note what it is NOT. `recap` is composed by
# this adapter out of its own disposition vocabulary; the bound is there
# because the worker frames it, not because anything untrusted reaches it.
#
# There were two more here -- `MAX_DIAGNOSTIC` and `MAX_VERIFICATION` -- and
# they are gone rather than raised. They existed to bound how much of a CHILD'S
# stream crossed into this process, and no child's stream crosses at all now,
# so a ceiling on the amount is a ceiling on nothing. See `_ran`.
MAX_RECAP = 4000

# THE COOPERATIVE MODE, and it is a stated cooperation rather than custody.
# W36540 owns unconditional custody; until it lands, a worker that writes
# owner-only material leaves a tree the manager fails closed on. So this writes
# group-readable and says so out loud -- it is not a security boundary and does
# not pretend to be one.
DIRECTORY_MODE = 0o2775
FILE_MODE = 0o664

# A source tree this adapter will copy, bounded on both axes. The manager
# measured and staged it; this is the second bound, at the party that actually
# walks it.
MAX_SOURCE_ENTRIES = 2000
MAX_SOURCE_BYTES = 64 * 1024 * 1024

_TASK_ID = re.compile(r"\A[a-zA-Z0-9][a-zA-Z0-9._-]{0,127}\Z")


class TaskRefusal(Exception):
    """Something this adapter will not proceed from.

    Raised rather than answered, because `baton_worker` turns an agent
    exception into a bounded correlated fault frame with no traceback -- which
    is exactly the right shape and is not this module's to reimplement.
    """


class ClaudeAgent:
    """One real provider turn, over one staged source tree."""

    def __init__(self, *, run=None, home=None):
        """`run` and `home` are SEAMS FOR TESTS and are not operands.

        A caller inside the image supplies neither: `main(agent=ClaudeAgent())`
        is the whole construction. They exist so the argv, the environment and
        the write boundary can be proved without a provider, a credential or a
        network -- which is what this checkpoint's acceptance asks for and what
        no live run could establish deterministically anyway.
        """
        self._run = run if run is not None else subprocess.run
        self._home = home

    # -- the two methods `baton_worker` calls --------------------------------

    def consider(self, seen, request):
        """This runtime is not entitled to be asked, and says so if it is.

        The one-container topology means `consider` never reaches an agent --
        `baton_worker` refuses the operation as an entitlement fault before
        dispatch. This exists so the object satisfies the whole agent contract
        rather than the half that happens to be reachable, and it declines
        rather than inventing a decision it has no basis for: a provider-backed
        adapter has not looked at anything at this point.
        """
        return {"decision": "decline",
                "contract_digest": _digest(seen.get("contract", "")),
                "reason": "this dogfood adapter does not consent; the "
                          "operator selected the task before the container "
                          "started"}

    def work(self, seen, declared):
        """Run the frozen task and author the declared proposal.

        `seen` is the validated launch document and `declared` is the manager's
        output declaration list, both handed over by `baton_worker`. Neither is
        second-guessed here: what is declared is what is written to, and the
        worker measures the result afterwards.
        """
        # W110772: WHICH JOB THIS CONTAINER WAS LAUNCHED FOR. The launch
        # document's validated `role` selects the branch; nothing here
        # inspects the filesystem to decide what kind of turn it is.
        if seen.get("role") == REVIEW_ROLE:
            return self._review(declared)
        if len(declared) == 1:
            # THE ORIGINAL SINGLE-OUTPUT WORKLOAD, byte-for-byte unchanged.
            one, absent = _one_declaration(declared), []
        else:
            produce, absent = _selected(declared, IMPLEMENTATION_OUTPUTS,
                                        "implementation")
            one = produce[0]
        proposal = os.path.join(OUTPUT_ROOT, one["path"])
        task = _task()
        scratch = self._scratch()
        # W71917: THE PLAN RUNS, AND IT RUNS IN THE WORKSPACE.
        #
        # What this replaces: the source mount was copied into a directory
        # under the 64 MiB tmpfs and the profile was never consulted at all.
        # Run7 review [P0] -- the profile package composed plans that no
        # component executed, so the ruled read-only-source-to-workspace
        # transition did not happen and a real build could not fit anywhere.
        #
        # `OUTPUT_ROOT` IS THE WORKSPACE. The manager binds one disk-backed
        # manager-created workspace there; the tmpfs keeps only the child
        # ephemera roots below, which is what bounded scratch is for.
        source = os.path.join(INPUT_ROOT, task["source_root"])
        plan = self._checkout(task, source)
        baseline = plan["source_root"]
        line = plan["profile"] == _profiles.checkout.GIT_LINE_PROFILE
        if line:
            # W105575: THERE IS NOTHING TO COPY. The workspace IS the durable
            # private repository the manager materialized and detached before
            # this container existed, so the candidate is the mounted worktree
            # and the baseline is a COMMIT rather than a second tree on disk.
            #
            # THE EXCLUSIONS ARE WRITTEN FIRST, before anything asks whether
            # the line is clean: the manager's own result root is already
            # sitting in this workspace, and an entry check taken before the
            # reservation would refuse the arrangement it was handed.
            candidate = OUTPUT_ROOT
            reserved = _reserved(declared)
            _reserve(candidate, reserved)
            entry = self._entered(candidate, plan["base"], reserved)
            skip, walk_skip, copied = None, reserved | {VCS_METADATA}, None
        else:
            # WHAT THE PROVIDER EDITS IS A COPY OF THE BASELINE, so the diff
            # has something unmodified to be a diff against. Both live in the
            # workspace: an editable tree on the tmpfs is the ceiling this Work
            # exists to remove.
            candidate = os.path.join(OUTPUT_ROOT, CANDIDATE_NAME)
            skip = VCS_METADATA if plan["profile"] == _profiles.GIT_PROFILE \
                else None
            copied = _copy_tree(baseline, candidate, skip=skip)
            entry, walk_skip = None, None
        what = "the candidate line" if line else "the candidate copy"
        # W85497 review 2026-09-04T14:44:23Z: every predictable child root is
        # created EXCLUSIVELY before the provider runs. The provider owns the
        # candidate turn and must not get a window in which an absent verifier
        # name can be replaced with a link into that candidate.
        environments = self._child_environments(scratch)
        verification_environment, verification_directories = (
            self._pinned_environment(scratch, environments["verification"]))
        try:
            provider = self._provider(task, candidate, scratch,
                                      environments["provider"])
            # THE PROVIDER OWNED THIS TREE, so it is held to the staged tree's
            # own rules before anything reads or copies it. Review [P1]: the
            # source check ran before Claude and nothing ran after, so a link
            # the provider created was dereferenced by the diff and copied as
            # regular bytes into the host-visible proposal -- and the
            # credential mount is one of the things a link can name.
            written = _checked_tree(candidate, what=what, skip=walk_skip)
            # THE PROVIDER'S ENDING DECIDES NOTHING ON ITS OWN. What is written
            # is decided by what is ON DISK afterwards, which is why the diff
            # is taken before the disposition is chosen: a provider that
            # exited 0 and changed nothing produced no candidate, and one that
            # exited non-zero after editing left something an operator still
            # has to see.
            # AGAINST THE BASELINE, WHICH IS WHAT THE COPY WAS MADE FROM.
            # For a git profile that is the checkout at the DECLARED BASE, so
            # the patch is against the revision the assignment named rather
            # than against whatever the mount happened to be on.
            if line:
                # THE SAME QUESTION, ASKED OF THE REPOSITORY. Which paths
                # changed is what the line already knows, and a second opinion
                # composed here would be this adapter deciding what Git
                # decides. What this still owns is the BYTES it measured, which
                # is what binds the account below to what was published.
                measured = _measured(candidate, written, what=what)
                self._unmoved(candidate, entry)
                patch = self._pending(candidate)
            else:
                patch, measured = _diff(baseline, candidate, written, skip=skip)
            verification = (self._verify(
                task, candidate, verification_environment,
                verification_directories)
                            if provider["ok"] and patch else None)
            # THE VERIFICATION COMMAND IS THE PAYLOAD'S, and it ran between
            # the measurement and the publication. Review [P1]: proving the
            # paths were still regular held their TYPE and not their BYTES, so
            # a command that overwrote a checked file in place published
            # contents the patch never described. What is proved here is the
            # measurement itself.
            _revalidated(candidate, written, measured, what=what,
                         skip=walk_skip)
            disposition, why = _disposition(provider, patch, verification)
            if line:
                # THE COMMIT HAPPENS WHATEVER THE DISPOSITION IS, and that is
                # deliberate. The manager freezes an immutable checkpoint over
                # this line after every ending, and its profile refuses a dirty
                # worktree -- so a turn that produced changes and declined to
                # commit them would leave the line unfreezable and the Work
                # stuck. What the disposition decides is whether anything is
                # PUBLISHED, not whether the private history is honest.
                head = self._commit(candidate, task, entry,
                                    measured) if patch else None
                changed = self._changed(candidate, plan["base"], head)
                self._publish_line(proposal, candidate, plan["base"], head,
                                   verification,
                                   result={"schema": LINE_RESULT_SCHEMA,
                                      "task_id": task["task_id"],
                                      "disposition": disposition,
                                      "why": why,
                                      "changed_paths": changed,
                                      "base": plan["base"],
                                      "entry_head": entry,
                                      "head": head,
                                      "provider": {
                                          "status": provider["status"],
                                          "failure_reason":
                                              provider.get("failure_reason"),
                                          "seconds_bound": PROVIDER_SECONDS},
                                      "verification": (
                                          {"status": verification["status"],
                                           "argv": list(task["verification"])}
                                          if verification is not None
                                          else None)})
            else:
                head, changed = None, sorted(patch)
                _publish(proposal, candidate, written, measured, patch,
                         verification,
                         result={"schema": "baton.dogfood-proposal/1",
                                 "task_id": task["task_id"],
                                 "disposition": disposition,
                                 "why": why,
                                 "changed_paths": changed,
                                 "source_entries": copied,
                                 # W55360: the mapped word, or null on a clean
                                 # turn. This is the ONLY member of this record
                                 # derived from anything a child wrote, and it
                                 # is one of a closed set this module spells.
                                 "provider": {
                                     "status": provider["status"],
                                     "failure_reason":
                                         provider.get("failure_reason"),
                                     "seconds_bound": PROVIDER_SECONDS},
                                 "verification": (
                                     {"status": verification["status"],
                                      "argv": list(task["verification"])}
                                     if verification is not None else None)})
        finally:
            for _name, descriptor in verification_directories:
                os.close(descriptor)
        recap = (f"{disposition}: {why}"
                 f" ({len(changed)} changed path(s))")[:MAX_RECAP]
        return {"disposition": ("completed" if disposition == "candidate"
                                else "unable"),
                "outputs": [{"name": one["name"], "status": "present",
                             "result_metadata": (
                                 _claim(plan["base"], head, recap)
                                 if head is not None else {})}]
                           + _absent(absent),
                "recap": recap}

    # -- W110772: the review turn --------------------------------------------

    def _review(self, declared):
        """Assess a frozen checkpoint and author a findings and a logs output.

        WHAT THIS DOES NOT DO, and each line is something the implementation
        branch above does that a review must not: it does not check out, copy,
        reserve, edit, commit, bundle or verify anything, and it never writes
        into the source it was given. The manager mounted the line READ-ONLY
        for exactly that reason and this reads it in place.

        THE OBSERVATION BRACKETS THE PROVIDER TURN. The head and tree are read
        before the provider runs and again afterwards, and a difference is a
        refusal rather than a disposition: a review of a tree that moved under
        it is a review of nothing in particular, and the manager would compare
        the second reading against a checkpoint frozen over the first.

        THE PROVIDER'S ENDING DECIDES NOTHING ON ITS OWN, which is the same
        rule the implementation branch keeps for the same reason. What decides
        the verdict is a report this adapter validated; a provider that exited
        0 and wrote nothing reviewed nothing, and one that exited non-zero
        after writing a valid report still did not earn a decision, because a
        turn that failed is a turn whose account is incomplete.
        """
        produce, absent = _selected(declared, REVIEW_OUTPUTS, "review")
        findings_output, logs_output = produce
        findings = os.path.join(OUTPUT_ROOT, findings_output["path"])
        logs = os.path.join(OUTPUT_ROOT, logs_output["path"])
        task = _task()
        # THE FIRST REVIEW WORKLOAD IS THE PREPARED LINE, EXPLICITLY. Another
        # profile is refused rather than attempted: what a review reads is a
        # frozen checkpoint on a private Git line, and there is no second
        # arrangement this adapter knows how to observe a base, head and tree
        # over.
        if task["source_profile"] != _profiles.checkout.GIT_LINE_PROFILE:
            raise TaskRefusal(
                f"this review workload reads the "
                f"{_profiles.checkout.GIT_LINE_PROFILE!r} profile and this "
                f"task names {task['source_profile']!r}; another review "
                f"profile is a workload this adapter does not have")
        source = os.path.join(INPUT_ROOT, task["source_root"])
        observed = self._observed(source, task)
        scratch = self._scratch()
        room = self._new_directory(scratch, REVIEW_ROOM)
        # A FRESH DESTINATION, PROVED. A previous turn's report standing in for
        # this one would be a verdict about a checkpoint nobody looked at, and
        # `_new_directory` creates exclusively -- so this is the second half of
        # that guarantee rather than a repetition of it.
        if os.path.lexists(os.path.join(room, REVIEW_REPORT)):
            raise TaskRefusal(
                f"the review report destination already exists; a report is "
                f"authored by this turn and never inherited")
        environments = self._child_environments(scratch)
        provider = self._provider(
            task, room, scratch, environments["provider"],
            prompt=_review_prompt(task, source, REVIEW_REPORT))
        report = _review_report(room) if provider["ok"] else None
        # THE SOURCE IS RE-READ AFTER THE TURN, whatever the turn did.
        again = self._observed(source, task)
        if again != observed:
            raise TaskRefusal(
                "the reviewed line moved while it was being reviewed; a "
                "verdict is about the exact objects this turn observed")
        _made(logs)
        _written(os.path.join(logs, REVIEW_LOG),
                 json.dumps({"schema": REVIEW_LOG_SCHEMA,
                             "task_id": task["task_id"],
                             "verdict": report["verdict"] if report else None,
                             "reviewed": observed,
                             "report_bytes": (len(report["findings"])
                                              if report else 0),
                             "provider": {
                                 "status": provider["status"],
                                 "failure_reason":
                                     provider.get("failure_reason"),
                                 "seconds_bound": PROVIDER_SECONDS},
                             "verification": None},
                            indent=1, sort_keys=True) + "\n")
        if report is None:
            # NO CLAIM ON ANY OUTPUT. The manager's reader finds none and
            # holds, which is what an unanswered review is worth. Answering
            # findings absent rather than empty is the same statement made in
            # the manager's own vocabulary.
            return {"disposition": "unable",
                    "outputs": [{"name": findings_output["name"],
                                 "status": "missing-optional",
                                 "result_metadata": {}},
                                {"name": logs_output["name"],
                                 "status": "present", "result_metadata": {}}]
                            + _absent(absent),
                    "recap": (f"unable: the review produced no usable report "
                              f"({provider.get('failure_reason') or 'absent'})"
                              )[:MAX_RECAP]}
        _made(findings)
        _written(os.path.join(findings, REVIEW_RESULT),
                 json.dumps(report, indent=1, sort_keys=True) + "\n")
        _written(os.path.join(findings, REVIEW_FINDINGS),
                 report["findings"] + ("" if report["findings"].endswith("\n")
                                       else "\n"))
        return {"disposition": "completed",
                "outputs": [{"name": findings_output["name"],
                             "status": "present",
                             "result_metadata": _review_claim(
                                 report["verdict"], observed)},
                            {"name": logs_output["name"], "status": "present",
                             "result_metadata": {}}] + _absent(absent),
                "recap": (f"{report['verdict']}: reviewed "
                          f"{observed['base'][:12]}..{observed['head'][:12]}"
                          )[:MAX_RECAP]}

    def _observed(self, source, task):
        """The three objects this turn is reviewing, read from the line.

        `head` AND `tree` ARE OBSERVED AND `base` IS PROVED. A repository
        cannot say which of its commits a checkpoint was declared against --
        the checkpoint profile takes that as an operand -- so the base is the
        one the frozen task names, and what this establishes is that the line
        actually contains it. Naming a base the mounted line has never heard of
        is a refusal here; naming one the checkpoint does not record is a
        refusal at the manager, which is where a claim about the checkpoint
        belongs.
        """
        declared = task["declared_base"]
        if declared is None:
            raise TaskRefusal(
                "this review task declares no base; a verdict is about a "
                "change from one revision to another and there is no first one")
        # `^{commit}` RATHER THAN THE BARE NAME. `rev-parse --verify` accepts
        # a well-formed forty-character object name as SYNTAX and echoes it
        # back whether or not the repository holds the object, so a base this
        # line has never seen would have verified itself. The peel is what
        # makes this a question about the line rather than about the spelling.
        base = self._revision(source, f"{declared}^{{commit}}",
                              "reviewed base")
        if base != declared:
            raise TaskRefusal(
                f"this review task declares base {declared!r} and the line "
                f"resolves it to {base!r}; a review names the object it read")
        return {"base": base,
                "head": self._revision(source, "HEAD", "reviewed head"),
                "tree": self._revision(source, "HEAD^{tree}",
                                       "reviewed tree")}

    # -- the private half ----------------------------------------------------

    def _checkout(self, task, source):
        """Turn the read-only mount into somewhere this worker may work.

        W71917. THE PLAN IS COMPOSED ELSEWHERE AND RUN HERE, which is the
        separation the profile package exists for: it never starts a process
        and imports no capability to, and this is the party that owns the
        failure of every command it named.

        EVERY STEP'S OUTPUT IS COMPARED WHEN THE PLAN SAYS SO. Run7 review
        [P1]: exit status alone cannot express "the worktree is at this exact
        commit", because the command that reports which commit it is on
        succeeds whatever the answer. A step carrying an expectation is
        checked against it, and a mismatch is a refusal rather than a
        disposition -- a worker that edited the wrong revision and said so
        afterwards would already have written the wrong patch.
        """
        try:
            plan = _profiles.checkout_plan(
                source, OUTPUT_ROOT, profile=task["source_profile"],
                declared=task["declared_base"])
        except _profiles.ProfileRefusal as refusal:
            raise TaskRefusal(
                f"this assignment's source profile cannot be planned: "
                f"{refusal}") from None
        for step in plan["steps"]:
            argv = list(step["argv"])
            try:
                answer = self._run(argv, capture_output=True, text=True,
                                   timeout=CHECKOUT_SECONDS)
            except OSError as failure:
                raise TaskRefusal(
                    f"the source checkout could not run {argv[0]!r} "
                    f"({type(failure).__name__})") from None
            except subprocess.TimeoutExpired:
                raise TaskRefusal(
                    f"the source checkout step {argv[0]!r} did not finish "
                    f"within {CHECKOUT_SECONDS} seconds") from None
            if answer.returncode != 0:
                # THE STEP'S OWN OUTPUT IS NOT REPRODUCED. It is composed from
                # a tree this worker was handed, which is the same reason
                # `verification.txt` carries no child output.
                raise TaskRefusal(
                    f"the source checkout step {argv[0]!r} failed with "
                    f"status {answer.returncode}")
            expect = step["expect_stdout"]
            if expect is not None \
                    and (answer.stdout or "").strip() != expect:
                raise TaskRefusal(
                    "the checkout is not at the base this assignment "
                    "declared; the source that was mounted contains that "
                    "commit or the step would have failed, so what differs "
                    "is which revision the worktree ended up on")
        return plan

    # -- W105575: the prepared private line ----------------------------------

    def _git(self, repository, *arguments, what, binary=False, allow=(0,),
             stdin=None):
        """One closed Git vector against the line, run through the same seam.

        THE OVERRIDES ARE COMPOSED, NEVER CONFIGURED. `safe.directory` is here
        because the repository is the manager's and this process is uid 65532;
        a configuration file written to make that go away would outlive the
        vector and apply to repositories nobody reviewed.

        `allow` EXISTS FOR THE ONE QUESTION GIT ANSWERS WITH A STATUS. An
        ancestry test is not an error when the answer is "no", and a helper
        that could not tell those apart would turn a fact into a failure.

        THE HOOK PATH IS ON EVERY VECTOR, not only on the commit. W105575
        candidate review 2026-09-07: `post-index-change` runs on an INDEX
        WRITE, so staging and even a status refresh reach a hook that a
        commit-only override never covers -- and the hooks directory belongs to
        a repository this worker did not create. One composed prefix rather
        than a policy applied at each call site, because a per-site rule is a
        rule with a gap in it the moment somebody adds a site.
        """
        argv = ["git", "-c", f"safe.directory={_line_path(repository)}",
                "-c", f"core.hooksPath={NO_HOOKS}",
                "-C", repository, *arguments]
        try:
            answer = self._run(argv, capture_output=True, text=not binary,
                               timeout=CHECKOUT_SECONDS, input=stdin) \
                if stdin is not None else \
                self._run(argv, capture_output=True, text=not binary,
                          timeout=CHECKOUT_SECONDS)
        except OSError as failure:
            raise TaskRefusal(
                f"the private line could not run {what} "
                f"({type(failure).__name__}); this profile is handed a "
                f"repository and never creates or repairs one") from None
        except subprocess.TimeoutExpired:
            raise TaskRefusal(
                f"the private line's {what} did not finish within "
                f"{CHECKOUT_SECONDS} seconds") from None
        if answer.returncode not in allow:
            raise TaskRefusal(
                f"the private line's {what} failed with status "
                f"{answer.returncode}")
        return answer

    def _revision(self, repository, revision, what):
        """One object name this line actually resolves, held to its grammar."""
        found = self._git(repository, "rev-parse", "--verify", revision,
                          what=what).stdout.strip()
        try:
            return _profiles.check_declared_base(found)
        except _profiles.ProfileRefusal as refusal:
            raise TaskRefusal(f"the private line's {what} is not one object "
                              f"name: {refusal}") from None

    def _pending(self, repository):
        """What the worktree is carrying that its HEAD commit is not.

        `--untracked-files=all` so a whole new directory is not one line, and
        `-z` so a path with a newline in it cannot forge an entry. Reserved
        names do not appear here at all: they are ignored, which is what
        `_reserve` established before this was ever asked.
        """
        return self._git(repository, "status", "--porcelain=v1", "-z",
                         "--untracked-files=all",
                         what="worktree status").stdout

    def _entered(self, repository, base, reserved):
        """The head this turn was ADMITTED at, proved rather than declared.

        TWO FACTS, AND THE WHOLE CORRECTION ROUND DEPENDS ON KEEPING THEM
        APART. `base` is the immutable revision this Work publishes against --
        the line's declared base, unchanged for every checkpoint the manager
        ever freezes. The ENTRY HEAD is where the line actually is right now:
        the base itself on the first turn, and the previous correction's
        checkpoint on every turn after that.

        An entry check that demanded `HEAD == base` would therefore reject the
        second round, and a claim that reported the entry head AS the base
        would publish a proposal whose source base is not the canonical target.
        So this proves the relationship instead of either equality: the line is
        clean, and the base is an ancestor of where it is.

        NOTHING TELLS THIS WORKER THE ENTRY HEAD. The manager's writer grant
        already validated it against the checkpoint it admitted; what is left
        for the worker is to confirm the line it received still descends from
        the revision it was told to build on, and to remember where it started
        so its own commit can be proved to continue it.
        """
        if not os.path.isdir(os.path.join(repository, VCS_METADATA)):
            raise TaskRefusal(
                f"this assignment declares a prepared development line and "
                f"{repository} is not a repository; a line is materialized by "
                f"the manager before the runtime starts and is never cloned, "
                f"reset or rebuilt here")
        # AN IGNORE RULE CANNOT UNTRACK ANYTHING, which is why this is a
        # refusal and not a repair. A line whose own history carries a file at
        # one of the reserved names would be dirty the moment the worker or
        # the manager wrote there, and no reservation this adapter makes can
        # change that -- so the arrangement is rejected while it is still
        # somebody's to correct.
        tracked = _paths(self._git(
            repository, "ls-files", "-z", "--", *sorted(reserved),
            what="reserved-name inventory").stdout)
        if tracked:
            raise TaskRefusal(
                f"the prepared development line already tracks "
                f"{tracked[0]}, which this workload reserves for the "
                f"manager's or the worker's own material; an ignore rule "
                f"cannot remove tracked content from a candidate")
        standing = self._pending(repository)
        if standing:
            raise TaskRefusal(
                "the prepared development line already carries uncommitted "
                "changes; this turn commits exactly what it produces, and a "
                "worktree that was handed over dirty makes that account "
                "impossible to take")
        entry = self._revision(repository, "HEAD", "admitted entry head")
        if entry != base:
            # THE BASE HAS TO BE IN THIS REPOSITORY BEFORE ANCESTRY MEANS
            # ANYTHING. An object the line does not hold makes the ancestry
            # question unanswerable rather than false, and the two deserve the
            # same refusal here for one reason: neither is a line this
            # assignment may publish against.
            if self._git(repository, "rev-parse", "--verify", "--quiet",
                         f"{base}^{{commit}}", what="declared base lookup",
                         allow=(0, 1)).returncode != 0 \
                    or self._git(repository, "merge-base", "--is-ancestor",
                                 base, entry, what="entry ancestry",
                                 allow=(0, 1)).returncode != 0:
                raise TaskRefusal(
                    "the prepared development line is not the base this "
                    "assignment publishes against, nor a descendant of it; a "
                    "correction continues one private history and this "
                    "worktree is on another")
        return entry

    def _unmoved(self, repository, entry):
        """The line is still where this turn was admitted, and nobody else
        wrote history into it.

        ASKED WHETHER OR NOT THE WORKTREE IS DIRTY, which is the correction
        this method exists for. A provider that COMMITS its own work leaves a
        clean worktree and an advanced head, so a check reached only on the way
        to committing would have adopted that history and reported it as this
        adapter's own account. Exactly one commit per turn is this module's,
        and that has to be true before anything is measured or published.
        """
        standing = self._revision(repository, "HEAD", "post-provider head")
        if standing != entry:
            raise TaskRefusal(
                "the private line's HEAD moved during the provider turn; this "
                "adapter authors exactly one commit per turn, and a history "
                "it did not write is not one it can give an account of")

    def _commit(self, repository, task, entry, measured):
        """ONE worker-authored commit, and the proof that it is this candidate.

        THE PROVIDER DOES NOT COMMIT, and `_unmoved` has already proved it --
        before the turn was measured, and whether or not the worktree was left
        dirty. This is the act, not the check.

        HOOKS ARE OFF BY PATH, NOT BY `--no-verify`. W105575 review 2026-09-07:
        that flag leaves `prepare-commit-msg` running, so it never was the
        no-hook guarantee it reads as. The override is composed by `_git` onto
        EVERY vector rather than onto this one, because the index write that
        stages the candidate reaches a hook of its own.

        THE MESSAGE IS THIS MODULE'S OWN WORDS. Nothing a child wrote is
        interpolated into it, for the reason `verification.txt` carries no
        child output: the provider holds the attempt's bearer.
        """
        self._git(repository, "add", "--all", "--", ".", what="candidate "
                  "staging")
        self._git(repository,
                  "-c", f"user.name={COMMIT_NAME}",
                  "-c", f"user.email={COMMIT_EMAIL}",
                  "commit", "--no-gpg-sign", "--allow-empty-message",
                  "--message", f"baton candidate: {task['task_id']}",
                  what="candidate commit")
        head = self._revision(repository, "HEAD", "committed head")
        if self._revision(repository, "HEAD^", "committed parent") != entry:
            raise TaskRefusal(
                "the commit this turn authored does not continue the head it "
                "was admitted at")
        self._identical(repository, entry, head, measured)
        return head

    def _identical(self, repository, entry, head, measured):
        """The COMMITTED change and the MEASURED change, proved to be one.

        W105575 review 2026-09-07. An empty status is a cleanliness gate and
        not this proof: a clean filter makes the committed blob differ from the
        bytes on disk while every status stays quiet, so the equality has to be
        taken over the objects themselves.

        AND IT IS PROVED IN BOTH DIRECTIONS. W105575 candidate review
        2026-09-07 found the hole that one direction leaves: a path Git IGNORES
        is not staged, does not appear in any status, and never enters the
        change set -- so a candidate whose verification passed BECAUSE that
        file was on disk committed a tree without it, and a recipient resolving
        the published head received something that was never verified. Reading
        the committed change and checking only its members against the measured
        tree cannot see that, because the missing path is in neither.

        So the equality that is actually taken is the one that matters to a
        recipient: THE COMMITTED TREE, RESTRICTED TO CANDIDATE MATERIAL, IS THE
        MEASURED TREE. The measured side comes from a filesystem walk that
        knows nothing about Git and cannot be talked out of seeing a file; an
        unrepresentable candidate is REFUSED rather than published, because the
        alternative is this adapter overriding a repository's own rules about
        what belongs in it.

        THREE MORE THINGS, AND A DELETION IS THE ONE WITH NO BLOB. Added and
        modified paths are compared byte for byte against what this adapter
        measured; a deleted path is proved ABSENT from that measurement, which
        is the only equality a removal has. Anything else Git can report --
        a type change, a rename, a submodule -- is refused rather than
        interpreted, because this adapter publishes an account of regular
        candidate bytes and nothing else.

        AND A TRANSFORMING FILTER IS REFUSED OUTRIGHT. `check-attr` is asked
        about exactly the paths in this change: an attribute that rewrites
        content on the way into the object store breaks the equivalence
        between what was verified and what was committed, and no comparison
        performed afterwards can restore it.
        """
        if self._pending(repository):
            raise TaskRefusal(
                "the private line is still not clean after its own commit; "
                "the worktree, the index and the new commit have to be one "
                "tree before anything is published")
        changed = _statuses(self._git(
            repository, "diff", "--name-status", "-z", "--no-renames",
            entry, head, what="committed change").stdout)
        for mark, relative in changed:
            if mark not in ("A", "M", "D"):
                raise TaskRefusal(
                    f"the commit carries a {mark!r} change at {relative}, "
                    f"which is not an added, modified or deleted regular path")
            _under(relative)
        _filterless(self._git(
            repository, "check-attr", "-z", "filter", "--",
            *[relative for _mark, relative in changed],
            what="candidate attribute inventory").stdout if changed else "")
        for mark, relative in changed:
            if mark == "D":
                if relative in measured:
                    raise TaskRefusal(
                        f"the commit deletes {relative} and this adapter "
                        f"measured bytes there; the account and the commit "
                        f"disagree about what the candidate contains")
                continue
            if relative not in measured:
                raise TaskRefusal(
                    f"the commit carries {relative} and this adapter measured "
                    f"nothing there; every committed byte is one this turn "
                    f"walked, bounded and read")
        self._representable(repository, head, measured)
        self._identical_bytes(repository, head, measured)
        return changed

    def _identical_bytes(self, repository, head, measured):
        """EVERY measured path's bytes against its committed blob, not only
        the ones Git said had changed.

        W105575 correction review 2026-09-07, and this is the third time one
        version of the same mistake has been caught, which is the reason the
        comparison finally does not consult Git's opinion at all. Equal PATH
        SETS still permit different BYTES: an index entry marked
        assume-unchanged makes a real edit invisible to status and to every
        diff, so the file is in both accounts, is absent from the reported
        change, and its committed blob is the ORIGINAL while the verification
        that passed read the new one. A recipient resolving the published head
        then receives something nobody verified.

        The lesson is the one the previous two rounds also taught and I kept
        re-learning too narrowly: a proof that asks Git WHICH paths matter
        inherits every reason Git might answer wrongly. So the subject here is
        the whole measured tree, one path at a time, and the only thing Git is
        asked for is the bytes it stored.

        ONE BATCH RATHER THAN ONE PROCESS PER FILE, bounded by the same ceiling
        `_checked_tree` already applies to the candidate. `-Z` so a path
        carrying any byte at all is still one request.
        """
        if not measured:
            return
        order = sorted(measured)
        request = b"".join(f"{head}:{one}".encode("utf-8") + b"\x00"
                           for one in order)
        raw = self._git(repository, "cat-file", "--batch", "-Z",
                        what="committed blob inventory", binary=True,
                        stdin=request).stdout
        offset = 0
        for relative in order:
            oid, kind, size, offset = _batch_header(raw, offset, relative)
            body = raw[offset:offset + size]
            if len(body) != size:
                raise TaskRefusal(
                    f"the committed blob for {relative} ended early")
            offset += size
            if raw[offset:offset + 1] not in (b"\n", b"\x00"):
                raise TaskRefusal(
                    f"the committed blob for {relative} is not delimited")
            offset += 1
            if kind != "blob":
                raise TaskRefusal(
                    f"the committed tree holds a {kind} at {relative}; this "
                    f"adapter publishes an account of regular candidate files")
            if _bytes_digest(body) != measured[relative]:
                raise TaskRefusal(
                    f"the bytes committed at {relative} are not the bytes "
                    f"this adapter measured and verified there; the object "
                    f"is {oid}")
        if offset != len(raw):
            raise TaskRefusal(
                "the committed blob inventory carries more records than this "
                "turn asked for")

    def _representable(self, repository, head, measured):
        """The committed tree and the measured tree, path for path.

        THE MEASURED SIDE IS THE INDEPENDENT ONE. It came from `_checked_tree`
        walking the filesystem, which is why this comparison can catch what
        Git's own reported change set cannot: an ignored addition is invisible
        to status, to staging and to every diff, and is sitting in the walk.

        `ls-tree -r` RATHER THAN A DIFF, for the same reason. A diff answers
        what CHANGED between two commits and this question is about what the
        published tree CONTAINS -- and the file that went missing never changed
        anything, because it was never in either commit.

        THE MODE IS CHECKED HERE TOO, and it is the committed half of the walk's
        own type boundary: `_checked_tree` refuses a link or a device in the
        worktree, and a gitlink or a symlink entry in the tree is the same
        refusal on the side a recipient actually resolves.
        """
        committed = {}
        for mode, relative in _tree_entries(self._git(
                repository, "ls-tree", "-r", "-z", head,
                what="committed tree inventory").stdout):
            if mode not in TREE_FILE_MODES:
                raise TaskRefusal(
                    f"the committed tree carries a {mode} entry at "
                    f"{relative}; this adapter publishes an account of regular "
                    f"candidate files and nothing else")
            committed[relative] = mode
        missing = sorted(set(measured) - set(committed))
        if missing:
            raise TaskRefusal(
                f"the candidate carries {missing[0]} and the commit does not; "
                f"a path this repository ignores is still material the turn "
                f"was measured and verified over, and a proposal whose own "
                f"head cannot carry it is not one this adapter will publish")
        extra = sorted(set(committed) - set(measured))
        if extra:
            raise TaskRefusal(
                f"the commit carries {extra[0]} and the candidate does not; "
                f"the published tree and the tree this turn measured are one "
                f"tree or this account is not about what was verified")

    def _changed(self, repository, base, head):
        """The paths this proposal changes, CUMULATIVELY from the base.

        FROM THE BASE AND NOT FROM THE ENTRY HEAD, because a proposal is
        offered against the canonical target rather than against the previous
        correction round. On the first turn the two ranges are the same; on
        every later one this is the whole of what the reviewer and the
        integrator are being asked to take.
        """
        if head is None:
            return []
        return sorted(_paths(self._git(
            repository, "diff", "--name-only", "-z", "--no-renames",
            f"{base}..{head}", what="proposed path inventory").stdout))

    def _publish_line(self, proposal, repository, base, head, verification,
                      result):
        """The declared tree for a prepared line: a patch, a transcript, a
        record, and the objects.

        NO CANDIDATE TREE. That is the whole difference from `_publish`, and it
        is a removal rather than a substitution: the candidate is a commit on a
        durable private line now, so a copy of its files beside it would be a
        second account of the same bytes for somebody to have to reconcile.

        THE BUNDLE IS CREATED LAST AND ONLY WHEN THERE IS A HEAD, AND A STALE
        ONE IS REMOVED FIRST. A turn that produced no commit has no objects to
        carry, and an empty bundle is a file that looks like evidence of one.

        W105575 candidate review 2026-09-07: on a persistent line the declared
        output directory SURVIVES the turn that wrote it, so a no-op correction
        left the previous attempt's bundle sitting byte-for-byte inside this
        turn's declared output -- objects for a head this turn does not claim,
        collected and sealed as though it did. The three text members are
        rewritten unconditionally and so were never exposed to this; the bundle
        is the one member whose absence is meaningful, so its absence is made
        rather than assumed.

        ONLY THIS WORKER'S OWN MEMBER IS REMOVED, by exact name and through a
        descriptor. Whatever else a previous attempt or another party left in
        the workspace is not this adapter's to clean up, and sealed custody and
        retained checkpoint refs are emphatically not.

        `HEAD` RATHER THAN THE OBJECT NAME in the range. A bundle carries the
        references it was asked for, and a raw object name is not a reference;
        the commit was taken immediately above, so `HEAD` is that exact object
        and is also a name the recipient can resolve.
        """
        _made(proposal)
        _discarded(proposal, BUNDLE)
        _written(os.path.join(proposal, PATCH),
                 self._git(repository, "diff", "--no-renames",
                           f"{base}..{head}",
                           what="proposed patch").stdout if head else "")
        _written(os.path.join(proposal, VERIFICATION),
                 verification["text"] if verification is not None
                 else "no verification was attempted\n")
        _written(os.path.join(proposal, RESULT),
                 json.dumps(result, indent=1, sort_keys=True) + "\n")
        if head is not None:
            self._git(repository, "bundle", "create", "--quiet",
                      os.path.join(proposal, BUNDLE), f"{base}..HEAD",
                      what="object transport")
            os.chmod(os.path.join(proposal, BUNDLE), FILE_MODE)

    def _scratch(self):
        """One bounded private directory under the tmpfs, mode 0700.

        WHAT IS STILL HERE, AND WHAT MOVED. The child ephemera roots below --
        the byte-code cache, the temporary directory and the cache home -- stay
        on the tmpfs: they are private, non-executable, and are meant to be
        destroyed with the container.

        THE EDITABLE TREE NO LONGER DOES, and the superseded reason is worth
        keeping because it reads as a rule. It said the workspace was "the
        host-visible output bind, and an editable copy left there would be
        material the manager has to collect and reason about". Collection is by
        DECLARATION, not by presence: `output._compare_declared` refuses an
        undeclared path outright -- "an undeclared path is never collected
        merely because the agent wrote there" -- so a checkout and a candidate
        beside the declared proposal are workspace material that goes away with
        the workspace. What the old placement did cost was real: the tmpfs is
        64 MiB, which is W71917's whole subject.
        """
        if self._home is not None:
            return self._home
        made = tempfile.mkdtemp(prefix="dogfood-", dir=PRIVATE_ROOT)
        os.chmod(made, 0o700)
        return made

    # THE THREE ROOTS EACH CHILD IS GIVEN, by environment name.
    #
    # Named in one place because they are made and pointed at in one place. A
    # name added here without a directory, or a directory made without a name,
    # is the review [P1] this structure exists to make impossible.
    EPHEMERA_ROOTS = (("PYTHONPYCACHEPREFIX", "pycache"),
                      ("TMPDIR", "tmp"),
                      ("XDG_CACHE_HOME", "cache"))

    def _new_directory(self, scratch, name):
        """Create one predictable child root exclusively, without repair.

        `exist_ok=True` is forbidden at this boundary. An existing name is not
        ours merely because it has the desired spelling, and chmodding it can
        follow a provider-created link. Production scratch is new, so a
        collision is a custody failure rather than reusable state.
        """
        made = os.path.join(scratch, name)
        try:
            os.mkdir(made, 0o700)
        except FileExistsError as failed:
            raise TaskRefusal(
                f"the private child root {made} already exists; predictable "
                f"runtime paths are created exclusively and never repaired") from failed
        os.chmod(made, 0o700)
        return made

    def _new_ephemera(self, scratch, name):
        made = self._new_directory(scratch, name)
        roots = {}
        for variable, leaf in self.EPHEMERA_ROOTS:
            roots[variable] = self._new_directory(made, leaf)
        return made, roots

    def _child_environments(self, scratch):
        """Create both child environments before either child may execute."""
        provider_home = self._prepared_home(scratch)
        _provider_root, provider_roots = self._new_ephemera(
            scratch, PROVIDER_EPHEMERA)
        verification_home = self._new_directory(scratch, VERIFICATION_HOME)
        _verification_root, verification_roots = self._new_ephemera(
            scratch, VERIFICATION_EPHEMERA)
        return {
            "provider": self._closed_environment(
                home=provider_home, roots=provider_roots, scratch=scratch),
            "verification": self._closed_environment(
                home=verification_home, roots=verification_roots,
                scratch=scratch),
        }

    @staticmethod
    def _checked_directory(scratch, place):
        """Prove every path component is an ordinary owned scratch directory.

        This check is repeated immediately before each child. The provider can
        write as the worker uid and knows the scratch layout, so creation alone
        is not evidence that a verifier path still names what we created.
        """
        import stat

        scratch = os.path.abspath(scratch)
        place = os.path.abspath(place)
        try:
            scratch_state = os.lstat(scratch)
        except OSError as failed:
            raise TaskRefusal(
                f"private scratch {scratch} cannot be validated "
                f"({type(failed).__name__})") from failed
        if not stat.S_ISDIR(scratch_state.st_mode):
            raise TaskRefusal(
                f"private scratch {scratch} is not an ordinary directory")
        try:
            inside = os.path.commonpath((scratch, place)) == scratch
        except ValueError:
            inside = False
        if not inside or place == scratch:
            raise TaskRefusal(
                f"the child root {place} is not beneath private scratch "
                f"{scratch}")
        current = scratch
        for component in os.path.relpath(place, scratch).split(os.sep):
            current = os.path.join(current, component)
            try:
                held = os.lstat(current)
            except OSError as failed:
                raise TaskRefusal(
                    f"the private child root component {current} cannot be "
                    f"validated ({type(failed).__name__})") from failed
            if not stat.S_ISDIR(held.st_mode):
                raise TaskRefusal(
                    f"the private child root component {current} is not an "
                    f"ordinary directory; links and special files are "
                    f"refused")
            if stat.S_IMODE(held.st_mode) != 0o700:
                raise TaskRefusal(
                    f"the private child root component {current} has mode "
                    f"{stat.S_IMODE(held.st_mode):04o}, not 0700")
        resolved = os.path.realpath(place)
        if os.path.commonpath((scratch, resolved)) != scratch:
            raise TaskRefusal(
                f"the private child root {place} resolves outside scratch "
                f"to {resolved}")
        return place

    def _closed_environment(self, *, home, roots, scratch):
        """The whole environment a child gets, composed member by member.

        `HOME` and `PATH` are what this adapter always gave. The three cache
        and temporary names are W85497's correction and they all point INSIDE
        `ephemera`, which is under the private scratch and outside `candidate`.
        Nothing else is added and `os.environ` is still never consulted.

        EVERY NAMED ROOT IS CREATED HERE, and review 2026-09-04T13-56-04Z [P1]
        is why that is not a detail. Only the OUTER directory was made; the
        three children were named and absent, and an absent directory is one
        the child silently ignores -- a probe of the composed environment found
        Python presented with that `TMPDIR` selecting `/tmp` instead. A
        boundary that depends on a directory existing is declarative until the
        directory exists, so the loop below makes each one at the same mode as
        its parent before either child is started.
        """
        composed = {"HOME": self._checked_directory(scratch, home),
                    "PATH": "/usr/local/bin:/usr/bin:/bin"}
        for name, _leaf in self.EPHEMERA_ROOTS:
            # `compileall` WRITES BYTECODE AS ITS PURPOSE and ignores
            # `PYTHONDONTWRITEBYTECODE`; `PYTHONPYCACHEPREFIX` is the name that
            # decides WHERE, and it is the one that keeps the candidate clean.
            composed[name] = self._checked_directory(scratch, roots[name])
        return composed

    def _revalidated_environment(self, scratch, environment):
        """Re-prove the prepared paths after the provider had write access."""
        checked = dict(environment)
        checked["HOME"] = self._checked_directory(scratch, checked["HOME"])
        for name, _leaf in self.EPHEMERA_ROOTS:
            checked[name] = self._checked_directory(scratch, checked[name])
        return checked

    def _pinned_environment(self, scratch, environment):
        """Open verifier roots before the provider can create descendants.

        Review 2026-09-04T18-59-48Z [P1]: checking a pathname immediately
        before launch still leaves a check/use interval. A provider descendant
        can outlive its leader, replace the checked name with a link to the
        candidate, and let the verifier resolve that link.

        These descriptors hold the exact directory objects created before the
        provider runs. The verifier inherits them explicitly and resolves only
        `/proc/self/fd/<n>`; replacing a scratch pathname cannot redirect an
        already-open object. The ordinary names remain useful for the provider
        environment and for operator inspection, but they are no longer the
        verifier's authority.
        """
        checked = self._revalidated_environment(scratch, environment)
        pinned = {"PATH": checked["PATH"]}
        held = []
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        try:
            for name in ("HOME", *(one for one, _leaf in self.EPHEMERA_ROOTS)):
                descriptor = os.open(checked[name], flags)
                state = os.fstat(descriptor)
                named = os.lstat(checked[name])
                if (not stat.S_ISDIR(state.st_mode)
                        or stat.S_IMODE(state.st_mode) != 0o700
                        or (state.st_dev, state.st_ino)
                        != (named.st_dev, named.st_ino)):
                    os.close(descriptor)
                    raise TaskRefusal(
                        f"the private verifier root {checked[name]} did not "
                        f"remain the exact owned mode-0700 directory while "
                        f"it was opened")
                held.append((name, descriptor))
                pinned[name] = f"/proc/self/fd/{descriptor}"
        except BaseException:
            for _name, descriptor in held:
                os.close(descriptor)
            raise
        return pinned, tuple(held)

    @staticmethod
    def _revalidated_directories(environment, directories):
        """Validate held objects, never provider-writable pathnames."""
        for name, descriptor in directories:
            try:
                state = os.fstat(descriptor)
            except OSError as failed:
                raise TaskRefusal(
                    f"the held verifier root {name} cannot be validated "
                    f"({type(failed).__name__})") from failed
            if not stat.S_ISDIR(state.st_mode):
                raise TaskRefusal(
                    f"the held verifier root {name} is not a directory")
            if stat.S_IMODE(state.st_mode) != 0o700:
                raise TaskRefusal(
                    f"the held verifier root {name} has mode "
                    f"{stat.S_IMODE(state.st_mode):04o}, not 0700")
            if state.st_nlink == 0:
                raise TaskRefusal(
                    f"the held verifier root {name} was removed after the "
                    f"provider ran")
            if environment[name] != f"/proc/self/fd/{descriptor}":
                raise TaskRefusal(
                    f"the verifier environment no longer names its held "
                    f"{name} directory")
        return tuple(descriptor for _name, descriptor in directories)

    def _provider(self, task, candidate, scratch, environment, prompt=None):
        """One provider turn, over a closed argv and a closed environment.

        THE ENVIRONMENT IS COMPOSED, NEVER INHERITED. `os.environ` is not
        forwarded, and that is the point rather than tidiness: a credential
        variable present in this process would silently outrank every other
        source and decide which account the trial ran as. What the child gets
        is `HOME`, `PATH` and W85497's three ephemeral roots -- nothing else.

        THE HOME IS STILL THE PREPARED CREDENTIAL HOME. The cache correction
        moves where bytecode and temporaries LAND; it does not move the
        provider's credential, which stays exactly where `_prepared_home` puts
        it and is the one thing this turn cannot run without.
        """
        argv = [PROVIDER_PROGRAM, *PROVIDER_ARGUMENTS,
                _prompt(task) if prompt is None else prompt]
        try:
            status, record, partial = self._ran_provider(
                argv, cwd=candidate, seconds=PROVIDER_SECONDS,
                env=self._revalidated_environment(scratch, environment))
        except subprocess.TimeoutExpired:
            return {"ok": False, "status": None,
                    "failure_reason": PROVIDER_TIMED_OUT,
                    "why": f"the provider did not finish within "
                           f"{PROVIDER_SECONDS}s"}
        except OSError as failed:
            return {"ok": False, "status": None,
                    "failure_reason": PROVIDER_START_ERROR,
                    "why": f"the provider could not be started: "
                           f"{type(failed).__name__}"}
        if status == 0:
            # A CLEAN TURN PUBLISHES NO REASON. There is nothing to classify,
            # and a `failure_reason` on a success would be a field readers
            # learn to ignore.
            return {"ok": True, "status": 0, "failure_reason": None,
                    "why": None}
        # THE DIAGNOSTIC IS STILL NOT THE PROVIDER'S PROSE. This read
        # `f"...{status}: {errors}"`, and `errors` was the provider's own
        # stderr -- the process that had just authenticated with the attempt's
        # bearer. It reached `result.json` through `why` AND the worker's
        # protocol `/output/output.json` through `recap`.
        #
        # W55360 CHANGES EXACTLY ONE THING: the STRUCTURED stdout record is
        # read, matched against a closed map, and discarded. What crosses the
        # boundary below is one of this module's own words -- never the
        # provider's spelling of it, never the document, never a parser
        # complaint. Stderr is still on `DEVNULL` and was never opened.
        reason = _failure_reason(record, partial=partial)
        return {"ok": False, "status": status, "failure_reason": reason,
                "why": f"the provider exited {status} ({reason}); its own "
                       f"diagnostic is not published, because the process "
                       f"that wrote it holds this attempt's credential"}

    def _ran_provider(self, argv, *, cwd, seconds, env):
        """The provider child, whose STDOUT ALONE is read, bounded and drained.

        W55360's approver ruling narrowly supersedes W39357's no-read rule for
        this one stream, because two supervised rounds established that `exit
        1 and nothing else` costs more than it protects. Everything else about
        that rule stands, and the shape here is what keeps it standing:

        STDERR IS UNTOUCHED, on `DEVNULL`, exactly as before. The provider's
        prose is where a bearer would appear and this module still has no
        descriptor onto it. The verification command's two streams are
        `_ran`'s and are not changed by this method's existence.

        THE PIPE IS DRAINED CONTINUOUSLY AND THE RETENTION IS BOUNDED, and
        those are two properties rather than one. A reader that stopped at the
        ceiling would leave a chatty provider blocked on a full pipe forever;
        a reader with no ceiling would let it decide this process's memory. So
        every byte is read and at most `MAX_PROVIDER_RECORD` are kept, with
        the rest dropped as they arrive.

        THE DRAIN RUNS BESIDE THE CHILD, in a thread, because `self._run`
        blocks until the child exits and the pipe would fill first otherwise.
        The parent's write end is closed after the run returns, which is what
        gives the reader its EOF; without that close the reader would wait on a
        descriptor this process itself still holds.

        AND THE DRAIN ENDS ON ITS OWN CLOCK, NOT ON EOF, which is W55360
        review (2026-09-01T03:35:56Z) [P1] and the sharper half of the same
        sentence. This process closing its write end is NOT enough to
        guarantee EOF: any descendant the provider started inherited the
        descriptor, so a leader that spawns something long-lived and exits
        leaves the read end open with nobody left who intends to close it.
        Waiting for that EOF wedged the worker after `self._run` had already
        returned -- past `PROVIDER_SECONDS`, which was supposed to be the
        bound on exactly this. So the reader carries `PROVIDER_DRAIN_SECONDS`
        of grace from the moment the provider ends and then STOPS, whether or
        not it saw EOF and whether or not bytes are still arriving, and a
        stream that was never proved finished is PARTIAL.

        THE READER OWNS THE READ END and closes it itself. Closing a
        descriptor another thread may still be reading is a use-after-close
        this module has no way to make safe, and the alternative -- leaking it
        -- would be a descriptor left open for the life of the turn. Handing
        the one thread that touches it the job of closing it is neither.

        NO PATHNAME AND NO FILE. W39357's first two review rounds were both
        about capture plumbing -- a path a child could replace, then a
        descriptor read back too late -- so this creates neither. The pipe is
        anonymous, lives in this process, and its contents never reach a host
        filesystem.
        """
        read_fd, write_fd = os.pipe()
        os.set_blocking(read_fd, False)
        held = bytearray()
        partial = [False]
        ended = threading.Event()

        def drain():
            deadline = None
            try:
                while True:
                    if deadline is None and ended.is_set():
                        deadline = time.monotonic() + PROVIDER_DRAIN_SECONDS
                    waiting = PROVIDER_DRAIN_SLICE
                    if deadline is not None:
                        waiting = min(waiting, deadline - time.monotonic())
                        if waiting <= 0:
                            # NOT FINISHED, JUST OVER. Somebody the provider
                            # started still holds the write end, so what was
                            # read is a prefix of a record rather than a
                            # record, and it is treated as one.
                            partial[0] = True
                            return
                    try:
                        if not select.select([read_fd], (), (), waiting)[0]:
                            continue
                        piece = os.read(read_fd, 4096)
                    except (BlockingIOError, InterruptedError):
                        continue
                    except OSError:
                        partial[0] = True
                        return
                    if not piece:
                        # EOF: every writer is gone and the record is whole.
                        return
                    room = MAX_PROVIDER_RECORD - len(held)
                    if room > 0:
                        held.extend(piece[:room])
                    if len(piece) > max(room, 0):
                        # READ AND DROPPED, which is the whole difference
                        # between a bound on memory and a bound on the child.
                        partial[0] = True
            finally:
                os.close(read_fd)

        reader = threading.Thread(target=drain, daemon=True)
        reader.start()
        try:
            return_code = self._run(argv, cwd=cwd, env=env, timeout=seconds,
                                    stdout=write_fd,
                                    stderr=subprocess.DEVNULL).returncode
        finally:
            # THE CLOSE AND THE SIGNAL ARE IN `finally`, in that order. A
            # timeout or a missing executable still leaves this process
            # holding the write end and still has to start the reader's
            # clock: `subprocess.run` kills its DIRECT child on timeout and
            # nothing else, so the descendant case above is reachable from
            # the timeout path too.
            os.close(write_fd)
            ended.set()
            reader.join()
        return return_code, bytes(held), partial[0]

    def _ran(self, argv, *, cwd, seconds, env, pass_fds=()):
        """One child, bounded, WITH BOTH STREAMS ON `/dev/null`.

        THIS IS THE WHOLE BOUNDARY, and it is one line rather than a
        discipline, which is the point. W39357 review (2026-08-30T04:01:29Z)
        [P1]: no pathname race and no link were needed to put the mounted
        bearer in the host-visible proposal. The provider is handed the
        credential and its stderr was interpolated into `result.json`; the
        task's verification command is code out of the candidate the provider
        just edited, running as the same uid with the same mount readable, and
        its two streams were copied verbatim into `verification.txt`. Printing
        the bearer was enough.

        THE OTHER REMEDY WAS UNAVAILABLE, and it is worth saying which. Making
        the mount unreachable to a child would end the class outright -- but
        the accepted posture is `--cap-drop ALL`, `--security-opt
        no-new-privileges`, one fixed uid and a read-only root, so this adapter
        has no mount namespace to alter, no second identity to drop to, and no
        way to revoke a read-only bind mount. Whatever the provider can read,
        a child of this process can read; if it could not, the provider could
        not authenticate and there would be no turn.

        REDACTION WAS NOT AVAILABLE EITHER, and for a better reason than
        difficulty: a redactor has to know the bearer's bytes, which means
        reading them, which the confirmed boundary forbids -- and a program
        holding the bearer in its own memory to scrub it is one formatting bug
        away from being the discloser.

        So the bytes are not read. Not bounded, not windowed, not held and
        discarded: `subprocess.DEVNULL` at both call sites, so there is no
        descriptor, no capture file, no buffer and no variable in this module
        that a later edit could interpolate somewhere. The two previous review
        rounds were both about capture plumbing -- a pathname a child could
        replace, then a descriptor read back too late -- and deleting the
        plumbing retires that class rather than defending it a third time.

        WHAT IS LOST IS REAL and is recorded rather than shrugged off: a failed
        provider turn now says only that it failed. The parent finding already
        rules that the evidence carries no provider diagnostic, and the
        operator's authoritative signal was always its own rerun of the frozen
        command against the collected candidate, never this file. If bringing
        up the first live turn (W39364) needs provider diagnostics, that is an
        explicitly operator-authorized diagnostic mode for a later pass and not
        a reason to publish untrusted bytes by default.
        """
        return self._run(argv, cwd=cwd, env=env, timeout=seconds,
                         pass_fds=pass_fds,
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL).returncode

    def _prepared_home(self, scratch):
        """A private HOME whose credential path POINTS AT the mounted slot.

        THE BEARER IS NEVER READ. `os.symlink` writes a path, not bytes; this
        program never opens the target, and nothing about it reaches argv, the
        environment, the result or the evidence. What it buys is that a
        provider whose root filesystem is read-only can still write beside its
        own credential, which W17110 measured as the difference between
        reaching an authentication decision and failing before one.

        AN ABSENT SLOT IS A REFUSAL, not a fallback. The finding forbids a
        home-directory default, so a container started without the explicit
        credential delivery must not quietly try an ambient one.
        """
        slot = os.path.join(CREDENTIAL_ROOT, CREDENTIAL_SLOT)
        if not os.path.exists(slot):
            raise TaskRefusal(
                f"this container has no credential at {slot}; the operator "
                f"authorizes the exact credential source and this adapter "
                f"has no home-directory or ambient fallback")
        # PRESENT IS NOT READABLE, and W52800 is what that distinction cost.
        #
        # The check above is a `stat`, which needs only search permission on
        # the parents -- so a slot delivered at a mode this container's fixed
        # uid cannot open passed it, was symlinked into the private home, and
        # became a provider that printed `Not logged in` and exited 1. The
        # manager's mode was the defect and is corrected there; this is the
        # half that makes the SAME failure say what it is. Three attempts and
        # a day of probing separated the symptom from the cause, and the
        # question that would have closed the gap is one line.
        #
        # `os.access` AND NOT AN OPEN. It answers for this process's effective
        # identity, which is exactly the question, and it does so without a
        # descriptor onto bearer bytes. This adapter must not read the
        # credential to find out whether it could have.
        if not os.access(slot, os.R_OK):
            raise TaskRefusal(
                f"this container cannot READ its credential at {slot}; the "
                f"delivery exists and its permissions do not admit this "
                f"runtime's identity, so the provider would fail to "
                f"authenticate for a reason no diagnostic of its own may "
                f"publish")
        home = os.path.join(scratch, "home")
        state = os.path.join(home, PROVIDER_HOME_STATE)
        os.makedirs(state, exist_ok=True)
        os.chmod(home, 0o700)
        os.chmod(state, 0o700)
        link = os.path.join(state, PROVIDER_CREDENTIAL)
        if not os.path.lexists(link):
            os.symlink(slot, link)
        return home

    def _verify(self, task, candidate, environment, directories):
        """The task's OWN command, in the candidate copy, bounded.

        Run here so the proposal carries evidence the worker produced; the
        operator reruns it outside the container, and the acceptance says
        plainly that this answer is not what an operator trusts.

        ITS OUTPUT IS NOT PUBLISHED AT ALL -- see `_ran`. This command is
        provider-edited code running with the attempt's credential mount
        readable, and its two streams were copied verbatim into the
        host-visible transcript.

        The capture this once handed the command is gone entirely, which
        retires two earlier corrections with it: the first round put the
        adapter's stream files in the command's own working directory, and the
        third moved them to an anonymous descriptor. There is nothing left to
        place safely.
        """
        # REMOVING THE PROVIDER'S CREDENTIAL LINK FIRST WAS CONSIDERED AND
        # REJECTED, because it is the shape this record has already ruled
        # against once. It would take away ONE NAME that points at the slot
        # while the slot's own fixed absolute path stays readable to anything
        # running as this uid, so it narrows nothing an attacker relies on --
        # it only makes the module look defended. The capture-directory move
        # was rejected for the same reason in the third round: a defence that
        # depends on the child not knowing a path is not a boundary. `_ran` is
        # the boundary.
        #
        # ITS HOME IS NO LONGER THE CANDIDATE, which W85497 corrects. `HOME`
        # pointed at the tree being measured, so anything the command wrote to
        # its own home wrote into the proposal. It now gets a private,
        # CREDENTIAL-FREE home beside the candidate rather than inside it: the
        # provider's prepared home is deliberately NOT shared with this child,
        # because that home exists to hold the link to the bearer and this
        # command is provider-edited code.
        try:
            pass_fds = self._revalidated_directories(environment, directories)
            status = self._ran(
                list(task["verification"]), cwd=candidate,
                seconds=VERIFICATION_SECONDS,
                env=environment, pass_fds=pass_fds)
        except subprocess.TimeoutExpired:
            return {"status": None,
                    "text": _transcript(task, f"did not finish within "
                                              f"{VERIFICATION_SECONDS}s")}
        except OSError as failed:
            return {"status": None,
                    "text": _transcript(task, f"could not be started "
                                              f"({type(failed).__name__})")}
        return {"status": status, "text": _transcript(task, f"exit: {status}")}


def _transcript(task, ending):
    """`verification.txt`, composed ENTIRELY from things a child did not write.

    W39357 review (2026-08-30T04:01:29Z) [P1]. The parent finding requires this
    file to carry no credential and no provider diagnostic content, and the
    previous form copied the command's stdout and stderr into it verbatim --
    from provider-edited code, running with the attempt's credential mount
    readable. There is no rule this adapter can apply to those bytes that does
    not require reading the bearer.

    So the file carries the frozen command, which the OPERATOR wrote into
    `/input/task.json` and this adapter read from a read-only mount, and the
    ending, which this adapter got from `wait` rather than from a stream. Both
    are already published in `result.json`; stating them here keeps the
    transcript a transcript rather than an empty file.

    AND IT SAYS WHAT IS MISSING AND WHY, because a reader who does not know
    the output was withheld will read its absence as the command being silent.
    """
    return (f"$ {' '.join(task['verification'])}\n"
            f"{ending}\n"
            f"\n"
            f"The command's own stdout and stderr are deliberately not\n"
            f"reproduced here. It is code from the candidate tree this turn's\n"
            f"provider edited, and it runs with the attempt's credential mount\n"
            f"readable -- so its output is exactly the content this proposal\n"
            f"must not carry, and nothing here can tell one of its bytes from\n"
            f"another without reading the bearer.\n"
            f"\n"
            f"Rerun the command yourself, from the collected candidate tree,\n"
            f"outside the worker. The acceptance already says that rerun and\n"
            f"not this file is what an operator trusts.\n")


def _failure_reason(record, *, partial):
    """One of THIS module's words for a nonzero provider turn.

    EVERY PATH OUT OF HERE IS A CONSTANT. The parameter is provider-authored
    bytes and nothing derived from them is returned, interpolated or reported:
    not the document, not a member name, not an unmatched `terminal_reason`,
    not the exception a parser raised, not a length and not an excerpt. The
    answer is `PROVIDER_FAILURE_REASONS[value]` or `UNCLASSIFIED`, and both are
    written in this file.

    WHY THE FAILURES ARE NOT DISTINGUISHED. Malformed JSON, invalid UTF-8, a
    non-object root, a missing reason, a duplicated reason, a non-string
    reason, an unknown reason, a partial record and a document the parser
    could not finish all answer the same word. Telling them apart in the
    published record would be publishing a parser's reading of untrusted bytes
    -- a channel with fewer values than the document but a channel all the
    same -- and the operator's next act is identical for all of them.

    DUPLICATES ARE REFUSED RATHER THAN RESOLVED. `json.loads` keeps the last
    of two equal keys, so a document carrying `terminal_reason` twice would be
    read as whichever the provider put second. That is a choice this module
    has no basis to make, so `object_pairs_hook` catches it and the record is
    unclassified.

    AND THE PARSER IS MADE STRICT AND MADE TOTAL, which is W55360 review
    (2026-09-01T03:35:56Z) [P1] and the reason the two guards below are not
    decoration. `json.loads` is PERMISSIVE by default and it is not a total
    function, so the approved rule -- every unusable document becomes
    `unclassified` -- was not what the code did:

      `NaN`, `Infinity` and `-Infinity` are not JSON, and Python accepts them
      anyway. A record carrying one earned `api-error` from a document this
      module had just called well-formed, so `parse_constant` refuses them and
      the extension is not silently part of the accepted grammar.

      A deeply nested record inside the 64 KiB ceiling raises `RecursionError`,
      which is not a `ValueError` and escaped this function entirely -- so a
      provider could fault the worker rather than be classified by it. It is
      caught here and answers the same one word, still without the exception.
    """
    if partial or not record:
        return UNCLASSIFIED

    def paired(items):
        seen = {}
        for name, value in items:
            if name in seen:
                raise ValueError("a duplicated member")
            seen[name] = value
        return seen

    def refused(literal):
        raise ValueError("a non-standard constant")

    try:
        # STRICT UTF-8 AND A COMPLETE DOCUMENT. `json.loads` refuses trailing
        # data of its own, which is the other half of "one document": a record
        # with a second object after it is not a record this module read.
        document = json.loads(record.decode("utf-8"), object_pairs_hook=paired,
                              parse_constant=refused)
    except (UnicodeDecodeError, ValueError, RecursionError):
        return UNCLASSIFIED
    if not isinstance(document, dict):
        return UNCLASSIFIED
    found = document.get("terminal_reason")
    if not isinstance(found, str):
        return UNCLASSIFIED
    # EQUALITY, AND A MAP THIS FILE OWNS. Not a prefix, not a substring, not a
    # pattern: an unknown spelling is unclassified rather than nearly matched.
    return PROVIDER_FAILURE_REASONS.get(found, UNCLASSIFIED)


def _disposition(provider, patch, verification):
    """What happened, and it can only be `candidate` when everything held.

    FAILURE IS HONEST, which is the acceptance's own word. Each branch below
    is a way the turn did not produce a useful result, and none of them may be
    reported as one -- a missing credential, a provider that would not run, a
    turn that changed nothing, or a change whose own verification failed.
    """
    if not provider["ok"]:
        return "provider-failed", provider["why"]
    if not patch:
        return "no-candidate", ("the provider ended cleanly and changed "
                                "nothing in the candidate copy")
    if verification is None:
        return "no-candidate", "no verification was attempted"
    if verification["status"] != 0:
        return "verification-failed", (
            f"the task's own command ended {verification['status']}")
    return "candidate", "the candidate changed the source and its own "\
                        "verification passed"


def _line_path(place):
    """One absolute, canonical, option-safe repository path.

    Every use of this value is ARGUMENT POSITION on a command line, which is
    what makes each rule here about safety rather than tidiness: a leading dash
    is read as an option by the program that receives it, and a relative or
    traversing spelling is a path this adapter computed rather than one it was
    handed.
    """
    if type(place) is not str or not place or not place.startswith("/") \
            or place.startswith("-") or "\x00" in place \
            or ".." in place.split("/") or os.path.normpath(place) != place:
        raise TaskRefusal(
            "a prepared development line is one canonical absolute path")
    return place


def _reserved(declared):
    """The names inside this workspace that are NEVER candidate material.

    THREE KINDS, AND EACH IS SOMEBODY ELSE'S. `output.json` and its staging
    name belong to `baton_worker` and are written after this adapter returns;
    `result-*` is the manager's per-attempt result root, whose exact name
    carries a runtime attempt id this adapter is never told; and each declared
    output path is where this adapter is required to write.

    A DECLARED PATH IS A PATH, NOT A PATTERN, and one carrying a character that
    would make it behave as a pattern is refused rather than escaped. Guessing
    at an escaping is how a reservation silently stops covering the thing it
    named -- and the consequence here is not cosmetic: an unreserved output
    directory is committed into somebody's candidate.
    """
    reserved = {COMPLETION_MANIFEST, COMPLETION_STAGING, RESULT_ROOT_PATTERN}
    for one in declared:
        relative = one["path"]
        if type(relative) is not str or not relative:
            raise TaskRefusal("a declared output path is non-empty text")
        _under(relative, what="a declared output path")
        if relative != RESULT_ROOT_PATTERN and any(
                mark in relative for mark in IGNORE_METACHARACTERS):
            raise TaskRefusal(
                f"the declared output path {relative!r} carries a character "
                f"this adapter cannot reserve as an exact name; a declared "
                f"path is not an ignore pattern and is not escaped into one")
        if relative != relative.rstrip() or relative.endswith("/"):
            raise TaskRefusal(
                f"the declared output path {relative!r} has more than one "
                f"spelling as an exact reservation")
        reserved.add(relative)
    return reserved


def _reserve(repository, reserved):
    """Put the reserved names out of the candidate's reach, in the repository.

    `.git/info/exclude` IS THE RIGHT HOME and the alternatives are not. A
    committed ignore file would be this adapter proposing a change to somebody
    else's tree; a global one would outlive the container. This is repository-
    local, is never committed, and dies with the line.

    ROOT-ANCHORED, so `output.json` reserves the workspace's own completion
    envelope and not a file of that name three directories down inside the
    candidate. Every entry is written on its own line and the file is REPLACED
    rather than appended, so a resumed turn reserves exactly this set.

    OPENED BY DESCRIPTOR AT EVERY COMPONENT, for the reason every other write
    in this module is: the provider owns this workspace for part of the turn,
    and `.git` replaced by a link is how a write lands somewhere nobody
    authorized.
    """
    walking = os.open(_line_path(repository),
                      os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        # THE REPOSITORY IS REQUIRED AND `info` IS ESTABLISHED. A missing
        # `.git` is a workspace that is not the prepared line this profile was
        # promised, and creating one here would be this adapter quietly
        # building the arrangement it was supposed to have been handed.
        step = os.open(VCS_METADATA,
                       os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                       dir_fd=walking)
        os.close(walking)
        walking = step
        try:
            os.mkdir("info", 0o755, dir_fd=walking)
        except FileExistsError:
            pass
        step = os.open("info", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                       dir_fd=walking)
        os.close(walking)
        walking = step
        opened = os.open("exclude",
                         os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW,
                         0o644, dir_fd=walking)
    except OSError as refused:
        os.close(walking)
        raise TaskRefusal(
            f"the prepared development line's own repository directory could "
            f"not be opened as its own directory ({type(refused).__name__}); "
            f"a line is materialized by the manager before the runtime starts "
            f"and is never cloned, reset or rebuilt here") from None
    os.close(walking)
    with os.fdopen(opened, "w", encoding="utf-8") as writing:
        writing.write("".join(f"/{name}\n" for name in sorted(reserved)))


def _statuses(raw):
    """`--name-status -z` as pairs, and a trailing field is a refusal.

    NUL-SEPARATED because a path may carry a newline, and `--no-renames` so
    every record is exactly two fields; a three-field rename record would make
    this parse mean something it was not written for.
    """
    fields = [one for one in raw.split("\x00") if one != ""]
    if len(fields) % 2:
        raise TaskRefusal(
            "the committed change could not be read as status-and-path pairs")
    return [(fields[index], fields[index + 1])
            for index in range(0, len(fields), 2)]


def _paths(raw):
    """`--name-only -z` as a list, held to the same canonical-path rule."""
    return [_under(one) for one in raw.split("\x00") if one != ""]


def _batch_header(raw, offset, relative):
    """One `cat-file --batch` record header: object, kind, size, and where the
    contents start.

    TERMINATED BY EITHER DELIMITER. `-Z` asks for NUL and older spellings use a
    newline; accepting whichever arrives first keeps this a parse of what was
    actually written rather than of what a flag was expected to change. A
    `missing` answer has two fields and is refused here, which is the honest
    place for it: path-set equality already proved the object should be there.
    """
    end = len(raw)
    for mark in (b"\n", b"\x00"):
        found = raw.find(mark, offset)
        if found != -1:
            end = min(end, found)
    if end >= len(raw):
        raise TaskRefusal(
            f"the committed blob inventory ends without a record for "
            f"{relative}")
    fields = raw[offset:end].decode("utf-8", "replace").split(" ")
    if len(fields) != 3 or not fields[2].isdigit():
        raise TaskRefusal(
            f"the committed tree holds no readable object for {relative}")
    return fields[0], fields[1], int(fields[2]), end + 1


def _tree_entries(raw):
    """`ls-tree -r -z` as mode-and-path pairs.

    One record is `<mode> SP <type> SP <object> TAB <path>` and the records are
    NUL-separated, which is what makes a path carrying a tab or a newline
    unable to forge a second entry. Split from the LEFT on the fixed prefix and
    once on the tab, so nothing in the path can be read as a field.
    """
    entries = []
    for record in raw.split("\x00"):
        if record == "":
            continue
        head, tab, relative = record.partition("\t")
        fields = head.split(" ")
        if not tab or len(fields) != 3:
            raise TaskRefusal(
                "the committed tree could not be read as mode, type, object "
                "and path")
        entries.append((fields[0], _under(relative, what="a committed tree "
                                          "path")))
    return entries


def _under(relative, what="a committed path"):
    """One relative, canonical path inside the candidate, and nothing else."""
    if type(relative) is not str or not relative or relative.startswith("/") \
            or ".." in relative.split("/") or "\x00" in relative:
        raise TaskRefusal(f"{what} is relative and canonical; {relative!r} "
                          f"is not")
    return relative


def _filterless(raw):
    """No path in this change may be rewritten on its way into the object.

    `check-attr -z` answers path, attribute and value in threes. A `filter`
    that is set to anything means content this adapter measured is not content
    the commit stores, and no comparison afterwards can tell the difference
    back apart -- so the turn refuses rather than publishing an account of
    bytes the object store does not hold.
    """
    fields = [one for one in raw.split("\x00") if one != ""]
    if len(fields) % 3:
        raise TaskRefusal(
            "the candidate's attribute inventory could not be read in threes")
    for index in range(0, len(fields), 3):
        relative, _attribute, value = fields[index:index + 3]
        if value not in ("unspecified", "unset"):
            raise TaskRefusal(
                f"{relative} is subject to a content filter; the bytes this "
                f"adapter verified and the bytes a commit would store are not "
                f"the same object, and this turn will not publish an account "
                f"of the difference")


def _measured(root, written, *, what):
    """Every checked path's bytes, as a digest, and no diff.

    The prepared line already knows WHICH paths changed; what it cannot answer
    is what this adapter actually read, and that digest is what binds the
    account to the commit. Read exactly as `_diff` reads: rooted and no-follow
    at every component.
    """
    return {relative: _bytes_digest(_read_under(root, relative, what))
            for relative in written}


def _claim(base, head, recap):
    """The worker-owned proposal claim, and every member is this turn's own.

    FOUR FACTS AND NO FIFTH. What this turn was built on, what it produced,
    where its objects are inside its own declared output, and what it did in
    words. The manager's measurements and identities are deliberately absent:
    a worker that named an artifact id, a content digest or a custody locator
    would be certifying its own output, and the composer that reads this
    refuses exactly that.

    THE BASE IS THE IMMUTABLE ONE. On a correction round this is still the
    revision the proposal is offered against, not the head the turn started
    from -- the publication driver requires the proposal's source base to be
    the canonical target, and the entry head is not that.

    PLAIN HEX rather than an algorithm-and-name pair: the width IS the
    namespace, and the party that composes the manifest derives it by the same
    rule the profile package already fixes.
    """
    transport = _under(BUNDLE, what="the object transport")
    if len(transport) > MAX_TRANSPORT:
        raise TaskRefusal("the object transport's name is not bounded")
    return {CLAIM_NAMESPACE: {"base": base, "head": head,
                              "transport": transport,
                              "recap": recap[:MAX_RECAP]}}


def _selected(declared, produce, what):
    """Which declared outputs this role writes, and which it answers absent.

    W110772. `_one_declaration` below is unchanged and still owns the original
    single-output workload; this owns the SHARED Job, whose declaration set is
    the union of what its stages produce. The two are separate functions rather
    than one with a mode, because the single-output rule is a statement about a
    workload that declares one thing and this is a statement about a workload
    whose stages declare each other's.

    AMBIGUITY REFUSES RATHER THAN BEING GUESSED AT. A name this workload does
    not recognise is not something to spread a proposal over -- which is
    exactly the mistake `_one_declaration`'s refusal exists to prevent, and
    admitting several declarations must not quietly reintroduce it.

    AND AN OUTPUT THIS ROLE DOES NOT WRITE MAY NOT BE REQUIRED. `answered`
    refuses a required output answered `missing-optional`, which is right; a
    manager that declared the other stage's half required has made a
    declaration no single turn can satisfy, and saying so here names the
    declaration rather than the answer.
    """
    if type(declared) is not list or not declared:
        raise TaskRefusal(
            f"a {what} turn needs its declared outputs and this assignment "
            f"declares "
            f"{len(declared) if type(declared) is list else 0}")
    names = [one["name"] for one in declared]
    if len(set(names)) != len(names):
        raise TaskRefusal("this assignment declares one output name twice; a "
                          "declaration answered twice is answered by neither")
    unknown = sorted(one for one in names if one not in COMMON_OUTPUTS)
    if unknown:
        raise TaskRefusal(
            f"this assignment declares {', '.join(unknown)} and a shared Job "
            f"declares {', '.join(COMMON_OUTPUTS)}; an unrecognised "
            f"declaration is not one this workload writes to")
    by = {one["name"]: one for one in declared}
    missing = [one for one in produce if one not in by]
    if missing:
        raise TaskRefusal(
            f"a {what} turn writes {', '.join(produce)} and this assignment "
            f"declares no {', '.join(missing)}")
    absent = [by[one] for one in names if one not in produce]
    for one in absent:
        if one["required"]:
            raise TaskRefusal(
                f"output {one['name']!r} is declared required and a {what} "
                f"turn does not write it; a shared Job's stages each produce "
                f"their own half and answer the rest missing-optional")
    return [by[one] for one in produce], absent


def _absent(declarations):
    """The answer for every declared output this turn did not write."""
    return [{"name": one["name"], "status": "missing-optional",
             "result_metadata": {}} for one in declarations]


def _no_duplicates(pairs):
    """One JSON object, refused if a name is answered twice.

    A duplicate key is not a document with a last-writer-wins rule; it is a
    document whose author and whose reader disagree about what it says, and
    `json` resolves that silently in the reader's favour.
    """
    held = {}
    for name, value in pairs:
        if name in held:
            # A `ValueError`, because that is what an unreadable document
            # raises and this IS one: `json` would otherwise resolve the
            # collision silently in the reader's favour, which is a document
            # whose author and whose reader disagree about what it says.
            raise ValueError(
                f"the review report names {name!r} twice; a document with two "
                f"answers to one question has none")
        held[name] = value
    return held


def _review_report(room):
    """The provider's report, read from a proved regular file and validated.

    EVERY RULE HERE IS THIS ADAPTER'S. The report is written by the provider --
    the least trusted thing in this container and the one holding the attempt's
    bearer -- so its size, its shape, its member set and its vocabulary are all
    bounded before one byte of it reaches an output. What is adopted is a
    closed three-member document; what is published from it is the verdict word
    and the findings prose, and nothing else the provider wrote exists here to
    be published by accident.

    A MISSING OR MALFORMED REPORT IS NOT A VERDICT. It answers `None`, the turn
    is `unable`, no claim is placed on any output, and the manager's own reader
    then finds no claim and holds. An exit status is not a decision and this
    adapter will not map one into a verdict.
    """
    raw = _read_bounded(room, REVIEW_REPORT, "the review report")
    if raw is None:
        return None
    try:
        document = json.loads(raw.decode("utf-8"),
                              object_pairs_hook=_no_duplicates)
    except (UnicodeDecodeError, ValueError):
        return None
    if type(document) is not dict \
            or sorted(document) != sorted(REVIEW_REPORT_MEMBERS):
        return None
    if document["schema"] != REVIEW_REPORT_SCHEMA:
        return None
    if document["verdict"] not in REVIEW_VERDICTS:
        return None
    findings = document["findings"]
    if type(findings) is not str or not findings.strip() \
            or len(findings) > MAX_FINDINGS:
        return None
    # AND IT MUST BE TEXT THIS ADAPTER CAN ACTUALLY WRITE. REVIEW
    # 2026-09-07T15-19-16Z [P1]: `json` decodes an escaped lone surrogate into
    # a `str` that no UTF-8 encoder will accept, so a report carrying one
    # passed every check here and then raised `UnicodeEncodeError` from the
    # `findings.txt` writer -- after the logs output had been published and
    # while the findings output was half written. Adopting text is adopting
    # the obligation to publish it, so the encode is proved at the point the
    # document is adopted and a failure takes the ordinary unable path with
    # no claim and no partial output.
    try:
        findings.encode("utf-8")
    except UnicodeEncodeError:
        return None
    return {"schema": REVIEW_REPORT_SCHEMA, "verdict": document["verdict"],
            "findings": findings}


def _read_bounded(root, relative, what):
    """At most `MAX_REPORT_BYTES` from a descriptor proved regular, or `None`.

    THE BOUND IS ON THE READ AND NOT ON A LATER CHECK. A file whose size is
    decided by the provider is a file whose read has to be bounded by this
    program, and one byte past the ceiling makes the report unusable rather
    than truncated -- a truncated JSON document is a different document.

    AND THE OPEN IS NON-BLOCKING, WHICH IS THE HALF THAT WAS MISSING. REVIEW
    2026-09-07T15-19-16Z [P1]: this routed the report through `_open_under`,
    whose final open is a blocking `O_RDONLY | O_NOFOLLOW` performed BEFORE
    `fstat` proves a regular file. A provider that creates
    `review-report.json` as a FIFO and exits successfully therefore leaves
    this adapter waiting for a writer that will never arrive -- outside the
    provider's own bounded invocation, so `PROVIDER_SECONDS` bounds nothing
    about it and the container hangs after the turn is over. The reviewer's
    probe reproduced exactly that.

    THIS BOUNDARY GETS ITS OWN OPENER RATHER THAN A REDESIGN OF THE OTHER
    ONE. `_open_under` walks every component of a path inside a tree this
    adapter measured and is correct for that; the report is one fixed name in
    a directory this adapter created exclusively for it, written by the least
    trusted process in the container. So the ordering here is
    `O_NONBLOCK` first, regular-file proof on the DESCRIPTOR second, bounded
    read third -- which is the same rule `baton_worker` and the integration
    delivery already apply to runtime-written documents, applied here.

    THE PARENT IS STILL OPENED NO-FOLLOW AND THE CHILD IS RELATIVE TO IT, so
    a link swapped in at either level is refused rather than resolved.
    """
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY
    try:
        parent = os.open(root, flags)
    except OSError:
        return None
    try:
        try:
            handle = os.open(relative,
                             os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                             dir_fd=parent)
        except OSError:
            # ABSENT, A LINK, OR A DEVICE THIS PROGRAM WILL NOT OPEN. All
            # three are "no usable report", which is the unable path.
            return None
    finally:
        os.close(parent)
    try:
        found = os.fstat(handle)
        if not stat.S_ISREG(found.st_mode):
            # A FIFO REACHES HERE RATHER THAN BLOCKING ABOVE, which is the
            # whole point of the ordering: `O_NONBLOCK` on a FIFO with no
            # writer opens immediately for reading, and this is where it is
            # refused as not being a document.
            return None
        raw = os.read(handle, MAX_REPORT_BYTES + 1)
    except OSError:
        return None
    finally:
        os.close(handle)
    return None if len(raw) > MAX_REPORT_BYTES else raw


def _review_claim(verdict, observed):
    """The worker-owned checkpoint-review claim, and every member is this
    turn's own.

    FOUR FACTS AND NO FIFTH. What this reviewer decided, and the base, head and
    tree of the source it decided over. The manager compares the three objects
    against the checkpoint's own frozen evidence, so a reviewer that named
    another line's objects is refused there rather than believed here.
    """
    return {REVIEW_CLAIM_NAMESPACE: {"verdict": verdict,
                                     "base": observed["base"],
                                     "head": observed["head"],
                                     "tree": observed["tree"]}}


def _review_prompt(task, source, report):
    """The one review prompt, composed from the frozen task and nothing else.

    THE PROVIDER IS STILL NOT TOLD ABOUT THE PROTOCOL. It learns where the
    source is, that the source is read-only, what the requirements are, and
    where to put its report. It learns nothing about `/output`, the assignment,
    the attachment, the checkpoint, the session or the manager.

    THE INSTRUCTIONS ARE PRESENTED AS REQUIREMENTS TO ASSESS, not as work to
    do. This is the difference between a reviewer and a second implementer, and
    it is stated in the prompt because the same provider and the same image run
    both roles.

    AND THE VERIFICATION COMMAND IS NAMED AS A CLAIM RATHER THAN AS EVIDENCE.
    A task that names a command is not a task whose command passed; a reviewer
    that reported it as passing without running it would be reporting an
    unsubstantiated check, which is the one thing a review must not do.
    """
    return (f"You are reviewing a change on a read-only source tree at "
            f"{source}. Do not modify anything there, and do not attempt to "
            f"build, commit or edit it.\n\n"
            f"The change was made to satisfy these requirements:\n\n"
            f"{task['instructions']}\n\n"
            f"Assess whether the change at {source} meets them. Report only "
            f"checks you actually substantiated by reading the tree; the task "
            f"names the command\n"
            f"  {' '.join(task['verification'])}\n"
            f"but naming it is not evidence that it passed, and you must not "
            f"report it as passing unless you ran it yourself.\n\n"
            f"When you are done, write your decision to {report} as a JSON "
            f"object with exactly these three members:\n"
            f'  "schema": "{REVIEW_REPORT_SCHEMA}"\n'
            f'  "verdict": one of {", ".join(REVIEW_VERDICTS)}\n'
            f'  "findings": non-empty text explaining the verdict\n'
            f"Write nothing else to that path and write no other file.\n")


def _one_declaration(declared):
    """Exactly one declared output, and this workload knows which.

    A second declaration is not something to guess about: the proposal is one
    tree with one identity, and an adapter that spread itself over several
    would be inventing a shape the manager never declared.
    """
    if type(declared) is not list or len(declared) != 1:
        raise TaskRefusal(
            f"this dogfood workload declares exactly one output and this "
            f"assignment declares {len(declared) if type(declared) is list else 0}")
    return declared[0]


def _task(place=None):
    """The frozen task, held to its own closed contract."""
    place = place or os.path.join(INPUT_ROOT, TASK_DOCUMENT)
    try:
        with open(place, "rb") as reading:
            raw = reading.read(1 << 20)
    except OSError:
        raise TaskRefusal(
            f"this assignment has no readable {place}; the dogfood task is "
            f"one versioned document at a path this workload fixes") from None
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise TaskRefusal(f"{place} is not a readable document") from None
    if type(document) is not dict:
        raise TaskRefusal(f"{place} is one JSON object")
    missing = sorted(one for one in TASK_MEMBERS if one not in document)
    extra = sorted(one for one in document if one not in TASK_MEMBERS)
    if missing or extra:
        raise TaskRefusal(
            f"{place} is exactly {', '.join(TASK_MEMBERS)}"
            + (f"; missing {', '.join(missing)}" if missing else "")
            + (f"; unexpected {', '.join(extra)}" if extra else ""))
    if document["schema"] != TASK_SCHEMA:
        raise TaskRefusal(
            f"{place} says it is {document['schema']!r} and this adapter "
            f"reads {TASK_SCHEMA!r}; a task from another generation is not "
            f"one to read the recognised parts out of")
    # W44424: TEXT BEFORE IT IS MATCHED. This read `_TASK_ID.match(str(...))`,
    # so a JSON number reached the regex as its decimal spelling and passed --
    # the identity of a versioned document decided by a coercion this module
    # performed rather than by what the document says. Every other member here
    # is held to its type before its shape, and this one was not.
    #
    # Found at the SENDER: W39358's operator refuses a numeric identity, so
    # the two ends disagreed about the same task document while an agreement
    # test compared the regex TEXT and reported them identical. That test now
    # asserts the asymmetry; this removes it.
    if type(document["task_id"]) is not str \
            or not _TASK_ID.match(document["task_id"]):
        raise TaskRefusal(f"{place} carries no usable task identity")
    for name in ("instructions", "source_root"):
        if type(document[name]) is not str or not document[name]:
            raise TaskRefusal(f"{place} carries a {name} that is not bounded "
                              f"non-empty text")
    # W39357 review [P2]: HELD BY EQUALITY, exactly as `schema` is. The
    # confirmed boundary says the adapter copies exactly `/input/source`, and
    # `SOURCE_ROOT` said so while nothing read it -- so the effective source
    # was selected by the task payload while the module and the dossier both
    # claimed it was a constant. A contained relative path is not the rule;
    # the rule is the one path this workload stages.
    if document["source_root"] != SOURCE_ROOT:
        raise TaskRefusal(
            f"{place} names source_root {document['source_root']!r} and this "
            f"workload stages exactly {SOURCE_ROOT!r}; the source is a "
            f"constant of the contract rather than a value the task selects")
    verification = document["verification"]
    if type(verification) is not list or not verification \
            or not all(type(one) is str and one for one in verification):
        raise TaskRefusal(
            f"{place} carries a verification that is a non-empty list of "
            f"words; a command this adapter has to assemble from a string is "
            f"a shell, and there is no shell here")
    # W71917: THE PROFILE AND ITS BASE, READ HERE AND NOWHERE ELSE.
    #
    # The manager carries a profile word through the input manifest as opaque
    # text for its own boundary composition and compares it against nothing;
    # this is the party that consumes the word, so this is the party that says
    # what the values are. `_task_bytes` on the host deliberately does not
    # parse this document for the same reason -- one contract, one reader.
    #
    # THE PAIRING IS THE PROFILE PACKAGE'S RULE, not a second copy of it:
    # `checkout_plan` refuses a git profile with no base and a generic profile
    # WITH one, so the pairing is validated where it is defined. What is
    # checked here is only that the two members are the shapes this document
    # may carry, which is this reader's job.
    if document["source_profile"] not in _profiles.PROFILES:
        raise TaskRefusal(
            f"{place} names source_profile "
            f"{document['source_profile']!r} and this workload consumes "
            f"{' and '.join(_profiles.PROFILES)}")
    declared = document["declared_base"]
    if declared is not None:
        try:
            _profiles.check_declared_base(declared)
        except _profiles.ProfileRefusal as refusal:
            raise TaskRefusal(f"{place} carries a declared_base this "
                              f"workload cannot use: {refusal}") from None
    return document


def _prompt(task):
    """The one prompt, composed from the frozen task and nothing else.

    THE PROVIDER IS NOT TOLD ABOUT THE PROTOCOL. It gets the instructions, the
    working directory it is already in, and the command that will judge it --
    nothing about `/output`, the assignment, the session or the manager. A
    provider that could see those could write into them.
    """
    return (f"{task['instructions']}\n\n"
            f"You are working in a private copy of the source tree, which is "
            f"the current working directory. Edit files here directly.\n"
            f"When you are done, the following command will be run from this "
            f"directory and must pass:\n"
            f"  {' '.join(task['verification'])}\n")


def _open_under(root, relative, what):
    """One descriptor on a regular file, proved AT EVERY PATH COMPONENT.

    W39357 review (2026-08-29T22:18:55Z) [P1]. The first round opened the
    final name with `O_NOFOLLOW`, which refuses a link only at the LAST
    component -- so `candidate/nested/claude` was still resolved through
    whatever `nested` happened to be at the moment of the open. The task's own
    verification command runs after the tree was checked and before it is
    published, it is provider-authored, and it owns that directory: replacing
    `nested` with a link to the credential root turned the mounted bearer into
    an ordinary final file.

    So the walk is done by DESCRIPTOR rather than by name. Each component is
    opened `O_NOFOLLOW | O_DIRECTORY` relative to the one above it, the final
    name is opened `O_NOFOLLOW` relative to its proved parent, and `fstat`
    proves what was actually opened. No component of the path is ever resolved
    by the kernel from a string this module composed, so there is no lookup
    left for a rename to redirect.

    A list of relative path strings is not a set of checked objects. This is
    what makes them one.
    """
    parts = relative.split(os.sep)
    try:
        walking = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            for name in parts[:-1]:
                step = os.open(name,
                               os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                               dir_fd=walking)
                os.close(walking)
                walking = step
            opened = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW,
                             dir_fd=walking)
        finally:
            os.close(walking)
    except OSError as refused:
        # THE KERNEL SPELLS IT TWO WAYS and both mean the same thing here:
        # ELOOP for a link at the final name under `O_NOFOLLOW`, ENOTDIR for
        # one at an intermediate component under `O_DIRECTORY | O_NOFOLLOW`.
        # Either says a path this module already checked is a link now, which
        # is a REFUSAL and not a fault.
        raise TaskRefusal(
            f"{what} could not be reopened at {relative} without following a "
            f"link at some component ({type(refused).__name__}: "
            f"{refused.strerror}); a link is how the credential mount reaches "
            f"an output") from None
    try:
        if not stat.S_ISREG(os.fstat(opened).st_mode):
            raise TaskRefusal(f"{what} carries a non-regular entry at "
                              f"{relative}")
    except BaseException:
        os.close(opened)
        raise
    return opened


def _read_under(root, relative, what):
    """One file under `root`, read whole from a descriptor proved regular."""
    descriptor = _open_under(root, relative, what)
    try:
        with os.fdopen(descriptor, "rb", closefd=False) as reading:
            return reading.read()
    finally:
        os.close(descriptor)


def _revalidated(root, written, measured, *, what, skip=None):
    """The checked tree, PROVED UNCHANGED, before one output byte is written.

    W39357 review (2026-08-29T22:51:53Z) [P1]. The first cut of this reopened
    each recorded path and proved it was still a regular file -- which holds
    the path's TYPE and says nothing about its bytes. The verification command
    is provider-authored, it runs after `_diff` measured the candidate and
    before `_publish` reads it, and overwriting an already-checked regular
    file in place needs no link, no rename and no new inode. The proposal then
    carried bytes that neither `change.patch` nor `changed_paths` described,
    and the mounted bearer is one of the things those bytes could be.

    So this proves three things, in the order that makes each cheap:

      1. THE CEILINGS AGAIN, over a fresh walk. A fixed list could not see
         what verification ADDED or how much it GREW, so the bound the module
         advertises stopped applying at exactly the moment untrusted code ran.
      2. EVERY MEASURED PATH IS STILL THERE. A checked file the command
         deleted is not something to publish an account of.
      3. EVERY MEASURED FILE STILL HAS THE BYTES THE PATCH DESCRIBES.

    WHAT IT DOES NOT DO is decide whether an ADDITION is allowed. A
    verification command that leaves a cache directory behind has not
    invalidated anybody's evidence: what it added was never measured and is
    never published, and the fresh walk still counts it against the ceilings.
    Refusing those would make ordinary tooling a fault; publishing them would
    put unmeasured bytes in the proposal. Neither is what this wants.
    """
    _checked_tree(root, what=what, skip=skip)
    for relative in written:
        if _bytes_digest(_read_under(root, relative, what)) \
                != measured[relative]:
            raise TaskRefusal(
                f"{what} changed at {relative} after its own verification "
                f"command ran; the proposal's patch describes the bytes this "
                f"adapter measured, and a candidate whose contents no longer "
                f"match that account is not one to publish")


def _checked_tree(root, *, what, skip=None):
    """Every entry under a tree, REVALIDATED, whoever wrote it.

    W105575: `skip` NAMES TOP-LEVEL ENTRIES THIS WALK DOES NOT DESCEND, and it
    is passed in rather than decided here for `_copy_tree`'s reason. Under a
    prepared development line the candidate root IS the workspace, so it holds
    the repository's own object store and the reserved names the manager and
    the worker write into -- none of which is candidate material, and all of
    which would otherwise be measured, bounded and published as though it
    were. A caller with no such arrangement passes nothing and walks
    everything, exactly as before.

    W39357 review [P1]: `_copy_tree` checked the STAGED source, and the
    provider owns the candidate afterwards -- so the diff walked and the
    publication copied a tree nothing had looked at since. Both follow a file
    symlink, and one of the things reachable through the container is the
    credential mount.

    So the provider-authored tree is held to the same rules the staged one is,
    at the moment it is used rather than at the moment it was made: regular
    files and directories only, no link at any depth, and bounded on both
    axes. Answers the sorted relative paths, which is all either caller needs.

    W39357 review (2026-08-29T22:18:55Z) [P2]: EVERY ENTRY THE WALK TOUCHES
    counts against the ceiling, directories as well as files. Counting only
    files left the traversal bounded by tmpfs inodes and wall-clock rather
    than by the number this module advertises -- a provider that made a
    million empty directories crossed no stated bound at all.
    """
    found, entries, total = [], 0, 0
    for base, directories, files in os.walk(root, followlinks=False):
        if skip is not None and base == root:
            # ONLY AT THE ROOT. A reservation is an anchored name -- the
            # workspace's own `output.json`, not one three directories down
            # inside somebody's candidate -- so a walk that pruned the same
            # names at every depth would be silently dropping material this
            # turn is supposed to publish.
            directories[:] = [name for name in directories
                              if not _reservation(name, skip)]
            files[:] = [name for name in files if not _reservation(name, skip)]
        for name in directories:
            if os.path.islink(os.path.join(base, name)):
                raise TaskRefusal(
                    f"{what} carries a link at "
                    f"{os.path.relpath(os.path.join(base, name), root)}")
            entries += 1
            _bounded(entries, total, what)
        for name in files:
            full = os.path.join(base, name)
            held = os.lstat(full)
            if not stat.S_ISREG(held.st_mode):
                raise TaskRefusal(
                    f"{what} carries a non-regular entry at "
                    f"{os.path.relpath(full, root)}"
                    + ("; a link is how the credential mount reaches an output"
                       if stat.S_ISLNK(held.st_mode) else ""))
            found.append(os.path.relpath(full, root))
            entries += 1
            total += held.st_size
            _bounded(entries, total, what)
    return sorted(found)


def _reservation(name, skip):
    """Whether one top-level entry is reserved, the same way Git ignores it.

    The reserved set is literal names plus the ONE deliberate namespace glob
    this workload owns, and that glob is matched here by the same prefix rule
    the pattern written into the exclude file expresses. Nothing else in the
    set is treated as a pattern, which is why `_reserved` refuses a declared
    path that could be read as one.
    """
    if name in skip:
        return True
    return RESULT_ROOT_PATTERN in skip \
        and name.startswith(RESULT_ROOT_PATTERN[:-1])


def _bounded(entries, total, what):
    """The one ceiling both walks are held to, counted the same way."""
    if entries > MAX_SOURCE_ENTRIES or total > MAX_SOURCE_BYTES:
        raise TaskRefusal(
            f"{what} exceeds this adapter's bound of "
            f"{MAX_SOURCE_ENTRIES} entries / {MAX_SOURCE_BYTES} bytes")


def _copy_tree(source, into, *, skip=None):
    """The baseline tree, copied into the workspace, bounded and no-follow.

    REGULAR FILES AND DIRECTORIES ONLY. A link in the staged tree is a way for
    the copy to reach outside it, and the manager already refuses one at
    delivery -- this is the second party proving it rather than assuming the
    first did.

    W71917: `skip` NAMES ONE DIRECTORY THIS COPY DOES NOT DESCEND, and it is
    passed in rather than decided here. The only caller passes the
    version-control metadata directory, and only when the assignment DECLARED
    the git profile -- so nothing is inferred from what a tree looks like, and
    a generic profile's directory of the same name is ordinary material. A
    checkout's object store is not part of the candidate: copying it would put
    tens of thousands of entries through the bound below and describe every one
    of them in a patch nobody asked for.
    """
    if not os.path.isdir(source):
        raise TaskRefusal(f"this assignment stages no source tree at {source}")
    what = "the staged source"
    entries, total, copied = 0, 0, 0
    for base, directories, files in os.walk(source, followlinks=False):
        if skip is not None and skip in directories:
            directories.remove(skip)
        for name in directories:
            if os.path.islink(os.path.join(base, name)):
                raise TaskRefusal(
                    f"{what} carries a link at "
                    f"{os.path.relpath(os.path.join(base, name), source)}")
            # Review [P2]: directories count here too. The staged tree is the
            # manager's and already measured, but this is the second party
            # proving it -- and a second party that counts differently from
            # the walk it is checking is not proving the same thing.
            entries += 1
            _bounded(entries, total, what)
        for name in files:
            full = os.path.join(base, name)
            if os.path.islink(full) or not os.path.isfile(full):
                raise TaskRefusal(
                    f"{what} carries a non-regular entry at "
                    f"{os.path.relpath(full, source)}")
            entries += 1
            copied += 1
            total += os.path.getsize(full)
            _bounded(entries, total, what)
            relative = os.path.relpath(full, source)
            landing = os.path.join(into, relative)
            os.makedirs(os.path.dirname(landing), exist_ok=True)
            shutil.copyfile(full, landing)
    if not copied:
        raise TaskRefusal(f"the staged source at {source} is empty")
    return copied


def _diff(source, candidate, written, *, skip=None):
    """Which paths the provider changed, the unified diff, AND what was read.

    W39357 review (2026-08-29T22:51:53Z) [P1]: this measured the candidate and
    kept nothing about what it had measured, so `change.patch` described one
    set of bytes and `_publish` copied whatever was on disk later. It answers
    the digest of every candidate file it read as well, and that digest is
    what binds the two.

    COMPUTED IN THE WORKER, WITHOUT GIT. `change.patch` is a review
    convenience and never the custody identity -- the operator diffs the
    collected candidate tree against the recorded input manifest, which is a
    comparison this file cannot influence. Git is a workload convention this
    image deliberately does not carry.
    """
    import difflib

    changed, measured = {}, {}
    for relative in written:
        # EVERY READ IS ROOTED AND NO-FOLLOW AT EVERY COMPONENT. The candidate
        # side is the provider's tree; the staged side is the read-only bind
        # `_copy_tree` already proved, and it is read the same way so that one
        # rule covers both rather than two rules covering one each.
        raw = _read_under(candidate, relative, "the candidate copy")
        measured[relative] = _bytes_digest(raw)
        after = _split(raw)
        original = (_lines(source, relative, "the staged source")
                    if os.path.exists(os.path.join(source, relative))
                    else None)
        if original == after:
            continue
        changed[relative] = "".join(difflib.unified_diff(
            original or [], after,
            fromfile=f"a/{relative}" if original is not None else "/dev/null",
            tofile=f"b/{relative}"))
    for base, directories, files in os.walk(source, followlinks=False):
        # THE SAME DIRECTORY THE COPY SKIPPED. Walking it here would report
        # every object file as a deletion, because the candidate never had one.
        if skip is not None and skip in directories:
            directories.remove(skip)
        for name in files:
            relative = os.path.relpath(os.path.join(base, name), source)
            if relative in written:
                continue
            changed[relative] = "".join(difflib.unified_diff(
                _lines(source, relative, "the staged source"), [],
                fromfile=f"a/{relative}", tofile="/dev/null"))
    return changed, measured


def _lines(root, relative, what):
    """One file's lines, opened no-follow at EVERY component.

    Review [P1]: this was `open(place)`, which follows a link at any depth --
    so the diff read whatever a provider-created link named and the bearer
    landed in `change.patch`.
    """
    return _split(_read_under(root, relative, what))


def _split(raw):
    return raw.decode("utf-8", "replace").splitlines(True)


def _bytes_digest(raw):
    """One file's identity as BYTES, which is the only thing that binds them.

    W39357 review (2026-08-29T22:51:53Z) [P1]. Path type is not content: the
    provider-authored verification command can overwrite an already-checked
    REGULAR file in place, no link and no rename involved, and a walk that
    proves shape accepts it. The bytes the patch measured and the bytes the
    proposal carries are held together by this and nothing else.

    IT IS NOT AN INSPECTION. Nothing here decides what the bytes MEAN, no
    digest is published, and a mismatch refuses rather than reporting what it
    saw -- which matters because the thing a verification command is most
    usefully caught substituting is the mounted bearer.
    """
    import hashlib

    return hashlib.sha256(raw).digest()


def _publish(proposal, candidate, written, measured, patch, verification,
             result):
    """The declared tree, written group-readable and in one order.

    `result.json` LAST of the four, so a reader that finds it finds the rest
    beside it. It is bounded application metadata and the acceptance says in
    terms that it is never an identity substitute -- the worker's own
    `/output/output.json`, published after this returns, is the protocol
    document.
    """
    _made(proposal)
    tree = os.path.join(proposal, CANDIDATE)
    _made(tree)
    # THE CHECKED LIST, AND A NO-FOLLOW READ OF EACH ENTRY. `shutil.copyfile`
    # opens the source by NAME and follows a link, which is exactly how the
    # credential became an output file; the copy is done from a descriptor
    # this module proved regular instead.
    for relative in written:
        landing = os.path.join(tree, relative)
        _made(os.path.dirname(landing))
        # READ ONCE, PROVED, THEN WRITTEN -- the bytes that go into the
        # proposal are the same object that was just held against the patch's
        # measurement, so there is no third reading for anything to differ
        # between. `_revalidated` has already refused a mismatch before this
        # function created anything; this is the same proof at the moment of
        # use, which is what keeps the guarantee from resting on the interval
        # between the two.
        raw = _read_under(candidate, relative, "the candidate copy")
        if _bytes_digest(raw) != measured[relative]:
            raise TaskRefusal(
                f"the candidate copy changed at {relative} while its proposal "
                f"was being written")
        with open(landing, "wb") as writing:
            writing.write(raw)
        os.chmod(landing, FILE_MODE)
    _written(os.path.join(proposal, PATCH),
             "".join(patch[one] for one in sorted(patch)))
    _written(os.path.join(proposal, VERIFICATION),
             verification["text"] if verification is not None
             else "no verification was attempted\n")
    _written(os.path.join(proposal, RESULT),
             json.dumps(result, indent=1, sort_keys=True) + "\n")


def _made(place):
    os.makedirs(place, exist_ok=True)
    os.chmod(place, DIRECTORY_MODE)


def _discarded(place, name):
    """One member of this adapter's own declared output, removed if it is there.

    BY EXACT NAME AND THROUGH A DESCRIPTOR on the directory, so the removal
    cannot be redirected by a link that appeared at the output root. Absence is
    the ordinary case and is not an error: this exists to make a member's
    ABSENCE a fact about THIS turn rather than an inheritance from the last one
    that used the same persistent workspace.
    """
    try:
        holding = os.open(place, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except OSError as refused:
        raise TaskRefusal(
            f"the declared output at {place} is not its own directory "
            f"({type(refused).__name__})") from None
    try:
        os.unlink(name, dir_fd=holding)
    except FileNotFoundError:
        pass
    except OSError as refused:
        raise TaskRefusal(
            f"a previous attempt's {name} could not be removed from this "
            f"turn's declared output ({type(refused).__name__}); a member "
            f"this turn did not produce is not one it will publish") from None
    finally:
        os.close(holding)


def _written(place, body):
    with open(place, "w", encoding="utf-8") as writing:
        writing.write(body)
    os.chmod(place, FILE_MODE)


# `_window` WAS HERE, and it is gone rather than corrected a third time. It
# read a bounded window of a captured child stream back into this process --
# first from a pathname a child could replace, then from a held descriptor.
# Both were answers to "how do we read this untrusted stream safely", and
# W39357 review (2026-08-30T04:01:29Z) [P1] is the finding that the question
# was wrong: the stream is written by a process holding this attempt's
# credential, so no amount of care about HOW it is read makes the bytes
# publishable. Nothing reads a child stream now, so nothing needs a window.


def _digest(value):
    import hashlib

    return "sha256:" + hashlib.sha256(
        json.dumps(value, sort_keys=True,
                   separators=(",", ":")).encode("utf-8")).hexdigest()
