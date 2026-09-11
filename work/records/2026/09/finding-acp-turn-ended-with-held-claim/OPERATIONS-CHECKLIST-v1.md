# External-terminal checklist — W133361

Owner acceptance133489 authorizes this sequence only after independent review
and all CORRECTION-RECOVERY-v1.md preconditions pass. This checklist is prepared,
not executed. Commands below name the human operator baton.slaw; the reviewer
does not run them or impersonate that participant. Execute each command as one
standalone request from an external terminal, never from the managed backend
which the lifecycle stop will terminate. Retain command output and elapsed
wall time in an append-only operations receipt under this dossier.90s operations
verification is separate from15s author/15s review and from every P allocation.

## Review inputs the tuner must produce

Under this dossier's `evidence/author/`:

- `baton.next.json`: full candidate rendered from the exact observed live config;
  only generation8 to9 and the approved impl instruction append differ.
- `manifest.json`: config base/candidate SHA256, exact candidate byte size,
  two policy file base/candidate hashes, path/mode set and measured author checks.
- Retained two-file policy diff and before bytes, and exact validation results.

The live config remains unchanged during authorship. The newest independent
review must explicitly bind these actual outputs and the policy bytes. A
candidate pathname without the review's digest is not authority. Review also
checks this checklist before approving recovery. If these files are missing or
review is not signed off, stop before the first mutation below.

## 1. Preflight and drain

Working directory for filesystem/lifecycle commands:

```sh
cd /home/sl/src/baton
```

Read the signed review, its author manifest, current FINDING/PLAN and the P
preservation manifest. Compare reviewed policy bytes/modes, source config base
and config candidate digest; refuse any unreviewed delta. Inspect the current
infra lifecycle manifest through the supported status command, ensuring the
external terminal can execute both stop and start before beginning recovery.

```sh
just status /home/sl/baton-v11.14aecfb
```

```sh
/home/sl/opt/baton/v11/0650c61/bin/baton --config /home/sl/baton-v11.14aecfb/baton.json --participant baton.slaw detail work=W133117
```

```sh
/home/sl/opt/baton/v11/0650c61/bin/baton --config /home/sl/baton-v11.14aecfb/baton.json --participant baton.slaw runtime
```

```sh
/home/sl/opt/baton/v11/0650c61/bin/baton --config /home/sl/baton-v11.14aecfb/baton.json --participant baton.slaw incidents include-dismissed=true
```

Confirm exact orphan identity and settled execution domain; do not infer absent
delegated resources solely from a failed state or kill a guessed PID. If current
implementation/dossier bytes advanced, refresh preservation evidence under
actual custody, with the full cumulative spending record, before proceeding.
Never restore the older preservation snapshot. Resolve unrelated active Work
by normal handoff and relinquish any operational Work claim before expecting
paused dispatch. The human operator's deployment control is not a second
managed readiness consumer or an excuse for an agent to execute unclaimed Work.

```sh
/home/sl/opt/baton/v11/0650c61/bin/baton --config /home/sl/baton-v11.14aecfb/baton.json --participant baton.slaw drain
```

```sh
/home/sl/opt/baton/v11/0650c61/bin/baton --config /home/sl/baton-v11.14aecfb/baton.json --participant baton.slaw dispatch
```

## 2. Recover only the reviewed orphan

Re-read W133117 immediately before release. The following exact command is
valid only while claim133353, episode133349 and baton.claude are still current,
the domain is settled, the review passed and dispatch is draining/paused. A
mismatch invalidates this command; do not simply substitute newer operands.

```sh
/home/sl/opt/baton/v11/0650c61/bin/baton --config /home/sl/baton-v11.14aecfb/baton.json --participant baton.slaw release work=W133117 expect=baton.claude episode=133349 reason='W133361 owner133489: independently reviewed correction and external recovery ready; domain settled; preserve P bytes, evidence and all cumulative spending under the reviewed preservation manifest. Release exact orphan for corrected delivery under drained dispatch.'
```

```sh
/home/sl/opt/baton/v11/0650c61/bin/baton --config /home/sl/baton-v11.14aecfb/baton.json --participant baton.slaw dispatch
```

Require `paused` with no blocking claims. If another claim prevents it, that
holder must resolve its Work normally. Do not stop its runtime to force pause.

## 3. Apply and accept the reviewed config

Only after reviewing the actual candidate and checking its digests, copy its
content over the live file using the following bounded command. It validates
the original proposal base, exact approved JSON change and a regular,
owner-writable live file before writing; existing live file mode is preserved.
The prior independent review's candidate digest must also have been checked
against `evidence/author/manifest.json` above. This command does not regenerate
or repair a candidate. If any check fails, stop and retain the error.

```sh
python3 - <<'PY'
import hashlib, json, os, stat
from pathlib import Path
record = Path('/home/sl/src/baton/work/records/2026/09/finding-acp-turn-ended-with-held-claim')
proposal = json.loads((record / 'evidence/config-change-proposal.json').read_text())
target = Path('/home/sl/baton-v11.14aecfb/baton.json')
candidate = record / 'evidence/author/baton.next.json'
info = target.lstat()
assert stat.S_ISREG(info.st_mode) and info.st_mode & stat.S_IWUSR
before = target.read_bytes()
assert hashlib.sha256(before).hexdigest() == proposal['source_sha256']
expected = json.loads(before)
generation, instruction = proposal['changes']
assert expected['generation'] == generation['before']
assert expected['teams']['baton']['roles']['impl']['instructions'] == instruction['before']
expected['generation'] = generation['after']
expected['teams']['baton']['roles']['impl']['instructions'] = instruction['after']
after = candidate.read_bytes()
assert json.loads(after) == expected
with target.open('r+b') as stream:
    opened = os.fstat(stream.fileno())
    assert (opened.st_dev, opened.st_ino) == (info.st_dev, info.st_ino)
    assert stream.read() == before
    stream.seek(0)
    stream.write(after)
    stream.truncate()
    stream.flush()
    os.fsync(stream.fileno())
assert target.read_bytes() == after
assert stat.S_IMODE(target.stat().st_mode) == stat.S_IMODE(info.st_mode)
print('Reviewed config bytes applied; canonical acceptance still required.')
PY
```

```sh
/home/sl/opt/baton/v11/0650c61/bin/baton --config /home/sl/baton-v11.14aecfb/baton.json --participant baton.slaw regen
```

If regen refuses, preserve the exact output and stop before restart/resume.
No SQL, guessed generation, unrelated config edit or implicit rollback. A
fresh approved correction is needed if the baseline changed.

## 4. Replace the lifecycle set, verify, then resume

Run these separately, in order, from the prepared external terminal. Confirm
successful stop before start; a partial stop requires exact operator disposition,
not an untracked process kill. Once the service set is stopped, restore it
through the supported start path even if that safety-critical completion takes
longer than the remaining estimate; record any overrun and run no further
verification without owner disposition. Never use the budget as a kill timer.

```sh
just stop /home/sl/baton-v11.14aecfb
```

```sh
just start /home/sl/baton-v11.14aecfb
```

```sh
just status /home/sl/baton-v11.14aecfb
```

Check canonical `dispatch` still paused; full service health and exact current
runtime/config identities; unchanged foreground-task flag and7200000ms deadline;
P files/modes/evidence still equal the reviewed preservation snapshot. Retain
the new runtime/session identifiers and configuration acceptance sequence.
Do not resume on partial health, file drift, missing instruction acceptance or
unresolved budget overrun. When every check passes:

```sh
/home/sl/opt/baton/v11/0650c61/bin/baton --config /home/sl/baton-v11.14aecfb/baton.json --participant baton.slaw resume
```

## 5. Observe actual delivery and custody completion

Retain the first corrected managed prompt, showing the exact approved append
and canonical launcher contract. Retain actual public tool results proving
current handoff and T133117/M133314 discussion reads after successful P claim.
The author must reconcile and retain all P run history before new verification;
latest2.54s/77s is an author report, not a fresh allocation. P review remains8s.

Observe a canonical P pass/return preceding the final response. Use `detail
work=W133117` and `work-events work=W133117 newest=true limit=20` with the same
explicit operator CLI prefix to correlate the new claim and handoff. A plain
final summary, seen marker, config diff or prompt delivery alone is insufficient.
If P needs more work, a correctly evidenced incomplete return is an acceptable
behavioral proof; it is not product completion. No extra product test is
commissioned by this checklist. A recurrence remains a failure for owner
disposition; do not release/restart again automatically or dismiss incidents
before the required proof. Record the complete operations receipt and return
the result for independent confirmation/owner closure.
