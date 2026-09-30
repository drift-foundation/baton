# The connected packet proof — actual partial harness and the exact next read

W236087 claim 310021, superseding CONNECTED-NEXT-309960.md.

## The reviewer disproved my last diagnosis; here is what it really was

Review 2026-09-29T22-44-32Z: `mounted` succeeded, and the failure was inside the
INHERITED provider-turn helper at `test_stage_execution.py:4160`. That helper
adopts its delivery with `launch.adopt(self.config['launch_home'], ...,
contract=self.config['launch_contract'], ...)`. `ConnectedPacket` replaced
`self.configuration` and `self.submission` and LEFT `self.config` alone, so the
helper looked in the OLD fixture launch root while the generated worker writes
under the packet instance's own. `adopt` found nothing and answered None.

FIXED BY MAKING THE FIXTURE'S OPERAND MAP COHERENT with the document the run is
composed from: `adopt_generated_worker` copies the named operands from the
GENERATED producer worker into `self.config` and creates the launch and
credential roots the generated document names. No delivery is fabricated, no
launch evidence is copied, no sweep is added and the manager is untouched; the
real `launch.adopt` and the real `serve_exchange` still run.

## What the connected run now reaches — and it is a long way further

    admissions        {'implementation': 1, 'review': 0}
    receipts          admit PERFORMED, claim PERFORMED, no refusal
    runtime           runtime-single-1, launched, then DESTROYED
    cleanup           'retained' -- POSITIVE cleanup, with the engine answering
                      that the identity does not exist
    provider          THE REAL SCRIPTED CHILD RAN, argv ['claude', '--print',
                      '--dangerously-skip-permissions', '--output-format',
                      'json', '--model', ...] carrying THIS PACKET'S OWN TASK
                      TEXT ("Write docs/v12-context-correction.md -- an operator
                      guide for the managed context-correction workflow...")
    stage states      implementation 'exceptional', review 'blocked'
    stopped           'exceptional'  (a terminal state, not a crash)
    serving_failure   None
    verdict           None -- no review invocation happened

So the packet's generated composition admits, claims, launches, runs a real
provider turn on its own task, and reaches positive cleanup for the runtime it
started. That is the connected path working end to end up to the ending.

## The exact command

    cd /home/sl/src/baton/work/records/2026/09/finding-v12-managed-session-resume
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/home/sl/src/baton/v12/python/src:/home/sl/src/baton/v12/python \
    /home/sl/.local/state/baton-v12-venv/bin/python -B -c \
      "import connected_packet_trace as c
       w = c.ConnectedPacket(); w.setUp()
       try:
           held, outcome = w.run_packet(dispositions=['accepted'])
           print(outcome['stopped'], outcome['stage_states'])
       finally:
           w.doCleanups()"

## The one open question, with the canonical evidence already read

The implementation stage is `exceptional` while its episode carries NO
`ended_state`, its receipts show `admit` and `claim` both `performed` with no
refusal, and its runtime is destroyed with `retained` cleanup. `projection` makes
a stage with a live episode `exceptional` on exactly three further conditions: a
settled `managed_failure`, a `refused` receipt, or a recorded
`start_failure`/`preparation_failure`. The receipts rule out the second and the
runtime facts make a failed start unlikely, so the next read is the settled
managed failure and the two failure members of the observation, for THIS attempt,
BEFORE the shutdown closes the gate.

The likely subject is the ENDING contract rather than the launch: the worker's
result has to satisfy the declared output and test scope, and this packet declares
`test_scope: ['docs/v12-context-correction.md']` with a verification command of
its own. Those are packet/fixture facts to check next, in that order. No scheduler
change, no extra sweep, no raised limit.

## What has NOT been reached

No review invocation, so no canonical attachment or verdict; no context save and
no restore. The second (review) attempt identity has `cleanup: null` -- the
manager holds no runtime for it, which is correct because it never launched, and
the supervisor reports it as cleanup it cannot prove. That distinction is the one
review 2026-09-29T22-36-24Z asked to be preserved, and it is visible in the
outcome.

## Honest boundaries of this fixture, unchanged

`ConnectedPacket.serving` performs the packet's preparation with INDIVIDUAL real
owner API calls rather than invoking `baseline.prepare` itself; the acts are real
and the grant is minted in disposable stores only. `tools.bootstrap` is not run:
the two instance facts `bind` reads are written by the fixture. The engine is the
accepted fixture's in-process one, the provider is a scripted child, and the
reviewer's dispositions are scripted and committed through the real
`review_cycles` owner API. All labelled simulated.
