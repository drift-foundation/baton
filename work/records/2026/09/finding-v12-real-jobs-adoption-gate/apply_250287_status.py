"""Claim-250287: the diagnostic reads `status` with a LIVE composition.

Every earlier receipt printed
`AttributeError: 'NoneType' object has no attribute 'canonical'` for its stage
states, because it called `projection.status(store, None, ...)` after `main`
had already closed everything. `status` asks the composition whether the
canonical store was read at all -- that is the whole point of its `canonical`
member -- so `None` is not a supported operand and the receipt said nothing
about the stages.

The supervisor already hands each tick's callback `operations`, `job` and
`control`. So the supported read is taken DURING the run, from inside the
turn, where the composition is open.
"""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
PLACE = HERE / "diagnostic_main_admissions.py"

OLD = '''        self.answering = lambda: answering_with_frames
        argv, outcome, into = self.entrypoint(total=600, cleanup=60)'''

NEW = '''        # THE SUPPORTED STATUS READ, TAKEN WHILE THE COMPOSITION IS OPEN.
        # Every earlier receipt called `status(store, None)` after `main` had
        # closed everything and printed the AttributeError that produces.
        captured = []

        def answering_and_reading(gate, context):
            try:
                return answering_with_frames(gate, context)
            finally:
                try:
                    held_status = projected(context["job"],
                                            context["operations"],
                                            observed_at=fixtures.NOW)
                except Exception as failure:                 # noqa: BLE001
                    captured.append(f"{type(failure).__name__}: {failure}")
                else:
                    captured.append({
                        "canonical": held_status["canonical"],
                        "jobs": {one["job_id"]: {two["kind"]: two["state"]
                                                 for two in one["stages"]}
                                 for one in held_status["jobs"]}})

        self.answering = lambda: answering_and_reading
        argv, outcome, into = self.entrypoint(total=600, cleanup=60)'''

OLD_STATES = '''        from baton_v12.job_manager import JobStore
        held = JobStore.open(os.path.join(into, "jobs.sqlite3"),
                             authority_uuid=self.config["authority_uuid"],
                             incarnation="diagnostic-read",
                             clock=lambda: fixtures.NOW)
        try:
            states = {
                one["job_id"]: {two["kind"]: two["state"]
                                for two in one["stages"]}
                for one in projected(held, None,
                                     observed_at=fixtures.NOW)["jobs"]}
        except Exception as failure:                         # noqa: BLE001
            states = f"{type(failure).__name__}: {failure}"
        finally:
            held.close()
'''

NEW_STATES = '''        # THE LAST LIVE READ is the stage picture this receipt reports. A read
        # taken after `main` returns has no composition to ask, and an
        # unsupported operand is not a measurement.
        states = captured[-1] if captured else "no tick took a status read"
'''

OLD_PRINT = '''            "stage_states": states,'''
NEW_PRINT = '''            "live_status_reads": len(captured),
            "live_status_first": captured[0] if captured else None,
            "stage_states": states,'''


def swap(body, old, new, what):
    if body.count(old) != 1:
        raise SystemExit(
            f"REFUSED: {what} appears {body.count(old)} times, not once")
    return body.replace(old, new, 1)


def main():
    body = PLACE.read_text(encoding="utf-8")
    body = swap(body, OLD, NEW, "the turn wrapper")
    body = swap(body, OLD_STATES, NEW_STATES, "the post-run status read")
    body = swap(body, OLD_PRINT, NEW_PRINT, "the receipt")
    PLACE.write_text(body, encoding="utf-8")

    written = PLACE.read_text(encoding="utf-8")
    for absent in ("projected(held, None,", "JobStore.open("):
        if absent in written:
            raise SystemExit(f"REFUSED: {absent!r} survives in the file")
    for present in ("answering_and_reading", '"live_status_reads"',
                    'observed_at=fixtures.NOW)'):
        if present not in written:
            raise SystemExit(f"REFUSED: {present!r} is not in the file")
    compile(written, str(PLACE), "exec")
    print("the diagnostic reads status live, and it is verified on disk")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
