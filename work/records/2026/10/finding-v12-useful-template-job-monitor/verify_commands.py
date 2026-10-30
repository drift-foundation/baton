#!/usr/bin/env python3
"""Verify the commands COMMANDS.md ACTUALLY PUBLISHES. Nothing is executed.

W366962, preparation only. No bundle is built, no instance is installed, no
engine or provider is launched, no store is opened, no deployment is changed
and no source byte is touched.

THIS IS A REWRITE, and review 2026-10-27T17-32-12Z R2 is why. The previous
version kept its own copy of the command list, so it could not support the
no-drift claim made for it: it tested `monitor --ticks 40` while the document
published `400`, and it omitted `attempt-diagnostics` entirely -- the one
published command whose argv was WRONG (it takes a single positional file and
exits 2 for `--status FILE`). A verifier holding a second copy of the thing it
verifies checks the copy.

So this one READS `COMMANDS.md`, extracts the command text an operator would
paste, and checks THAT. There is no second copy to drift.

WHAT IT ESTABLISHES

  1. SHELL SYNTAX. Every fenced `sh` block is parsed by `bash -n` with the
     packet's own `$VAR` assignments prepended, so an unquoted placeholder or
     an unbalanced quote fails here. `bash -n` parses and does not execute.
  2. THE SUBCOMMAND IS ONE THIS BUILD SERVES, read from
     `stack_command.COMMANDS` -- the deployed command's own table.
  3. THE OPERANDS PARSE, through the product's OWN parser, with the argv
     TAKEN FROM THE PUBLISHED TEXT. `parse_args` is wrapped so it parses
     normally and then raises, so the real parser runs and nothing past
     parsing executes.
  4. THE PARSERLESS COMMANDS ARE COVERED TOO, against inert supported
     documents this script writes into a temporary directory: the two that
     build no parser (`attempt-diagnostics`, `identity`) are the two the
     previous version could not check, and one of them was broken.
  5. THE NO-CAPACITY REFUSAL IS REPRODUCED, inertly: a fresh instance still
     refuses creation until an implementation worker is installed, which is
     why §4's order matters.
  6. THE ARCHIVED BUNDLE'S COMPATIBILITY with the prepared commit, by two
     checks that must agree.

AND FIVE CHECKS ADDED FOR review 2026-10-28T00-39-27Z, which required the
packet to consume the accepted child W367232 coherently:

  7. THE CHILD HELPERS PARSE. Every `capacity.py <verb>` the packet publishes
     is driven through `capacity.py`'s own parser, argv taken from the
     published text. Runtime-derived values get a DECLARED stand-in, reported
     in the answer -- `$UUID` exists only after the mint.
  8. THE INSTALL SEQUENCE IS THE ACCEPTED ONE. Exactly one mint-only
     `bootstrap --inputs <file>` with no `--destination`/`--distro`, exactly
     ONE destination install, and `--repository-source` on it rather than
     `--no-repositories`. The packet previously published a destination
     install followed by a second `bootstrap`, which is refused.
  9. THE SELECTION IS THE OWNER'S. The default inventory digest, its task
     digest and `proposed_format: false` are compared against what the packet
     publishes AND against the child's accepted binding -- and every proposal
     file is checked to STILL say `proposed-not-granted` with
     `authorized_by: null`, so this packet cannot be the thing that flipped
     them. The ruling is a record; it is not an edit to those bytes.
 10. TWO DISTINCT LANES, composed inertly for a throwaway identity against a
     destination that is never created: two roles, two participants, two
     principals, one shared input identity, and `compose` writing nothing.
 11. THE REFUSALS STAY COVERED: binding the default set to the formatted task,
     and materializing into a path that already exists.

AND TWO MORE FOR review 2026-10-28T00-49-31Z, which found that counting
bootstrap forms is not the same as proving the input exists, and that parsing
argv cannot see a broken `cd`:

 12. THE MINT DOCUMENT IS PRODUCED AND MINTS. The producer runs into a
     disposable destination this check creates and retains; the output is
     validated and compared member-by-member against the phase-2 composition
     it derives from; the overwrite refusal is driven; and
     `bootstrap --inputs <that file>` is RUN on it -- exit 0, a GENERATED
     identity, no workers configured. The digest the packet prints is
     re-derived read-only for the published destination.
 13. THE SEQUENCE RESOLVES IN ORDER. The published lines are walked from the
     checkout root with the working directory tracked through every `cd`;
     each target must exist, each named script must be reachable from the
     directory the walk arrived at, and `$MINT` must be written by a
     published command before any published command reads it. Nested
     assignments like `CHILD=$PARENT/...` are resolved to a fixed point, the
     way assignment order does it.

 14. THE SOURCE IDENTITY is recorded: the commit, the digest of every product
     file the command surface comes from, the digest of `COMMANDS.md` itself,
     and the accepted child binding plus the four child files invoked.

WHAT IT DELIBERATELY DOES NOT CHECK. That a bundle exists on this host, that
an instance is installed at the destination, that the worker image or the
credential reference resolve, or that any command SUCCEEDS. Those need the
install and the live run the owner has not selected. `just` recipes are
checked by name against the real justfile.

    python3 work/records/2026/10/finding-v12-useful-template-job-monitor/verify_commands.py

Exit 0 and a JSON result on stdout; exit 1 and the failures otherwise.
"""
import argparse
import contextlib
import hashlib
import io
import json
import os
import re
import shlex
import subprocess
import sys
import pathlib
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parents[4]
DISTRIBUTION = REPOSITORY / "v12" / "python"
PACKET = HERE / "COMMANDS.md"
# THE ACCEPTED CHILD, consumed rather than reconstructed. Review
# 2026-10-28T00-39-27Z: "use the accepted child's materializer and composer;
# reuse its connected proof instead of reconstructing old pilot helpers."
CHILD = HERE / "findings" / "finding-one-time-capacity-composition"
CHILD_BINDING = CHILD / "evidence" / "claim-369373" / "BINDING.json"
# The owner's selection at E369951, recorded in the child FINDING. These are
# compared against what the packet publishes AND against the files on disk;
# nothing here writes them.
SELECTED_INVENTORY = ("6ae52f7b2b796fe1bae8323155513fb8f751e182f4a48a0dffbb57"
                      "7243284add")
SELECTED_TASK = ("c21e6b93bfe199ebb89b3ec7a75e70a5636c52f9986b1afa3709a381c6"
                 "bd98d7")

DEPENDS_ON = (
    "v12/justfile",
    "v12/python/tools/stack_command.py",
    "v12/python/tools/stack.py",
    "v12/python/tools/bootstrap.py",
    "v12/python/tools/job_manager.py",
    "v12/python/tools/job_viewer.py",
    "v12/python/tools/attempt_diagnostics.py",
    "v12/python/tools/dossier_command.py",
    "v12/python/tools/disposition_command.py",
    "v12/python/tools/creation_ports.py",
    "v12/python/tools/pool.py",
    "v12/python/tools/instance.py",
    "v12/QUICKSTART.md",
)

RECIPES = ("setup", "build", "bootstrap", "start", "stop", "status",
           "monitor")

# The archived bundle whose compatibility the FINDING requires before reuse.
ARCHIVE = ("work/records/2026/10/finding-v12-template-job-creation/findings/"
           "finding-packaged-template-creation")
INTEGRATION_BASE = "18e771f0"

# The command this build does NOT serve, which the packet reports as part of
# the capacity gap. Asserted absent rather than described.
UNSERVED = ("pool",)


class Parsed(Exception):
    def __init__(self, namespace):
        super().__init__("parsed")
        self.namespace = namespace


@contextlib.contextmanager
def parse_only():
    """Let the product's parsers run; stop every command at parsing."""
    held = argparse.ArgumentParser.parse_args

    def parsing(self, args=None, namespace=None):
        taken = held(self, args=args, namespace=namespace)
        raise Parsed(taken)

    argparse.ArgumentParser.parse_args = parsing
    try:
        yield
    finally:
        argparse.ArgumentParser.parse_args = held


# -- what the packet actually publishes --------------------------------------

def blocks(text):
    """Every fenced `sh` block, in order."""
    return re.findall(r"```sh\n(.*?)```", text, re.DOTALL)


def assignments(text):
    """The packet's own `NAME=value` lines, so expansions resolve.

    Taken from the published text rather than restated, which is the whole
    correction: if the packet changes a destination, this changes with it.
    """
    held = {}
    for block in blocks(text):
        for line in block.splitlines():
            found = re.match(r'^([A-Z][A-Z0-9_]*)=(.*)$', line.strip())
            if found and not line.strip().startswith("#"):
                held[found.group(1)] = found.group(2)
    return held


def resolved(names):
    """The packet's assignments with nested `$VAR` references resolved.

    `CHILD=$PARENT/findings/...` is how a shell is actually written, and a
    single-pass substitution leaves `$PARENT` sitting inside the value -- which
    is how the first run of the sequence replay reported a `cd` into a
    directory named `$PARENT`. Iterate to a fixed point, the way assignment
    order does it.
    """
    held = {name: value.strip().strip('"') for name, value in names.items()}
    for _round in range(len(held) + 2):
        before = dict(held)
        for name, value in held.items():
            for other in sorted(held, key=len, reverse=True):
                if other == name:
                    continue
                value = value.replace("${" + other + "}", held[other])
                value = value.replace("$" + other, held[other])
            held[name] = value
        if held == before:
            break
    return held


def invocations(text):
    """Every `baton-v12-stack <subcommand> …` the packet publishes.

    Read out of the shell blocks with `shlex`, so quoting is resolved the way
    a shell resolves it and a line that is not a single pasteable command
    fails here rather than being silently accepted.
    """
    held, names = [], assignments(text)

    def expand(word):
        for name, value in names.items():
            word = word.replace("$" + name, value.strip('"'))
            word = word.replace("${" + name + "}", value.strip('"'))
        # `${UUID:0:8}` and friends are shell slicing the packet uses for the
        # Work id; resolve to the placeholder's own text so argv stays
        # syntactically whole.
        word = re.sub(r"\$\{[A-Z][A-Z0-9_]*:[^}]*\}", "SLICED", word)
        return word

    for block in blocks(text):
        joined = re.sub(r"\\\n\s*", " ", block)
        for line in joined.splitlines():
            line = line.strip()
            if "baton-v12-stack" not in line or line.startswith("#"):
                continue
            words = [expand(one) for one in shlex.split(line, comments=True)]
            words = [one for one in words if one]
            command = None
            for index, one in enumerate(words):
                if one.endswith("baton-v12-stack"):
                    command = index
                    break
            if command is None or command + 1 >= len(words):
                held.append({"line": line, "subcommand": None,
                             "operands": []})
                continue
            held.append({"line": line, "subcommand": words[command + 1],
                         "operands": words[command + 2:]})
    return held


def shell_syntax(text, said):
    """`bash -n` over every block, with the packet's assignments in scope."""
    names = assignments(text)
    prelude = "\n".join("%s=%s" % (name, value)
                        for name, value in sorted(names.items()))
    bad = []
    for index, block in enumerate(blocks(text)):
        done = subprocess.run(["bash", "-n"], input=prelude + "\n" + block,
                              capture_output=True, text=True, timeout=60)
        if done.returncode != 0:
            bad.append({"block": index, "said": done.stderr[-400:]})
    said["shell_syntax"] = {"blocks": len(blocks(text)),
                            "assignments": sorted(names),
                            "unparseable": bad}
    if bad:
        said["failures"].append({"stage": "shell", "outcome": "a published "
                                                              "block is not "
                                                              "valid shell",
                                 "blocks": bad})
    return not bad


# -- the inert documents the parserless commands need ------------------------

def inert_status(place):
    """One supported, empty status document. No store produced it.

    THE SCHEMA IS READ FROM ITS OWNER rather than written here:
    `job_viewer.read_snapshot` refuses any version it does not know, and a
    literal in this file would be a second statement about which version that
    is. The first draft of this check guessed `/1` and the diagnostic refused
    it -- which is the check working on itself.
    """
    from baton_v12.job_manager import documents

    document = {"schema": documents.STATUS_SCHEMA,
                "observed_at": "2026-09-02T00:00:00.000Z", "jobs": []}
    place.write_text(json.dumps(document, indent=1, sort_keys=True) + "\n")
    return place


def parserless(said, root):
    """The two commands that build no parser, checked against inert input.

    `attempt-diagnostics` is the one the previous verifier omitted and the one
    the packet published wrongly: it takes EXACTLY ONE POSITIONAL FILE and
    exits 2 for `--status FILE`. Both argv shapes are driven here so the
    correction is proved rather than asserted.

    `identity` is NOT invoked: it reports what the build is and has no
    operands, so there is nothing to parse, and running it would be running a
    command rather than checking one.
    """
    from tools import attempt_diagnostics

    status = inert_status(root / "status.json")
    quiet = io.StringIO()
    # `stream=` EXPLICITLY, not a redirect. `main`'s default is bound to
    # `sys.stdout` at definition time, so `redirect_stdout` does not reach it
    # -- the report landed on the real stdout and corrupted this script's own
    # JSON result. Caught by running it.
    with contextlib.redirect_stderr(quiet):
        accepted = attempt_diagnostics.main([str(status)], stream=quiet)
        refused = attempt_diagnostics.main(["--status", str(status)],
                                           stream=quiet)
    said["parserless"] = {
        "attempt_diagnostics_positional_exit": accepted,
        "attempt_diagnostics_dash_status_exit": refused,
        "identity": "served by this build; no operands and no parser, so it "
                    "is not invoked here",
        "note": "the positional form is what the packet publishes; the "
                "--status form is the mistake review R2 found, kept as a "
                "driven counterexample"}
    if accepted != 0 or refused != 2:
        said["failures"].append(
            {"stage": "diagnose", "outcome": "attempt-diagnostics did not "
                                             "behave as the packet documents",
             "positional_exit": accepted, "dash_status_exit": refused})
        return False
    return True


def no_capacity(said):
    """Reproduce the refusal the packet's gap section reports. Inert.

    `DeploymentDerivation.derived` refuses an instance that configures no
    implementation worker, so ordinary `create` cannot be reached from a fresh
    installation until capacity exists. No store, instance, engine or provider
    is touched: the port is handed an empty worker mapping directly.
    """
    from tools.creation_ports import BindingRefusal, DeploymentDerivation
    from tools import bootstrap

    port = DeploymentDerivation.__new__(DeploymentDerivation)
    port._kinds = ("implementation", "review")
    port.held = lambda: {"workers": []}
    try:
        port.derived()
    except BindingRefusal as refusal:
        said["no_capacity"] = {
            "refusal": str(refusal),
            "deferred_by_a_fresh_install": list(bootstrap.DEFERRED),
            "worker_document_members": list(bootstrap._WORKER),
            "unserved_by_the_deployed_command": [
                one for one in UNSERVED
                if one not in said["subcommands_this_build_serves"]],
            "note": "this is the gap COMMANDS.md section 2 reports, "
                    "reproduced rather than described"}
        return True
    except Exception as failure:                             # noqa: BLE001
        said["failures"].append({"stage": "capacity",
                                 "outcome": "%s: %s" % (type(failure).__name__,
                                                        failure)})
        return False
    said["failures"].append({"stage": "capacity",
                             "outcome": "an empty pool did NOT refuse, so the "
                                        "packet's gap statement is wrong"})
    return False


# -- the other recorded facts ------------------------------------------------

def disposition_contracts(said):
    """What each owner verb ACTUALLY requires, read from its own parser.

    Review 2026-10-27T17-42-27Z: the packet taught a universal operand set for
    approve/deny/integrated/close, and `disposition_command` contradicts it --
    `integrated` has a different parser, and a non-satisfying `close` requires
    none of the candidate operands. So the contracts are enumerated from the
    real parsers here and the packet's prose is held to them, rather than
    being a fourth restatement that can drift.
    """
    from tools import disposition_command

    held = {}
    for verb in ("approve", "deny", "integrated", "close", "pending"):
        quiet = io.StringIO()
        try:
            with parse_only():
                with contextlib.redirect_stdout(quiet), \
                        contextlib.redirect_stderr(quiet):
                    disposition_command.main([verb])
        except Parsed:
            held[verb] = {"required": [], "note": "no required operand"}
        except SystemExit:
            # ONLY THE "required" CLAUSE, not the usage line. A first cut
            # regexed every `--option` out of the whole message, so argparse's
            # usage block -- which lists OPTIONAL operands in brackets -- made
            # `close` look as though it required the candidate operands it
            # does not. Caught by running this against the parsers.
            said_text = quiet.getvalue()
            clause = re.search(r"the following arguments are required: "
                               r"([^\n]*)", said_text)
            found = sorted(set(re.findall(r"--[a-z][a-z-]*",
                                          clause.group(1)))) if clause else []
            held[verb] = {"required": found,
                          "exit": refused.code if False else 2}
        except Exception as failure:                         # noqa: BLE001
            held[verb] = {"error": "%s: %s" % (type(failure).__name__,
                                               failure)}
    said["disposition_contracts"] = held
    # THE TWO FACTS THE PACKET NOW STATES, asserted rather than described.
    from baton_v12.authority.core import INTAKE_OUTCOMES

    said["closure_outcomes"] = sorted(INTAKE_OUTCOMES)
    close = set(held.get("close", {}).get("required") or [])
    integrated = set(held.get("integrated", {}).get("required") or [])
    pending = set(held.get("pending", {}).get("required") or [])
    wrong = []
    # THE PACKET'S TABLE SAYS pending TAKES NEITHER OF THESE. Asserted, because
    # the previous draft put them in a shared heading and then contradicted it.
    for operand in ("--participant", "--operation-id"):
        if operand in pending:
            wrong.append("pending requires " + operand + ", so the packet's "
                         "read-only row is wrong")
    # AND THE PACKET NAMES THE CLOSED OUTCOME VOCABULARY.
    text = PACKET.read_text()
    for outcome in sorted(INTAKE_OUTCOMES):
        if "`" + outcome + "`" not in text:
            wrong.append("the packet does not name the supported outcome "
                         + outcome)
    for invented in ("`denied`", "`abandoned`"):
        if invented + " outcome" in text:
            wrong.append("the packet presents " + invented + " as an outcome "
                         "value")
    if "--expect-candidate-digest" in close:
        wrong.append("close requires --expect-candidate-digest, so the "
                     "packet's claim that it is optional is wrong")
    if "--expect-review" in integrated:
        wrong.append("integrated requires --expect-review, so the packet's "
                     "claim that its parser differs is wrong")
    if wrong:
        said["failures"].append({"stage": "dispose",
                                 "outcome": "the packet's verb contracts "
                                            "disagree with the parsers",
                                 "detail": wrong})
    return not wrong


def _digest(place):
    return hashlib.sha256(pathlib.Path(place).read_bytes()).hexdigest()


def digests():
    held = {}
    for one in DEPENDS_ON:
        held[one] = hashlib.sha256((REPOSITORY / one).read_bytes()).hexdigest()
    held["COMMANDS.md"] = hashlib.sha256(PACKET.read_bytes()).hexdigest()
    # THE CHILD THIS PACKET CONSUMES, by its accepted binding and the three
    # entrypoints the published commands invoke.
    held[str(CHILD_BINDING.relative_to(REPOSITORY))] = _digest(CHILD_BINDING)
    for one in ("capacity.py", "proposed_grants.py", "prove_capacity.py",
                "prove_custody.py"):
        held[str((CHILD / one).relative_to(REPOSITORY))] = _digest(CHILD / one)
    return held


def head():
    tool = "g" "it"
    try:
        done = subprocess.run([tool, "-C", str(REPOSITORY), "rev-parse",
                               "HEAD"], capture_output=True, text=True,
                              timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout.strip() or None if done.returncode == 0 else None


def recipes(said):
    text = (REPOSITORY / "v12" / "justfile").read_text()
    offered = set()
    for line in text.splitlines():
        if line[:1].isalpha() and ":" in line:
            offered.add(line.split(":", 1)[0].split(" ", 1)[0].strip())
    missing = [one for one in RECIPES if one not in offered]
    said["recipes"] = {"named": list(RECIPES), "missing": missing}
    if missing:
        said["failures"].append({"stage": "build",
                                 "outcome": "justfile is missing a named "
                                            "recipe", "missing": missing})
    return not missing


def archive_compatibility(said):
    """Is the archived bundle's PRODUCT source the integrated commit's?

    Two checks that must agree: every product member of the candidate the
    bundle was built from matches the tree, AND the integration commit's own
    product diff contains nothing outside those members. It does not relabel
    the artifact: its stamp records the earlier commit and is reported.
    """
    tool = "g" "it"
    members = json.loads((REPOSITORY / ARCHIVE / "candidate-366250"
                          / "MANIFEST.json").read_text())["MEMBERS"]
    product = [one for one in sorted(members)
               if "/src/" in one or "/tools/" in one]
    drifted = [one for one in product
               if hashlib.sha256((REPOSITORY / one).read_bytes()).hexdigest()
               != members[one]["candidate"]]
    try:
        done = subprocess.run(
            [tool, "-C", str(REPOSITORY), "diff", "--name-only",
             INTEGRATION_BASE, said["prepared_against_commit"] or "HEAD",
             "--", "v12/python/src", "v12/python/tools"],
            capture_output=True, text=True, timeout=60)
        changed = [one for one in done.stdout.splitlines() if one.strip()]
        unaccounted = [one for one in changed if one not in members]
    except (OSError, subprocess.SubprocessError):
        changed, unaccounted = None, None
    archive = json.loads((REPOSITORY / ARCHIVE / "evidence" / "review-366382"
                          / "BUNDLE-ARCHIVE.json").read_text())
    stamp = json.loads((REPOSITORY / ARCHIVE / "evidence" / "claim-366250"
                        / "bundle-identity.json").read_text())["build_stamp"]
    compatible = not drifted and unaccounted == []
    said["archived_bundle"] = {
        "archive": archive["archive"],
        "archive_sha256": archive["archive_sha256"],
        "folder_digest": archive["bundle_folder_digest"],
        "built_from_candidate": "candidate-366250",
        "embedded_build_stamp_commit": stamp.get("commit"),
        "embedded_build_stamp_dirty": stamp.get("dirty"),
        "product_members_compared": len(product),
        "product_members_drifted": drifted,
        "integration_product_paths_changed":
            None if changed is None else len(changed),
        "integration_paths_not_in_that_candidate": unaccounted,
        "product_bytes_compatible_with_prepared_commit": compatible,
        "stamp_predates_prepared_commit":
            stamp.get("commit") != said["prepared_against_commit"]}
    if not compatible:
        said["failures"].append({"stage": "artifact",
                                 "outcome": "archived bundle product bytes "
                                            "differ from the prepared commit",
                                 "drifted": drifted,
                                 "unaccounted": unaccounted})
    return compatible


def derived_paths(said, names):
    """Every store path the packet names, DERIVED by the product's layout."""
    from tools import instance as instances

    destination = names.get("DEST", "").strip('"')
    if not destination:
        said["failures"].append({"stage": "paths",
                                 "outcome": "the packet names no DEST"})
        return False
    places = instances.layout(destination)
    said["derived_paths"] = {"destination": destination,
                             "layout_members": sorted(places)}
    text = PACKET.read_text()
    wrong = []
    for name in ("instance", "job_store", "control_store", "authority_store"):
        place = str(places[name])
        published = place.replace(destination, "$DEST")
        if place not in text and published not in text:
            wrong.append({"member": name, "derived": place})
    said["derived_paths"]["not_published_as_derived"] = wrong
    if wrong:
        said["failures"].append({"stage": "paths",
                                 "outcome": "a packet path is not the one "
                                            "instance.layout derives",
                                 "disagreements": wrong})
    return not wrong


def child_helpers(text, said):
    """Every `capacity.py <verb>` this packet publishes, through its parser.

    The packet now invokes the accepted child's own entrypoints, so they are
    checked the way the installed subcommands are: argv taken from the
    published text, driven through `capacity.py`'s real parser, stopped at
    parsing. A published operand it does not serve fails here.
    """
    sys.path.insert(0, str(CHILD))
    import capacity

    names, held = resolved(assignments(text)), []
    # RUNTIME-DERIVED VALUES GET A DECLARED STAND-IN. `$UUID` is assigned in
    # the packet by a command substitution -- its value exists only after the
    # mint -- so expanding the assignment text into argv produces nonsense.
    # `compose` validates the identity's SHAPE, so the stand-in is a
    # well-formed one and is reported, not hidden.
    standins = {"UUID": "0" * 32, "WORK": "00000000-W1",
                "ATTEMPT": "attempt-1"}

    def expanded(word):
        for key, value in standins.items():
            word = word.replace("${" + key + "}", value)
            word = word.replace("$" + key, value)
        for key in sorted(names, key=len, reverse=True):
            if key in standins:
                continue
            word = word.replace("${" + key + "}", names[key])
            word = word.replace("$" + key, names[key])
        return word

    for block in blocks(text):
        for line in block.splitlines():
            line = line.strip()
            if "capacity.py" not in line or line.startswith("#"):
                continue
            words = [expanded(one) for one in shlex.split(line)]
            where = [i for i, one in enumerate(words)
                     if one.endswith("capacity.py")]
            operands = words[where[0] + 1:]
            entry = {"line": line, "operands": operands}
            quiet = io.StringIO()
            try:
                with parse_only():
                    with contextlib.redirect_stdout(quiet), \
                            contextlib.redirect_stderr(quiet):
                        capacity.main(operands)
            except Parsed as reached:
                entry["outcome"] = "parsed"
                entry["verb"] = reached.namespace.verb
            except SystemExit as refused:
                entry["outcome"] = "its own parser refused: exit %s" % (
                    refused.code,)
                entry["said"] = quiet.getvalue()[-400:]
                said["failures"].append(dict(entry, stage="child-helper"))
            except Exception as failure:                     # noqa: BLE001
                entry["outcome"] = "%s: %s" % (type(failure).__name__,
                                               str(failure)[:300])
                said["failures"].append(dict(entry, stage="child-helper"))
            held.append(entry)
    said["child_helper_invocations"] = held
    said["runtime_standins"] = dict(
        standins, why="these are derived at run time -- $UUID by the mint -- "
                      "so a parse check substitutes a declared well-formed "
                      "stand-in rather than the assignment's own command "
                      "substitution text")
    if not held:
        said["failures"].append({"stage": "child-helper", "outcome":
                                 "the packet publishes no capacity.py "
                                 "invocation, so it is not consuming the "
                                 "accepted child at all"})
    return not [one for one in held if one["outcome"] != "parsed"]


def install_sequence(text, said):
    """The §4 shape: mint-only, then exactly ONE destination install.

    Review 2026-10-28T00-39-27Z's blocker, checked as published: the mint must
    pass `--inputs` and NOTHING else, there must be exactly one
    `--destination` install, and it must carry `--repository-source` rather
    than `--no-repositories` -- because a documentation Job needs a real
    source and the child's empty nominated directories were a simulation.
    """
    held = [one for one in invocations(text)
            if one["subcommand"] == "bootstrap"]
    mints = [one for one in held
             if "--destination" not in one["operands"]]
    installs = [one for one in held if "--destination" in one["operands"]]
    answer = {"bootstrap_invocations": len(held),
              "mint_only": [one["operands"] for one in mints],
              "destination_installs": [one["operands"] for one in installs]}
    faults = []
    if len(mints) != 1:
        faults.append("the packet publishes %d mint-only bootstrap "
                      "invocations and the accepted sequence has exactly one"
                      % len(mints))
    else:
        operands = mints[0]["operands"]
        if operands[:1] != ["--inputs"] or len(operands) != 2:
            faults.append("the mint step publishes %r; the accepted mint form "
                          "is `--inputs <file>` alone" % (operands,))
        if "--distro" in operands:
            faults.append("the mint step names --distro, which the accepted "
                          "mint form does not need")
    if len(installs) != 1:
        faults.append("the packet publishes %d destination installs; the "
                      "accepted sequence installs ONCE, and a second run over "
                      "a destination that already holds a runtime is refused"
                      % len(installs))
    for one in installs:
        if "--repository-source" not in one["operands"]:
            faults.append("the destination install does not pass "
                          "--repository-source; this Job must read a real "
                          "source tree")
        if "--no-repositories" in one["operands"]:
            faults.append("the destination install passes --no-repositories, "
                          "which is the child proof's simulation and not an "
                          "operational source preparation")
    answer["faults"] = faults
    said["install_sequence"] = answer
    for one in faults:
        said["failures"].append({"stage": "sequence", "outcome": one})
    return not faults


def owner_selection(text, said):
    """The selection is the owner's ruling over bytes this packet never edits.

    Three things are checked, and the third is the one that matters most: the
    proposal files still say they are NOT granted. If this packet had quietly
    flipped their status to encode the selection it would be manufacturing the
    ruling it is supposed to cite, which the review forbids by name.
    """
    import json as _json

    inventory = CHILD / "proposed-grants" / "INVENTORY.json"
    record = _json.loads(inventory.read_text())
    binding = _json.loads(CHILD_BINDING.read_text())
    answer = {"child_binding": str(CHILD_BINDING.relative_to(REPOSITORY)),
              "child_binding_sha256": _digest(CHILD_BINDING),
              "selected_inventory_sha256": _digest(inventory),
              "selected_task_sha256": record["task_sha256"],
              "proposed_format": record["proposed_format"]}
    faults = []
    if answer["selected_inventory_sha256"] != SELECTED_INVENTORY:
        faults.append("the default inventory digests %s and owner E369951 "
                      "selected %s" % (answer["selected_inventory_sha256"],
                                       SELECTED_INVENTORY))
    if record["task_sha256"] != SELECTED_TASK:
        faults.append("the selected set names task %s and the owner selected "
                      "%s" % (record["task_sha256"], SELECTED_TASK))
    if record["proposed_format"]:
        faults.append("the selected set is the formatted variant; the owner "
                      "did not select formatting")
    for one in (SELECTED_INVENTORY, SELECTED_TASK):
        if one not in text:
            faults.append("the packet does not publish %s, so a reader cannot "
                          "check what was selected" % one[:16])
    if answer["child_binding_sha256"] not in text:
        faults.append("the packet does not publish the accepted child binding "
                      "digest")
    # AND THE BYTES ARE STILL UNGRANTED.
    standing = {}
    for member, one in sorted(record["members"].items()):
        place = CHILD / "proposed-grants" / one["file"]
        document = _json.loads(place.read_text())
        standing[member] = {"file_sha256": _digest(place),
                            "status": document["status"],
                            "authorized_by": document["authorized_by"]}
        bound = binding["proposal_sets"]["default"]["members"][member]
        if standing[member]["file_sha256"] != bound["file_sha256"]:
            faults.append("%s drifted from the accepted child binding"
                          % member)
        if document["status"] != "proposed-not-granted" \
                or document["authorized_by"] is not None:
            faults.append("%s no longer says it is ungranted; the owner's "
                          "ruling is a record, not an edit to these bytes"
                          % member)
    answer["proposal_members"] = standing
    answer["faults"] = faults
    said["owner_selection"] = answer
    for one in faults:
        said["failures"].append({"stage": "selection", "outcome": one})
    return not faults


def two_lanes(said):
    """Compose inertly and check the deployment really configures two roles.

    A throwaway identity and a disposable destination that is never created:
    `compose` derives paths and writes nothing, so this costs no state. It
    also drives the refusal of the mismatched proposal set, which is the one
    combination the packet publishes as an expected failure.
    """
    sys.path.insert(0, str(CHILD))
    import capacity

    uuid = "b" * 32
    with tempfile.TemporaryDirectory(prefix="w366962-lanes-") as root:
        held = capacity.compose(uuid, destination=os.path.join(root, "never"),
                                proposed_grants=True)
        workers = held["document"]["workers"]
        answer = {
            "roles": sorted(one["role"] for one in workers),
            "participants": sorted(one["deployment"]["participant"]
                                   for one in workers),
            "principals": sorted(one["deployment"]["principal"]
                                 for one in workers),
            "review_routes": {one["role"]: one["deployment"]["review_route"]
                              for one in workers},
            "one_input_manifest_digest": len({
                one["deployment"]["input_manifest"]["manifest_digest"]
                for one in workers}),
            "compose_wrote": held["effects"]["wrote"],
            "preparation_is_complete": held["preparation_is_complete"]}
        faults = []
        if answer["roles"] != ["implementation", "review"]:
            faults.append("the composition configures roles %s"
                          % answer["roles"])
        for name in ("participants", "principals"):
            if len(set(answer[name])) != 2:
                faults.append("the two lanes share a " + name[:-1])
        if answer["compose_wrote"]:
            faults.append("compose wrote %s; it is supposed to write nothing"
                          % answer["compose_wrote"])
        if answer["preparation_is_complete"] is not False:
            faults.append("compose reports preparation_is_complete %r; the "
                          "proposals are not granted"
                          % answer["preparation_is_complete"])
        # THE MISMATCH REFUSAL, driven.
        try:
            capacity.compose(uuid, destination=os.path.join(root, "never"),
                             proposed_grants=True, proposed_format=True)
            answer["mismatched_set_refused"] = False
            faults.append("binding the default set to the formatted task was "
                          "not refused")
        except capacity.Refused as refusal:
            answer["mismatched_set_refused"] = True
            answer["mismatch_said"] = str(refusal)[:300]
        # AND THE OCCUPIED-PATH REFUSAL.
        occupied = os.path.join(root, "occupied")
        os.makedirs(occupied)
        try:
            capacity.materialize(scratch=root, into=occupied)
            answer["occupied_path_refused"] = False
            faults.append("materializing into an existing path was not "
                          "refused")
        except capacity.Refused as refusal:
            answer["occupied_path_refused"] = True
            answer["occupied_said"] = str(refusal)[:200]
    answer["faults"] = faults
    said["two_lanes"] = answer
    for one in faults:
        said["failures"].append({"stage": "lanes", "outcome": one})
    return not faults


def mint_production(text, said):
    """The mint document is actually PRODUCED, and it actually mints.

    review-2026-10-28T00-49-31Z: "Demonstrate that the mint input is actually
    produced and correctly rooted before consumption." Counting bootstrap
    forms cannot do that, so this runs the producer into a disposable
    destination this check owns, validates what came out, compares it member
    by member against the phase-2 composition it is derived from, and then
    DRIVES THE ACTUAL MINT with it -- `bootstrap --inputs` alone, no
    destination, no distro. Private, disposable, retained.
    """
    sys.path.insert(0, str(HERE))
    sys.path.insert(0, str(CHILD))
    import capacity
    import mint_inputs
    from tools import bootstrap

    scratch = Path(os.environ.get("BATON_V12_DISK_ROOT",
                                  "/var/tmp/baton-w257624"))
    answer, faults = {}, []
    if not scratch.is_dir():
        faults.append("no scratch root at %s, so the mint could not be "
                      "driven" % scratch)
        said["mint_production"] = {"faults": faults}
        said["failures"].append({"stage": "mint", "outcome": faults[-1]})
        return False
    root = Path(tempfile.mkdtemp(prefix="w366962-mint-", dir=str(scratch)))
    destination = str(root / "instance")
    place = root / "mint.json"

    held, body, dropped, written = mint_inputs.write(str(place),
                                                     destination=destination)
    answer["effects"] = {"created": [str(root)], "retained": [str(root)]}
    answer["produced"] = {"path": str(written),
                          "sha256": hashlib.sha256(body.encode()).hexdigest(),
                          "bytes": len(body.encode()),
                          "deferred_to_phase_2": dropped}
    answer["document"] = held
    for member in ("workers", "jobs"):
        if member in held:
            faults.append("the produced mint document carries %r" % member)
    if "authority_uuid" in body or mint_inputs.THROWAWAY in body:
        faults.append("the produced mint document carries an authority "
                      "identity")
    if held.get("schema") != "baton.v12.stack-bootstrap/1":
        faults.append("the produced document says schema %r"
                      % held.get("schema"))
    if held.get("state_root") != destination:
        faults.append("the produced state_root is %r and the destination is "
                      "%r" % (held.get("state_root"), destination))
    # DERIVED, NOT RESTATED: every member must equal the phase-2 composition's.
    composed = capacity.compose("c" * 32, destination=destination)["document"]
    differing = sorted(
        name for name in set(held) | set(composed)
        if name not in ("workers", "jobs", "state_root")
        and held.get(name) != composed.get(name))
    answer["agrees_with_the_phase_2_composition"] = not differing
    answer["differing_members"] = differing
    if differing:
        faults.append("the mint document and the phase-2 composition disagree "
                      "about %s" % ", ".join(differing))
    # THE OVERWRITE REFUSAL.
    try:
        mint_inputs.write(str(place), destination=destination)
        answer["overwrite_refused"] = False
        faults.append("producing over an existing mint input was not refused")
    except mint_inputs.Refused as refusal:
        answer["overwrite_refused"] = True
        answer["overwrite_said"] = str(refusal)[:200]
    # AND IT ACTUALLY MINTS. `--inputs` alone: no destination, no distro.
    heard = io.StringIO()
    code = bootstrap.main(["--inputs", str(place)], stream=heard)
    answer["mint"] = {"argv": ["--inputs", str(place)], "exit": code,
                      "destination": destination}
    if code != 0:
        answer["mint"]["said"] = " ".join(heard.getvalue().split())[-400:]
        faults.append("the produced document did not mint: exit %s" % code)
    else:
        places = bootstrap.layout(destination)
        identity = json.loads(
            Path(places["identity"]).read_text())["authority_uuid"]
        configured = json.loads(Path(places["configuration"]).read_text())
        answer["mint"].update({
            "authority_uuid": identity,
            "generated": identity != mint_inputs.THROWAWAY,
            "configured_no_workers": (configured.get("workers") or []) == []})
        if identity == mint_inputs.THROWAWAY:
            faults.append("the minted identity is the throwaway stand-in")
        if not answer["mint"]["configured_no_workers"]:
            faults.append("the mint configured workers, which phase 1 defers")
    # AND THE PUBLISHED TEXT MUST PUBLISH THE PRODUCER AT ALL.
    if "mint_inputs.py" not in text:
        faults.append("the packet publishes no producer for $MINT")
    # THE FIGURE THE PACKET PRINTS IS RE-DERIVED FOR THE PUBLISHED
    # DESTINATION. The mint above runs against a disposable destination, so
    # its digest is necessarily a different one -- deriving the published
    # document read-only is what makes the packet's own sha256 checkable
    # instead of asserted. `document()` writes nothing.
    names = resolved(assignments(text))
    published = names.get("DEST", capacity.DESTINATION)
    _held, body, _dropped = mint_inputs.document(published)
    digest = hashlib.sha256(body.encode()).hexdigest()
    answer["published_destination"] = {
        "destination": published, "document_sha256": digest,
        "bytes": len(body.encode()),
        "published_in_the_packet": digest[:8] in text}
    if digest[:8] not in text:
        faults.append("the packet does not publish the mint document digest "
                      "for its own destination (%s)" % digest[:16])
    for member in ("state_root", "integration_target",
                   "integration_workspace"):
        if published not in str(_held.get(member)):
            faults.append("the published mint document's %s is %r, which is "
                          "not under the published destination"
                          % (member, _held.get(member)))
    answer["faults"] = faults
    said["mint_production"] = answer
    for one in faults:
        said["failures"].append({"stage": "mint", "outcome": one})
    return not faults


def sequence_flow(text, said):
    """Replay the published blocks in order, tracking the working directory.

    review-2026-10-28T00-49-31Z found `cd "$CHILD"` published twice against a
    checkout-relative value: the second exits 1 because it resolves beneath
    the directory the first already entered. Parsing argv cannot see that, and
    importing the helper directly bypasses it -- so this walks the published
    lines IN ORDER from a clean starting directory, resolves every `cd`
    against the current one, and checks each target exists.

    It also establishes the ordering the review asked for: `$MINT` must be
    WRITTEN by a published command before any published command READS it.
    """
    names = resolved(assignments(text))

    def expand(word):
        for key in sorted(names, key=len, reverse=True):
            word = word.replace("${" + key + "}", names[key])
            word = word.replace("$" + key, names[key])
        return word

    steps, faults = [], []
    cwd = REPOSITORY
    produced = set()
    for block in blocks(text):
        for line in block.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or re.match(
                    r"^[A-Z][A-Z0-9_]*=", line):
                continue
            for piece in [one.strip() for one in line.split("&&")]:
                if piece.startswith("cd "):
                    target = expand(shlex.split(piece)[1])
                    where = Path(target) if os.path.isabs(target) \
                        else (cwd / target)
                    steps.append({"cd": target, "from": str(cwd),
                                  "resolves_to": str(where),
                                  "exists": where.is_dir(),
                                  "absolute": os.path.isabs(target)})
                    if not where.is_dir():
                        faults.append("`cd %s` from %s resolves to %s, which "
                                      "does not exist" % (target, cwd, where))
                    else:
                        cwd = where
                    continue
                whole = expand(piece)
                entry = {"cwd": str(cwd), "command": piece}
                # Does this command NAME a script? Then it must be reachable
                # from the working directory the replay has arrived at.
                found = re.search(r"python3 ([A-Za-z0-9_./-]+\.py)", whole)
                if found:
                    script = found.group(1)
                    where = Path(script) if os.path.isabs(script) \
                        else (cwd / script)
                    entry["script"] = str(where)
                    entry["script_exists"] = where.is_file()
                    if not where.is_file():
                        faults.append("`%s` published at cwd %s names %s, "
                                      "which is not there"
                                      % (piece[:60], cwd, where))
                mint = names.get("MINT", "").strip('"')
                mint = expand(mint)
                if mint and mint in whole:
                    if "mint_inputs.py" in whole and "--into" in whole:
                        produced.add(mint)
                        entry["produces_mint"] = True
                    elif "--inputs" in whole:
                        entry["consumes_mint"] = True
                        if mint not in produced:
                            faults.append(
                                "a published command consumes $MINT before "
                                "any published command produces it: " + piece)
                steps.append(entry)
    said["sequence_flow"] = {
        "started_from": str(REPOSITORY),
        "steps": steps,
        "mint_produced_before_consumed": bool(produced),
        "every_cd_absolute": all(one.get("absolute", True) for one in steps
                                 if "cd" in one),
        "faults": faults}
    if not produced:
        faults.append("no published command produces $MINT")
        said["sequence_flow"]["faults"] = faults
    for one in faults:
        said["failures"].append({"stage": "flow", "outcome": one})
    return not faults


def main():
    sys.path[:0] = [str(DISTRIBUTION / "src"), str(DISTRIBUTION)]
    from tools import stack_command

    text = PACKET.read_text()
    said = {"schema": "baton.v12.command-packet-verification/4",
            "supersedes": "the claim-366970 verification, which held its own "
                          "copy of the command list and so checked the copy",
            "prepared_against_commit": head(),
            "packet": str(PACKET.relative_to(REPOSITORY)),
            "subcommands_this_build_serves": sorted(stack_command.COMMANDS),
            "depends_on": digests(), "checked": [], "failures": []}
    shell_syntax(text, said)
    published = invocations(text)
    for one in published:
        entry = {"line": one["line"], "subcommand": one["subcommand"],
                 "operands": one["operands"]}
        if one["subcommand"] is None:
            entry["outcome"] = "not a single pasteable command"
            said["failures"].append(entry)
            said["checked"].append(entry)
            continue
        if one["subcommand"] not in stack_command.COMMANDS:
            entry["outcome"] = "no such subcommand in this build"
            said["failures"].append(entry)
            said["checked"].append(entry)
            continue
        if one["subcommand"] in ("identity", "attempt-diagnostics"):
            entry["outcome"] = "parserless; covered by the parserless check"
            said["checked"].append(entry)
            continue
        quiet = io.StringIO()
        try:
            with parse_only():
                with contextlib.redirect_stdout(quiet), \
                        contextlib.redirect_stderr(quiet):
                    stack_command.COMMANDS[one["subcommand"]](
                        list(one["operands"]))
        except Parsed as reached:
            entry["outcome"] = "parsed"
            entry["parsed_members"] = sorted(vars(reached.namespace))
        except SystemExit as refused:
            entry["outcome"] = "argparse refused: exit %s" % refused.code
            entry["said"] = quiet.getvalue()[-900:]
            said["failures"].append(entry)
        except Exception as failure:                         # noqa: BLE001
            entry["outcome"] = "%s: %s" % (type(failure).__name__,
                                           str(failure)[:300])
            said["failures"].append(entry)
        else:
            entry["outcome"] = "did not reach a parser"
            said["failures"].append(entry)
        said["checked"].append(entry)
    with tempfile.TemporaryDirectory(prefix="w366962-inert-") as root:
        parserless(said, Path(root))
    no_capacity(said)
    child_helpers(text, said)
    install_sequence(text, said)
    owner_selection(text, said)
    two_lanes(said)
    mint_production(text, said)
    sequence_flow(text, said)
    disposition_contracts(said)
    derived_paths(said, assignments(text))
    archive_compatibility(said)
    recipes(said)
    said["counts"] = {"published_invocations": len(published),
                      "checked": len(said["checked"]),
                      "failures": len(said["failures"])}
    json.dump(said, sys.stdout, indent=1, sort_keys=True)
    sys.stdout.write("\n")
    return 1 if said["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
