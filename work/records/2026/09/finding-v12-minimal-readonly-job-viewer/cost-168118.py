"""W167896 cost check, corrected under review claim168071.

SCOPE, STATED RATHER THAN IMPLIED. This measures the VIEWER: the selected
refresh adapter (`_source_from`, which re-reads the status file each tick),
the parse, the staleness arithmetic and the render. It does NOT include
periodic canonical status PRODUCTION -- writing that document is
`job_manager ... status`, a separate command with its own cost, and calling
this a whole-pipeline figure would be a claim this harness cannot support.

CHILDREN ARE INCLUDED because the viewer is entitled to have none and that
should be measured rather than assumed.
"""
import json, os, platform, resource, sys, tempfile, time
sys.path.insert(0, "/home/sl/src/baton/v12/python")
sys.path.insert(0, "/home/sl/src/baton/v12/python/tests/job_manager")
from fixtures import NOW, UUID, job, stage, WORK_A
from baton_v12.job_manager import Unobserved, submit
from baton_v12.job_manager.projection import status
from baton_v12.job_manager.store import JobStore
from tools.job_viewer import JobViewer, _source_from, render_list

JOBS, SECONDS, INTERVAL = 20, 60.0, 1.0
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
assert len(document["jobs"]) == JOBS

devnull = open(os.devnull, "w")
# THE SELECTED ADAPTER ITSELF, not a closure written for the benchmark.
viewer = JobViewer(_source_from(place), interval=INTERVAL)

def rusage():
    me = resource.getrusage(resource.RUSAGE_SELF)
    kids = resource.getrusage(resource.RUSAGE_CHILDREN)
    return me.ru_utime + me.ru_stime + kids.ru_utime + kids.ru_stime

reads = []
before, started = rusage(), time.monotonic()
deadline = started + SECONDS
while time.monotonic() < deadline:
    at = time.monotonic()
    viewer.refresh()
    reads.append(time.monotonic() - at)
    for line in render_list(viewer.snapshot, now=time.monotonic(),
                            wall_now=time.time()):
        print(line, file=devnull)
    left = deadline - time.monotonic()
    if left > 0:
        time.sleep(min(INTERVAL, left))
cpu, wall = rusage() - before, time.monotonic() - started
kids = resource.getrusage(resource.RUSAGE_CHILDREN)
print(json.dumps({
    "scope": ("viewer refresh adapter + parse + staleness + render, "
              "children included; EXCLUDES canonical status production"),
    "host": platform.node(), "platform": platform.platform(),
    "python": platform.python_version(),
    "jobs": JOBS, "input_bytes": size, "interval_seconds": INTERVAL,
    "wall_seconds": round(wall, 3),
    "cpu_seconds_including_children": round(cpu, 3),
    "child_cpu_seconds": round(kids.ru_utime + kids.ru_stime, 3),
    "target_cpu_seconds": round(0.01 * wall, 3),
    "percent_of_one_core": round(100.0 * cpu / wall, 4),
    "refreshes": viewer.reads, "failures": viewer.failures,
    "source_read_seconds_max": round(max(reads), 4),
    "source_read_seconds_total": round(sum(reads), 4),
    "meets_target": cpu <= 0.01 * wall}, indent=1))
