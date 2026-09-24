"""Step 7 now has a command, because the supervisor now exists."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

NEW = '''## Step 7 — stop, and prove the runtimes stopped

**A process exit or `SIGTERM` alone is not proof that worker runtimes
stopped.** The bounded run is driven by `two_job_supervisor.supervise`, which
reuses W239528's accepted termination, cleanup-journal and publication
machinery — bound by digest, so a change underneath it is a refusal rather
than a passing run.

```sh
BATON_V12_STAGE_EXECUTION_CONFIG="<run root>/deployment.json" \\
PYTHONPATH="$BOUND:$DOSSIER" "$PY" -B -c '
import sys, two_job_supervisor
from baton_v12.job_manager import JobStore
from baton_v12.worker_manager import ControlStore
# Open this run own stores and composed operations exactly as step 4 does,
# then hand them to the bounded supervisor with this packet own bounds.
two_job_supervisor.supervise(
    job, control, composed,
    job_ids=("job-a", "job-b"),
    bounds={"total_seconds": 600, "cleanup_seconds": 60},
    outcome_path="<run root>/outcome.json",
    deployment_path="<run root>/deployment.json")'
```

What it does, in this order: serves through the four-admission gate; stops at
`total_seconds - cleanup_seconds` (600 − 60 = **540**, so the reserve is INSIDE
the total rather than an extension); **closes admission BEFORE cancelling
anything**; cancels every attempt this run launched; reads the manager own
cleanup journal for each of them; and publishes an outcome at `outcome.json`
**on every path** — the bounded stop, a serving failure, a cap refusal and an
interruption alike. An interruption still raises after the outcome is
retained, carrying it.

`state: settled` means every admitted runtime has positive cleanup and nothing
was refused or uncertain. `state: held` names each reason in `held_because`.
Positive cleanup vocabulary is the accepted one: `complete` or `retained`;
missing, failed or uncertain cleanup is outstanding, not success.
'''


def main():
    place = HERE / "ADOPTION-247941.md"
    body = place.read_text(encoding="utf-8")
    start = body.index("## Step 7 — stop, and prove the runtimes stopped")
    end = body.index("## What is deterministically witnessed")
    body = body[:start] + NEW + "\n" + body[end:]
    body = body.replace(
        '''1. **No two-Job bounded supervisor exists.** Step 7 names accepted
   machinery but no command drives it for four admissions. This is the
   smallest concrete implementation gap left, and it is an implementation gap
   rather than a product defect.''',
        '''1. **The bounded run is deterministic evidence, not a live one.** The
   supervisor is driven over the real composed deployment with an injected
   clock, so the 600-second arithmetic is proved in milliseconds. No container
   was started and no engine was asked to destroy one; what the cleanup
   journal is asked about is what this run actually launched.''')
    place.write_text(body, encoding="utf-8")
    print("step 7 rewritten")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
