"""W167896 selected cost check: 20 Jobs, 1s polling, 60s idle.

Measures THIS PROCESS AND ITS CHILDREN, because a viewer that forked its
polling would otherwise measure zero.
"""
import json, os, platform, resource, sys, tempfile, time
sys.path.insert(0, "/home/sl/src/baton/v12/python")
sys.path.insert(0, "/home/sl/src/baton/v12/python/tests/job_manager")
from fixtures import NOW, UUID, job, stage, WORK_A
from baton_v12.job_manager import Unobserved, submit
from baton_v12.job_manager.projection import status
from baton_v12.job_manager.store import JobStore
from tools.job_viewer import JobViewer, render_list

JOBS = 20
SECONDS = 60.0
INTERVAL = 1.0

root = tempfile.mkdtemp(prefix="v12-viewer-cost-")
store = JobStore.open(os.path.join(root, "jobs.sqlite"), authority_uuid=UUID,
                      incarnation="v", clock=lambda: NOW)
submit(store, {"schema": "baton.v12.job-submission/1", "submission_id": "sub-cost",
               "jobs": [job("job-%02d" % n, stages=[stage("implementation", WORK_A)])
                        for n in range(JOBS)]})
document = status(store, Unobserved(), observed_at=NOW)
place = os.path.join(root, "status.json")
with open(place, "w", encoding="utf-8") as handle:
    json.dump(document, handle)
size = os.path.getsize(place)
assert len(document["jobs"]) == JOBS, len(document["jobs"])

def source():
    with open(place, "rb") as handle:
        return handle.read()

devnull = open(os.devnull, "w")
viewer = JobViewer(source, interval=INTERVAL)

def rusage():
    me = resource.getrusage(resource.RUSAGE_SELF)
    kids = resource.getrusage(resource.RUSAGE_CHILDREN)
    return (me.ru_utime + me.ru_stime + kids.ru_utime + kids.ru_stime)

before, started = rusage(), time.monotonic()
deadline = started + SECONDS
while time.monotonic() < deadline:
    viewer.refresh()
    for line in render_list(viewer.snapshot, now=time.monotonic()):
        print(line, file=devnull)
    left = deadline - time.monotonic()
    if left > 0:
        time.sleep(min(INTERVAL, left))
cpu, wall = rusage() - before, time.monotonic() - started
target = 0.01 * wall
print(json.dumps({
    "host": platform.node(), "platform": platform.platform(),
    "python": platform.python_version(),
    "jobs": JOBS, "input_bytes": size,
    "interval_seconds": INTERVAL,
    "wall_seconds": round(wall, 3),
    "cpu_seconds_including_children": round(cpu, 3),
    "target_cpu_seconds": round(target, 3),
    "percent_of_one_core": round(100.0 * cpu / wall, 4),
    "refreshes": viewer.reads, "failures": viewer.failures,
    "meets_target": cpu <= target}, indent=1))
