#!/usr/bin/python3
"""SCRIPTED DOUBLES for the qualification script's two external programs: the engine CLI and the
instance's installed command. No engine, no container, no manager. Every call is logged, so a run
can assert exactly which containers the script acted on. World: $FAKE_WORLD/world.json."""
import json, os, sys, time
def _world():
    # Found from where this double was INVOKED (a symlink inside the run), because the script runs the
    # installed command with an empty environment and nothing may be handed to it that way.
    at = os.path.dirname(os.path.abspath(sys.argv[0]))
    while not os.path.isdir(at + "/world"): at = os.path.dirname(at)
    return at + "/world"
W = _world(); world = json.load(open(W + "/world.json"))
def log(kind, argv):
    with open(W + "/calls.log", "a") as out: out.write(json.dumps({"t": round(clock(), 1), "kind": kind, "argv": argv}) + "\n")
def clock():
    try: return time.time() - os.stat(W + "/started").st_mtime
    except OSError: return -1.0
def flag(name): return os.path.exists(W + "/" + name)
PUB, REV = world["publisher"], world["reviewer"]
def containers():
    """id -> (attempt label, image, mounts) for what exists NOW."""
    t = clock(); found = dict(world.get("foreign", {}))
    if world["scenario"] == "recovery":
        if 2 <= t < 6: found["c-pub"] = [PUB, world["images"]["publication"], [world["storage"] + "/" + PUB + "/out"]]
        if 6 <= t < 12: found["c-rev"] = [REV, world["images"]["provider"], [world["storage"] + "/" + REV + "/in"]]
    else:
        if t >= 2 and not flag("unpaused"): found["c-pub"] = [PUB, world["images"]["publication"], [world["storage"] + "/" + PUB + "/out"]]
    return found
def inspect(cid):
    label, image, mounts = containers()[cid]
    return {"Id": cid, "Image": image, "State": {"Paused": flag("paused-" + cid) and not flag("unpaused")},
            "Config": {"Labels": {"baton.v12.runtime_attempt_id": label}, "User": "65532:65532", "Env": ["PATH=/usr/bin"]},
            "HostConfig": {"NetworkMode": "none"},
            "Mounts": [{"Type": "bind", "Source": mounts[0], "Destination": "/output", "RW": True},
                       {"Type": "bind", "Source": os.path.dirname(mounts[0]) + "/source", "Destination": "/input/source", "RW": False}]}
def engine(argv):
    log("engine", argv)
    verb = argv[0]
    # AN ENGINE THAT DOES NOT ANSWER: every observation and release fails, which is not "the container is gone".
    if flag("engine-down") and verb in ("ps", "inspect", "unpause", "image"):
        print("Cannot connect to the daemon", file=sys.stderr); sys.exit(125)
    if verb == "ps":
        want = [a.split("=", 2)[2] for a in argv if a.startswith("label=baton.v12.runtime_attempt_id=")]
        ids = [a.split("=", 1)[1] for a in argv if a.startswith("id=")]
        for cid, (label, _i, _m) in containers().items():
            if ids and cid != ids[0]: continue
            if not want or label == want[0]: print(cid if "--format" not in argv else cid + " Up")
    elif verb == "inspect":
        cid = argv[-1]
        if cid not in containers(): sys.exit(1)
        if "--format" in argv: print("true" if inspect(cid)["State"]["Paused"] else "false")
        else: print(json.dumps([inspect(cid)]))
    elif verb == "pause":
        time.sleep(float(world.get("pause_seconds", 0)))       # a request that is slow to take effect
        open(W + "/paused-" + argv[1], "w").close()
        if world.get("engine") == "down-after-pause": open(W + "/engine-down", "w").close()
        # A LOST REPLY: the container IS paused and the caller is told the call failed.
        if world.get("pause") == "lost-reply": sys.exit(1)
    elif verb == "unpause":
        how = world.get("unpause")
        if how == "fails": sys.exit(1)                          # no effect, and it says so
        if how == "fails-then-down": open(W + "/engine-down", "w").close(); sys.exit(1)
        open(W + "/unpaused", "w").close()
        if how == "lost-reply": sys.exit(1)                     # the effect happened; the caller is told it failed
    elif verb == "exec":
        if world.get("exec") == "fails": sys.exit(126)
        print(json.dumps({"input": {"regular": True, "handoff_digest": "sha256:h", "reviewer_verification": {"command_seconds": 900, "required": True}},
                          "write": world.get("exec", "refused:EROFS"), "supervisor": {"executable": True, "writable": False}}, sort_keys=True))
    elif verb == "events":
        while not flag("unpaused"): time.sleep(0.2)
        print(json.dumps({"Action": "die", "Actor": {"Attributes": {"exitCode": "137"}}}), flush=True)
    elif verb == "image":
        tag = argv[-1]; now = world.get("tags", {}).get(tag)
        if argv[1] == "inspect":
            if now is None: sys.exit(1)
            print(now)
        elif argv[1] == "ls":
            if now is not None: print(now)
        elif argv[1] == "rm": open(W + "/removed-" + tag.replace("/", "_"), "w").close()
def installed(argv):
    log("installed", argv)
    if argv[0] == "identity": print(json.dumps({"frozen": True, "command": "baton-v12-stack"})); return
    verb = argv[1]
    if verb == "settlement-preview":
        stopped = clock() >= 3 and world.get("producers") != "never-stop"
        print(json.dumps({"request": {"operation_id": argv[argv.index("--operation-id") + 1]}, "eligibility": {"eligibility": "eligible" if stopped else "held"}})); return
    if verb == "settle-stopped":
        if flag("started") and not flag("stops"): sys.exit("refused: a serving manager holds this instance")
        print(json.dumps({"settlement": {"state": "settled"}})); return
    if verb == "settlement-remove":
        print(json.dumps({"removed": world.get("remove") != "fails", "replayed": False})); sys.exit(0 if world.get("remove") != "fails" else 1)
    if verb == "publication-inspect":
        print(json.dumps({"eligible": True, "holds": [], "selector": {"attempt_id": "orig"}, "selection_digest": "sha256:s",
            "producer": {"base": "b", "head": "h", "context_digest": "sha256:c", "argv": ["python3", "harness.py"]},
            "output": {"tree_digest": "sha256:t", "total_bytes": 1052672, "exceeded": True, "fits_corrective": True}, "declaration": {"digest": "sha256:d"}, "profile": {"profile": "p", "digest": "sha256:p"}}))
    elif verb == "publication-decide": print(json.dumps({"admitted": True}))
    elif verb == "publication-status":
        t = clock(); s = {"recovery": {"handed_off": False, "outcome": None, "settled": False, "published": False, "review": None,
                                         "publication_deadline": {"reached": False}}, "publication_attempt": None, "review": {"attempt_id": None, "state": "not-started"}, "owner_item": None}
        if t >= 2: s["publication_attempt"] = {"attempt_id": PUB, "recorded": {"execution_runtime": "running", "cleanup": "pending"}}
        if world["scenario"] == "recovery":
            if t >= 6:
                s["recovery"].update(handed_off=True, outcome="published"); s["publication_attempt"]["recorded"]["execution_runtime"] = "destroyed"
                s["review"] = {"attempt_id": REV, "state": "in-progress", "reviewer": None, "verdict": None}
            if t >= 12: s["review"].update(state="completed", reviewer="baton.reviewer", verdict={"disposition": "accepted", "candidate_is_the_approved_original": True})
        else:
            if t >= 6: s["recovery"]["publication_deadline"]["reached"] = True
            if flag("unpaused"):
                s["recovery"].update(outcome="expired", settled=True, published=False, review="blocked")
                s["publication_attempt"]["recorded"]["execution_runtime"] = "destroyed"
                s["owner_item"] = {"outcome": "expired", "automatic_retry": False}
        print(json.dumps(s))
me = os.path.basename(sys.argv[0])
(engine if me == "docker" else installed)(sys.argv[1:])
