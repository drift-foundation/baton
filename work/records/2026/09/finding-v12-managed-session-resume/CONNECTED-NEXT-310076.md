# The connected packet proof — actual partial harness and the exact next read

W236087 claim 310076, superseding CONNECTED-NEXT-310021.md.

## My speculation was wrong and is withdrawn

I guessed the ending was about the declared test scope or the verification
command. Review 2026-09-29T22-51-42Z read the retained proposal and the real
answer was neither: `verification.txt` says "no verification was attempted",
`changed_paths` is empty, and the disposition is `provider-failed` with
`failure_reason: start-error`, `status: 1`, `why: provider context terminal
identity is unproved`. Withdrawn.

## What I fixed this claim, and why it was the right seam

`ServingContextCase.setUp` patches `oci.OciAdapter._context_execution` to return
None, because the composed flow it serves uses a `/1` context profile whose state
path is FIXED (`.claude/projects/output/session.json`). THIS packet requires the
SESSION profile, whose allowlist names `{conversation_id}.jsonl` -- that
substitution is what makes a restore possible at all -- and with the seam stubbed
out the adapter cannot prove the conversation's terminal identity. The accepted
`ManagedSessionResume` case restores the real function for exactly this reason,
and `ConnectedPacket` now does the same. No identity or receipt check was
weakened.

## Where the run reaches, with the full adapter evidence retained

`CONNECTED-EVIDENCE-310076.json` holds the canonical output, both frozen
artifacts' files and the provider event. The state:

    admissions      implementation 1, review 0
    receipts        admit PERFORMED, claim PERFORMED, no refusal
    runtime         runtime-single-1 launched, destroyed, cleanup 'retained'
    output          disposition 'unable'  ->  projection 'exceptional'
    proposal        disposition 'provider-failed', failure_reason 'start-error',
                    status 1, changed_paths [], verification null
    receipt         baton.provider-context-receipt/3, complete FALSE,
                    terminal 'unproved', mode 'open',
                    observed_conversation_id NULL, observed_model NULL,
                    provider_result_digest sha256:e3b0c442...b7852b855
                    (the digest of NOTHING), status 1
    stage states    implementation 'exceptional', review 'blocked'

## The exact next read, narrowed by this claim

`provider_result_digest` is the digest of the EMPTY string and both observed
identities are null, so the adapter saw no provider output at all -- and the
scripted child exited 1. `child_diagnostics()` is empty, so the child's own
status, stdout and stderr are not being captured anywhere this fixture can read.

THE NEXT STEP IS TO CAPTURE THEM DIRECTLY, which is what review
2026-09-29T22-51-42Z asked for: wrap the scripted provider `run` callable this
fixture passes into the turn, record its argv, exit status, stdout and stderr,
and compare what it returns against what `claude_agent` needs to observe a
conversation id and a model. One concrete hypothesis to test first, not to
assume: `test_stage_execution.provider` returns
`CompletedProcess(argv, status, None, None)` -- stdout None -- while the
managed-context cases override `provider` to return real JSON output. If that is
the difference, the correction belongs in this owned harness's own provider
override, not in the shared fixture.

Do not weaken the identity or receipt checks, do not fabricate provider output,
and do not change the adapter to accept an unproved terminal.

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

## What has NOT been reached

No successful provider completion, no review invocation, no canonical verdict,
no context save and no restore. Provider INVOCATION is not completion, and this
record does not treat it as one.

## Honest boundaries of this fixture, unchanged

The preparation performs the packet's owner acts with INDIVIDUAL real APIs rather
than through `baseline.prepare`; `tools.bootstrap` is not run and the two
instance facts `bind` reads are written by the fixture; the engine is the accepted
in-process one; the provider is a scripted child; the reviewer's dispositions are
scripted and committed through the real `review_cycles` owner API. All labelled
simulated.
