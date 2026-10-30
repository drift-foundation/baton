#!/usr/bin/env python3
"""Seven PROPOSED policy artifacts, with real sources — and not one grant.

Owner selection E369183: *"Select preparation of concrete proposed artifacts
for the seven missing policy/instruction/toolchain inputs, reusing documented
existing policies where supported. Make proposed grants explicit for review;
do not infer authorization from fixture values."*

THE WORD "PROPOSED" IS NOT DECORATION. `tools/dogfood_operator.input_manifest`
is explicit: *"EVERY POLICY IDENTITY IS AN OPERAND … A tool that filled one in
would be making a grant on an operator's behalf."* So every document here
carries `status: "proposed-not-granted"` and `authorized_by: null`, binding
them is an explicit opt-in (`compose --proposed-grants`), and even with them
bound the composition still reports `preparation_is_complete: false`. A
proposal an owner has not selected is not a grant, and nothing here pretends
otherwise.

WHERE EACH ONE COMES FROM. Five are composed from content that ALREADY EXISTS
at the selected revision and is read here; two are authored from documented
deployment facts because no such document exists anywhere to reuse. Each
artifact says which it is, in its own `derivation` member, with the file and
the sha256 it was read from.

    role_instructions    REUSED   the product's own two prompt composers,
                                  `claude_agent._prompt` and
                                  `_review_prompt`, RENDERED against this
                                  Job's own task document
    toolchain            REUSED   `v12/worker/Dockerfile.claude`, the image
                                  recipe at the selected revision
    tool_policy          REUSED   `provider_context.ARGV_POLICY` and
                                  `ENVIRONMENT_POLICY`, the real constants the
                                  product digests for its own context profile
    mount_policy         REUSED   the reviewed manifest's own
                                  `sources[].consumption` and
                                  `single_worker.SOURCE_DESTINATION`
    credential_policy    REUSED   the reviewed pilot worker's credential
                                  profile, slots and sources registry path
    resource_policy      AUTHORED from documented deployment values: the
                                  reviewed worker's workspace capacity, the
                                  product's own scratch and workspace minima,
                                  and this Job's selected limits
    network_policy       AUTHORED from the documented `bridge` selection; the
                                  product ships no network policy document

THE TOOLCHAIN CAVEAT, SAID OUT LOUD. The recipe is not the built image.
`worker_image_digest` names `sha256:c862c055…` and nothing here contacts a
container engine, so the proposed toolchain describes WHAT THE RECIPE BUILDS
at the selected revision and NOT what is inside that image. An owner binding
it is accepting the recipe as the toolchain statement, or must inspect the
image first. Its artifact says so.

NO SECRET APPEARS HERE. The credential proposal carries the slot name, the
provider kind and the operator's own reference string — the same three the
reviewed deployment already publishes — and never a credential.
"""
import ast
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import capacity                                              # noqa: E402

sys.path[:0] = [str(capacity.DISTRIBUTION / "src"),
                str(capacity.DISTRIBUTION)]

REPOSITORY = capacity.REPOSITORY
WORKER = REPOSITORY / "v12" / "worker"
AGENT = WORKER / "claude_agent.py"
RECIPE = WORKER / "Dockerfile.claude"
PROVIDER_CONTEXT = (REPOSITORY / "v12/python/src/baton_v12/worker_manager"
                    / "provider_context.py")
SOURCE_BOUNDARY = (REPOSITORY / "v12/python/src/baton_v12/worker_manager"
                   / "source_boundary.py")
SINGLE_WORKER = REPOSITORY / "v12/python/tools/single_worker.py"

# The seven, in the order the input manifest names them.
MEMBERS = ("role_instructions_digest", "toolchain_digest",
           "resource_policy_digest", "network_policy_digest",
           "mount_policy_digest", "tool_policy_digest",
           "credential_policy_digest")

PLACE = HERE / "proposed-grants"
INVENTORY = "INVENTORY.json"


def _named(place, name):
    """One module-level constant's value, by literal evaluation.

    `claude_agent` cannot be imported from this checkout -- it does
    `import source_profiles`, a module the image builds and the tree does not
    carry -- so its constants are read out of the source rather than guessed.
    Literal evaluation only: nothing in that file is executed here.
    """
    tree = ast.parse(pathlib.Path(place).read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return ast.literal_eval(node.value)
    raise capacity.Refused("%s defines no %s" % (place, name))


def _rendered_prompts(task):
    """The product's own two prompt composers, RENDERED for this task.

    The same reason as `_named`: the module will not import from a checkout,
    so the two functions are extracted by name from its syntax tree and
    executed ALONE, with only the constants they reference in scope. What
    comes out is the text this deployment's own workload would compose for
    this Job -- real existing content, not instructions I wrote.
    """
    text = AGENT.read_text(encoding="utf-8")
    tree = ast.parse(text)
    wanted = {"_prompt", "_review_prompt"}
    found = {node.name: node for node in tree.body
             if isinstance(node, ast.FunctionDef) and node.name in wanted}
    if set(found) != wanted:
        raise capacity.Refused(
            "%s no longer defines %s; the proposed role instructions are "
            "rendered from those composers and will not be guessed"
            % (AGENT, ", ".join(sorted(wanted - set(found)))))

    class _Refusal(Exception):
        pass

    room = {"TaskRefusal": _Refusal,
            "MAX_FEEDBACK_BYTES": _named(AGENT, "MAX_FEEDBACK_BYTES"),
            "REVIEW_REPORT_SCHEMA": _named(AGENT, "REVIEW_REPORT_SCHEMA"),
            "REVIEW_VERDICTS": _named(AGENT, "REVIEW_VERDICTS")}
    exec(compile(ast.Module(body=[found["_prompt"], found["_review_prompt"]],
                            type_ignores=[]), str(AGENT), "exec"), room)
    _context, _boundary, worker = _owning()
    staged = "/input/" + worker.SOURCE_DESTINATION
    return ({"role": "implementation",
             "composer": "claude_agent._prompt",
             "lines": [found["_prompt"].lineno,
                       found["_prompt"].end_lineno],
             "rendered": room["_prompt"](task)},
            {"role": "review",
             "composer": "claude_agent._review_prompt",
             "lines": [found["_review_prompt"].lineno,
                       found["_review_prompt"].end_lineno],
             "staged_source": staged,
             "report": _named(AGENT, "REVIEW_REPORT"),
             "rendered": room["_review_prompt"](
                 task, staged, _named(AGENT, "REVIEW_REPORT"))})


def _owning():
    """The three product modules that DO import from a checkout.

    `claude_agent` does not -- it reaches for `source_profiles`, which the
    image builds -- so only its constants are read out of its syntax tree.
    Everything else is taken from the module itself, which is stronger: a
    renamed or recomputed constant fails here instead of being read as a
    literal that no longer describes anything.
    """
    from baton_v12.worker_manager import provider_context, source_boundary
    from tools import single_worker
    return provider_context, source_boundary, single_worker


def _shown(place):
    """Repository-relative when it is in the repository, absolute otherwise.

    A variant published into owned scratch is deliberately NOT in the
    repository, and a path helper that assumed it was is what broke the first
    run of the two-arm proof.
    """
    place = pathlib.Path(place)
    try:
        return str(place.relative_to(REPOSITORY))
    except ValueError:
        return str(place)


def _from(place, what):
    return {"path": str(pathlib.Path(place).relative_to(REPOSITORY)),
            "sha256": capacity._digest_of(place), "what": what}


def documents(task_document):
    """The seven proposed artifacts, composed for THIS Job's task."""
    worker = capacity._pilot_deployment_base(capacity.LANES[0]["role"])
    reviewed = json.loads(capacity.PILOT_MANIFEST.read_text())
    manifest = reviewed["workers"][0]["deployment"]["input_manifest"]
    context, boundary, staging = _owning()
    implementation, review = _rendered_prompts(task_document)
    recipe = RECIPE.read_text(encoding="utf-8")
    installs = [one.strip() for one in recipe.splitlines()
                if one.strip().startswith(("RUN ", "FROM ", "COPY "))]

    held = {
        "role_instructions_digest": {
            "schema": "baton.v12.proposed-role-instructions/1",
            "derivation": "reused",
            "read_from": [_from(AGENT, "the product's own prompt composers")],
            "why_one_identity_for_two_roles":
                "contracts/manifest.py excludes role_instructions_digest from "
                "JOB_INPUT_EXCLUDED's complement -- it is projected OUT of the "
                "Job-scoped identity precisely because the two roles are told "
                "different things -- so one manifest may carry one identity "
                "for the PAIR, and this artifact names both renderings",
            "roles": [implementation, review]},
        "toolchain_digest": {
            "schema": "baton.v12.proposed-toolchain/1",
            "derivation": "reused",
            "read_from": [_from(RECIPE, "the worker image build recipe at "
                                        "the selected revision")],
            "image_this_describes": worker.get("image_digest"),
            "CAVEAT": "this is the RECIPE, not an inspection of the built "
                      "image. Nothing here contacts a container engine, so "
                      "binding this accepts the recipe at %s as the toolchain "
                      "statement for image %s. An owner who needs the image's "
                      "actual inventory must inspect the image."
                      % (capacity.SOURCE_COMMIT[:8], worker.get("image_digest")),
            "recipe_sha256": capacity._digest_of(RECIPE),
            "build_steps": installs},
        "resource_policy_digest": {
            "schema": "baton.v12.proposed-resource-policy/1",
            "derivation": "authored",
            "why_authored": "the product ships no resource policy document; "
                            "these are the documented values the deployment "
                            "and this Job already carry, collected into one",
            "read_from": [_from(capacity.PILOT, "the reviewed pilot worker's "
                                                "workspace capacity"),
                          _from(SOURCE_BOUNDARY, "the workspace minimum")],
            "workspace_capacity": worker.get("workspace_capacity"),
            "workspace_group": worker.get("workspace_group"),
            "workspace_min_bytes": boundary.MIN_WORKSPACE_BYTES,
            "scratch_bytes": boundary.SCRATCH_BYTES,
            "shared_memory_bytes": boundary.SHARED_MEMORY_BYTES,
            "provider_turn_seconds": capacity.PROVIDER_TURN_SECONDS,
            "verification_command_seconds":
                capacity.VERIFICATION_COMMAND_SECONDS,
            "automatic_retry": False},
        "network_policy_digest": {
            "schema": "baton.v12.proposed-network-policy/1",
            "derivation": "authored",
            "why_authored": "the product ships no network policy document; "
                            "this states the network the reviewed deployment "
                            "selects and nothing more",
            "read_from": [_from(capacity.PILOT, "the reviewed pilot worker's "
                                                "network selection")],
            "network": worker.get("network"),
            "engine": worker.get("engine"),
            "egress": "not stated by any document this preparation can read; "
                      "an owner binding this is accepting the network NAME "
                      "and not an egress ruling"},
        "mount_policy_digest": {
            "schema": "baton.v12.proposed-mount-policy/1",
            "derivation": "reused",
            "read_from": [_from(capacity.PILOT_MANIFEST,
                                "the reviewed manifest's own source "
                                "consumption"),
                          _from(SINGLE_WORKER, "the staged source "
                                               "destination")],
            "consumption": manifest["sources"][0]["consumption"],
            "destination": manifest["sources"][0]["destination"],
            "source_destination": staging.SOURCE_DESTINATION,
            "nominated_mount_is_read_only": "stated by the reviewed "
                                            "deployment's delivery kind "
                                            "'nominated-mount'"},
        "tool_policy_digest": {
            "schema": "baton.v12.proposed-tool-policy/1",
            "derivation": "reused",
            "read_from": [_from(PROVIDER_CONTEXT, "the product's own argv "
                                                  "and environment policy")],
            "argv_policy": dict(context.ARGV_POLICY),
            "environment_policy": dict(context.ENVIRONMENT_POLICY),
            "note": "tools/next_run_bindings.py digests these same two "
                    "constants for its context profile, so this proposal "
                    "reuses content the product already treats as policy"},
        "credential_policy_digest": {
            "schema": "baton.v12.proposed-credential-policy/1",
            "derivation": "reused",
            "read_from": [_from(capacity.PILOT, "the reviewed pilot worker's "
                                                "credential profile")],
            "slots": worker.get("credential_slots"),
            "profile": worker.get("credential_profile"),
            "sources_registry": worker.get("credential_sources"),
            "no_secret_here": "the slot name, the provider kind and the "
                              "operator's own reference string -- the three "
                              "the reviewed deployment already publishes. No "
                              "credential is read, resolved or written.",
            "resolution_is_the_operator's": "nothing here contacts the "
                                            "credential provider, so an "
                                            "owner must confirm the "
                                            "reference resolves on the "
                                            "installing host"},
    }
    for member, document in held.items():
        document.update({
            "proposed_for": member,
            "status": "proposed-not-granted",
            "authorized_by": None,
            "selected_by": None,
            "for_selection": capacity.SOURCE_COMMIT,
            "missing_selection_this_answers":
                capacity.OPERATOR_GRANTS[member][1]})
    return held


def sealed(task_document):
    """The seven, each with the identity it would carry if granted."""
    from baton_v12.contracts import digest as seal

    held = documents(task_document)
    return {member: {"document": document, "digest": seal(document)}
            for member, document in held.items()}


def inventory(task_document, task_bytes, *, into=PLACE, proposed_format=False):
    """What a published set IS, without publishing anything.

    The inventory is what makes read-only consumption possible: it names the
    TASK the seven were composed for, by digest, so a composition can prove
    the published bytes describe the task it is binding them to instead of
    quietly regenerating them. `capacity.compose` reads this and refuses a
    mismatch; it no longer writes.
    """
    into = pathlib.Path(into)
    held = sealed(task_document)
    return {"schema": "baton.v12.proposed-grants-inventory/1",
            "status": "PROPOSED, NOT GRANTED",
            "authorized_by": None,
            "task_id": task_document["task_id"],
            "task_sha256": capacity.sha256_of(task_bytes),
            "proposed_format": bool(proposed_format),
            "for_selection": capacity.SOURCE_COMMIT,
            "members": {
                member: {
                    "file": member.replace("_digest", "") + ".json",
                    "identity_if_granted": one["digest"],
                    "derivation": one["document"]["derivation"],
                    "status": one["document"]["status"]}
                for member, one in sorted(held.items())},
            "note": "a set is identified by the task it was composed for. "
                    "The default and the format-selected variant are "
                    "DIFFERENT SETS with different role instructions, and "
                    "neither may be written over the other."}


def published(into=PLACE):
    """READ-ONLY: load a published set and hold every file to its inventory.

    review-2026-10-27T22-59-54Z: "composition must consume explicitly pinned
    proposal bytes or generate proposed documents purely in memory." This is
    the first of those. It opens files, digests them, compares, and writes
    nothing -- a set that has drifted from its own inventory is refused here
    rather than silently rebuilt.
    """
    into = pathlib.Path(into)
    record = into / INVENTORY
    if not record.is_file():
        raise capacity.Refused(
            "%s publishes no %s, so there is no pinned proposal set to "
            "consume. Publish one with `python3 proposed_grants.py --into "
            "%s`." % (into, INVENTORY, into))
    held = json.loads(record.read_text(encoding="utf-8"))
    drifted, missing = [], []
    for member, one in sorted(held["members"].items()):
        place = into / one["file"]
        if not place.is_file():
            missing.append(one["file"])
            continue
        found = capacity._digest_of(place)
        if found != one["file_sha256"]:
            drifted.append("%s digests %s and the inventory pins %s"
                           % (one["file"], found, one["file_sha256"]))
        one["read_from"] = str(place)
    if missing or drifted:
        raise capacity.Refused(
            "the published proposal set at %s does not match its own "
            "inventory%s%s; nothing was consumed"
            % (into,
               ("; missing " + ", ".join(missing)) if missing else "",
               ("; " + "; ".join(drifted)) if drifted else ""))
    held["read_from"] = str(record)
    return held


def write(task_document, task_bytes, *, into=PLACE, proposed_format=False):
    """Publish the seven AND their inventory. THE ONLY THING THAT WRITES.

    IT REFUSES TO WRITE OVER ANOTHER SET. review-2026-10-27T22-59-54Z found
    the defect this exists to make impossible: a composition proving the
    format-selected variant overwrote the DEFAULT proposal that was awaiting
    owner selection, because both went to one fixed directory and nothing
    compared them. Now a directory that already publishes an inventory for a
    different task is refused, by name, with the remedy -- publish the
    variant to a fresh output set of its own.
    """
    into = pathlib.Path(into)
    record = inventory(task_document, task_bytes, into=into,
                       proposed_format=proposed_format)
    standing = into / INVENTORY
    if standing.is_file():
        before = json.loads(standing.read_text(encoding="utf-8"))
        if (before.get("task_sha256") != record["task_sha256"]
                or before.get("proposed_format")
                != record["proposed_format"]):
            raise capacity.Refused(
                "%s already publishes a proposal set for task digest %s "
                "(proposed_format=%s) and this one is for %s "
                "(proposed_format=%s). These are different sets with "
                "different role instructions, and nothing here writes over "
                "a set awaiting selection. Publish this one somewhere of "
                "its own: `--into <a fresh directory>`."
                % (into, (before.get("task_sha256") or "?")[:16],
                   before.get("proposed_format"),
                   record["task_sha256"][:16], record["proposed_format"]))
    into.mkdir(parents=True, exist_ok=True)
    held, wrote = sealed(task_document), {}
    for member, one in sorted(held.items()):
        place = into / record["members"][member]["file"]
        place.write_text(json.dumps(one["document"], indent=1,
                                    sort_keys=True) + "\n")
        record["members"][member]["file_sha256"] = capacity._digest_of(place)
        wrote[member] = dict(record["members"][member],
                             path=_shown(place))
    standing.write_text(json.dumps(record, indent=1, sort_keys=True) + "\n")
    return {"members": wrote, "inventory": _shown(standing),
        "inventory_sha256": capacity._digest_of(standing),
        "wrote": sorted([str(standing)] + [str(into / one["file"])
                                           for one in
                                           record["members"].values()])}


def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--into", default=str(PLACE),
                        help="where to publish. A directory already "
                             "publishing a set for another task is REFUSED.")
    parser.add_argument("--proposed-format", action="store_true",
                        help="compose for the format-selected task. This is "
                             "a DIFFERENT SET -- its role instructions "
                             "differ -- so it needs an --into of its own.")
    parser.add_argument("--verify", action="store_true",
                        help="READ-ONLY: hold a published set to its own "
                             "inventory and report; write nothing")
    parser.add_argument("--print-rendered", action="store_true",
                        help="also print the two rendered role prompts")
    taken = parser.parse_args(argv)
    held = capacity.source_identity()
    if not held["at_selected_commit"]:
        print("refused: the selected source is at %s and this preparation is "
              "for %s" % (held["commit"], held["selected"]), file=sys.stderr)
        return 2
    task_document, task_bytes = capacity.installed_task(
        held, proposed_format=taken.proposed_format)
    try:
        if taken.verify:
            record = published(taken.into)
            answer = {"schema": "baton.v12.proposed-grants/2",
                      "command": "verify",
                      "effects": {"wrote": [], "created": [], "removed": []},
                      "read_only": True,
                      "inventory": record,
                      "matches_the_task_composed_now":
                          record["task_sha256"]
                          == capacity.sha256_of(task_bytes)}
        else:
            wrote = write(task_document, task_bytes, into=taken.into,
                          proposed_format=taken.proposed_format)
            answer = {"schema": "baton.v12.proposed-grants/2",
                      "command": "publish",
                      "status": "PROPOSED, NOT GRANTED -- an owner selects "
                                "these or names others; nothing here "
                                "authorizes anything",
                      "effects": {"wrote": wrote["wrote"], "created": [],
                                  "removed": []},
                      "members": wrote["members"],
                      "inventory": wrote["inventory"],
                      "inventory_sha256": wrote["inventory_sha256"],
                      "proposed_format": bool(taken.proposed_format),
                      "task_this_was_composed_for":
                          task_document["task_id"],
                      "task_sha256": capacity.sha256_of(task_bytes),
                      "bind_them_with":
                          "python3 capacity.py compose --minted-uuid <uuid> "
                          "--grants-from " + str(taken.into),
                      "even_then": "preparation_is_complete stays false: "
                                   "binding a proposal is not receiving a "
                                   "grant"}
    except capacity.Refused as refusal:
        print("refused: " + str(refusal), file=sys.stderr)
        return 2
    if taken.print_rendered:
        roles = sealed(task_document)["role_instructions_digest"]["document"]
        answer["rendered_role_instructions"] = {
            one["role"]: one["rendered"] for one in roles["roles"]}
    json.dump(answer, sys.stdout, indent=1, sort_keys=True, default=str)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
