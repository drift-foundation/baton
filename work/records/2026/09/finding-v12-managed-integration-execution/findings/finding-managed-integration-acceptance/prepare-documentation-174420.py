"""Build the selected four-region manual candidate from its retained base."""
from pathlib import Path
import hashlib
import json

record = Path(__file__).resolve().parent
manual = Path('v12/python/DEPLOYMENT.md')
base = (record / 'DEPLOYMENT-base-174271.md').read_bytes()
assert manual.read_bytes() == base
assert hashlib.sha256(base).hexdigest() == '48a3268e456765c02696c897558f1aed9511c39a4188480a8d194b21ac50077f'
text = base.decode()
regions = []

def replace(old, new, name):
    global text
    assert text.count(old) == 1, name
    start = base.index(old.encode())
    regions.append({'name': name, 'base_start': start, 'base_end': start + len(old.encode()), 'replacement': new})
    text = text.replace(old, new)

replace('host composition verification |', 'legacy host or managed preparation/apply verification |', 'host_verification table owner cell')
old = '''`host_verification` bounds the required test the host composition runs directly,
outside any container. This deployment's **Git** deadline stays at its own 300 s
and is never moved by a Job: archiving a revision is this deployment's tooling
over its own repository, and only what runs afterwards is the Job's to bound.'''
new = '''`host_verification` bounds the required test run directly on the host by the
legacy composition, or in the managed preparation/apply execution when that path
is selected. Relocation preserves the original Job's boundary: 300 s by default,
or its explicit `verification_command_seconds`. This deployment's **Git** deadline
stays at its own 300 s and is never moved by a Job: archiving a revision is this
deployment's tooling over its own repository, and only what runs afterwards is
the Job's to bound.'''
replace(old, new, 'host_verification paragraph')
old = '''- **`host_verification`** — the host-side reconciled owners (the causal observer
  and the imported verifier) run the required test under the Job's number,
  resolved through the Job owner. A stage with no Job keeps 300 s.'''
new = '''- **`host_verification`** — the legacy host-side causal observer and imported
  verifier run the required test under the Job's number. Managed preparation
  and private apply carry that same Job-owned boundary to their worker commands:
  300 s by default, with an explicit `verification_command_seconds` override
  resolved through the Job owner. A legacy stage with no Job keeps 300 s.'''
replace(old, new, 'host_verification applied ceiling bullet')
start = text.index('**What an operator cannot do to a host hold.**')
end = text.index('\n\n', start)
old = text[start:end]
new = old.replace('Explicit recovery\n', 'In the legacy direct host\nreconciliation account, explicit recovery\n').replace('A post-import hold has no such\nassignment, because the reconciled branch starts no integration runtime', 'A legacy post-import hold has no such\nassignment, because that direct branch starts no integration runtime').replace('rather than something this Work relabels.', 'rather than something this interface relabels.')
new += ' Managed preparation and apply do have\nordinary attempts and fixed assignments; see [Managed integration](#managed-integration)\nfor their retained cleanup, replay and unresolved-hold boundaries.'
replace(old, new, 'legacy host hold paragraph')
start = text.index('## Managed integration: what exists so far (W161230 slice 1)')
end = text.index('## Runtime-attempt deadlines', start)
old = text[start:end]
capacity = old.index('### Capacity is named, not duplicated')
new = '''## Managed integration

Managed integration carries an ordinary child preparation through retained
candidate custody, independent judgments, private apply and final settlement.
The target repository remains under its local owner's control. A worker answer
alone establishes neither an accepted candidate nor a successful integration.

### Selecting the managed path

Set the boolean `"integration_preparation": true` in the stage-serving document
to select this path. Omission or `false` keeps the direct path; strings such as
`"false"` refuse. The selection requires a serving deployment, its integrator and
configured integration worker, including the actual Authority route/handler and
ordinary runtime, input and output configuration. An already-claimed legacy
parent cannot be converted into a concurrently claimed preparation child.

`v12/worker/Dockerfile.reconciliation` supplies the preparation recipe. It requires
an explicit selected `PROVIDER_BASE` with compatible Python and Git, copies the
ordinary worker and preparation entry/workload, and uses UID/GID 65532 with an
exec-form Python entrypoint. Select a base digest through the deployment's own
qualification process. There is no certified managed-flow image digest supplied
here: configuration selects behavior and does not prove an image is provisioned.

### From preparation to an honest final result

The scheduler reserves one integration actor. The composition registers one root
and planned prepare/apply memberships, commits immutable preparation intent and
creates the child Work with its replay identity. That child receives an ordinary
offer, claim, attempt, fixed assignment and committed admission before runtime
start. The parent's apply remains planned and unclaimed during preparation.

Read-only accepted inputs and the measured immutable request travel through the
ordinary worker boundary. Separate worker and harness processes derive the
combined, base and isolated trees and run the configured causal sequence. The
coordinator does not run the merge or candidate harness. The measured outputs
include the exact derived Git objects and modes needed for later materialization.
An older collection missing that output cannot be repaired by silently rerunning
candidate code on the coordinator.

Positive quiescence, output freeze, accepted intake, retained custody and ordinary
cleanup precede adoption. Adoption binds the retained report, candidate, request,
task, assignment, source and harness; it survives removal of the execution root.
Frozen output alone is insufficient. The child relinquishes its claim before
the parent claims. The retained derived proposal then becomes the subject of
three configured independent `JudgmentExecution` instances with ordinary scoped
receipts. Preparation success does not substitute for these judgments.

After approval and grant-bound admission, managed apply runs the pinned harness
against the approved candidate in a private checkout. The worker receives the
original Job's inputs and limits, with neither a target mount nor Authority
sessions. After the command, the worker checks the same revision, tree and index,
then compares actual file bytes, types and executable modes with the approved
Git objects, including extra or missing files. A clean checkout of another
revision or a change hidden from Git status fails this proof.

Both preparation and private apply preserve the original Job's per-command
`host_verification` default of 300 s and explicit `verification_command_seconds`
override. Relocation does not substitute the distinct `integration_verification`
default of 1800 s or `provider_turn` default of 3600 s. Git tooling retains its
separate deployment deadline of 300 s. Managed commands use a dedicated process
group with bounded termination; signal exits retain the observed shell-compatible
status (128 plus the signal number). Missing status is neither success nor a
command that never ran.

The manager collects and retains apply output and proves cleanup/exclusion. The
local target owner imports verified objects, rechecks the live grant and
atomically updates the configured Git ref together with its exact publication
receipt ref. Coordinator settlement, the Authority integration receipt, lease
release and fenced parent handoff/gate discharge precede root closure and
capacity release. Only that completed owner chain produces a successful final
result. Automatic scheduler release waits for the integration root's ending;
the transactional release guard and quarantine remain in force.

''' + old[capacity:]
fake_start = new.index('**Slice-1 status of that owner.**')
fake_end = new.index('\n\n', fake_start)
new = new[:fake_start] + '''**The local target owner.** The managed composition uses real Git target and
publication-receipt operations. The ref advance and its operation-bound receipt
are one atomic target-side update. Recovery uses that receipt to identify the
effect; a ref pointing at the desired commit is insufficient. Deterministic
qualification exercises this owner against disposable local Git repositories;
it does not certify a remote target backend.''' + new[fake_end:]
limit_start = new.index('### Current limitations, stated plainly')
new = new[:limit_start] + '''### Failure, restart and operator recovery

Reopening replays committed identities and owner evidence. Accepted cutpoints
include retained preparation adoption and derived publication, a target effect
before coordination settlement, an Authority receipt or recorded failure before
root closure, and reopening an already completed result. These continuations
finish the missing owner acts without repeating the target update. A mismatching
request or owner record refuses instead of obtaining replacement identities.

A known failed start with an identified runtime uses the actual manager's
cancellation, fence and failed-start cleanup owners. Membership ends only after
ordinary retained cleanup completes; unfinished teardown remains available for
retry with the root held. Final known preparation failure cancels planned apply
and produces an exceptional parent result without inventing a parent runtime.

A measured apply harness failure retains its report and cleanup evidence. A zero
exit with a changed checkout is also a verification failure; its measured zero
stays zero. The failure owner checks the report against sealed bytes and accepted
custody, binds the actual phase and candidate, and journals the reason. It refuses
its own target entry and releases its lease/capacity without a publication.
Success-dependent gates remain closed; the known apply-failure path preserves
its parent fence and Authority gate rather than reporting a successful handoff.
Forged or non-owned failure reports cannot authorize that settlement.

**Unknown runtime means human inspection is required.** When the initial failed
start identified no runtime, the ordinary sweep reports that a worker may still
exist and that human inspection and cleanup are required. Its action detail names
the exact Job, Work, attempt and start-operation identities, and the current
runtime identity or an explicit unknown. Inspect those identities through the
deployment's authorized owner/runtime surfaces and preserve the report. Unknown
does not mean absent. Restart preserves the report and capacity/apply holds.
Later runtime visibility does not rewrite the original receipt or authorize a
second launch. There is no automatic late-runtime attachment, cleanup convergence
or release command supplied here; human cleanup and subsequent release require
their existing operational authority.

**Uncertain target effects remain held.** The target is blocked with the live
lease and root retained, exact publication/result/attempt identities and a human
inspection instruction. The composition does not issue a second compare-and-swap,
roll back, invent a not-applied receipt or automatically repair the unknown effect.

### Qualification and remaining limits

The complete managed flow is qualified with deterministic providers and engine
simulation at their normal boundaries, real local worker/harness processes,
ordinary disposable Authority/Job/Control owners, retained custody, scoped
judgments and actual disposable Git target/receipt operations. This establishes
the selected local behavior, not actual OCI/runtime, live-provider, image or
remote-backend qualification. Other bounded OCI evidence in this manual retains
its own scope; it does not certify this combined managed flow.

General partial-delivery recovery remains unproved. Expanded adversarial
identity/artifact/custody cases, causal/timeout/limit permutations, two-Job
combinations and uncertain-ending/leader-first/TERM-resistant shutdown coverage
are deferred to v13 and unproved. Existing integrity and cleanup checks remain;
deferral neither passes an omitted case nor fixes a known defect. The selected
evidence is not exhaustive recovery or a suite-wide pass.

'''
replace(old, new, 'whole managed integration section')
regions.sort(key=lambda x: x['base_start'])
rebuilt = bytearray(); cursor = 0
for region in regions:
    rebuilt += base[cursor:region['base_start']] + region['replacement'].encode()
    cursor = region['base_end']
rebuilt += base[cursor:]
assert bytes(rebuilt) == text.encode()
(record / 'regions-174420.json').write_text(json.dumps(regions, indent=2) + '\n')
manual.write_bytes(rebuilt)
print('Applied only the selected manual regions.')
