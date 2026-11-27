"""Replace one stopped instance worker's immutable image, preserving attempt history."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re

from baton_v12 import provider_policy
from baton_v12.contracts import ContractRefusal, digest
from tools import installed_worker, instance, job_status, next_run_bindings
from tools import pool, runtime_upgrade, stack
from tools.fresh_attempt_ports import DeploymentBinding

INTENT = "worker-image-upgrade.json"


def file_identity(document):
    return hashlib.sha256(json.dumps(document, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def arguments(verbs):
    parser = verbs.add_parser("upgrade-image", help="replace one stopped instance worker's image for future admissions")
    for flag in ("instance", "worker-id", "from-image", "image", "cli-build", "source"):
        parser.add_argument("--" + flag, required=True, help={
            "instance": "installed instance.json", "worker-id": "existing worker identity",
            "from-image": "expected current immutable image ID", "image": "selected new immutable image ID",
            "cli-build": "exact selected provider CLI version", "source": "v12 directory for installed adapter comparison"}[flag])


def worker_in(document, worker_id):
    matches = [one for one in document["workers"] if one["worker_id"] == worker_id]
    if len(matches) != 1:
        raise pool.PoolRefusal(f"expected one configured worker {worker_id!r}")
    return matches[0]


def replacement(worker, image, build):
    deployment = worker["deployment"]
    binding = deployment.get("provider_contract")
    if not binding or worker["role"] not in ("implementation", "review"):
        raise pool.PoolRefusal("upgrade-image selects an ordinary implementation or review provider worker")
    selection = provider_policy.selection(dict(binding["selection"], cli_build=build))
    adapter = provider_policy.adapter(selection, network=deployment["network"])
    profile = dict(binding["runtime_profile"], image_reference=image, image_digest=image, cli_build=build)
    # Certification keys include the name. A new digest must never reuse the old certification key.
    profile["name"] = selection["provider"] + "-" + digest({k: v for k, v in profile.items() if k != "name"})[7:]
    manifest = dict(deployment["input_manifest"], worker_image_digest=image, runtime_profile_digest=digest(profile),
                    toolchain_digest=next_run_bindings.toolchain_digest(image, image, build))
    del manifest["manifest_digest"]
    manifest["manifest_digest"] = digest(manifest)
    return dict(image_digest=image, profile_name=profile["name"], profile_digest=digest(profile),
                adapter_digest=digest(adapter), input_manifest=manifest,
                provider_contract=dict(selection=selection, adapter=adapter, runtime_profile=profile))


def qualify(worker, source, build):
    report = installed_worker.measure({"workers": [worker]}, source)
    if not report["qualified"]:
        raise pool.PoolRefusal("installed image qualification failed: " + "; ".join(report["workers"][0]["problems"]))
    measured = report["workers"][0]
    provider = measured["provider"]
    raw = installed_worker._docker("docker", "run", "--rm", "--pull=never", "--network=none", "--read-only",
                                  "--cap-drop=ALL", "--security-opt=no-new-privileges",
                                  "--entrypoint", provider, measured["image"], "--version")
    actual = raw.decode("utf-8").strip()
    accepted = (build, build + " (Claude Code)") if provider == "claude" else ("codex-cli " + build,)
    if actual not in accepted:
        raise pool.PoolRefusal(f"{provider} in the selected image did not report CLI build {build}")
    return dict(measured, version_output=actual)


def prepare(document, inputs, status, selected):
    from tools import stage_execution
    worker = worker_in(document, selected["worker"])
    old = worker["deployment"]
    installed = worker_in(inputs, selected["worker"])
    if (installed["role"] != worker["role"] or installed["participant"] != old["participant"]
            or any(installed["deployment"].get(k) != old.get(k) for k in
                   ("provider_contract", "image_digest", "profile_digest", "input_manifest"))):
        raise pool.PoolRefusal("the selected worker differs between install-inputs and deployment")
    if old.get("provider_contract", {}).get("runtime_profile", {}).get("image_digest") != old["image_digest"]:
        raise pool.PoolRefusal("configured image differs from the provider runtime profile")
    if old["image_digest"] != selected["from_image"]:
        raise pool.PoolRefusal("current worker image differs from --from-image")
    if inputs.get("stage_image_upgrades", {}) != document.get("stage_image_upgrades", {}):
        raise pool.PoolRefusal("stored stage upgrades disagree between install inputs and deployment")
    changes = replacement(worker, selected["image"], selected["cli_build"])
    after = deepcopy(document)
    worker_in(after, selected["worker"])["deployment"].update(changes)
    updates = after.setdefault("stage_image_upgrades", {})
    for job in status["jobs"]:
        if job.get("integration"):
            continue
        for stage in job["stages"]:
            if stage["kind"] != worker["role"]:
                continue
            key = stage["stage_id"]
            if key in updates or (stage["profile_name"], stage["profile_digest"]) != (old["profile_name"], old["profile_digest"]):
                continue
            if any(other is not worker and other["role"] == worker["role"]
                   and other["deployment"]["profile_digest"] == old["profile_digest"] for other in document["workers"]):
                raise pool.PoolRefusal(f"stage {key} has more than one possible worker for its original profile")
            updates[key] = dict(worker_id=worker["worker_id"], kind=stage["kind"], original_name=old["profile_name"],
                                original_digest=old["profile_digest"])
    if not updates:
        del after["stage_image_upgrades"]
    held = stage_execution.held_configuration(after)
    after["pool_generation"] = pool.minted_generation(document, held)
    new_inputs = deepcopy(inputs)
    worker_in(new_inputs, selected["worker"])["deployment"].update(changes)
    new_inputs["pool_generation"] = after["pool_generation"]
    if updates:
        new_inputs["stage_image_upgrades"] = deepcopy(updates)
    return new_inputs, after


def run(args, stream):
    try:
        upgrade(args, stream)
        return 0
    except (pool.PoolRefusal, runtime_upgrade.UpgradeRefusal, instance.InstanceRefusal, stack.StackRefusal,
            installed_worker.Unreadable, ContractRefusal, OSError, ValueError) as error:
        print("refused: " + str(error), file=stream)
        return 2


def upgrade(args, stream):
    selected = dict(worker=args.worker_id, from_image=args.from_image, image=args.image,
                    cli_build=args.cli_build, source=str(Path(args.source).resolve()))
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", args.cli_build):
        raise pool.PoolRefusal("select an exact provider CLI version")
    if not all(re.fullmatch(r"sha256:[0-9a-f]{64}", selected[k]) for k in ("image", "from_image")):
        raise pool.PoolRefusal("both images must be immutable sha256 IDs")
    selector = instance.read(args.instance)
    root = Path(selector["destination"])
    pending = root / INTENT
    places = (root / "install-inputs.json", Path(selector["deployment"]))
    # Refuse existing reservations before even creating a lifecycle or publication lock file.
    # Recheck after locking because an admission could have won in between.
    runtime_upgrade._quiet(selector, job_status.read, worker_id=args.worker_id)
    with stack.admission(Path(selector["state"])), DeploymentBinding(root)._publishing(image_upgrade=True):
        instance.verify(selector)
        runtime_upgrade._stopped(Path(selector["state"]))
        status = runtime_upgrade._quiet(selector, job_status.read, worker_id=args.worker_id)
        if (root / runtime_upgrade.INTENT).exists():
            raise pool.PoolRefusal("finish the pending host runtime upgrade first")
        if any(path.is_symlink() for path in (*places, pending)):
            raise pool.PoolRefusal("instance configuration and upgrade intent must be local regular files")
        inputs, deployment = [pool.read_configuration(path) for path in places]
        worker = worker_in(deployment, args.worker_id)
        if deployment["authority_uuid"] != selector["authority_uuid"] or pool.job_store_of(deployment) != selector["job_store"]:
            raise pool.PoolRefusal("worker deployment and instance selector identify different stores")
        if pending.exists():
            intent = json.loads(pending.read_bytes())
            if intent.get("content_digest") != file_identity({k: v for k, v in intent.items() if k != "content_digest"}):
                raise pool.PoolRefusal("the pending image upgrade does not match its recorded content digest")
            if intent["selection"] != selected:
                raise pool.PoolRefusal("another image upgrade is pending; retry its exact selection")
        else:
            if worker["deployment"]["image_digest"] == args.image:
                installed = worker_in(inputs, args.worker_id)["deployment"]
                if installed.get("provider_contract") != worker["deployment"].get("provider_contract") or installed.get("image_digest") != args.image:
                    raise pool.PoolRefusal("the installation inputs and active deployment disagree on the selected image")
                if worker["deployment"].get("provider_contract", {}).get("selection", {}).get("cli_build") != args.cli_build:
                    raise pool.PoolRefusal("the configured image has another CLI build")
                print("unchanged  worker already configured for selected image and CLI build", file=stream)
                return
            new_inputs, new_deployment = prepare(deployment, inputs, status, selected)
            evidence = qualify(worker_in(new_deployment, args.worker_id), args.source, args.cli_build)
            intent = dict(selection=selected, qualification=evidence, before=[file_identity(inputs), file_identity(deployment)],
                          after=[new_inputs, new_deployment])
            intent["content_digest"] = file_identity(intent)
            instance.publish(pending, intent)
        for path, current, original, new in zip(places, (inputs, deployment), intent["before"], intent["after"], strict=True):
            if current != new and file_identity(current) != original:
                raise pool.PoolRefusal(f"{path.name} changed during this upgrade; retained the intent")
        for path, current, new in zip(places, (inputs, deployment), intent["after"], strict=True):
            if current != new:
                instance.publish(path, new)
        receipt = root / ("worker-image-" + file_identity(intent) + ".json")
        evidence = {key: intent[key] for key in ("selection", "qualification", "before")}
        evidence["after"] = [file_identity(one) for one in intent["after"]]
        if receipt.exists():
            if json.loads(receipt.read_bytes()) != evidence:
                raise pool.PoolRefusal("existing image upgrade receipt conflicts with the pending selection")
        else:
            instance.create(receipt, evidence)
        pending.unlink()
        print(f"upgraded   {args.worker_id} to {args.image}, CLI {args.cli_build}; receipt {receipt}", file=stream)
