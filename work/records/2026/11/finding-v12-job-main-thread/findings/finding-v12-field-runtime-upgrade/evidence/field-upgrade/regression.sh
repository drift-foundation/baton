#!/usr/bin/env bash
# W386447 review 2026-11-27 regressions for the FIELD GUARDS, offline: fixtures only, no instance, no engine.
#   regression.sh <candidate tree root, holding v12/>
# [3] the positive source check is a whole-file read, so it passes under pipefail on the real adapter where the
#     reviewed `git show | grep -q` returned 141/0; the watcher's verdicts are exact. [1] the launcher's settled rule
#     is the upgrade's: a held, destroyed-runtime M386446 shape passes and the real waiting shape refuses.
# The image guard's own regressions, including the passing check against the exact installed contents, are product
# tests: v12/python/tests/tools/test_installed_worker.py.
set -Eeuo pipefail
umask 077
here=$(cd "$(dirname "$0")" && pwd)
cand=$(cd "$1" && pwd)
py=/home/sl/.local/state/baton-v12-venv/bin/python
# shellcheck source=field-guards.sh
source "$here/field-guards.sh"
work=$(mktemp -d /var/tmp/w386447-guard-regression.XXXXXXXX)
trap 'chmod -R u+rwx "${work:?}" && rm -r -- "${work:?}"' EXIT
failures=0
check() {  # <name> <expected> <actual>
    if [[ $2 == "$3" ]]; then echo "ok    $1"; else echo "FAIL  $1: expected [$2], got [$3]"; failures=$((failures+1)); fi
}
marker="THE OWNER'S DECISION ON THAT ESCALATION"
adapter=$cand/v12/worker/claude_agent.py

# [3] positive source check under pipefail, on the real adapter bytes.
set +e
file_has "$adapter" "$marker"; check "file_has finds the marker in the candidate adapter under pipefail" 0 $?
cp "$adapter" "$work/old_adapter.py"; sed -i "s/$marker/THE REVIEWER'S/g" "$work/old_adapter.py"
file_has "$work/old_adapter.py" "$marker"; check "file_has refuses an adapter without it" 1 $?
file_has "$work/absent.py" "$marker"; check "file_has refuses a missing file" 1 $?
set -e

# [1] the launcher's settled rule over durable-document shapes.
stage() {  # <name> <state> <episode> <attempt> <runtime axis or null>
    local runtime=null; [[ $5 == null ]] || runtime="{\"runtime_id\":\"r-$1\",\"execution_runtime\":\"$5\"}"
    printf '{"stage_id":"job-x/%s","state":"%s","episode":%s,"attempt_id":"%s","runtime":%s}' "$1" "$2" "$3" "$4" "$runtime"
}
doc() { printf '{"schema":"baton.v12.job-status/9","canonical":true,"jobs":[{"job_id":"job-x","stages":[%s]}]}' "$1"; }
doc "$(stage implementation awaiting-answer 1 attempt-1 destroyed),$(stage review answered 1 attempt-r destroyed),$(stage integration blocked 0 null null)" > "$work/held.json"
doc "$(stage implementation waiting 2 attempt-2 null),$(stage review answered 1 attempt-r destroyed)" > "$work/waiting.json"
set +e
settled "$cand" "$work/held.json" >/dev/null; check "settled accepts the held, runtime-destroyed shape" 0 $?
settled "$cand" "$work/waiting.json" >/dev/null; check "settled refuses the real waiting attempt" 1 $?
held_for_owner "$work/held.json" job-x; check "held_for_owner accepts the held shape" 0 $?
held_for_owner "$work/waiting.json" job-x; check "held_for_owner refuses the waiting shape" 1 $?
set -e

# [3] the watcher's verdicts.
thread() {  # <request state> <decision id>
    printf '{"entries":[],"requests":[{"request_id":"message-q","state":"%s","decision":{"message_id":"%s"}}]}' "$1" "$2"
}
verdict() {  # <status doc> <thread doc>
    printf '%s' "$1" > "$work/s.json"; printf '%s' "$2" > "$work/t.json"
    continuation_verdict "$work/s.json" "$work/t.json" job-x message-q answer-a attempt-1 1
}
check "held with the answer recorded is PENDING" PENDING "$(verdict "$(doc "$(stage implementation awaiting-answer 1 attempt-1 destroyed)")" "$(thread answer-recorded answer-a)")"
check "delivered, attempt not yet admitted is PENDING" PENDING "$(verdict "$(doc "$(stage implementation queued 1 attempt-1 destroyed)")" "$(thread delivered answer-a)")"
check "a new attempt with the answer delivered is CONFIRMED" CONFIRMED "$(verdict "$(doc "$(stage implementation running 2 attempt-2 running)")" "$(thread delivered answer-a)")"
check "a completed new attempt with the answer delivered is CONFIRMED" CONFIRMED "$(verdict "$(doc "$(stage implementation completed 2 attempt-2 destroyed)")" "$(thread delivered answer-a)")"
v=$(verdict "$(doc "$(stage implementation running 2 attempt-2 running)")" "$(thread answer-recorded answer-a)"); check "a new attempt WITHOUT the delivery is UNRELATED" UNRELATED "${v%%:*}"
v=$(verdict "$(doc "$(stage implementation running 2 attempt-2 running)")" "$(thread delivered answer-b)"); check "a delivery of another answer is UNRELATED" UNRELATED "${v%%:*}"
v=$(verdict "$(doc "$(stage implementation exceptional 2 attempt-2 destroyed)")" "$(thread delivered answer-a)"); check "a failed new attempt is UNRELATED" UNRELATED "${v%%:*}"
v=$(verdict "$(doc "$(stage implementation running 3 attempt-3 running)")" "$(thread delivered answer-a)"); check "a second continuation is UNRELATED" UNRELATED "${v%%:*}"
v=$(verdict "$(doc "$(stage implementation awaiting-answer 1 attempt-1 destroyed)")" "$(thread open answer-a)"); check "a held request that lost its answer is UNRELATED" UNRELATED "${v%%:*}"

# The field script itself parses, and no positive check in it or its guards is a `| grep -q` pipeline.
bash -n "$here/field-upgrade.sh" && bash -n "$here/field-guards.sh"
check "no | grep -q pipeline in the field script or its guards" 0 "$(grep -hvE '^[[:space:]]*#' "$here/field-upgrade.sh" "$here/field-guards.sh" | grep -cE '\|[[:space:]]*grep[[:space:]]+-[a-zA-Z]*q' || true)"
check "no override that resumes without the prompt" 0 "$(grep -c -- '--accept-unprompted-images' "$here/field-upgrade.sh" || true)"
(( failures == 0 )) && echo "FIELD GUARD REGRESSIONS PASSED" || { echo "$failures FIELD GUARD REGRESSION(S) FAILED"; exit 1; }
