# Proposed bounded stats-observation correction — 2026-09-11T14:52:15Z

Owning Work W71879; research by baton.codex claim145165 for owner145162 disposition.
Evidence and failed outcome: review-2026-09-11T14-52-15Z.md. This is a concrete proposal, not an
implementation or another-model-run authorization. The owning FINDING records
this runner defect before any workaround or correction.

1. Produce a new immutable helper candidate, preserving prepared-144859 and all
   three failed runs. Product protocol/application/image/task behavior stays
   unchanged. The primary change is the stats call in the proof runner and its
   focused dossier tests. Scope any fresh packaging/identity operands separately
   in the concrete handoff; never reuse a submitted run root or erase history.
2. Isolate stats collection from the strict general command helper. Make one
   bounded stats call for the exact IDs from that iteration's already-authorized
   inspect rows; no per-sample retry, backoff, extra model or Docker mutation.
   Preserve the current maximum10-second command timeout and the independently
   armed earlier absolute wall/claim deadline. Nonzero return, including EOF,
   and subprocess.TimeoutExpired become an explicit unavailable observation.
   Do not catch BaseException, generic Exception or OSError: the runner's alarm
   raises built-in TimeoutError, which is an OSError subclass and MUST propagate
   to deadline containment. A missing engine executable or programming error
   is not an observation to silently swallow.
3. Retain an observation object with state available/unavailable/not-requested,
   requested IDs, start/end time or elapsed duration, exit code or typed timeout,
   bounded stdout/stderr and explicit truncation indicators where needed. Preserve
   successful raw stats and partial output as evidence; never manufacture zeros,
   substitute a previous sample or call an absent row a measurement. Empty output
   for requested IDs is unavailable; no IDs means not-requested. Write/flush the
   same iteration's claims/status/runtime/cap/storage observations even if stats
   is unavailable. Final evidence reports the number and locators of gaps, and
   cannot claim complete observed utilization coverage.
4. Preserve strict behavior for required Docker ps/inspect/authority-label checks,
   public status/claim observations, missing claim timestamps and all actual
   command failures outside stats. Preserve2CPU/2GiB/512PID enforced engine caps,
   host capacity checks,16GiB retained-storage stop and1200/240/180/120 deadlines
   (including B judges within integration120). Stats telemetry is not the cap
   enforcer. Do not remove or reset any independent guard, timer, final tests,
   custody/authorization check or both-terminal condition. Continuing with a
   telemetry gap is never proof of lifecycle completion or resource usage.
5. Add focused offline tests: successful stats retained; nonzero EOF records an
   unavailable gap and flushes surrounding observations while serving continues;
   no IDs is not-requested; requested empty output and subprocess timeout retain
   unavailable status; a built-in deadline TimeoutError still propagates and
   causes containment; required status/inspect/label/storage failures remain
   fatal; no timer/budget reset or automatic stats retry; incomplete Jobs remain
   incomplete while terminal acceptance still requires all existing gates.
   Use injected subprocess/clock/fake owner responses only in unit fixtures,
   never fabricated live review/runtime/terminal evidence. Test paths and reasons
   belong in the implementation handoff under W71830 standing authority.

Acceptance is a small offline-tested candidate with independent digest-bound
review and exact execution-package implications. No actual run, root repair,
deletion, deadline increase, persistent daemon outage recovery, inspect-race
repair, monitoring redesign or provider probe is part of this correction.
W144813/W144335/authentication UX/fault-C/stronger monitoring remain deferred.
The owner must separately authorize any further model attempt on a reviewed
fresh package. Carry all three spent runs and costs; do not reset reserves.
