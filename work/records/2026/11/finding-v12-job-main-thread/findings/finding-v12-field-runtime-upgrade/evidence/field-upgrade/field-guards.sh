# W386447 field guards, sourced by field-upgrade.sh and by regression.sh. Functions only; every input is an argument.
# Review 2026-11-27: [1] the held-state guard uses the product's own `runtime_upgrade.unresolved`, over a DURABLE
# read, so the launcher and the upgrade apply one meaning of "settled"; [3] no positive check is a `cmd | grep -q`
# pipeline (under pipefail an early-exiting grep makes the writer's SIGPIPE, 141, fail a check that matched), and the
# watcher answers CONFIRMED only for the one continuation that carries the recorded answer.

# Source-form Python at <root>/v12/python, with nothing ambient.
py_at() {  # <source root> <python arguments...>
    local root=$1; shift
    (cd "$root/v12/python" && env -i PATH=/usr/bin:/bin HOME=/var/tmp LANG=C.UTF-8 PYTHONPATH=src:. PYTHONDONTWRITEBYTECODE=1 \
        timeout 300 "$py" -B "$@")
}
# The durable Job status of an instance, read by the code at <root> (never the published snapshot).
durable_status() {  # <source root> <instance.json>
    py_at "$1" -c 'import json,sys;from tools import instance,job_status;print(json.dumps(job_status.read(instance.settings(instance.read(sys.argv[1]))),sort_keys=True))' "$2"
}
thread_read() {  # <source root> <instance.json> <job>
    py_at "$1" -m tools.job_thread read --instance "$2" --job "$3"
}
# Nothing is, or may be, executing: the upgrade's own rule, applied to a status document file.
settled() {  # <source root> <status document file>
    py_at "$1" -c 'import json,sys;from tools import runtime_upgrade;found=runtime_upgrade.unresolved(json.load(open(sys.argv[1])))
print("; ".join(found) or "settled");sys.exit(1 if found else 0)' "$2"
}
# Exactly this Job, implementation held for the owner and review answered.
held_for_owner() {  # <status document file> <job>
    jq -e --arg j "$2" '[.jobs[].job_id]==[$j] and ([.jobs[0].stages[] | select(.stage_id==($j+"/implementation") or .stage_id==($j+"/review")) | {(.stage_id): .state}] | add) == {($j+"/implementation"): "awaiting-answer", ($j+"/review"): "answered"}' "$1" >/dev/null
}
# The main thread holds the escalated request, its escalation to the owner and the recorded, not yet delivered answer.
thread_holds_answer() {  # <thread file> <request> <escalation> <answer>
    jq -e --arg r "$2" --arg e "$3" --arg a "$4" \
        '([.entries[] | select(.message_id==$r and .kind=="finding-request")] | length)==1
         and ([.entries[] | select(.message_id==$e and .kind=="escalation" and .destination=="baton.slaw")] | length)==1
         and ([.entries[] | select(.message_id==$a and .kind=="main.owner-answer" and .request_id==$r and .escalation_id==$e)] | length)==1
         and ([.requests[] | select(.request_id==$r and .state=="answer-recorded" and .decision.message_id==$a)] | length)==1' "$1" >/dev/null
}
# A fixed string in a FILE: grep reads all of its own input, so nothing upstream can be cut off.
file_has() {  # <file> <fixed string>
    [[ -f $1 ]] && grep -qF -- "$2" "$1"
}
# One verdict over a durable status file and a main-thread file read after the start:
#   CONFIRMED  the request is delivered WITH the recorded answer, and the implementation runs a NEW attempt, the
#              held episode plus one, not failed;
#   PENDING    still held, or the delivery is committed and the new attempt not yet admitted;
#   UNRELATED: anything else -- a new attempt without that delivery, a failure, a different Job set.
continuation_verdict() {  # <status file> <thread file> <job> <request> <answer> <held attempt> <held episode>
    local delivered stage
    [[ $(jq -c '[.jobs[].job_id]' "$1") == "[\"$3\"]" ]] || { echo "UNRELATED: the instance's Jobs are $(jq -c '[.jobs[].job_id]' "$1")"; return; }
    stage=$(jq -c --arg j "$3" '.jobs[0].stages[] | select(.stage_id==($j+"/implementation")) | {state, episode, attempt_id}' "$1")
    delivered=$(jq -r --arg r "$4" --arg a "$5" '[.requests[] | select(.request_id==$r)] | if length != 1 then "missing" elif .[0].state != "delivered" then .[0].state elif .[0].decision.message_id != $a then "another-answer" else "delivered" end' "$2")
    if jq -e --arg h "$6" --argjson e "$7" '.attempt_id==$h and .episode==$e and .state=="awaiting-answer"' <<<"$stage" >/dev/null; then
        [[ $delivered == answer-recorded || $delivered == delivered ]] && { echo PENDING; return; }
        echo "UNRELATED: still held but the request is $delivered"; return
    fi
    if [[ $delivered == delivered ]] && jq -e --arg h "$6" --argjson e "$7" '.attempt_id==$h and .episode==$e and .state!="exceptional"' <<<"$stage" >/dev/null; then
        echo PENDING; return    # the continuation is committed; its attempt is not admitted yet
    fi
    if jq -e --arg h "$6" --argjson e "$7" '.attempt_id!=$h and .episode==($e+1) and .state!="exceptional" and .state!="awaiting-answer"' <<<"$stage" >/dev/null; then
        [[ $delivered == delivered ]] && { echo CONFIRMED; return; }
        echo "UNRELATED: a new attempt $stage but the request is $delivered"; return
    fi
    echo "UNRELATED: the implementation is $stage and the request is $delivered"
}
