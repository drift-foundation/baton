#!/usr/bin/env bash
# run-all.sh -- every dry-run scenario of revision 4, each with what it must show. Doubles only.
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

echo "######## A. retained from revision 3: selection, refusal, ordinary endings"
run recovery-ok qualify recovery;                                   expect 0 1 'instance stack stopped \(this run' 'UNRESOLVED'
run deadline-ok qualify deadline;                                   expect 0 1 "engine effects: \[\('pause', 'c-pub'\), \('unpause', 'c-pub'\)\]" 'UNRESOLVED'
run exec-fails qualify recovery '{"exec": "fails"}';                expect 1 1 'an exec failure is not a refusal'
run source-writable qualify recovery '{"exec": "wrote"}';           expect 1 1 'could write into /input/source'
run decoy-recovery qualify recovery "$FOREIGN_DECOY_REV";           expect 1 1 'the reviewer container was not observed' "'exec'"
run decoy-deadline qualify deadline "$FOREIGN_DECOY_PUB";           expect 1 1 'the selected publisher was never observed and frozen' "'pause'"
run wrong-image qualify deadline '{"images": {"publication": "sha256:not-this-runs", "provider": "sha256:fixture"}}'; expect 1 1 'the selected publisher was never observed and frozen' "'pause'"
run live-provider-selected qualify preflight "$LIVE";               expect 1 0 "not this run's Option A selection"
run cleanup qualify cleanup;                                        expect 0 0 'left alone'
START=preexisting run stack-preexisting qualify recovery;           expect 1 0 'STILL RUNNING \(untouched\)' 'WAS STOPPED'
START=fail-clean run start-fails-clean qualify recovery;            expect 1 0 'positively records no live process; nothing to stop'
START=fail-partial run start-fails-partial qualify recovery;        expect 1 1 'instance stack stopped \(this run' 'UNRESOLVED'

echo "######## B. C5.1 -- the start effect is reconciled on every exit (qualify-w385695.sh)"
START=slow-before:4 INTERRUPT_WHEN=evidence/recovery.stack-start-op run q-term-while-start-in-flight qualify recovery
expect 143 1 'instance stack stopped \(this run' 'UNRESOLVED|still alive'
START=slow-after:4 INTERRUPT_WHEN=world/effect run q-term-after-effect-before-answer qualify recovery
expect 143 1 'instance stack stopped \(this run' 'UNRESOLVED|still alive'
INTERRUPT_WHEN=evidence/recovery.stack-started run q-term-after-acknowledgment qualify recovery
expect 143 1 'instance stack stopped \(this run' 'UNRESOLVED|still alive'
GROUP=1 START=slow-after:4 INTERRUPT_WHEN=world/effect run q-group-term-after-effect qualify recovery
expect 143 1 'instance stack stopped \(this run' 'UNRESOLVED|still alive'
START=foreign run q-live-but-not-this-runs qualify recovery;        expect 1 0 "UNRESOLVED: the stack's live process.*are not all this run's start" 'instance stack stopped'
START=ok+corrupt-record run q-ownership-unknown qualify recovery;   expect 1 0 "UNRESOLVED: the instance stack's state could not be established" 'instance stack stopped'
START=ok+status-down run q-status-does-not-answer qualify recovery; expect 1 0 "UNRESOLVED: the instance stack's state could not be established" 'instance stack stopped'
START=unrecorded run q-started-but-unrecorded qualify recovery;     expect 1 0 'UNRESOLVED: process\(es\) this run.s start command started are alive outside'
STOP=refuses run q-stop-does-not-stop qualify recovery;             expect 1 1 'UNRESOLVED: the instance stack was asked to stop and is not positively stopped'

echo "######## C. C5.1 -- the same, option-a-setup.sh failures"
run s-ok setup failures;                                            expect 0 1 'failures: source' 'UNRESOLVED'
PRODUCER_SECONDS=8 run s-producers-never-stop setup failures '{"producers": "never-stop"}'
expect 1 1 'instance stack stopped \(this run' 'UNRESOLVED'
run s-remove-refused setup failures '{"remove": "fails"}';          expect 1 1 'settlement-remove refused producer 1'
START=slow-before:4 INTERRUPT_WHEN=evidence/option-a.stack-start-op run s-term-while-start-in-flight setup failures
expect 143 1 'instance stack stopped \(this run' 'UNRESOLVED|still alive'
START=slow-after:4 INTERRUPT_WHEN=world/effect run s-term-after-effect-before-answer setup failures
expect 143 1 'instance stack stopped \(this run' 'UNRESOLVED|still alive'
INTERRUPT_WHEN=evidence/option-a.stack-started run s-term-after-acknowledgment setup failures
expect 143 1 'instance stack stopped \(this run' 'UNRESOLVED|still alive'
GROUP=1 START=slow-after:4 INTERRUPT_WHEN=world/effect run s-group-term-after-effect setup failures
expect 143 1 'instance stack stopped \(this run' 'UNRESOLVED|still alive'
START=preexisting run s-stack-preexisting setup failures;           expect 1 0 'STILL RUNNING \(untouched\)' 'WAS STOPPED'
START=foreign run s-live-but-not-this-runs setup failures;          expect 1 0 "UNRESOLVED: the stack's live process.*are not all this run's start" 'instance stack stopped'
START=ok+corrupt-record run s-ownership-unknown setup failures;     expect 1 0 "UNRESOLVED: the instance stack's state could not be established" 'instance stack stopped'
STOP=refuses run s-stop-does-not-stop setup failures;               expect 1 2 'nothing is settled under a manager that may be serving'

echo "######## D. C5.2 -- positive absence and not-paused versus an engine that did not answer; requests in flight"
INTERRUPT_WHEN=evidence/deadline.paused run d-term-mid-freeze qualify deadline
expect 143 1 'cleanup: unpaused c-pub \(read back: not paused\)|ended while it was being released' 'UNRESOLVED'
INTERRUPT_WHEN=evidence/deadline.pause-op-done INTERRUPT_DELAY=1 run d-pause-reply-lost qualify deadline '{"pause": "lost-reply"}'
expect 143 1 "\('unpause', 'c-pub'\)" 'UNRESOLVED'
run d-engine-stops-answering qualify deadline '{"engine": "down-after-pause"}'
expect 1 1 'UNRESOLVED: the pause state of c-pub could not be read.*NOT unpaused blind' "'unpause'"
run d-unpause-reply-lost qualify deadline '{"unpause": "lost-reply"}'
expect 1 1 'cleanup: c-pub (positively no longer exists|is positively not paused)' 'UNRESOLVED'
run d-unpause-fails qualify deadline '{"unpause": "fails"}'
expect 1 1 'UNRESOLVED: container c-pub is still paused and could not be released'
run d-unpause-fails-and-readback-fails qualify deadline '{"unpause": "fails-then-down"}'
expect 1 1 'UNRESOLVED: the pause state of c-pub could not be read.*NOT unpaused blind'
INTERRUPT_WHEN=evidence/deadline.pause-op run d-term-while-pause-in-flight qualify deadline '{"pause_seconds": 4}'
expect 143 1 "engine effects: \[\('pause', 'c-pub'\), \('unpause', 'c-pub'\)\]" 'UNRESOLVED'
KILL_WATCHER_WHEN=evidence/deadline.pause-op INTERRUPT=0.5 run d-watcher-killed-while-pause-in-flight qualify deadline '{"pause_seconds": 6}'
expect 143 1 "engine effects: \[\('pause', 'c-pub'\), \('unpause', 'c-pub'\)\]" 'UNRESOLVED'

echo "######## $total scenarios; $bad not as required"
exit "$bad"
