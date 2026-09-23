"""Claim-244292 dossier entries: R1, the preparation step."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PROGRESS = """
## 2026-09-23 -- baton.claude, claim 244292, the preparation step

Review 2026-09-23T03:30:58Z R1; owner reroute 244290 selects only it. Done. No
image rebuild, no live provider, no deployed provisioning, no recovery, no
reviewer stage, no resume, no closure. No file under `v12/` was edited.

**R1, and it was a real trap.** `OPERATOR-SUCCESSOR-244216.md` told an operator
to follow `OPERATOR-SUCCESSOR-243284.md`'s step-5a block "with `$SEL` pointing
at this packet's selections" -- but that block hardcodes the 243284 selections
path and asserts `"single-implementation-243284" in store`, so pointing it at
the 244216 file raises `AssertionError` before `Authority.open` is reached. A
preparation step that cannot be pointed at the packet it is documented beside
is not a preparation step.

`prepare_instance.py` is that step, parameterized. It takes `--selections` and
`--base`, and its freshness check is DERIVED from the selections' own `run_id`
rather than naming a run -- a helper carrying a literal would be the same
defect one release later. It refuses before opening anything if a store does
not name this run, if one names a consumed instance, if any `<OWNER>` member is
unresolved, or if `--base` is not a full object name. Then it performs the acts
the old block performed. The document references it instead of reprinting a
block that only ever worked for one packet.

**Tested through supported interfaces, not prose.** `test_preparation.py`
drives `prepare_instance.prepare` against a DISPOSABLE Authority made with
`Authority.create`, then reads the results back through the Authority's own
public readers: `project_work` for the Work and scope, `capabilities_of` for
each of the four grants, `policy("canonical_target")` for the base. The same
delivered selections then go through `baseline_bindings.compose`, so
preparation and composition are exercised over ONE document. The freshness
check is also asked about the PREDECESSOR's selections and answers
`single-implementation-243284` -- which is the point: it is not that 243284 was
wrong, it is that a literal cannot answer for two packets.

**A claim of mine was wrong and the measurement corrected it.** The helper's
first draft said in its own docstring that a second run would refuse, and the
operator page repeated it. Driving it twice showed otherwise: `create_work` is
journalled under an operation identity derived from the run, so a repeat
REPLAYS and answers the same Work and scope. Both documents now say that, and
`test_a_repeat_replays_the_same_act` holds them to it. I have left the
correction visible in the docstring rather than quietly rewriting it.

**Outcome diagnoses qualified.** The document's `no-progress` entry asserted a
mechanism -- "the CLI did something a mask cannot govern" -- that no run has
shown. Each entry now names a STATE and what to read, in order, and says
plainly that an explicit `chmod` and a reset umask are both consistent with
non-private directories and the modes alone do not separate them. The
`overall-bound-exceeded`/traceback entry no longer calls itself a regression in
advance.

**The reviewer's inspection limit is disclosed on the page.** Its no-network
read-only container was denied Docker API access before it could read content,
and it took no stronger retry or fallback. So the inside-image byte and version
claims are AUTHOR evidence, independently corroborated at the image-metadata
level but not independently re-read from inside the image, and the document
says so rather than leaving the reader to assume otherwise.

Verification: 166 focused deterministic checks, measured 27.029541312003857s,
receipt `verification-10.json` with `verification-10.log`; 15 are new.

Cumulative measured for W239528: 758.235461713s (through claim 244216) +
27.029541312 + 0.073 + 4.906 (claim 244292) = **790.244003025s**.

State: awaiting independent review.
"""

PLAN_DONE = """
## Done under this claim

1. `prepare_instance.py`: the step 5a acts, parameterized by `--selections`
   and `--base`, with the freshness marker DERIVED from the selections' own
   `run_id` and refusals for a foreign store, a consumed instance, an
   unresolved owner operand and a malformed base.
2. `OPERATOR-SUCCESSOR-244216.md` references it, stops telling an operator to
   reuse a block that asserts another packet's run name, qualifies every
   outcome entry as a state plus what to read rather than a cause, and
   discloses the reviewer's inside-image inspection limit.
3. `test_preparation.py`: fifteen checks driving the helper against a
   disposable Authority through its public readers, composing the same
   delivered selections, and holding the document to what it says.
4. A claim corrected by measurement: the step REPLAYS on a repeat rather than
   refusing.

Verification: 166 dossier checks, 27.029541312003857s, receipt
`verification-10.json`.
"""

OWNERSHIP = """
## Claim 244292 -- the parameterized preparation step

Added: `prepare_instance.py`, `test_preparation.py`, `records_244292.py`,
`verification-10.json/.log`.

Edited: `OPERATOR-SUCCESSOR-244216.md`, `verify.py`, `PLAN.md`, `PROGRESS.md`,
this file.

**No file under `v12/` was edited, and no image was rebuilt.** Both images,
both manager-source snapshots and every consumed instance are untouched.
`OPERATOR-SUCCESSOR-243284.md` is kept as it stands: its block is historical
and the successor page now says why not to reuse it.
"""


def main():
    progress = HERE / "PROGRESS.md"
    if "claim 244292" not in progress.read_text(encoding="utf-8"):
        progress.write_text(
            progress.read_text(encoding="utf-8").rstrip("\n") + "\n" + PROGRESS,
            encoding="utf-8")
    plan = HERE / "PLAN.md"
    body = plan.read_text(encoding="utf-8")
    old = "## Not in scope\n"
    if "prepare_instance.py`: the step 5a acts" not in body:
        plan.write_text(body.replace(old, PLAN_DONE + "\n" + old, 1),
                        encoding="utf-8")
    owner = HERE / "OWNERSHIP-239528.md"
    if "Claim 244292" not in owner.read_text(encoding="utf-8"):
        owner.write_text(
            owner.read_text(encoding="utf-8").rstrip("\n") + "\n" + OWNERSHIP,
            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
