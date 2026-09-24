"""Claim-249364 dossier entries for W247941."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 249364

ASSESSMENT-249338.md's G1 and G2 are prepared. **Recommendation: NOT READY as a
resolved current deployment; READY IN ARRANGEMENT.**

## Done under claim 249364

  * G1: `two_jobs.py` composes ONE manager, ONE pool, one
    `baton.v12.stage-execution-deployment/2` document with four stage workers
    and two `job_bindings`, held by the product's own `held_configuration`.
    `SELECTIONS-247941.json` pins what the assessment selected and names every
    remaining owner choice. `ADOPTION-247941.md` is the report and the literal
    step 1-7 recipe.
  * G2: `CONTINUITY-247941.md` maps each accepted concurrency seam onto this
    arrangement, and `test_two_jobs.py` (16 checks) drives THIS document
    through W130224's accepted two-Job fixture: both implementations `waiting`
    at one observed instant, own allocated producers, own lines, own mounted
    workspaces, Job B's own reviewer, and five arrangement refusals -- with a
    guard case proving the served document is this arrangement's.
  * `verify_247941.py --pins` independently re-verifies the 106-file snapshot,
    `stage_execution.py` at `6a212c3a...` and the runtime executable at
    `04aa459a...`. All three agree.

## The one implementation gap left, named rather than papered over

**No two-Job bounded supervisor exists.** Both accepted supervisors cap ONE
workload -- W239528 admits one implementation, W239533 one review -- so no
command yet closes admission, cancels four admitted attempts and proves
positive cleanup for them. ADOPTION-247941.md step 7 says this instead of
presenting a single-workload runner as a parallel one.

## Next

1. Independent review of this preparation.
2. The two-Job bounded supervisor and its stop/cleanup accounting, if the
   reviewer agrees that is the remaining gate.
3. Owner resolves the selections; any live two-Job question is a separately
   selected runnable packet.

## Ownership

Reviewer-owned and immutable: ASSESSMENT-249338.md,
ASSESSMENT-EVIDENCE-249338.json. baton.claude owns, from claim 249364:
two_jobs.py, test_two_jobs.py, ADOPTION-247941.md, CONTINUITY-247941.md,
SELECTIONS-247941.json, verify_247941.py, verification-1.json/.log,
PROGRESS.md, records_249364.py, and this PLAN.md. No product file, no v11
authority, no historical evidence and no consumed root was touched.
"""

PROGRESS = """# Implementer progress — W247941

## 2026-09-23 — baton.claude, claim 249364

PROGRESS.md was absent on pickup, as the reviewer recorded; this is its first
entry and it invents no earlier history.

### G1 — the arrangement is chosen, and it is not new

One manager, one pool, one `baton.v12.stage-execution-deployment/2` document
with four stage workers and two `job_bindings`. That is W119405's supported
multi-Job composition, and `two_jobs.py` resolves its operands and holds the
result against `stage_execution.held_configuration` rather than a local
imitation of it.

NOT two isolated managers, and the packet says why: two managers would prove
that two single-Job deployments still work -- which W239528 and W239533 already
established one at a time -- and would say nothing about shared capacity,
per-Job allocation or cross-Job isolation inside one pool.

### G2 — the witness, and two things it corrected in my own arrangement

`test_two_jobs.py` subclasses W130224's independently accepted two-Job fixture
and substitutes THIS arrangement's document. 16 checks, 0 failures, measured
1.6781809749954846s.

Twice the product told me my arrangement was wrong, and both corrections are
worth keeping:

**A `/2` document still carries the instance-level Job members.** I removed
them on the reading that "two places for one fact is how they drift" -- but
that rule is `_held_bindings` refusing `job_bindings` in a `/1` document, not
the `/2` document dropping members `_MEMBERS` requires. Every document composed
that way was refused by `held_configuration`. What makes the per-Job facts
authoritative is that ALLOCATION reads `job_bindings`.

**Two Jobs may share a source and a base.** My first isolation rule demanded a
distinct `nominated_source`, `declared_base`, `workspace_storage`,
`launch_home` and `credential_home` per Job. The storage roots are INSTANCE
members with per-attempt directories beneath, and two Jobs are often TWO
DEVELOPMENT LINES OF ONE TARGET -- an Authority holds one canonical revision.
So the accepted traversal could not compose under my rule, and the profile said
so plainly: "not our ref". Refusing the supported shape is not a stricter rule,
it is a wrong one. `PER_JOB` is now the five facts that actually make two Jobs
two, and a case asserts a shared source is NOT refused.

What isolation means is asserted on a RUN instead: distinct lines, distinct
allocated producers, distinct mounted workspaces, distinct attempts, each Job
its own reviewer. A guard case asserts the document that actually served is
this arrangement's, by worker order -- without it these would be W130224's
accepted evidence re-presented under this Work's name.

### What I did not do

No live run, no container, image, engine, network or credential, no deployed
store, no deployment change, no consumed-root reuse, no product edit, no broad
suite, no repository history mutation. The old roots are untouched.

### Verification spending

16 focused deterministic checks, 0 failures, measured **1.6781809749954846s**,
receipt `verification-1.json` with `verification-1.log`. All 16 are new; this
dossier had no implementer receipts before. The pin check is separate and its
elapsed time was not measured.

Historical spending from other Works is theirs and is preserved where it lives.

State: returned for independent review.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    if not progress.exists():
        progress.write_text(PROGRESS, encoding="utf-8")
    elif "claim 249364" not in progress.read_text(encoding="utf-8"):
        progress.write_text(
            progress.read_text(encoding="utf-8").rstrip("\n") + "\n\n"
            + PROGRESS.split("\n", 2)[2], encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
