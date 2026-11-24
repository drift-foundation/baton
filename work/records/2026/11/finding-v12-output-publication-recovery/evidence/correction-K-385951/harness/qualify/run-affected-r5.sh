#!/usr/bin/env bash
# run-affected-r5.sh -- ONLY the scenarios whose path the revision-5 edits touch; the 40-scenario matrix is not repeated.
#   expect EXIT STOPS-ASKED 'regex that must appear' ['regex that must NOT appear']  -- applied to the scenario just run
set -u
H="$(dirname "$(realpath "$0")")"
export RUNS="${RUNS:-$(dirname "$H")/runs}"
S="$H/scenario.sh"; bad=0; total=0
run() { OUT="$("$S" "$@" 2>&1)"; printf '%s\n' "$OUT"; }
expect() {
  total=$((total + 1)); local why=""
  printf '%s\n' "$OUT" | grep -q "^== .*: exit $1\$" || why="$why exit-not-$1"
  printf '%s\n' "$OUT" | grep -q "stops asked: $2\$" || why="$why stops-not-$2"
  printf '%s\n' "$OUT" | grep -Eq "$3" || why="$why missing:[$3]"
  if [ -n "${4:-}" ] && printf '%s\n' "$OUT" | grep -Eq "$4"; then why="$why present:[$4]"; fi
  if [ -z "$why" ]; then echo "   AS REQUIRED"; else echo "   NOT AS REQUIRED:$why"; bad=$((bad + 1)); fi
}
FOREIGN_DECOY_REV='{"foreign": {"c-decoy": ["attempt-rev", "sha256:fixture", ["/srv/other-instance/storage/y/in"]], "c-foreign-pub": ["attempt-other-pub", "sha256:pub", ["/srv/other/out"]]}}'
FOREIGN_DECOY_PUB='{"foreign": {"c-decoy": ["attempt-pub", "sha256:pub", ["/srv/other-instance/storage/x/out"]]}}'
LIVE='{"workers": [{"worker_id": "qualify-impl", "role": "implementation", "deployment": {"image_digest": "sha256:prov"}}, {"worker_id": "qualify-review", "role": "review", "deployment": {"image_digest": "sha256:fixture"}}, {"worker_id": "qualify-publisher", "role": "publication", "deployment": {"image_digest": "sha256:pub"}}]}'
export RUNS="$(dirname "$H")/runs-r5"
run recovery-ok qualify recovery;                                   expect 0 1 'instance stack stopped \(this run' 'UNRESOLVED'
run deadline-ok qualify deadline;                                   expect 0 1 "engine effects: \[\('pause', 'c-pub'\), \('unpause', 'c-pub'\)\]" 'UNRESOLVED'
run cleanup qualify cleanup;                                        expect 0 0 'left alone' 'UNRESOLVED'
START=slow-before:4 INTERRUPT_WHEN=evidence/recovery.stack-start-op run q-term-while-start-in-flight qualify recovery
expect 143 1 'instance stack stopped \(this run' 'UNRESOLVED|still alive'
START=slow-before:4 INTERRUPT_WHEN=evidence/option-a.stack-start-op run s-term-while-start-in-flight setup failures
expect 143 1 'instance stack stopped \(this run' 'UNRESOLVED|still alive'
INTERRUPT_WHEN=evidence/deadline.paused run d-term-mid-freeze qualify deadline
expect 143 1 'cleanup: unpaused c-pub \(read back: not paused\)|ended while it was being released' 'UNRESOLVED'
INTERRUPT_WHEN=evidence/deadline.pause-op-done INTERRUPT_DELAY=1 run d-pause-reply-lost qualify deadline '{"pause": "lost-reply"}'
expect 143 1 "\('unpause', 'c-pub'\)" 'UNRESOLVED'
INTERRUPT_WHEN=evidence/deadline.pause-op run d-term-while-pause-in-flight qualify deadline '{"pause_seconds": 4}'
expect 143 1 "engine effects: \[\('pause', 'c-pub'\), \('unpause', 'c-pub'\)\]" 'UNRESOLVED'
KILL_WATCHER_WHEN=evidence/deadline.pause-op INTERRUPT=0.5 run d-watcher-killed-while-pause-in-flight qualify deadline '{"pause_seconds": 6}'
expect 143 1 "engine effects: \[\('pause', 'c-pub'\), \('unpause', 'c-pub'\)\]" 'UNRESOLVED'
echo "######## $total scenarios; $bad not as required"; exit "$bad"
