# The connected packet proof — actual partial harness and the exact next read

W236087 claim 310127, superseding CONNECTED-NEXT-310076.md.

## Two corrections to my own record, from the reviewer's captured child error

1. MY STDOUT-NONE HYPOTHESIS WAS WRONG. The active provider is
   `correction_restart_trace.World.provider`, a real subprocess, not the generic
   stub I guessed at.
2. THE `_context_execution` RESTORATION DID NOT FIX THE CHILD ERROR, and I am not
   claiming it did. It is still the right seam for a SESSION profile -- the
   substitution is what a restore needs -- but it was not what made the turn fail.

The actual cause, captured by the reviewer: `FileNotFoundError` writing
`docs/v12-context-correction.md` because the `docs` parent did not exist in the
candidate. The child exited 1 BEFORE emitting terminal JSON, and the adapter then
correctly reported the context terminal identity as unproved.

## Fixed: the simulated provider's edit boundary

This packet's task names a file in a SUBDIRECTORY, and that is the point of it --
`docs/v12-context-correction.md` is where an operator guide belongs. A real
provider creates the directory it writes into; the SIMULATED one this fixture
scripts did not. `ConnectedPacket.provider` now creates the parents and changes
nothing else: the proposal is still authored by the provider writing into the
candidate, the real version-control child still runs, the task's own verification
command still runs, and no identity or receipt check is touched.

## What that moved, measured

    BEFORE   implementation 'exceptional'; frozen output 'unable'; proposal
             'provider-failed' / 'start-error' / status 1
    NOW      implementation 'answering'; the provider turn SUCCEEDS
    progression  offered -> waiting -> answering, and then no further change
    receipts     admit PERFORMED, claim PERFORMED
    exchange     null in the projection
    stopped      'serving-failed' -- my own scenario guard, "the scenario did not
                 converge", after the hook's 90 steps with the state unchanged

`CONNECTED-EVIDENCE-310127.json` retains the progression, the canonical stage
observation, the receipts, the cleanup and the counts.

## The exact next read

The stage sits at `answering` and does not leave it. `answering` is the state
between the worker being asked and the manager observing a terminal exchange, and
the projection's `exchange` member is NULL -- so this control plane holds no
exchange read for the attempt. The next step is to establish whether the worker's
terminal EVENT was written where the manager looks for it, and whether the
ordinary sweep is reaching the observation at all:

    * read `exchange.observation` for this attempt directly, before the shutdown;
    * compare the event and command roots the adopted delivery names against the
      ones `serve_exchange` was given by the inherited helper;
    * check whether the accepted World's own `tick` does anything functional that
      `serve`'s sweep does not -- it wraps `exchange.observation` to REMEMBER
      terminal observations "before ordinary cleanup discards delivery files",
      which is diagnostic, but the discarding is the part worth checking.

NOT to be done: raising the scenario guard to see if it converges later, adding
sweeps, or changing the manager. The guard tripping is a symptom; the state is
unchanged across all 90 steps, so waiting longer answers nothing.

## The exact command

    cd /home/sl/src/baton/work/records/2026/09/finding-v12-managed-session-resume
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/home/sl/src/baton/v12/python/src:/home/sl/src/baton/v12/python \
    /home/sl/.local/state/baton-v12-venv/bin/python -B -c \
      "import connected_packet_trace as c
       w = c.ConnectedPacket(); w.setUp()
       try:
           held, outcome = w.run_packet(dispositions=['accepted'])
           print(outcome['stopped'], outcome['serving_failure'], w.stage_states)
       finally:
           w.doCleanups()"

## What has NOT been reached

No stage completion, no review invocation, no canonical verdict, no context save
and no restore. The provider turn now SUCCEEDS, which is further than before, and
that is not the same as the Job completing.

## Honest boundaries of this fixture, unchanged

The preparation performs the packet's owner acts with INDIVIDUAL real APIs rather
than through `baseline.prepare`; `tools.bootstrap` is not run and the two instance
facts `bind` reads are written by the fixture; the engine is the accepted
in-process one; the provider is a scripted child, now with its edit parents
created; the reviewer's dispositions are scripted and committed through the real
`review_cycles` owner API. All labelled simulated.
