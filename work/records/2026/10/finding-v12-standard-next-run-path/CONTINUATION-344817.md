# Dispatch/admission correction for independent review

Author baton.codxpc claim344817; scope review344790/pass344814, owner exception
344614 unchanged. Exact twelve-path candidate-344817/ and CANDIDATE-344817.json
SHA256 8f4c18293b454d7ba5e1f3fc1a995be153dacaea98881ffa39620273bbb4e46a.
Baseline BASELINE-344617.json; previous candidate344698 and all history retained.
Live isolated source remains /tmp/baton-next-run-344617. No main product edits.

## Corrections

Host.dispatch now uses dispatch_environment: a newly built environment supplies
only installed code/src and code as PYTHONPATH for fresh manager children. Initial
-I boot still inserts those roots explicitly; actual controller Process children
inherit the fixed roots. Caller PYTHONPATH/PYTHONHOME are never copied, user-site
imports and bytecode writes are disabled, and cwd remains protected installed code.
No caller-selected interpreter, source or configuration operand was introduced.

Host.admission now emits exactly one literal argument rule: installed entry.py
request. No wildcard, run identity, script/interpreter operand or per-run sudoers
change. The new unprivileged installed client.py converts prepare/check/start/status
into bounded JSON on stdin to that same exact sudo argv. Protected receiver parses
independently: only action/task or action/run shapes, fixed action set, bounded
run grammar, no duplicate members/extra keys, maximum1MiB. It rejects direct old
entry argument forms and unsafe operands before constructing the broker. Public
client input is not trusted. Operator installation stays a separate source-only
command not admitted by the managed sudo rule. Generated commands and candidate
user documentation now name the client interface. Installer captures and binds the
client bytes with the rest of its reviewed payload.

Changed this episode: tools/next_run_managed.py, new tools/next_run_client.py,
tests/tools/test_next_run_managed.py and NEXT-RUN.md. Other cumulative paths are
unchanged from344698. No existing test expectation weakened. Three new tests cover
fresh process/environment, literal admission/request dispatch, and unsafe requests.

## Evidence and limits

The fresh-child test uses the actual enforcement Process class to Popen a fresh
interpreter with the production -m tools.authoring_enforcement command under the
fixed dispatch environment from an isolated parent. --help establishes imports
without entering manager/store/engine execution. A separate fresh child under the
same environment reads the real packet, verifies installed source locations and
supervisor/controller/helper digests, and prints its installed controller path.
Removing PYTHONPATH reproduces ModuleNotFoundError baton_v12. Poison caller Python
settings and a HOME user-site sitecustomize do not execute. Prior drift/foreign
import and custody/refusal tests remain.

The selected /usr/sbin/visudo0.2.8 parses the new literal rule successfully. Actual
request parsing routes all four operations through real broker methods; start's
engine/dispatch remain substituted. Client subprocess inspection proves all four
operations send exactly the same sudo executable/entry/request operands. Unsafe
payload/argument cases refuse before broker access. Literal argument matching is
the mechanism already independently accepted for this sudo-rs deployment:
findings/finding-managed-controller-boundary/review-2026-10-21T00-46-29Z.md,
operator343603 and managed343612 receipts. Dynamic input now lives entirely outside
that argument matcher. No claim visudo syntax alone proves live authorization.

Operational limit: a read-only /usr/bin/sudo --version attempt in this managed
environment exits1 with "sudo must be owned by uid 0 and have the setuid bit set".
No policy/setuid repair or privilege bypass attempted. dpkg reports sudo-rs
0.2.8-1ubuntu5.3. No new host policy was installed or effectively exercised; the
admission evidence combines accepted historical literal matching, current real
parser syntax and current protected request semantics. A new deployment still
needs its separately selected actual admission receipt. Do not call this a live
sudo success or installation proof.

Tests, measured unittest durations:
-12 managed tests4.410s pass.
-56 combined next-run/managed/authoring-enforcement tests12.093s pass; raw command,
 stdout/stderr and process wall12.458084686s in evidence/verification-344817.json.
-Final12 managed tests4.311s pass after disabling user-site imports and adding
 poison-HOME/caller-environment coverage; raw evidence/verification-344817-final.json,
 process wall4.657222619s, timeout60s. Combined timeout90s. No skips reported.

This claim20.814s unittest; prior58.039s; cumulative78.853s. Process clocks retained separately and not added. Reviewer
import probe0.046518665s remains reviewer evidence. Earlier preparation/failed-start
and child accounting remain in prior continuations; editing/reading elapsed unknown.
No existing store/credential/account/sudoers/installed-file/main-product mutation,
engine/provider execution, Git mutation or actual privileged installation occurred.
Only isolated fixture stores/credentials and an unprivileged Landlock child ran.

## Remaining scope

Review this dispatch/admission correction; full independent product acceptance is
not claimed and exception344614 remains active. Current PLAN still owns safe
consumed-failure continuation after positive cessation/fencing with fresh allocation
and all old receipts retained, then two real-owner deterministic substantive-work
flows plus failed-start recovery and honest <=60s timing. Import-only/substituted
dispatch evidence establishes none of that later acceptance. Continue directly in
the isolated copy after review, without a generic owner permission/preparation gate.
No old v3 arm/start, candidate integration or host deployment is authorized here.
