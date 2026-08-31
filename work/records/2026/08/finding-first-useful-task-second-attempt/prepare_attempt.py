"""Prepare the fresh deployment state one supervised dogfood attempt needs.

`tools/dogfood_operator.py` documents its command as reusable for another
bounded task, and it is -- but it OPENS an authority and expects a configured
control store, and nothing in the record said where those come from. Every
earlier attempt in this record reconstructed that step by hand from the test
fixtures. This is that step, written down once.

    cd v12/python
    PYTHONPATH=src python3 \
      ../../work/records/2026/08/finding-first-useful-task-second-attempt/prepare_attempt.py \
      /tmp/w51487/run4/grants.json

It performs the deployment's own acts and nothing else: create the authority
at the grants' fresh `authority_uuid`, create the Work its `work_ref` names on
`baton.impl` with the granted assignment contract, install the `baton.impl`
and review-route handlers, then open the control store at the granted
incarnation, certify the granted runtime profile, configure the deployment's
workspace group and workspace storage, and close.

IT MINTS NO IDENTITY OF ITS OWN. Every value it writes is read out of the
grants file the operator already decided, so this cannot become a second place
where a grant is made. It refuses rather than overwrites if the authority
store already exists: a fresh attempt uses fresh identities, and silently
adopting a previous attempt's authority is exactly the reuse the record
forbids.
"""

import datetime
import json
import os
import pathlib
import sys

sys.path.insert(0, "src")

from baton_v12.authority import Authority  # noqa: E402
from baton_v12.worker_manager import (ControlStore, certify_profile,  # noqa: E402
                                      configure_workspace_group,
                                      configured_workspace_group)
from baton_v12.worker_manager.workspaces import (  # noqa: E402
    configure_workspace_storage)


def _now():
    moment = datetime.datetime.now(datetime.timezone.utc)
    return moment.strftime("%Y-%m-%dT%H:%M:%S.") + f"{moment.microsecond // 1000:03d}Z"


def _group():
    """The deployment's configured workspace gid.

    `BATON_V12_WORKSPACE_GROUP` is the operand a real deployment passes. The
    fallback to this process's own group is NAMED rather than silent, because
    a run that meant to prove a dedicated group and quietly proved the login
    group would be the substitution W33936 exists to close.
    """
    named = os.environ.get("BATON_V12_WORKSPACE_GROUP")
    if named is None:
        return os.getgid(), "this process's own group (no dedicated group configured)"
    if not named.lstrip("-").isdigit():
        raise SystemExit(f"BATON_V12_WORKSPACE_GROUP is {named!r}; the "
                         f"deployment's configured workspace group is a gid")
    return int(named), "BATON_V12_WORKSPACE_GROUP"


def main(argv):
    given = json.loads(pathlib.Path(argv[0]).read_text(encoding="utf-8"))
    place = given["authority_store"]
    if os.path.exists(place):
        raise SystemExit(f"there is already an authority store at {place}; a "
                         f"fresh attempt uses fresh identities")
    work = given["work_ref"]
    authority = Authority.create(place,
                                 authority_uuid=work["authority_uuid"],
                                 clock=_now)
    try:
        authority.create_work(work["work_id"], "baton.impl",
                              contract=given["assignment_contract"],
                              operation_id=f"create-{given['attempt_id']}")
        authority.add_route_handler("baton.impl", given["participant"])
        authority.add_route_handler(given["review_route"], given["participant"])
    finally:
        authority.dispose()

    for root in ("storage", "launch_home", "credential_home"):
        os.makedirs(given[root], exist_ok=True)

    store = ControlStore.open(given["control_store"],
                              incarnation=given["incarnation"], clock=_now)
    try:
        certify_profile(store, "runtime", "dogfood",
                        given["runtime_profile_digest"])
        gid, source = _group()
        configure_workspace_group(store, gid)
        configure_workspace_storage(store, given["storage"])
        held = configured_workspace_group(store)
    finally:
        store.close()

    print(f"authority   {place}  uuid {work['authority_uuid']}")
    print(f"work        {work['work_id']} on baton.impl, contract "
          f"{given['assignment_contract']}")
    print(f"routes      baton.impl, {given['review_route']} -> "
          f"{given['participant']}")
    print(f"control     {given['control_store']}  incarnation "
          f"{given['incarnation']}")
    print(f"profile     runtime/dogfood = {given['runtime_profile_digest']}")
    print(f"group       gid {held.gid} from {source}")
    print(f"storage     {given['storage']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
