"""Revision 5 (review 2026-11-24T05-49-33Z R1, R2). Each replacement must match exactly once."""
import pathlib
OLD_START = '''  if [ ! -e "$PREFIX.stack-start-op-done" ]; then
    end=$(( $(date +%s) + 3 )); until [ -s "$PREFIX.stack-start-op" ] || [ "$(date +%s)" -ge "$end" ]; do sleep 0.2; done
    if [ -s "$PREFIX.stack-start-op" ]; then
      end=$(( $(date +%s) + 330 )); while op_alive "$PREFIX.stack-start-op" && [ "$(date +%s)" -lt "$end" ]; do sleep 0.2; done
      if op_alive "$PREFIX.stack-start-op"; then
        say "UNRESOLVED: this run's start command ($(cat "$PREFIX.stack-start-op")) has not ended; nothing is stopped under a start in flight; intent retained at $PREFIX.stack-start-intent"
        UNRESOLVED=1; return 0
      fi
    fi
  fi
'''
NEW_START = '''  #    ONLY POSITIVE EVIDENCE ENDS THIS STEP: the completion record; or the command's own record with that
  #    process positively ended; or THIS invocation knowing it wrote the intent and never forked. An intent with
  #    no readable record of its command proves nothing about a command that may yet act -- waiting is not
  #    proof -- so it stays UNRESOLVED, retained, and no new start is made over it.
  if [ ! -e "$PREFIX.stack-start-op-done" ]; then
    if [ "${STACK_START_STAGE:-}" = intent-only ]; then
      echo never-launched > "$PREFIX.stack-start-op-done"
    else
      end=$(( $(date +%s) + 3 )); until op_recorded "$PREFIX.stack-start-op" || [ "$(date +%s)" -ge "$end" ]; do sleep 0.2; done
      if ! op_recorded "$PREFIX.stack-start-op"; then
        say "UNRESOLVED: the start intent has no readable record of its start command ($PREFIX.stack-start-op), so it is not known to have ended or never begun; nothing was reconciled; intent retained at $PREFIX.stack-start-intent"
        UNRESOLVED=1; return 0
      fi
      end=$(( $(date +%s) + 330 )); while op_alive "$PREFIX.stack-start-op" && [ "$(date +%s)" -lt "$end" ]; do sleep 0.2; done
      if op_alive "$PREFIX.stack-start-op"; then
        say "UNRESOLVED: this run's start command ($(cat "$PREFIX.stack-start-op")) has not ended; nothing is stopped under a start in flight; intent retained at $PREFIX.stack-start-intent"
        UNRESOLVED=1; return 0
      fi
    fi
  fi
'''
OP_ALIVE_OLD = '''op_alive() {  # FILE holding "pid start-tick" -> success while THAT process (pid AND start time) has not ended
'''
OP_ALIVE_NEW = '''op_recorded() {  # FILE -> success only for a readable record of exactly "pid start-tick", both numbers
  local pid tick rest
  read -r pid tick rest < "$1" 2>/dev/null || return 1
  case "$pid:$tick:$rest" in *[!0-9:]*|:*|*::*) return 1;; esac
  [ -z "$rest" ]
}
op_alive() {  # FILE holding "pid start-tick" -> success while THAT process (pid AND start time) has not ended
'''
COMMON = [
    (OLD_START, NEW_START), (OP_ALIVE_OLD, OP_ALIVE_NEW),
    ('''  echo "$token" > "$PREFIX.stack-start-intent"
''', '''  echo "$token" > "$PREFIX.stack-start-intent"; STACK_START_STAGE=intent-only
  STACK_START_STAGE=launched            # set BEFORE the fork: only the one step above is "intent and no command"
'''),
]
def edit(path, pairs):
    p = pathlib.Path(path); s = p.read_text()
    for old, new in pairs:
        assert s.count(old) == 1, (path, s.count(old), old[:70]); s = s.replace(old, new)
    p.write_text(s)
edit("option-a-setup.sh", COMMON)
edit("qualify-w385695.sh", COMMON + [
    ("revision 4 (reviews 2026-11-24T01-52-00Z, T03-03-48Z and T04-42-16Z, C5).", "revision 5 (reviews 2026-11-24T01-52-00Z, T03-03-48Z, T04-42-16Z and T05-49-33Z, C5)."),
    ('''  local id seen="" state end
''', '''  local id seen="" state end open=""
'''),
    ('''    end=$(( $(date +%s) + 3 )); until [ -s "$PREFIX.pause-op" ] || [ "$(date +%s)" -ge "$end" ]; do sleep 0.2; done
    if [ -s "$PREFIX.pause-op" ]; then
      end=$(( $(date +%s) + ${ENGINE_SECONDS:-60} + 20 )); while op_alive "$PREFIX.pause-op" && [ "$(date +%s)" -lt "$end" ]; do sleep 0.2; done
      if op_alive "$PREFIX.pause-op"; then
        say "UNRESOLVED: the pause request ($(cat "$PREFIX.pause-op")) has not ended; the selected container may yet be paused; intent retained at $PREFIX.pause-intent"
        UNRESOLVED=1
      fi
    fi
''', '''    end=$(( $(date +%s) + 3 )); until op_recorded "$PREFIX.pause-op" || [ "$(date +%s)" -ge "$end" ]; do sleep 0.2; done
    if ! op_recorded "$PREFIX.pause-op"; then
      # NO READABLE RECORD OF THE REQUEST IS NOT PROOF THERE WAS NONE. What is paused now is still released
      # below; the intent stays, because a request that has not yet recorded itself may pause afterwards.
      say "UNRESOLVED: the pause intent has no readable record of its request ($PREFIX.pause-op), so the request is not known to have ended or never begun; the selected container may yet be paused; intent retained at $PREFIX.pause-intent"
      UNRESOLVED=1; open=1
    else
      end=$(( $(date +%s) + ${ENGINE_SECONDS:-60} + 20 )); while op_alive "$PREFIX.pause-op" && [ "$(date +%s)" -lt "$end" ]; do sleep 0.2; done
      if op_alive "$PREFIX.pause-op"; then
        say "UNRESOLVED: the pause request ($(cat "$PREFIX.pause-op")) has not ended; the selected container may yet be paused; intent retained at $PREFIX.pause-intent"
        UNRESOLVED=1; open=1
      fi
    fi
'''),
    ('''          true) say "UNRESOLVED: container $id is still paused and could not be released; intent retained at $PREFIX.pause-intent"; UNRESOLVED=1;;
          *) say "UNRESOLVED: container $id was paused and its release could not be read back; intent retained at $PREFIX.pause-intent"; UNRESOLVED=1;;
''', '''          true) say "UNRESOLVED: container $id is still paused and could not be released; intent retained at $PREFIX.pause-intent"; UNRESOLVED=1; open=1;;
          *) say "UNRESOLVED: container $id was paused and its release could not be read back; intent retained at $PREFIX.pause-intent"; UNRESOLVED=1; open=1;;
'''),
    ('''it was NOT unpaused blind; intent retained at $PREFIX.pause-intent"; UNRESOLVED=1;;
    esac
  done
}
''', '''it was NOT unpaused blind; intent retained at $PREFIX.pause-intent"; UNRESOLVED=1; open=1;;
    esac
  done
  # A PAUSE POSITIVELY SETTLED IS FILED AS THAT; one that is not keeps its intent, and `deadline` refuses over it.
  if [ -z "$open" ] && [ -e "$PREFIX.pause-intent" ]; then mv -f "$PREFIX.pause-intent" "$PREFIX.pause-reconciled"; fi
}
'''),
    ('''  : "${JOB2:?}" "${STAGE2:?}" "${EPISODE2:?}" "${DECISION2:?}"; stores
''', '''  : "${JOB2:?}" "${STAGE2:?}" "${EPISODE2:?}" "${DECISION2:?}"; stores
  [ ! -e "$PREFIX.pause-intent" ] || fail "an earlier pause of this phase is not reconciled ($PREFIX.pause-intent); it is reconciled now and nothing new is frozen over it"
'''),
    ('''    else say "UNRESOLVED: $tag could not be removed (in use?); see $PREFIX.cleanup.log"; fi
''', '''    else say "UNRESOLVED: $tag could not be removed (in use?); it stays recorded in images.owned as $id and is not forced; see $PREFIX.cleanup.log"; UNRESOLVED=1; fi
'''),
])
