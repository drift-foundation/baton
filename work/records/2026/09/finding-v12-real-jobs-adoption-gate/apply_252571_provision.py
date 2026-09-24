"""Claim-252571: the preparation provisions the directories it declares.

Owner 2026-09-23 startup entry, which review 2026-09-24T01:14:08Z pointed me
back to: "the prepared instance passed composition, but the live supervisor
refused in `worker_preflight` because its configured `run/workspaces` directory
did not exist. Preparation declares that path but does not provision it."

`workspaces.check_workspace_storage` asks with `lstat` and refuses a name that
is not there -- so the packet named four owned roots and created none of them,
and `operations_from` raised before `submit` and before `supervise`. The
operator's stopgap was to `mkdir` the one path by hand.

MY DIAGNOSIS SAID THIS WAS UNIDENTIFIED. It was not: the owner had already
identified it precisely, one entry above the one I was reading, and I recorded
an unknown where a finding existed. The correction is appended to
DIAGNOSIS-252472.md as well as made here.

WHAT IS PROVISIONED, and only this: the four roots the composed deployment
names under the run root -- the workspace store, the launch home, the
credential home and the deployment state root -- created 0o700 and owned by
this user, which is what `check_workspace_storage` requires. Nothing outside
the run root is touched, and provisioning happens AFTER the composer has made
`run/`, so the create-only rule is untouched.
"""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
PLACE = HERE / "prepare_two_jobs.py"

OLD_LAYOUT = '''        "bootstrap_inputs": os.path.join(run_root, "bootstrap-inputs.json"),
    }
'''

NEW_LAYOUT = '''        "bootstrap_inputs": os.path.join(run_root, "bootstrap-inputs.json"),
        "workspace_storage": os.path.join(run_root, "run", "workspaces"),
        "launch_home": os.path.join(run_root, "run", "launch"),
        "credential_home": os.path.join(run_root, "run", "credentials"),
    }


# THE OWNED ROOTS A LIVE PREFLIGHT REQUIRES TO EXIST. Owner 2026-09-23:
# `worker_preflight` refused because `run/workspaces` was not there, and
# `workspaces.check_workspace_storage` asks with `lstat` -- an absent name is a
# refusal, a symlink is a refusal, and a directory this uid does not own is a
# refusal. The packet named these and created none.
PROVISIONED = ("workspace_storage", "launch_home", "credential_home",
               "state_root")


def provision(places):
    """Create the owned roots the composed deployment names. 0o700, ours.

    AFTER THE COMPOSER, never before: `run/` must not exist when the composer
    runs, and these live under it. Each is created with `exist_ok` because the
    composer may have made one already, and each is then READ BACK through the
    product's own check so this reports what the live preflight will find
    rather than what it intended.
    """
    from baton_v12.worker_manager import workspaces
    held = {}
    for name in PROVISIONED:
        place = places[name]
        os.makedirs(place, mode=0o700, exist_ok=True)
        held[name] = {"path": place, "created": True}
    # THE PRODUCT'S OWN JUDGMENT on the one it refuses most sharply, so a
    # provisioning that satisfies this file but not the manager is a refusal
    # here rather than a refusal at the operator's next command.
    workspaces.check_workspace_storage(places["workspace_storage"])
    held["workspace_storage"]["held_by_product"] = True
    return held
'''

OLD_INSTANCE = '''        "workspace_storage": os.path.join(run, "workspaces"),
        "launch_home": os.path.join(run, "launch"),
        "credential_home": os.path.join(run, "credentials"),'''

NEW_INSTANCE = '''        "workspace_storage": places["workspace_storage"],
        "launch_home": places["launch_home"],
        "credential_home": places["credential_home"],'''

OLD_COMPOSE = '''    composed = compose(places["selections"], places["run"], stream=stream)'''

NEW_COMPOSE = '''    composed = compose(places["selections"], places["run"], stream=stream)
    # AND THE OWNED ROOTS THE LIVE PREFLIGHT WILL LOOK FOR. Owner
    # 2026-09-23: the previous packet declared them and created none, so the
    # supervisor refused in `worker_preflight` before it submitted anything
    # and the operator had to `mkdir` by hand.
    provisioned = provision(places)'''

OLD_RECEIPT = '''        "places": places, "tasks_touch": touched,'''

NEW_RECEIPT = '''        "places": places, "tasks_touch": touched,
        "provisioned": provisioned,'''


def swap(body, old, new, what):
    if body.count(old) != 1:
        raise SystemExit(
            f"REFUSED: {what} appears {body.count(old)} times, not once")
    return body.replace(old, new, 1)


def main():
    body = PLACE.read_text(encoding="utf-8")
    if "def provision(" in body:
        raise SystemExit("REFUSED: provisioning is already applied")
    body = swap(body, OLD_LAYOUT, NEW_LAYOUT, "the layout tail")
    body = swap(body, OLD_INSTANCE, NEW_INSTANCE, "the instance members")
    body = swap(body, OLD_COMPOSE, NEW_COMPOSE, "the composition call")
    body = swap(body, OLD_RECEIPT, NEW_RECEIPT, "the receipt")
    PLACE.write_text(body, encoding="utf-8")

    written = PLACE.read_text(encoding="utf-8")
    for present in ("def provision(", "PROVISIONED = (",
                    "check_workspace_storage", '"provisioned": provisioned'):
        if present not in written:
            raise SystemExit(f"REFUSED: {present!r} is not in the file")
    compile(written, str(PLACE), "exec")
    print("the preparation provisions the roots it declares")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
