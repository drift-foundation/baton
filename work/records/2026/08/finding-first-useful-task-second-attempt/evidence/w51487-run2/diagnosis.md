# Why the worker was unable — measured, and the part that had to be inferred

`baton.claude`, 2026-08-31, attempt `attempt-w51487-run2`.

W39364 could not answer this question at all: its retained record said
`worker_disposition: unable` and the account that would have explained it was
destroyed by the hard-coded discard. W51473 made retention an operator
decision, this attempt asked for `retain`, and the account survived.

## What the worker itself says

`proposal/result.json`, retained verbatim, is the whole of it:

    "disposition": "provider-failed",
    "provider": { "status": 1, "seconds_bound": 3600 },
    "why": "the provider exited 1; its own diagnostic is not published,
            because the process that wrote it holds this attempt's credential"

So the task was never attempted. The provider process started, exited 1 well
inside its 3600-second bound — this is not a timeout — and `claude_agent._ran`
sends both of its streams to `/dev/null` by design. That design is right and
its reasoning is on the record: the provider holds the bearer, and W39357
already had the bearer reach `result.json` through exactly that channel.

`verification.txt` says `no verification was attempted`, and `change.patch` is
zero bytes. Both agree with the worker: there was nothing to verify and
nothing changed.

## Three credential-free probes, run outside the attempt

None of these touched `/run/baton/credentials/claude`, and no credential bytes
were opened or recorded.

**1. Egress from the authorized posture works.** The same image, the same
`bridge` network, the same fixed uid and read-only root, no credential mounted
at all:

    DNS  api.anthropic.com -> 160.79.104.10
    TCP  443 ok

So the provider failure is not a network fault, and not the TLS trust-store
defect W17110 paid two review rounds to find.

**2. The provider CLI works in this image.** It is present and answers
`--version` as `2.1.247 (Claude Code)`.

**3. An INVALID credential produces exactly this signature.** With a
credentials document I invented — no real material involved — mounted at the
slot the adapter uses, in the same posture:

    EXIT=1
    stdout: {"is_error":true, "duration_api_ms":0,
             "terminal_reason":"api_error", ...}

## The conclusion, and the size of it

The measured facts are: the CLI runs, the network is reachable, the provider
exited 1 with no time spent, and an invalid credential reproduces that exact
exit status. The most likely cause is that the authorized credential is not
being accepted by the API — expired, invalid, or without the scope the turn
needs.

That is an INFERENCE and it is stated as one. Other API errors also exit 1. I
did not read the credential and will not; establishing which it is belongs to
the operator who owns the source.

## The finding this attempt produced

**A provider failure is not diagnosable from the retained evidence.** The
account says `status: 1` and deliberately says nothing else, so an operator
cannot tell an expired credential from a rejected scope from a malformed
request. It took three probes outside the attempt to get as far as "probably
the credential", and a supervised pilot cannot depend on the operator
happening to think of them.

The remedy already exists in this campaign and is not published: the CLI's own
`--output-format json` carries a structured, non-prose `terminal_reason`
(`api_error` above) on STDOUT rather than in the stream that may carry the
bearer. W17110's `trial.mjs` classifier — the very file this frozen task adds
coverage for — does exactly this shape of work, mapping observed text to a
closed vocabulary.

The safe form is a CLOSED VOCABULARY, not a passthrough: map the provider's
`terminal_reason` to one of this deployment's OWN fixed words and publish only
the mapped word, never the provider's text. A field that could echo a bearer
must not be copied even from stdout; a word this deployment chose cannot.

That belongs to `claude_agent`, which this child does not own. It is offered
as a finding rather than taken.
