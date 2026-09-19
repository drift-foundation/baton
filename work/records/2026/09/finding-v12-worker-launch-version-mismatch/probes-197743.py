"""The reported hang, reproduced and measured. Claim197743, W197661.

NO ENGINE, IMAGE, MODEL, NETWORK OR STORE. It runs `v12/worker/baton_worker.py`
in this process over real pipes and a temporary launch document.

Each case starts `serve` with a stdin pipe NOBODY EVER WRITES TO -- which is
what a container's stdin is when its production channel is the file exchange --
and reports whether the program was still inside `read_frame` when the bound
expired. Against the candidate, every generation that speaks the exchange ends
at once with status 3 and a bounded diagnostic; the preserved one-shot `/1`
still waits, because a manager really does write frames there.

Against the PRE-CORRECTION worker every case blocks for the whole bound with an
empty stderr and no status -- measured by reverting the `serve` branch in a
scratch copy of this file, which is the reversal recorded in EVIDENCE-197743.json.
"""
import io, json, os, sys, tempfile, threading, time

sys.path.insert(0, "/home/sl/src/baton/v12/worker")
import baton_worker


def launch(document):
    home = tempfile.mkdtemp(prefix="w197661-")
    place = os.path.join(home, "launch.json")
    with open(place, "w", encoding="utf-8") as handle:
        json.dump(document, handle)
    os.chmod(place, 0o444)
    return place


def run(document, seconds=3.0):
    """`serve` over a stdin pipe NOBODY EVER WRITES TO -- the container's own."""
    place = launch(document)
    to_worker, held = os.pipe()          # held open, exactly like `docker run`
    read_out, worker_out = os.pipe()
    stdin = io.BufferedReader(io.FileIO(to_worker, "rb"))
    stdout = io.FileIO(worker_out, "wb")
    stderr = io.StringIO()
    answer = {}

    def serve():
        try:
            answer["status"] = baton_worker.serve(stdin, stdout, object(),
                                                  place, stderr=stderr)
        except BaseException as failed:
            answer["error"] = f"{type(failed).__name__}: {failed}"
        finally:
            stdout.close()

    started = time.monotonic()
    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    thread.join(seconds)
    blocked = thread.is_alive()
    elapsed = time.monotonic() - started
    wrote = b""
    if not blocked:
        os.set_blocking(read_out, False)
        try:
            wrote = os.read(read_out, 4096)
        except BlockingIOError:
            wrote = b""
    os.close(held)
    return {"blocked_for_the_whole_bound": blocked,
            "seconds": round(elapsed, 4),
            "status": answer.get("status"), "error": answer.get("error"),
            "stdout_bytes": len(wrote),
            "stderr": stderr.getvalue().strip()}


SESSION = "session-w197661"
BASE = {"session": SESSION, "contract": "do the thing", "role": "coder"}
out = {"engine": "none; in-process worker over real pipes"}

# THE REPORTED DOCUMENT: `/3` with job_execution and transport, against a
# worker that validates it and refuses.
out["reported_three"] = run({
    "schema": "baton.worker-launch/3", **BASE,
    "transport": "baton.worker-exchange/1",
    "job_execution": {"job_id": "codex-adapter-first"}})
# A FUTURE GENERATION this worker does not read at all.
out["future_five"] = run({"schema": "baton.worker-launch/5", **BASE})
# AN INVALID `/2`.
out["invalid_two"] = run({"schema": "baton.worker-launch/2", **BASE})
# A DOCUMENT THAT DECLARES NO READABLE VERSION.
out["schema_not_text"] = run({"schema": 3, **BASE})
# THE PRESERVED ONE-SHOT: an invalid `/1` still waits for the frame a manager
# really does write there, so this one SHOULD still block on an empty stdin.
out["invalid_one_shot"] = run({"schema": "baton.worker-launch/1", **BASE,
                               "transport": "baton.worker-exchange/1"},
                              seconds=1.0)
print(json.dumps(out, indent=2))
