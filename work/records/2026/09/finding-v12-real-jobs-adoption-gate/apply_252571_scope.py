"""Claim-252571: 180 seconds is PER INVOCATION, and the packet said per attempt.

Review 2026-09-24T01:14:08Z accepted the submitted ceilings and narrowed what
they mean: "This is a per-invocation ceiling, not a 180-second total attempt
lifetime. execution_limits.py explicitly distinguishes those concepts. Correct
the packet's per-attempt language or identify and prove the separate mechanism
enforcing that selected total; do not describe these settings as that proof."

There is no such separate mechanism in this packet, so the language is what
changes. `execution_limits.BOUNDARIES` maps `provider_turn_seconds` to one
provider invocation and `verification_command_seconds` to one verification
command; nothing there bounds an attempt's whole life. What this packet DOES
bound in total is the RUN, at 600 seconds including the 60-second cleanup
reserve, and that is `supervise`'s own arithmetic -- proved on a controlled
clock and asserted by its own cases.
"""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

SWAPS = {
    "two_jobs.py": [
        ('    "per_attempt_seconds": 180,',
         '    # PER INVOCATION, not per attempt. Review 2026-09-24T01:14:08Z:\n'
         '    # `execution_limits` bounds ONE provider invocation and ONE\n'
         '    # verification command; nothing in it bounds an attempt\'s whole\n'
         '    # life, and this packet has no other mechanism that does. The\n'
         '    # name said otherwise and the table repeated it.\n'
         '    "per_invocation_seconds": 180,'),
        ('    return {"provider_turn_seconds": LIMITS["per_attempt_seconds"],\n'
         '            "verification_command_seconds": '
         'LIMITS["per_attempt_seconds"]}',
         '    return {"provider_turn_seconds": LIMITS["per_invocation_seconds"],\n'
         '            "verification_command_seconds":\n'
         '                LIMITS["per_invocation_seconds"]}'),
    ],
    "ADOPTION-247941.md": [
        ('| Limits | `two_jobs.LIMITS`: 2 Jobs, 2+2 admissions, 0 correction '
         'rounds, no retry, no session restoration, 180s per attempt, 600s '
         'total including a 60s cleanup reserve |',
         '| Limits | `two_jobs.LIMITS`: 2 Jobs, 2+2 admissions, 0 correction '
         'rounds, no retry, no session restoration, **180s per provider '
         'invocation and per verification command**, 600s total for the RUN '
         'including a 60s cleanup reserve |'),
        ('**What each Job owns alone** is `two_jobs.PER_JOB`:',
         '**WHAT 180 SECONDS BOUNDS, exactly.** It is `execution_limits`:\n'
         'one provider invocation (`provider_turn_seconds`) and one\n'
         'verification command (`verification_command_seconds`). **It is not a\n'
         'total attempt lifetime**, and this packet has no mechanism that\n'
         'bounds one — review 2026-09-24T01:14:08Z corrected the earlier\n'
         '"180s per attempt" wording, which claimed a guarantee these settings\n'
         'do not give. What IS bounded in total is the RUN: 600 seconds\n'
         'including the 60-second cleanup reserve, enforced by\n'
         '`two_job_supervisor.supervise` and asserted on a controlled clock.\n'
         '\n'
         '**What each Job owns alone** is `two_jobs.PER_JOB`:'),
    ],
}

APPENDED = """
## Correction, claim 252571 — item 4 was not unknown, it was recorded

Review 2026-09-24T01:14:08Z: "FINDING's preceding owner startup entry
identifies it precisely... Append a correction to the diagnosis rather than
presenting the owner observation as an unknown directory."

That is right and the mistake is mine. Item 4 above says I had not identified
which directory was missing. The owner's entry of 2026-09-23 — one entry above
the one I was working from — identifies it exactly:

> the live supervisor refused in `worker_preflight` because its configured
> `run/workspaces` directory did not exist. Preparation declares that path but
> does not provision it.

`operations_from` raised **before** `submit` and before `supervise`, so that
invocation admitted nothing and started no container; an operator stopgap
created the one directory by hand. The attempt directories I looked at were
made by the LATER invocation, after that stopgap — so what I read as evidence
against a missing directory was evidence from after it had been created. I was
reading the wrong invocation's leftovers.

**Corrected in the packet, not just in the record.**
`prepare_two_jobs.PROVISIONED` names the four owned roots the composed
deployment declares — the workspace store, the launch home, the credential home
and the deployment state root — and `provision()` creates them 0o700 after the
composer has made `run/`, then reads the workspace store back through
`workspaces.check_workspace_storage`, which is the same judgment
`worker_preflight` makes. A case drives that check over the composed path
before and after preparation: absent is refused by name, provisioned is held.

**Item 4 above is therefore superseded.** The preserved failed instance was not
touched to establish this and is not repaired by it; the correction is on the
NEW-instance path.

## Correction, claim 252571 — what the 180 seconds actually bounds

Item 1 above describes the corrected ceiling without saying what it bounds.
Review 2026-09-24T01:14:08Z: it is per invocation — one provider turn and one
verification command — and **not** a total attempt lifetime. This packet has no
mechanism that bounds an attempt's whole life, and the earlier "180s per
attempt" wording claimed a guarantee these settings do not give. The total this
packet does bound is the RUN, at 600 seconds including the 60-second cleanup
reserve, which is `supervise`'s arithmetic.
"""


def main():
    for name, swaps in sorted(SWAPS.items()):
        place = HERE / name
        body = place.read_text(encoding="utf-8")
        for old, new in swaps:
            if body.count(old) != 1:
                raise SystemExit(
                    f"REFUSED: a block appears {body.count(old)} times in "
                    f"{name}, not once:\n{old[:90]}")
            body = body.replace(old, new, 1)
        place.write_text(body, encoding="utf-8")

    for name in ("two_jobs.py",):
        written = (HERE / name).read_text(encoding="utf-8")
        if "per_attempt_seconds" in written:
            raise SystemExit(f"REFUSED: per_attempt_seconds survives in {name}")
        compile(written, str(HERE / name), "exec")

    page = (HERE / "ADOPTION-247941.md").read_text(encoding="utf-8")
    # THE PHRASE SURVIVES ONLY INSIDE THE SENTENCE THAT CORRECTS IT, in
    # quotes. A check that cannot tell a claim from a correction of one
    # refuses a corrected page, which is the shape of an earlier mistake in
    # this dossier.
    if page.count("180s per attempt") != 1 \
            or '"180s per attempt" wording' not in page:
        raise SystemExit("REFUSED: the per-attempt wording survives as a claim")

    diagnosis = HERE / "DIAGNOSIS-252472.md"
    body = diagnosis.read_text(encoding="utf-8")
    if "claim 252571" not in body:
        diagnosis.write_text(body.rstrip("\n") + "\n" + APPENDED,
                             encoding="utf-8")
    print("the scope of 180 seconds is stated, and the diagnosis is corrected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
