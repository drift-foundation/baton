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
import shutil
import stat
import subprocess
import tempfile

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
TASK_SCHEMA = "baton.dogfood-task/1"
TASK_MEMBERS = ("schema", "task_id", "instructions", "verification",
                "source_root")

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
# to edit files. `acceptEdits` is the deliberate change and it is the single
# operand in this module a golden test cannot establish -- the first live turn
# under W39364 is what proves it, and if the spelling is wrong the correction
# is this tuple and its vector case.
#
# `--print` is the non-interactive mode: one prompt, one answer, no terminal.
PROVIDER_PROGRAM = "claude"
PROVIDER_ARGUMENTS = ("--print", "--permission-mode", "acceptEdits")

# How long one provider turn is given. A real turn is minutes; a bound that
# cannot be reached turns ordinary work into a failure, and a bound that does
# not exist turns a wedged provider into a wedged container.
PROVIDER_SECONDS = 3600

# How long the task's own verification command is given. Bounded separately
# because it is the WORKLOAD's command rather than the provider's, and the two
# have nothing to do with each other.
VERIFICATION_SECONDS = 900

# -- what this adapter writes ------------------------------------------------

CANDIDATE = "candidate"
PATCH = "change.patch"
RESULT = "result.json"
VERIFICATION = "verification.txt"

# Bounded, because every one of these is text this adapter did not write and
# is putting into a durable artifact. Provider stdout is model output and the
# verification streams are whatever the task's command emits.
MAX_RECAP = 4000
MAX_DIAGNOSTIC = 16384
MAX_VERIFICATION = 262144

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
        one = _one_declaration(declared)
        proposal = os.path.join(OUTPUT_ROOT, one["path"])
        task = _task()
        scratch = self._scratch()
        candidate = os.path.join(scratch, CANDIDATE)
        source = os.path.join(INPUT_ROOT, task["source_root"])
        copied = _copy_tree(source, candidate)
        provider = self._provider(task, candidate, scratch)
        # THE PROVIDER OWNED THIS TREE, so it is held to the staged tree's own
        # rules before anything reads or copies it. Review [P1]: the source
        # check ran before Claude and nothing ran after, so a link the
        # provider created was dereferenced by the diff and copied as regular
        # bytes into the host-visible proposal -- and the credential mount is
        # one of the things a link can name.
        written = _checked_tree(candidate, what="the candidate copy")
        # THE PROVIDER'S ENDING DECIDES NOTHING ON ITS OWN. What is written is
        # decided by what is ON DISK afterwards, which is why the diff is taken
        # before the disposition is chosen: a provider that exited 0 and
        # changed nothing produced no candidate, and one that exited non-zero
        # after editing left something an operator still has to see.
        patch, measured = _diff(source, candidate, written)
        verification = (self._verify(task, candidate, scratch)
                        if provider["ok"] and patch else None)
        # THE VERIFICATION COMMAND IS THE PAYLOAD'S, and it ran between the
        # measurement and the publication. Review [P1]: proving the paths were
        # still regular held their TYPE and not their BYTES, so a command that
        # overwrote a checked file in place published contents the patch never
        # described. What is proved here is the measurement itself.
        _revalidated(candidate, written, measured, what="the candidate copy")
        disposition, why = _disposition(provider, patch, verification)
        _publish(proposal, candidate, written, measured, patch, verification,
                 result={"schema": "baton.dogfood-proposal/1",
                         "task_id": task["task_id"],
                         "disposition": disposition,
                         "why": why,
                         "changed_paths": sorted(patch),
                         "source_entries": copied,
                         "provider": {"status": provider["status"],
                                      "seconds_bound": PROVIDER_SECONDS},
                         "verification": (
                             {"status": verification["status"],
                              "argv": list(task["verification"])}
                             if verification is not None else None)})
        recap = (f"{disposition}: {why}"
                 f" ({len(patch)} changed path(s))")[:MAX_RECAP]
        return {"disposition": ("completed" if disposition == "candidate"
                                else "unable"),
                "outputs": [{"name": one["name"], "status": "present",
                             "result_metadata": {}}],
                "recap": recap}

    # -- the private half ----------------------------------------------------

    def _scratch(self):
        """One bounded private directory under the tmpfs, mode 0700.

        Under `/tmp` rather than under the workspace on purpose: the workspace
        is the host-visible output bind, and an editable copy left there would
        be material the manager has to collect and reason about. The tmpfs is
        private, non-executable and destroyed with the container.
        """
        if self._home is not None:
            return self._home
        made = tempfile.mkdtemp(prefix="dogfood-", dir=PRIVATE_ROOT)
        os.chmod(made, 0o700)
        return made

    def _provider(self, task, candidate, scratch):
        """One provider turn, over a closed argv and a closed environment.

        THE ENVIRONMENT IS COMPOSED, NEVER INHERITED. `os.environ` is not
        forwarded, and that is the point rather than tidiness: a credential
        variable present in this process would silently outrank every other
        source and decide which account the trial ran as. What the child gets
        is `HOME`, `PATH` and nothing else.
        """
        home = self._prepared_home(scratch)
        argv = [PROVIDER_PROGRAM, *PROVIDER_ARGUMENTS, _prompt(task)]
        try:
            # PROVIDER STDOUT IS DISCARDED, not captured and dropped. Review
            # [P1]: nothing reads it, so accumulating it was pure exposure --
            # a chatty model turn could exhaust the container before the
            # ceiling that was supposed to bound it ever applied.
            status, _out, errors = self._capture(
                argv, cwd=candidate, scratch=scratch,
                seconds=PROVIDER_SECONDS,
                env={"HOME": home, "PATH": "/usr/local/bin:/usr/bin:/bin"},
                keep_stdout=False, tail=MAX_DIAGNOSTIC)
        except subprocess.TimeoutExpired:
            return {"ok": False, "status": None,
                    "why": f"the provider did not finish within "
                           f"{PROVIDER_SECONDS}s"}
        except OSError as failed:
            return {"ok": False, "status": None,
                    "why": f"the provider could not be started: "
                           f"{type(failed).__name__}"}
        return {"ok": status == 0, "status": status,
                "why": (None if status == 0
                        else f"the provider exited {status}: {errors}")}

    def _capture(self, argv, *, cwd, scratch, seconds, env, keep_stdout,
                 tail=None, head=None):
        """Run one child with GENUINELY BOUNDED capture.

        Review [P1]: both call sites used `capture_output=True` and then
        sliced. Python accumulates the whole of each stream in memory before
        `run` returns, so `[-MAX_DIAGNOSTIC:]` and `[:MAX_VERIFICATION]` were
        POST-ALLOCATION truncations -- a wedged or noisy child exhausted the
        container and turned the worker into transport loss instead of the
        typed bounded failure the acceptance requires.

        The streams go to files under the private tmpfs, which is itself
        size-capped, and only the bounded window is ever read into this
        process. `tail` is for a diagnostic, where the end is what explains
        the ending; `head` is for a transcript, where the command and its
        first output are what a reader starts from.

        W39357 review (2026-08-29T22:18:55Z) [P1]: THE CAPTURE HAS NO NAME.
        The first round put the streams in a `capture-*` directory inside the
        candidate and then REOPENED those pathnames once the child returned --
        and for the verification run the child is provider-authored code whose
        working directory that is. Unlinking `capture-*/stdout` and putting a
        link to the credential there made the bounded reader transcribe the
        bearer into `verification.txt`.

        `tempfile.TemporaryFile` hands back a descriptor on a file with no
        directory entry anywhere, and the window is read back from that same
        descriptor. There is no pathname for a child to replace and no second
        lookup to redirect, which retires the class rather than defending one
        instance of it -- and the same-uid child could have reached a renamed
        private directory just as easily as the candidate.
        """
        with tempfile.TemporaryFile(dir=scratch) as writing_out, \
                tempfile.TemporaryFile(dir=scratch) as writing_err:
            done = self._run(
                argv, cwd=cwd, env=env, timeout=seconds,
                stdout=(writing_out if keep_stdout else subprocess.DEVNULL),
                stderr=writing_err)
            return (done.returncode,
                    _window(writing_out, tail=tail, head=head)
                    if keep_stdout else "",
                    _window(writing_err, tail=tail, head=head))

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
        home = os.path.join(scratch, "home")
        state = os.path.join(home, PROVIDER_HOME_STATE)
        os.makedirs(state, exist_ok=True)
        os.chmod(home, 0o700)
        os.chmod(state, 0o700)
        link = os.path.join(state, PROVIDER_CREDENTIAL)
        if not os.path.lexists(link):
            os.symlink(slot, link)
        return home

    def _verify(self, task, candidate, scratch):
        """The task's OWN command, in the candidate copy, bounded.

        Run here so the proposal carries evidence the worker produced; the
        operator reruns it outside the container, and the acceptance says
        plainly that this answer is not what an operator trusts.

        THE CAPTURE IS NOT IN THE CANDIDATE. Review [P1]: this passed the
        candidate as its own capture scratch, so the one command in this module
        that is written by the payload ran with the adapter's stream files in
        its working directory.
        """
        try:
            status, out, errors = self._capture(
                list(task["verification"]), cwd=candidate, scratch=scratch,
                seconds=VERIFICATION_SECONDS,
                env={"HOME": candidate,
                     "PATH": "/usr/local/bin:/usr/bin:/bin"},
                keep_stdout=True, head=MAX_VERIFICATION // 2)
        except subprocess.TimeoutExpired:
            return {"status": None,
                    "text": f"the verification command did not finish within "
                            f"{VERIFICATION_SECONDS}s"}
        except OSError as failed:
            return {"status": None,
                    "text": f"the verification command could not be started: "
                            f"{type(failed).__name__}"}
        return {"status": status,
                "text": (f"$ {' '.join(task['verification'])}\n"
                         f"exit: {status}\n"
                         f"--- stdout ---\n{out}\n"
                         f"--- stderr ---\n{errors}")}


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
    if not _TASK_ID.match(str(document["task_id"])):
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


def _revalidated(root, written, measured, *, what):
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
    _checked_tree(root, what=what)
    for relative in written:
        if _bytes_digest(_read_under(root, relative, what)) \
                != measured[relative]:
            raise TaskRefusal(
                f"{what} changed at {relative} after its own verification "
                f"command ran; the proposal's patch describes the bytes this "
                f"adapter measured, and a candidate whose contents no longer "
                f"match that account is not one to publish")


def _checked_tree(root, *, what):
    """Every entry under a tree, REVALIDATED, whoever wrote it.

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


def _bounded(entries, total, what):
    """The one ceiling both walks are held to, counted the same way."""
    if entries > MAX_SOURCE_ENTRIES or total > MAX_SOURCE_BYTES:
        raise TaskRefusal(
            f"{what} exceeds this adapter's bound of "
            f"{MAX_SOURCE_ENTRIES} entries / {MAX_SOURCE_BYTES} bytes")


def _copy_tree(source, into):
    """The staged tree, copied into private scratch, bounded and no-follow.

    REGULAR FILES AND DIRECTORIES ONLY. A link in the staged tree is a way for
    the copy to reach outside it, and the manager already refuses one at
    delivery -- this is the second party proving it rather than assuming the
    first did.
    """
    if not os.path.isdir(source):
        raise TaskRefusal(f"this assignment stages no source tree at {source}")
    what = "the staged source"
    entries, total, copied = 0, 0, 0
    for base, directories, files in os.walk(source, followlinks=False):
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


def _diff(source, candidate, written):
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
    for base, _directories, files in os.walk(source, followlinks=False):
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


def _written(place, body):
    with open(place, "w", encoding="utf-8") as writing:
        writing.write(body)
    os.chmod(place, FILE_MODE)


def _window(handle, *, tail=None, head=None):
    """A bounded window of one captured stream, read from the HELD descriptor.

    Only the window crosses into this process, which is the whole difference
    from slicing an already-accumulated buffer: a child that wrote gigabytes
    costs a seek and one bounded read here rather than its own size in memory.

    Review [P1]: it took a PATHNAME and reopened it after the child returned.
    It takes the open file the stream was written to, so what is read back is
    the object the child actually wrote to and not whatever now answers to a
    name the child could rename.
    """
    bound = tail if tail is not None else head
    if tail is not None:
        handle.seek(0, os.SEEK_END)
        handle.seek(max(0, handle.tell() - bound))
    else:
        handle.seek(0)
    return handle.read(bound).decode("utf-8", "replace")


def _digest(value):
    import hashlib

    return "sha256:" + hashlib.sha256(
        json.dumps(value, sort_keys=True,
                   separators=(",", ":")).encode("utf-8")).hexdigest()
