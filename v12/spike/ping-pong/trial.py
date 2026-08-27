"""SPIKE ONLY — W17110. The host half of one trial. Not a v12 contract.

Builds one provider's spike image, stages a read-only `/input` carrying one
correlation identity, runs the container with a writable `/output` and the
operator's nominated credential provider mounted read-only, collects the
result, validates the correlation, and proves cleanup by asking the engine.

Run:  python3 trial.py claude --credentials <PATH>
      python3 trial.py codex  --credentials <PATH>

`--credentials` is REQUIRED and has no default. The ruling puts the credential
source in the operator's hands, and a default here would be this program
choosing one.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
MARK = "baton-w17110-spike"

# Where each runtime looks for its own authentication inside the container. The
# provider is mounted at exactly one of these, read-only, and nothing copies it.
#
# TWO SHAPES, because the trials proved one is not enough. A DIRECTORY provider
# is mounted over the runtime's whole state directory; a FILE provider is
# mounted over just the credential file, leaving the state directory writable.
#
# Codex is why the second exists: with its state directory mounted read-only it
# will not start at all -- "failed to initialize in-process app-server client:
# Read-only file system" -- because it writes there while running. Claude
# reaches its authentication decision either way. That difference is one of the
# wrapper-boundary facts this experiment exists to produce.
CREDENTIAL_TARGET = {
    "claude": {"dir": "/home/nonroot/.claude",
               "file": "/home/nonroot/.claude/.credentials.json"},
    "codex": {"dir": "/home/nonroot/.codex",
              "file": "/home/nonroot/.codex/auth.json"},
}

# One word, and a reason to say it. This is the whole assignment: the ruling
# says "an exact textual pong is sufficient Work for this experiment".
PROMPT = ("Reply with exactly one word and nothing else. "
          "The word is: pong")

# The exact word, and the digest of it. The container publishes the digest of
# what the agent said; this is what it is compared against, derived here rather
# than trusted from the document.
# THE ENGINE SAYING AN IMAGE IS NOT THERE, positively.
#
# W17110's sixth review [P1], proved against a nonexistent socket: `docker
# image inspect` exits 1 for "no such image" AND exits 1 for "permission denied
# while trying to connect to the Docker API". The exit-status contract I
# invented -- 0 present, 1 observed absent, anything else failed -- is not one
# the CLI provides, so a daemon that could not be reached still read as an
# image that is gone.
#
# The engine does distinguish them, in the one place it actually says so. This
# is a match against the ENGINE's own diagnostic, never a provider's, and the
# text never reaches the report: only the category does.
# NARROW ON PURPOSE. The unreachable-daemon message on this engine reads
# "...: dial unix /tmp/x.sock: connect: no such file or directory" -- so a
# looser `not found` or `no such` alternative would match the very failure this
# is meant to tell apart. Only the engine's exact not-found wording counts.
NOT_FOUND = re.compile(r"no such image", re.I)

EXPECTED = "pong"
EXPECTED_DIGEST = "sha256:" + hashlib.sha256(
    EXPECTED.encode("utf-8")).hexdigest()

# WHAT MAY CROSS FROM A PUBLISHED DOCUMENT INTO A DURABLE REPORT, exhaustively.
#
# W17110's first review [P0]. This used to copy the whole published document
# and separately record redacted container stderr, on the reasoning that the
# redaction caught what mattered. The rule is not "remove the token spellings I
# recognise": a real agent holds the mounted credential and can emit arbitrary
# stdout, and a heuristic over text somebody else chooses is a guess.
#
# So nothing is redacted, because nothing that could carry provider text is
# read. Every name below is a fact the container COMPUTED -- an identity it was
# given, an exit state, a digest, a byte count, or one word from a closed
# vocabulary.
PUBLISHED_FACTS = ("spike", "provider", "correlation_id", "started_at",
                   "finished_at", "exit_status", "result_digest",
                   "result_bytes", "stderr_bytes", "failure_category")

# AND THE EXACT SHAPE, which is a different question from the one above.
#
# W17110's re-review [P1]. Filtering to an allowlist keeps unknown material out
# of the printed report -- and says nothing about whether the document is this
# harness's own. A file carrying every valid fact PLUS raw provider text was
# still accepted as a satisfying result, because the extra members were quietly
# dropped rather than refused.
#
# So the two boundaries are separated. `allowlisted` is the DURABLE-REPORT
# boundary: what may be copied. `_closed_shape` is the DOCUMENT boundary: what
# this harness will accept as its own at all. A published document is exactly
# the required members, plus `failure_category` and only when something failed.
REQUIRED_FACTS = ("spike", "provider", "correlation_id", "started_at",
                  "finished_at", "exit_status", "result_digest",
                  "result_bytes", "stderr_bytes")

# AND WHAT EACH ONE MAY BE. W17110's third review [P1]: the shape proved member
# NAMES and nothing else, so `result_bytes: "four"` was allowlisted to null,
# kept `closed_result_shape: true`, and could satisfy the trial -- because a
# byte count is not otherwise part of the verdict, so nothing else would ever
# have noticed.
#
# A name is not a value, in the same way an allowlist was not a validation and a
# member set was not a member's value. Each rule below is a bounded predicate
# over one fact.
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
INSTANT = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$")


def _whole(value, ceiling):
    """A JSON integer in range. BOOLEANS ARE NOT INTEGERS: `isinstance(True,
    int)` is true in Python and false in JSON, and `exit_status: true` would
    otherwise pass for the number one."""
    return type(value) is int and 0 <= value <= ceiling


def _text(value, holds):
    """A string, and only then whatever else is asked of it.

    W17110's fourth review [P1]: `provider` went straight to
    `value in CREDENTIAL_TARGET`, and a JSON array is unhashable -- so a
    perfectly valid JSON document raised `TypeError` out of the validator
    instead of being refused by it.
    """
    return type(value) is str and holds(value)


FACT_RULES = {
    "spike": lambda value: value == "w17110-ping-pong",
    "provider": lambda value: _text(value, lambda one: one in CREDENTIAL_TARGET),
    "correlation_id": lambda value: _text(value, lambda one: 0 < len(one) <= 200),
    "started_at": lambda value: _text(value, INSTANT.match),
    "finished_at": lambda value: _text(value, INSTANT.match),
    # The provider's exit as the container observed it. `null` is the container
    # reporting that it could not observe one, which is a real state.
    "exit_status": lambda value: value is None or _whole(value, 255),
    "result_digest": lambda value: _text(value, DIGEST.match),
    "result_bytes": lambda value: _whole(value, 1 << 24),
    "stderr_bytes": lambda value: _whole(value, 1 << 24),
}

# And the closed vocabulary itself, so a document cannot introduce a category
# by inventing one.
# `credential-expired` DESCRIBES; `credential-write-denied` EXPLAINS. W17110's
# eighth review [P1]: the earlier `credential-refresh-blocked` did both at once
# on evidence for only the first, and the record then carried the delivery shape
# as a proved cause. A category that names a mechanism has to be earned by a
# signal for that mechanism.
CATEGORIES = ("credential-write-denied", "write-denied", "credential-expired",
              "authentication", "quota", "network", "packaging", "timeout",
              "unrecognized")


def _closed_shape(document):  # noqa: C901
    """Whether a published document is exactly ONE of two EXCLUSIVE shapes.

    Missing, unknown and extra members all refuse. A document that is not this
    program's own is not made into one by dropping the parts it did not expect.

    THE VALUES ARE HELD TOO, not only the names.

    AND THE TWO SHAPES ARE DISJOINT. W17110's third review [P1]: any recognised
    `failure_category` was accepted whatever the document's exit and digest
    said, so a zero-exit exact-pong document carrying
    `failure_category: authentication` was satisfying -- neither the success
    shape nor a truthful failure one. A document has to be one thing:

      SUCCESS: zero provider exit, the exact pong digest, and NO category;
      FAILURE: a recognised category, and at least one of those two actually
      failed.

    A category is a claim that something went wrong. A document making that
    claim while reporting a clean exit and the right answer is not a shape this
    harness has -- it is a document disagreeing with itself, and accepting it
    would mean accepting whichever half happened to be read.
    """
    if type(document) is not dict:
        return False
    present = set(document)
    required = set(REQUIRED_FACTS)
    if not required <= present:
        return False
    extra = present - required
    if extra - {"failure_category"}:
        return False
    # TOTAL OVER EVERY JSON VALUE, not only the ones this wrapper emits. The
    # document is worker-authored, so "the container would never write that"
    # is not a property this validator may rely on -- a rule that RAISES on a
    # value has not refused it, it has escaped.
    for name, holds in FACT_RULES.items():
        try:
            if not holds(document[name]):
                return False
        except (TypeError, ValueError):
            return False

    answered = document["result_digest"] == EXPECTED_DIGEST
    exited_clean = document["exit_status"] == 0
    if "failure_category" in extra:
        return (document["failure_category"] in CATEGORIES
                and not (answered and exited_clean))
    return answered and exited_clean


def allowlisted(document):
    """A published document, reduced to the facts a report may carry.

    An UNKNOWN member is dropped rather than copied, and that direction is the
    whole point: a document this program did not write is a document whose
    extra members it cannot vouch for.
    """
    if type(document) is not dict:
        return {"malformed": True}
    taken = {}
    for name in PUBLISHED_FACTS:
        if name not in document:
            continue
        value = document[name]
        if name == "failure_category":
            taken[name] = value if value in CATEGORIES else "unrecognized"
        elif name in ("exit_status", "result_bytes", "stderr_bytes"):
            taken[name] = value if type(value) is int else None
        elif type(value) is str and len(value) <= 200:
            taken[name] = value
        else:
            taken[name] = None
    return taken


def engine(*arguments, timeout=900, check=True):
    """One engine command. A timeout here RAISES rather than hanging.

    The Codex trial is why this is stated: a provider runtime that neither
    answers nor exits leaves `docker run` waiting for ever, and an operator
    watching a spike with no output has no way to tell that from slow work.
    """
    found = subprocess.run(["docker", *arguments], capture_output=True,
                           timeout=timeout)
    if check and found.returncode != 0:
        # The engine's own diagnostic, not the provider's. A build or an
        # inspect failing is an operator-facing fault and nothing in it came
        # from an agent that holds a credential.
        raise SystemExit(
            f"docker {' '.join(arguments[:2])} failed ({found.returncode}): "
            f"{found.stderr.decode('utf-8', 'replace')[:600]}")
    return found


def built(provider, tag):
    """One image, and the identity the engine gave it.

    `--no-cache` is deliberately NOT used: this is a spike run repeatedly by
    hand, and the ruling asks for image identity rather than for a
    reproducibility proof. W6633 owns that property for the reviewed image.
    """
    engine("build", "-f", os.path.join(HERE, f"Dockerfile.{provider}"),
           "-t", tag, HERE)
    found = engine("image", "inspect", tag, "--format", "{{.Id}}")
    return found.stdout.decode("utf-8").strip()


def staged(home, correlation):
    """A read-only `/input` and a writable `/output`, as the host sees them."""
    inputs = os.path.join(home, "input")
    outputs = os.path.join(home, "output")
    os.makedirs(inputs)
    os.makedirs(outputs)
    # The container runs as an unprivileged uid the host does not have, so the
    # writable side has to admit it. The input side does not: it is mounted
    # read-only, which is what actually protects it.
    os.chmod(outputs, 0o777)
    with open(os.path.join(inputs, "input.json"), "w", encoding="utf-8") as one:
        json.dump({"spike": "w17110-ping-pong",
                   "correlation_id": correlation,
                   "request": PROMPT}, one, indent=1)
    return inputs, outputs


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("provider", choices=sorted(CREDENTIAL_TARGET))
    parser.add_argument("--credentials", required=True,
                        help="the operator's read-only credential provider "
                             "directory for this runtime; never copied")
    parser.add_argument("--deadline", type=int, default=240,
                        help="seconds the provider runtime gets to answer; "
                             "the container is given this and the host waits "
                             "two minutes longer before ending it itself")
    parser.add_argument("--keep", action="store_true",
                        help="leave the staged roots for inspection")
    taken = parser.parse_args(argv)

    provider = taken.provider
    source = os.path.realpath(os.path.expanduser(taken.credentials))
    if os.path.isdir(source):
        target, shape = CREDENTIAL_TARGET[provider]["dir"], "directory"
    elif os.path.isfile(source):
        target, shape = CREDENTIAL_TARGET[provider]["file"], "file"
    else:
        raise SystemExit(
            f"the credential provider {source!r} is neither a directory nor a "
            f"file; the operator nominates it and this trial will not choose "
            f"one")

    tag = f"{MARK}-{provider}:{uuid.uuid4().hex[:12]}"
    name = f"{MARK}-{provider}-{uuid.uuid4().hex[:12]}"
    correlation = f"w17110-{uuid.uuid4()}"
    home = tempfile.mkdtemp(prefix="v12-spike-ping-pong-")

    report = {"spike": "w17110-ping-pong", "provider": provider,
              "correlation_id": correlation, "image_tag": tag,
              "container_name": name,
              "credential_provider": {"source": source, "shape": shape,
                                      "mounted_read_only": True,
                                      "copied_into_image": False,
                                      "target": target}}
    timed_out = False
    try:
        report["image_id"] = built(provider, tag)
        inputs, outputs = staged(home, correlation)
        report["mounts"] = [
            {"source": inputs, "target": "/input", "readonly": True},
            {"source": outputs, "target": "/output", "readonly": False},
            {"source": source, "target": target, "readonly": True}]
        found = engine(
            "run", "--name", name, "--rm",
            "--mount", f"type=bind,source={inputs},target=/input,readonly=true",
            "--mount", f"type=bind,source={outputs},target=/output",
            "--mount", f"type=bind,source={source},"
                       f"target={target},readonly=true",
            "--env", f"SPIKE_PROVIDER={provider}",
            "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
            "--memory", "2g", "--pids-limit", "512",
            "--env", f"SPIKE_DEADLINE_MS={taken.deadline * 1000}",
            # The classifier needs the exact mounted path to tell a write
            # denied SOMEWHERE from a write denied to THE CREDENTIAL.
            "--env", f"SPIKE_CREDENTIAL_PATH={target}",
            tag, check=False, timeout=taken.deadline + 120)
        report["exit_status"] = found.returncode
        # The engine's stderr is deliberately NOT recorded. It is the last
        # place provider text could reach a durable file, and its length is
        # the only part of it this report needs.
        report["container_stderr_bytes"] = len(found.stderr)

        published = os.path.join(outputs, "output.json")
        report["completion_signal_present"] = os.path.isfile(published)
        if report["completion_signal_present"]:
            try:
                with open(published, encoding="utf-8") as one:
                    answer = json.load(one)
            except (OSError, ValueError):
                answer = None
            report["published"] = allowlisted(answer)
            report["published_shape_closed"] = _closed_shape(answer)
        else:
            report["published"] = {}
            report["published_shape_closed"] = False
    except subprocess.TimeoutExpired:
        # THE OUTER BOUND, and reaching it is a RESULT rather than a crash.
        # "The provider never answered and never exited" is one of the wrapper
        # behaviours this experiment exists to compare, so it is recorded in
        # the same shape as any other failure.
        timed_out = True
        report["exit_status"] = None
        report["failure_category"] = "timeout"
        report["failure_detail"] = (
            f"the container did not finish within {taken.deadline + 120}s")
        report["completion_signal_present"] = False
        report["correlation_matches"] = False
        report["pong"] = False
    finally:
        if timed_out:
            # It is still running, and `--rm` only fires when it ends. Ending
            # it is this program's job rather than the operator's -- and the
            # engine's answers are read, so a kill that did not work cannot
            # pass for one that did.
            killed = engine("kill", name, check=False, timeout=120)
            removed = engine("rm", "--force", name, check=False, timeout=120)
            report["timeout_kill_status"] = killed.returncode
            report["timeout_remove_status"] = removed.returncode
        # PROVED BY ASKING THE ENGINE, not by remembering. `--rm` is what should
        # have removed it; this is what establishes that it did.
        # AND THE QUERY'S OWN STATUS IS READ. W17110's re-review [P1]: a failed
        # `docker ps` returns empty stdout, which became an empty survivor list
        # and then "nothing survived". An observation that did not happen is
        # not an observation of absence.
        survivors = engine("ps", "--all", "--filter", f"name={name}",
                           "--format", "{{.Names}}", check=False)
        report["container_query_ok"] = survivors.returncode == 0
        report["containers_surviving"] = [
            one for one in survivors.stdout.decode("utf-8").split() if one]

        # THE REMOVAL'S OWN ANSWER IS READ. It was unchecked, so a refused
        # `image rm` followed by an empty tag lookup reported nothing
        # surviving -- while the immutable image may still be there, untagged.
        removal = engine("image", "rm", "--force", tag, check=False,
                         timeout=300)
        report["image_removed"] = removal.returncode == 0
        remaining = engine("image", "ls", "--filter", f"reference={tag}",
                           "--format", "{{.ID}}", check=False)
        report["image_query_ok"] = remaining.returncode == 0
        surviving = [one for one in remaining.stdout.decode("utf-8").split()
                     if one]
        # AND THE RECORDED IDENTITY IS ASKED ABOUT, AFTER EVERY ATTEMPT.
        #
        # W17110's fourth review [P1]. Removing the unique tag and then
        # querying by that same removed tag proves nothing: an image that
        # survives under ANOTHER reference is untagged successfully, the tag
        # query comes back empty, `image_removed` is true, and the trial
        # reported a clean engine while the identity it built is still there.
        #
        # A tag is a name. The id is the image. So the id is queried whatever
        # the removal said -- and a removal that failed is still treated as a
        # survivor, because a command that did not report success is not
        # evidence of absence either.
        recorded = report.get("image_id")
        if recorded:
            asked = engine("image", "inspect", "--format", "{{.Id}}",
                           recorded, check=False, timeout=300)
            # THE OUTCOME IS THREE-VALUED, AND THE STATUS ALONE CANNOT SAY
            # WHICH. The fifth review made this three-valued; the sixth showed
            # that I had invented the mapping. `1` is both "no such image" and
            # "I could not reach the daemon", so only the engine's own
            # not-found wording separates them:
            #
            #   present      status 0;
            #   OBSERVED ABSENT   non-zero, and the engine positively says
            #                     there is no such image -- the one case that
            #                     may conclude anything;
            #   DID NOT RUN  anything else. Not an observation, and it cannot
            #                establish absence.
            said = asked.stderr.decode("utf-8", "replace")
            observed_absent = (asked.returncode != 0
                               and bool(NOT_FOUND.search(said)))
            report["image_identity_query_ok"] = (asked.returncode == 0
                                                 or observed_absent)
            # AND A SECOND, STATUS-BEARING WITNESS. A successful inventory is
            # orthogonal to the wording above: if it ran and lists this id, the
            # image is there whatever `inspect` said. It may only ADD a
            # survivor -- an inventory that does not list an id cannot rescue
            # an identity query that never ran.
            inventory = engine("image", "ls", "--all", "--no-trunc",
                               "--quiet", check=False, timeout=300)
            listed = (inventory.returncode == 0
                      and recorded in inventory.stdout.decode("utf-8").split())
            if asked.returncode == 0 or listed \
                    or not report["image_removed"]:
                surviving.append(recorded)
        report["images_surviving"] = sorted(set(surviving))

        if taken.keep:
            report["staged_root_kept"] = home
            report["staged_root_removed"] = False
        else:
            shutil.rmtree(home, ignore_errors=True)
            report["staged_root_removed"] = not os.path.exists(home)

    # THE VERDICT IS THE HOST'S, RECOMPUTED. W17110's first review [P1]: this
    # used to accept the truthiness of the document's own `pong` member, so a
    # container that said `pong: true` beside the text "not pong" and exited 9
    # was reported satisfying. A worker-authored success bit is a claim, and
    # the party that has to be convinced is this one.
    #
    # Every clause below is decided here, from a fact the container computed
    # rather than a conclusion it drew.
    published = report.get("published") or {}
    report["verdict"] = {
        # The document is the one this trial asked for, not some other run's
        # left in the output root.
        "expected_spike": published.get("spike") == "w17110-ping-pong",
        "expected_provider": published.get("provider") == provider,
        "correlation_matches": published.get("correlation_id") == correlation,
        # BOTH exit states. The provider's, as the container observed it, and
        # the container's own.
        "provider_exit_zero": published.get("exit_status") == 0,
        "container_exit_zero": report.get("exit_status") == 0,
        # AN EXACT ANSWER. `sha256("pong")` is derived here, so this is a
        # comparison rather than a belief -- and "not pong" has a different
        # digest, which a substring test could never have told apart.
        "answer_is_exactly_pong":
            published.get("result_digest") == EXPECTED_DIGEST,
        # THE DOCUMENT IS THIS HARNESS'S OWN, exactly. Not "contains the facts
        # I wanted after I dropped the rest".
        "closed_result_shape": bool(report.get("published_shape_closed")),
    }
    report["pong"] = report["verdict"]["answer_is_exactly_pong"]
    report["correlation_matches"] = report["verdict"]["correlation_matches"]

    # AND CLEANUP IS ENFORCED RATHER THAN OBSERVED. Every removal reports
    # whether it worked, the image is queried by the IMMUTABLE ID rather than
    # by the tag that was just removed, and the staged root's absence is part
    # of the verdict instead of a fact recorded beside it.
    # EVERY OUTCOME, not just the ones that answered. A query that failed and a
    # removal that failed both mean this program cannot say the engine is
    # clean, and saying so anyway is the whole defect.
    report["clean"] = bool(
        not report.get("containers_surviving")
        and not report.get("images_surviving")
        and report.get("image_removed")
        and report.get("container_query_ok")
        and report.get("image_query_ok")
        # The identity query too. Absent when there was no recorded id to ask
        # about, and absent is not a failure -- there was nothing to observe.
        and report.get("image_identity_query_ok", True)
        and report.get("staged_root_removed")
        # On the timeout path these exist and must have succeeded; off it they
        # are absent, and absent is not a failure.
        and report.get("timeout_kill_status", 0) == 0
        and report.get("timeout_remove_status", 0) == 0)
    report["satisfying"] = bool(all(report["verdict"].values())
                                and report["completion_signal_present"]
                                and report["clean"])
    print(json.dumps(report, indent=1))
    return 0 if report["satisfying"] else 1


if __name__ == "__main__":
    sys.exit(main())
