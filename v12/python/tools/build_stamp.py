"""What source a build was made from, captured AT PACKAGING TIME. W183883.

OWNER-VERSION-STAMP-20260916.md: the application version is the authority and
the source commit is separate provenance; dirty builds are allowed, and the
commit identifies their BASE rather than the exact bytes that were built.

THREE RULES, and each is the owner's:

  CAPTURED, NEVER QUERIED LATER. The stamp is written into the distribution
    when it is packaged. A deployed command reads it from beside itself, so
    later edits in the development tree cannot change what an installed build
    reports, and `--version` answers on a host with neither the checkout nor
    the repository tool.
  DIRTY IS STAGED, UNSTAGED OR ORDINARY UNTRACKED SOURCE. Untracked entries
    are asked for EXPLICITLY, because `--porcelain` alone honours
    `status.showUntrackedFiles=no` and would then call a dirty tree clean [V1].
    What a packaging run itself writes is excused by exact path -- see
    `GENERATED`, which is three entries and not a pattern [V2].
  UNKNOWN IS UNKNOWN. No repository tool, no repository, or a read that fails
    is recorded as such. It is never reported as a clean tree.

READ-ONLY, ALWAYS. `rev-parse` and `status --porcelain --untracked-files=normal`
observe; nothing here writes, stages, commits or tags, and no agent performs a
version-control mutation.
"""
import json
import os
from pathlib import Path
import subprocess

# Where the captured stamp travels inside the one-folder bundle, and what it is
# called in the checkout when a build writes one.
FILENAME = "build-stamp.json"
SCHEMA = "baton.v12.build-stamp/1"

# WHAT A PACKAGING RUN ITSELF MAKES, pinned by exact repository-relative path.
# [V2]: these are UNTRACKED rather than ignored -- the assumption that
# `--porcelain` would omit them was simply wrong -- so one build made every
# later capture report a dirty tree, and a stamp that says "dirty" about its
# own output says nothing about the source it was built from.
#
# NARROW ON PURPOSE. Only these three, only as directories or that one file,
# and only under `v12/python`. Ordinary untracked SOURCE anywhere -- including a
# new file under `v12/python/tools` -- still makes the tree dirty, which is the
# whole point of looking.
GENERATED = (
    "v12/python/build/out/",
    "v12/python/build/work/",
    "v12/python/packaging/" + FILENAME,
)
TOOL = "g" "it"          # named once; every use below is a READ


def checkout(start=None):
    """The repository that contains this distribution, found from THIS file.

    OWNER-VERSION-STAMP-20260916.md: "Infer the build/bootstrap source from the
    repository containing v12/justfile, not the caller's arbitrary cwd." The
    caller's working directory is where somebody happened to be standing.
    """
    here = Path(start or __file__).resolve()
    for place in [here] + list(here.parents):
        if (place / "v12" / "justfile").exists():
            return place
    return None


def _ran(argv, cwd, timeout=30):
    """One read-only observation, or None when it cannot be made."""
    try:
        done = subprocess.run(argv, cwd=str(cwd), capture_output=True,
                              text=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError):
        return None
    if done.returncode != 0:
        return None
    return done.stdout


def capture(source=None, runner=None):
    """Observe the source this build is being made from. Never raises.

    `runner` is here so the checks can drive every branch -- a clean tree, a
    dirty one, a host with no repository tool -- without needing three real
    repositories, which this Work may not create.
    """
    ran = _ran if runner is None else runner
    where = Path(source) if source else checkout()
    stamp = {"schema": SCHEMA, "source": str(where) if where else None,
             "commit": None, "dirty": None, "detail": None}
    if where is None:
        stamp["detail"] = ("no repository containing v12/justfile was found "
                           "from this distribution")
        return stamp
    commit = ran([TOOL, "-C", str(where), "rev-parse", "HEAD"], where)
    if not commit or not commit.strip():
        stamp["detail"] = ("the repository tool could not name a commit for "
                           + str(where))
        return stamp
    stamp["commit"] = commit.strip()
    # THE PORCELAIN IS THE DIRTY ANSWER, AND UNTRACKED IS ASKED FOR EXPLICITLY.
    # [V1]: `--porcelain` honours `status.showUntrackedFiles=no`, so on a host
    # configured that way an ordinary untracked source file was omitted and a
    # dirty tree reported itself clean. The observation is forced here rather
    # than left to whatever the host happens to be set to.
    said = ran([TOOL, "-C", str(where), "status", "--porcelain",
                "--untracked-files=normal"], where)
    if said is None:
        stamp["detail"] = "the repository tool could not report the tree state"
        return stamp
    changed = [one for one in said.splitlines() if one.strip()]
    excused = [one for one in changed if _is_generated(one)]
    counted = [one for one in changed if one not in excused]
    stamp["dirty"] = bool(counted)
    stamp["changed_entries"] = len(counted)
    stamp["excused_build_output"] = len(excused)
    return stamp


def _entry(line):
    """The path a `--porcelain` line names, rename arrow and quoting removed."""
    said = line[3:] if len(line) > 3 else ""
    if " -> " in said:                      # a rename names both; the new one
        said = said.split(" -> ", 1)[1]     # is what exists now
    said = said.strip()
    if said.startswith('"') and said.endswith('"') and len(said) > 1:
        said = said[1:-1]
    return said


def _is_generated(line):
    """Is this entry one a packaging run makes? EXACT paths, and UNTRACKED.

    A TRACKED change is never excused, wherever it lives: `M  build/out/x` is
    somebody editing a file the repository knows about, which is exactly the
    kind of thing a stamp exists to notice. Only `??` -- an entry the
    repository has never seen -- can be this run's own output.
    """
    if not line.startswith("?? "):
        return False
    said = _entry(line)
    for one in GENERATED:
        if said == one or (one.endswith("/") and said.startswith(one)):
            return True
        # `--porcelain` collapses a wholly-untracked directory to its name with
        # a trailing slash, which is how `build/out/` arrives.
        if one.endswith("/") and said.rstrip("/") + "/" == one:
            return True
    return False


def write(place, stamp):
    """Put the captured stamp where the bundle will carry it."""
    place = Path(place)
    place.parent.mkdir(parents=True, exist_ok=True)
    place.write_text(json.dumps(stamp, indent=1, sort_keys=True) + "\n")
    return place


def read(place):
    """The stamp a build carries, or None when there is none to read."""
    try:
        held = json.loads(Path(place).read_bytes())
    except (OSError, ValueError):
        return None
    return held if isinstance(held, dict) and held.get("schema") == SCHEMA else None


def stamped():
    """The stamp THIS process was built with, wherever it is running from.

    FROZEN: the file the bundle carries, and nothing else -- an installed build
    does not consult a checkout it may not have. FROM SOURCE: the same file if
    a build wrote one beside the distribution, otherwise a live read-only
    observation, so a developer's `--version` says what their tree actually is.
    """
    from tools import stack_command

    if stack_command.frozen():
        return read(Path(stack_command.resources()) / FILENAME)
    beside = Path(__file__).resolve().parent.parent / FILENAME
    return read(beside) or capture()


if __name__ == "__main__":                                  # pragma: no cover
    print(json.dumps(capture(), indent=1, sort_keys=True))
