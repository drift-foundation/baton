"""The SELECTED useful tasks as a builder, beside the greeting fixture rather than replacing it.

W247941 review 2026-09-29T12-34-10Z named this design: keep the greeting fixture builder, ADD an
explicitly selected useful-doc builder and its input set, let the owner's setup select it, and cover
that path with connected deterministic tests. This module is that addition. `prepare_two_jobs` keeps
its own `TASKS`/`task_document` untouched and asks here when `--tasks useful` is selected.

WHAT IS HERE:

  `TASKS`             the two documentation tasks, imported from `check_useful_tasks` so the CONTRACT
                      and the CHECKER cannot drift apart -- one table, two readers.
  `EXCERPTS`          the finite frozen input set of `USEFUL-TASKS-305440.md`, each with its full
                      SHA-256 and its repository locator.
  `task_document`     the same shape `prepare_two_jobs.task_document` returns, so the preparation's
                      manifest/`human_contract` binding needs no special case for these.
  `deliver`           SEEDS a fixture repository's worktree with those bytes under `SOURCE_INPUTS`,
                      COMPARING each copy's digest to the pin. This is the operator's step before the
                      commit whose object name becomes `--base`; the preparation itself writes none
                      of it.
  `present`           the preparation's READ-ONLY proof that a nominated source ALREADY carries the
                      whole set at the pinned digests. It writes nothing, so it sits among the
                      refusals instead of after them.
  `verification`      the checker invocation for one Job, as the emitted task carries it.

WHY THE CONTEXT LIVES IN THE SOURCE. This is the owner simplification of 2026-09-29
(OWNER-SIMPLIFY-PARALLEL-PROOF-20260929.md) applied, not a preference of mine. The ACCEPTED
single-Job packet delivered its frozen excerpt as a FILE IN THE NOMINATED REPOSITORY --
`work/records/2026/09/finding-v12-startup-failure-fresh-packet/SOURCE-EXCERPTS-20260928.md`, named
repo-relative in the brief ("The supplied excerpt is at ...; read only that source document") -- and
the worker read it through the ordinary `sources` mount of `source`. That mechanism is accepted, needs
no new mount plumbing, and actually reaches both workers.

MY PREVIOUS VERSION DID NEITHER. It copied the excerpts into `<run root>/tasks/excerpts` and mounted
nothing, so the bytes never reached a Job; and because the PREPARATION wrote them, a refusal after
that point left them behind. Moving the delivery into the source repository removes both defects with
less code rather than more: the preparation now only PROVES the set is there, which is a read.

NO STORES, NO ENGINE, NO GIT. This composes documents, copies four files and hashes them.
"""
import hashlib
import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:                                # pragma: no cover
    sys.path.insert(0, str(HERE))

import check_useful_tasks                                    # noqa: E402

# ONE TABLE, TWO READERS. The checker owns the paths, headings and line bound; this builder reads them
# rather than restating them, so a heading added in one place cannot be missing in the other.
TASKS = check_useful_tasks.TASKS

TASK_SCHEMA = "baton.dogfood-task/2"
CHECKOUT = HERE.parents[4]

# THE FINITE FROZEN INPUT SET, exactly as `USEFUL-TASKS-305440.md` pins it: full digests, and the
# locator each is copied from.
EXCERPTS = {
    "E1-DESIGN.md": {
        "source": "v12/DESIGN.md",
        "sha256": "ea224a281d320077e0cc906ba91672930c8975660a453c49804dea888b92cbff",
    },
    "E2-E2E-OPERATOR-302142.md": {
        "source": "work/records/2026/09/finding-v12-startup-failure-fresh-packet"
                  "/E2E-OPERATOR-302142.md",
        "sha256": "ce0a7c931e005af6c039978346aff5ae30044efebcf08322d9e031912385f357",
    },
    "E3-EXECUTION-REVIEW-304782.json": {
        "source": "work/records/2026/09/finding-v12-startup-failure-fresh-packet"
                  "/EXECUTION-REVIEW-304782.json",
        "sha256": "de48a0cdae7870d2f640377e53f4c1e1b48d5fe932af27df5efc8261ae3ed895",
    },
    "E4-RESIDUAL-CLASSIFICATION-304829.md": {
        "source": "work/records/2026/09/finding-v12-failed-run-resource-hold"
                  "/RESIDUAL-CLASSIFICATION-304829.md",
        "sha256": "642dba931753d2a291965fd399b468a671b60b5b5f3d8cc96e5f583ff934531a",
    },
}

CONTRACT = "USEFUL-TASKS-305440.md"

# WHERE THE FROZEN CONTEXT SITS INSIDE THE NOMINATED SOURCE, repo-relative. The worker's checkout is
# mounted at `source`, so these are the paths a Job reads and the paths the brief names. One root
# keeps the whole set together and keeps it out of `docs/`, which is where both Jobs write.
SOURCE_INPUTS = "context/w247941"


def relative(name, into):
    """One delivered member's repo-relative path inside the nominated source."""
    return "/".join((SOURCE_INPUTS, into, name))


INSTRUCTIONS = """\
THE CHANGE THIS JOB IS ABOUT. Write `{path}`, and nothing else. It must be UTF-8, UNDER {bound} lines,
and carry every one of these headings exactly:

{headings}

`{path}` is the only file this Job may add or alter; another development line is being written against
this same base at the same time and it owns everything else.

YOUR ONLY SOURCES are the frozen excerpts already committed in your own checkout, under
`{inputs}/`, with the contract that lists them at `{contract}`:
{excerpts}
Each path is relative to the root of the checkout you were given, and each digest is over the bytes at
your declared base. A statement you cannot derive from those has been invented, and the reviewer is
asked to say so.

ONE DOCUMENT, TWO STAGES, and the Job's input identity is deliberately shared between them -- the
manager delivers this same requirement to both, because it is the same requirement they are held to.
Read the part that is yours.

IF YOUR STAGE IS THE IMPLEMENTATION. Write that file and nothing else. Do not judge your own work: the
verdict is a separate run by somebody else, and a turn that both writes and accepts has reviewed
nothing.

IF YOUR STAGE IS THE REVIEW. Your checkout is READ-ONLY and you have no stage in which to fix
anything. The structural check has already run, so it is not your job: judge whether the CONTENT is
correct against the excerpts and whether anything required is missing or overstated.

  Report `accepted` if it meets the requirement, `changes-requested` if it does not and you can say
  what would fix it, and `rejected` if it should not be taken at all. All three are valid results and
  none is better for you than another.
"""


def _brief(job_id):
    held = TASKS[job_id]
    headings = "\n".join("  " + one for one in held["headings"])
    # THE PATHS THE JOB ACTUALLY HAS, repo-relative in its own checkout -- not `/input/...`, which
    # named a mount this packet never arranged and no worker could have read.
    excerpts = "\n".join(f"  {relative(name, 'excerpts')}  sha256 {one['sha256']}"
                         for name, one in sorted(EXCERPTS.items()))
    return INSTRUCTIONS.format(path=held["path"],
                               bound=held["line_bound_exclusive"],
                               headings=headings, inputs=SOURCE_INPUTS,
                               contract=relative(CONTRACT, "contract"),
                               excerpts=excerpts)


def task_document(job_id, *, run_id, base):
    """One selected Job's frozen task, in the shape the preparation already binds.

    THE SAME MEMBERS `prepare_two_jobs.task_document` returns, so the manifest's `human_contract`
    digest, the disjoint-path check and the emitted submission need no special case for these tasks.
    `verification` is the STRUCTURAL check -- the semantic one is a person, and no document can carry
    it.
    """
    held = TASKS[job_id]
    return {
        "schema": TASK_SCHEMA,
        "task_id": f"{run_id}-{job_id}",
        "declared_base": base,
        "source_profile": "git-line",
        "source_root": "source",
        "instructions": _brief(job_id),
        "verification": verification(job_id),
    }


def verification(job_id):
    """The checker invocation the emitted task carries for one Job.

    RUN FROM THE CHECKOUT, against a checker that is IN the checkout. The previous version named
    `/input/checker/check_useful_tasks.py`, a mount nothing in this packet created, so the emitted
    verification could only have failed to start. The accepted single-Job task ran
    `python3 -c "<one-liner>"` in the workspace; this runs a committed script in the same place, which
    is the same mechanism with the structural checks already written for it.
    """
    held = TASKS[job_id]
    return ["python3", relative("check_useful_tasks.py", "checker"),
            "--job", job_id, "--root", ".", "--changed", held["path"]]


# WHAT TRAVELS WITH THE EXCERPTS. W247941 review 2026-09-29T12-42-29Z: the contract was NAMED in the
# brief and never delivered, so a reviewer asked to judge against `USEFUL-TASKS-305440.md` had no copy
# of it. The checker travels for the same reason -- the task's `verification` runs it.
CARRIED = ((CONTRACT, "contract"), ("check_useful_tasks.py", "checker"))


def _gates(into, planned):
    """Every refusal BEFORE the first byte is written. W247941 review 2026-09-29T12-42-29Z.

    THREE GATES, and the order is the point -- my first version created the directories and wrote as
    it walked, so a refusal halfway left a partial delivery behind:

      IMPORT PROVENANCE. The bytes come from the SELECTED checkout, and a source whose digest has
      moved is refused before anything is copied rather than after some of it is.
      AN EXISTING TARGET with DIFFERENT bytes is a refusal, not an overwrite: a delivery that
      silently replaced a Job's mounted input would erase the evidence of what it read.
      AN EXISTING TARGET with IDENTICAL bytes is an exact replay and is allowed to stand, which is
      what makes a repeated preparation idempotent instead of refused.
    """
    for name, held in sorted(planned.items()):
        place = pathlib.Path(into) / held["relative"]
        if place.exists():
            current = hashlib.sha256(place.read_bytes()).hexdigest()
            if current != held["sha256"]:
                raise ValueError(f"{place} already exists with DIFFERENT bytes "
                                 f"({current} rather than {held['sha256']}); a delivery "
                                 f"does not overwrite a mounted input")


def _planned(checkout=None):
    """The whole set to be seeded or proved, read from the SELECTED checkout and hashed.

    THE PINS ARE CHECKED HERE, before any decision about the target: a source whose bytes have moved
    is refused rather than copied, and the same reading serves both `deliver` and `present`.
    """
    root = pathlib.Path(checkout or CHECKOUT)
    planned = {}
    for name, held in sorted(EXCERPTS.items()):
        source = root / held["source"]
        if not source.is_file():
            raise FileNotFoundError(f"the excerpt source {source} is absent")
        raw = source.read_bytes()
        found = hashlib.sha256(raw).hexdigest()
        if found != held["sha256"]:
            raise ValueError(f"{held['source']} hashes {found} and this packet pins "
                             f"{held['sha256']}; the frozen input moved")
        planned[name] = {"raw": raw, "sha256": found,
                         "relative": relative(name, "excerpts"),
                         "source": held["source"]}
    for name, into in CARRIED:
        source = HERE / name
        if not source.is_file():                             # pragma: no cover
            raise FileNotFoundError(f"the carried file {source} is absent")
        raw = source.read_bytes()
        planned[name] = {"raw": raw, "sha256": hashlib.sha256(raw).hexdigest(),
                         "relative": relative(name, into), "source": name}
    return planned


def present(source_root, *, checkout=None):
    """PROVE the nominated source ALREADY carries the whole frozen set. Reads only.

    THE PREPARATION'S GATE, and it is a gate precisely because it writes nothing: it can sit with the
    other refusals rather than after them, which is exactly what the writes-before-refusal defect was.
    An absent member and a member whose bytes differ are both refusals that name the path.
    """
    planned = _planned(checkout)
    proven = {}
    for name, held in sorted(planned.items()):
        place = pathlib.Path(source_root) / held["relative"]
        if not place.is_file():
            raise FileNotFoundError(
                f"the nominated source does not carry {held['relative']}; seed the fixture "
                f"repository with `useful_tasks.py --seed <worktree>` and commit it BEFORE this "
                f"preparation, because each Job reads this set through its own checkout")
        found = hashlib.sha256(place.read_bytes()).hexdigest()
        if found != held["sha256"]:
            raise ValueError(f"{held['relative']} in the nominated source hashes {found} and this "
                             f"packet pins {held['sha256']}; the Jobs would read bytes no digest "
                             f"here names")
        proven[name] = {"relative": held["relative"], "sha256": found,
                        "bytes": len(held["raw"]), "source": held["source"],
                        "place": str(place)}
    return proven


def deliver(into, *, checkout=None):
    """SEED a fixture repository's worktree with the excerpts, the contract and the checker.

    DELIVERY IS NOT PINNING, which is the whole reason this exists: a Job reads the COPY, so the copy
    is what has to be proved. Nothing is created or written until `_gates` has passed over the WHOLE
    planned set. The operator runs this ONCE, before the commit whose object name becomes `--base`;
    committing it is an operator step, because nothing here performs a Git operation.
    """
    planned = _planned(checkout)

    _gates(into, planned)

    delivered = {}
    for name, held in sorted(planned.items()):
        place = pathlib.Path(into) / held["relative"]
        # AN IDENTICAL REPLAY IS NOT REWRITTEN. W247941 review 2026-09-29T12-50-22Z: rewriting bytes
        # that already match changes an mtime for nothing and, on a mounted input, touches a file a
        # Job may be reading. The gate above has already proved the existing bytes are the pinned
        # ones, so the honest act here is to leave them alone.
        if place.exists():
            delivered[name] = {"place": str(place), "relative": held["relative"],
                               "sha256": held["sha256"],
                               "bytes": len(held["raw"]), "source": held["source"],
                               "replayed": True}
            continue
        place.parent.mkdir(parents=True, exist_ok=True)
        place.write_bytes(held["raw"])
        landed = hashlib.sha256(place.read_bytes()).hexdigest()
        if landed != held["sha256"]:                         # pragma: no cover
            raise ValueError(f"the delivered copy {place} hashes {landed}, not "
                             f"{held['sha256']}")
        delivered[name] = {"place": str(place), "relative": held["relative"],
                           "sha256": landed,
                           "bytes": len(held["raw"]), "source": held["source"],
                           "replayed": False}
    return delivered


def _cli(argv=None):
    """The operator's two read/seed modes, so the recipe has commands rather than prose."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="useful_tasks",
        description="Seed a fixture repository worktree with this packet's frozen context, or "
                    "prove a repository already carries it. Opens no store, reaches no engine or "
                    "network, and performs no Git operation -- committing the seeded files is the "
                    "operator's own step.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--seed", metavar="WORKTREE",
                       help="copy the frozen set into this worktree under " + SOURCE_INPUTS)
    group.add_argument("--prove", metavar="WORKTREE",
                       help="read-only: refuse unless this worktree already carries the whole set "
                            "at the pinned digests")
    taken = parser.parse_args(argv)
    # A REFUSAL IS ONE SENTENCE AND A STATUS, not a traceback: the setup recipe reads this output,
    # and an operator reading a stack trace has to work out which line was the answer.
    try:
        if taken.seed:
            print(json.dumps(deliver(taken.seed), indent=2, sort_keys=True))
        elif taken.prove:
            print(json.dumps(present(taken.prove), indent=2, sort_keys=True))
        else:
            print(json.dumps({job_id: task_document(job_id, run_id="probe", base="0" * 40)
                              for job_id in sorted(TASKS)}, indent=2, sort_keys=True))
    except (FileNotFoundError, ValueError) as refused:
        print(f"refused: {refused}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(_cli())
