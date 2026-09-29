#!/usr/bin/env bash
# The pair's setup, as ONE ordered sequence over ONE topology. W247941 claim 305611.
#
# Corrections in this version, all from W247941 review 2026-09-29T12-26-38Z and all of them mine:
#
#   THE TOPOLOGY WAS SPLIT. `tools.bootstrap --destination X` OVERRIDES `state_root` to X and writes
#   `X/bootstrap.json` and `X/db/`, while the preparation reads `<run root>/bootstrap.json` and
#   `<run root>/db/`. My previous version installed into an `instances/` path and then prepared
#   against a different `runs/` path, so step 7 could only fail. There is now ONE root: the
#   destination IS the run root. The instance and the run are the same place, which is what the
#   supported layout actually is, and no receipt is copied anywhere to paper over a mismatch.
#   `--destination` REQUIRES `--distro`, which I never passed. It is the ACCEPTED PINNED RUNTIME
#   (`prepare_two_jobs.ACCEPTED["runtime_path"]`, digest-pinned by `verify_247941.PINNED`), read from
#   the module rather than named here, and NOTHING IS BUILT.
#   BASE IS HELD TO THE SOURCE'S ACTUAL HEAD, not just to 40 hex characters: the validation resolves
#   the repository's own `HEAD` (one symref hop, packed-refs included) and refuses a mismatch.
#
# AND ONE CHANGE FROM THE OWNER RULING OF 2026-09-29 (OWNER-SIMPLIFY-PARALLEL-PROOF-20260929.md):
# the frozen context is SEEDED INTO THE SOURCE AND COMMITTED BY THE OPERATOR, before this runs, and
# step 1 proves it is there at the pinned digests. It used to be copied into the run root by the
# preparation and mounted nowhere, so it reached no Job. Seeding is step 0 of the plan below and the
# commit is the operator's, because nothing here performs a Git operation on the fixture.
#
# IT PERFORMS NOTHING WITHOUT --commit: with operands and no flag it prints the ordered plan and exits
# 0. It creates no container, opens no store, reaches no engine, provider or network, and performs no
# Git operation on this checkout -- the one clone it makes writes only inside the new run root.
set -euo pipefail

RUN_ID="${RUN_ID:-}"                 # required: names the run; every path derives from it
SOURCE="${SOURCE:-}"                 # required: the fixture repository both Jobs read
BASE="${BASE:-}"                     # required: that repository's CURRENT HEAD, 40 hex characters
SNAPSHOT="${SNAPSHOT:-/home/sl/baton-instances/single-job-257627-291715/manager-source}"
DOSSIER="/home/sl/src/baton/work/records/2026/09/finding-v12-real-jobs-adoption-gate"
PYTHON="${PYTHON:-/home/sl/.local/state/baton-v12-venv/bin/python}"
COMMIT="no"
[ "${1:-}" = "--commit" ] && COMMIT="yes"

for name in RUN_ID SOURCE BASE; do
  if [ -z "${!name}" ]; then
    echo "refused: $name is required; this script invents no identity" >&2
    exit 2
  fi
done
case "${RUN_ID}" in
  ""|*/*|*..*|.*) echo "refused: RUN_ID is one path component, not ${RUN_ID}" >&2; exit 2 ;;
esac

IMPORT_PATH="${SNAPSHOT}/v12/python/src:${SNAPSHOT}/v12/python"

# ONE ROOT, AND THE MODULE DECIDES WHERE IT MAY BE. The bootstrap's destination, its `state_root` and
# the preparation's `--run-root` are all this path, so every later command names the same
# `bootstrap.json` and `db/`.
#
# THIS LINE USED TO READ `/home/sl/baton-runs/${RUN_ID}`, A LITERAL OF ITS OWN, and W247941 owner
# reroute 306323 is the consequence: `prepare_two_jobs` REFUSES that directory -- the pinned
# validator treats it as a checkout, and mutable deployment state belongs outside one -- so the
# owner's setup could only fail, before the run root was even created. Two places held the same
# decision and they disagreed. Now there is one: `prepare_two_jobs.supported_root` builds the path
# under the module's own `SUGGESTED_ROOT` and validates it -- consumed identity, self-naming, the
# campaign's historical boundaries AND the boundary the pinned product itself answers today -- so
# this script cannot propose a root the preparation will reject.
#
# INSTANCE_ROOT overrides the parent directory for an operator who has a different disk. It is
# validated exactly the same way; there is no unchecked path into this.
INSTANCE_ROOT="${INSTANCE_ROOT:-}"
RUN_ROOT="$(env PYTHONPATH="${IMPORT_PATH}:${DOSSIER}" "${PYTHON}" -B -c '
import sys
sys.path.insert(0, sys.argv[1])
import prepare_two_jobs

dossier, run_id, under = sys.argv[1:4]
try:
    print(prepare_two_jobs.supported_root(run_id, under=under or None))
except prepare_two_jobs.PreparationRefusal as refused:
    print("refused: " + str(refused), file=sys.stderr)
    raise SystemExit(2)
' "${DOSSIER}" "${RUN_ID}" "${INSTANCE_ROOT}")"
CLONE="${RUN_ROOT}/source"
JOB_STORE="${RUN_ROOT}/db/jobs.sqlite3"
CONTROL_STORE="${RUN_ROOT}/db/control.sqlite3"
INPUTS="${RUN_ROOT}/bootstrap-inputs.json"

# THE VALIDATION IS THE MODULE'S WHERE THE MODULE HAS IT, and file reads where it does not. Operands
# arrive through argv; nothing is interpolated into program text.
validate() {
  env PYTHONPATH="${IMPORT_PATH}:${DOSSIER}" "${PYTHON}" -B -c '
import os, pathlib, sys
sys.path.insert(0, sys.argv[1])
import prepare_two_jobs, verify_247941

dossier, run_root, run_id, source, base, phase = sys.argv[1:7]

def refuse(why):
    print("refused: " + why, file=sys.stderr)
    raise SystemExit(2)

# THE REPOSITORY AND ITS HEAD, asked of Git READ-ONLY. W247941 review 2026-09-29T12-30-40Z prefers
# this to the partial `.git` parser I wrote: `rev-parse` resolves symrefs, packed refs, worktrees and
# every other arrangement I would otherwise reimplement one case at a time. `--git-dir` is not passed
# and nothing is written -- `rev-parse` and `status --porcelain` are reads.
import subprocess

def git(*operands):
    held = subprocess.run(("git", "-C", source) + operands, capture_output=True, text=True)
    if held.returncode != 0:
        refuse(f"{source} did not answer git {chr(32).join(operands)}: "
               f"{(held.stderr or held.stdout).strip()[:160]}")
    return held.stdout.strip()

head = git("rev-parse", "HEAD")
if head != base:
    refuse(f"BASE is not the HEAD of this repository: HEAD is {head} and BASE is {base}")

# AND THE TREE IS CLEAN, which the review requires of the source before it is cloned: a Job that reads
# a dirty fixture is reading bytes no base names.
dirty = git("status", "--porcelain")
if dirty:
    refuse(f"{source} has uncommitted changes and is not a clean base: "
           f"{dirty.splitlines()[0][:80]}")

# THE PINNED RUNTIME, from the accepted configuration rather than from this script.
distro = prepare_two_jobs.ACCEPTED["runtime_path"]
if not os.path.isdir(distro):
    refuse(f"the pinned runtime {distro} is absent; nothing here builds one")

# AND THE FROZEN CONTEXT IS ALREADY COMMITTED IN THE SOURCE. W247941 owner ruling 2026-09-29: the
# two Jobs read their excerpts, the contract and the checker through their own checkout, the way the
# accepted single-Job packet delivered SOURCE-EXCERPTS-20260928.md. Seeding and committing them is
# the operator step named in the plan below; this only proves the result, and the proof is a read.
import useful_tasks

try:
    useful_tasks.present(source)
except (FileNotFoundError, ValueError) as missing:
    refuse(str(missing))

if phase == "fresh":
    prepare_two_jobs.fresh(run_root, run_id)

print(distro)
' "${DOSSIER}" "${RUN_ROOT}" "${RUN_ID}" "${SOURCE}" "${BASE}" "$1"
}

DISTRO="$(validate check)"

cat <<PLAN
ordered plan for ${RUN_ID} -- ONE root, ${RUN_ROOT}
  0  seed ${SOURCE}                OPERATOR STEP, already done if step 1 passed:
                                     ${PYTHON} ${DOSSIER}/useful_tasks.py --seed ${SOURCE}
                                   then add and commit those files in ${SOURCE}. This script performs
                                   no Git operation, and ${BASE} must be that commit.
  0b root                          done: ${RUN_ROOT}, built and validated by
                                   prepare_two_jobs.supported_root -- not by a literal in this file
  1  validate                      done: identity is one component, ${SOURCE} is a repository whose
                                   HEAD IS ${BASE}, it is clean, it already carries the frozen
                                   context at the pinned digests, and the pinned runtime is present
  2  fresh(${RUN_ROOT}, ${RUN_ID})
  3  mkdir ${RUN_ROOT}             refuse if it exists
  4  clone ${SOURCE} -> ${CLONE}
  5  prepare_two_jobs --emit-bootstrap-inputs > ${INPUTS}
  6  tools.bootstrap --inputs ${INPUTS} --destination ${RUN_ROOT} --distro ${DISTRO}
                                   --no-repositories
  7  prepare_two_jobs --tasks useful
                                   EMITS deployment, submission, the SELECTED documentation tasks,
                                   selections and commands, and PROVES the frozen context is in the
                                   clone each Job reads. It delivers nothing: a step that writes
                                   cannot also refuse without leaving bytes behind
  stores after 6                   ${JOB_STORE}
                                   ${CONTROL_STORE}
  import path                      ${IMPORT_PATH}
  commit?                          ${COMMIT}
PLAN

if [ "${COMMIT}" != "yes" ]; then
  echo "printed the ordered plan and did nothing; re-run with --commit to perform it"
  exit 0
fi

validate fresh >/dev/null

if [ -e "${RUN_ROOT}" ]; then
  echo "refused: ${RUN_ROOT} already exists; a successor takes a new identity" >&2
  exit 2
fi
mkdir -p "${RUN_ROOT}"

git clone --quiet "${SOURCE}" "${CLONE}"

env PYTHONPATH="${IMPORT_PATH}:${DOSSIER}" PYTHONDONTWRITEBYTECODE=1 "${PYTHON}" -B \
  "${DOSSIER}/prepare_two_jobs.py" \
  --run-root "${RUN_ROOT}" --source "${CLONE}" --base "${BASE}" \
  --run-id "${RUN_ID}" --emit-bootstrap-inputs > "${INPUTS}"

env PYTHONPATH="${IMPORT_PATH}" PYTHONDONTWRITEBYTECODE=1 "${PYTHON}" -B \
  -m tools.bootstrap --inputs "${INPUTS}" --destination "${RUN_ROOT}" \
  --distro "${DISTRO}" --no-repositories

# `--tasks useful` IS THE SELECTION. W247941 review 2026-09-29T12-42-29Z: without it this setup
# prepared the greeting fixture, so the owner would have selected a run over the machinery payload
# instead of the two documentation tasks this packet is about. The clone at ${CLONE} carries the
# frozen context because ${SOURCE} does at ${BASE}, which step 1 proved before anything was created.
env PYTHONPATH="${IMPORT_PATH}:${DOSSIER}" PYTHONDONTWRITEBYTECODE=1 "${PYTHON}" -B \
  "${DOSSIER}/prepare_two_jobs.py" \
  --run-root "${RUN_ROOT}" --source "${CLONE}" --base "${BASE}" --run-id "${RUN_ID}" \
  --tasks useful

echo
echo "setup complete under ${RUN_ROOT}: the preparation has EMITTED the deployment, submission,"
echo "task documents, selections and the serve/status commands. Nothing has been started, and the"
echo "live run is a separate owner selection using the serve command the preparation printed."
