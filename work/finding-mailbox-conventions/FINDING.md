# Mailbox-use conventions

Two conventions for USING a Baton mailbox. Neither is a wire-protocol
feature; neither needs a protocol or schema change; an instance that ignores
them is still conformant, just harder to work with.

## Where these live

**Normatively in `AGENTS-MAILBOX-PROTO.md`**, under "Mailbox-use conventions".
Slawomir approved editing that document on the grounds that it carries
conventions rather than Baton's own wire protocol.

The text below is retained here as the working record of the decision and its
one mechanical consequence, described because it touched a frozen artifact:

`AGENTS-MAILBOX-PROTO.md` is hash-pinned by `DISTRIBUTION.json`
(`protocol_doc_sha256`), so editing it makes the committed manifest stale --
`test_distribution_root_contract` fails immediately. Refreshing the manifest
was therefore required, and was done with `just build`.

What that actually changed, measured rather than assumed:

    bin/baton            BYTE-IDENTICAL
    DISTRIBUTION.json    one field: protocol_doc_sha256
                         b5b79601... -> 8014c2cb...

The CLI EXECUTABLE is untouched. The manifest moved by exactly the field whose
job is to track that document, which is the manifest doing its job rather than
the freeze being broken. `baton_v6.py` and `build_zipapp.py` are unchanged.

## 1. File references travel as their own part

When a message refers to or discusses repository files or changes, it carries
a separate REFERENCES leaf in its multipart content.

    content type   text/vnd.baton.references; charset=utf-8
    disposition    inline
    content        one repository-relative POSIX path per line, ordered by
                   first material mention

Paths here are NAVIGATIONAL METADATA: they say where to look. They are not
copied content and not hash pins. When the sender means "this exact evidence,
immutable", that is an EXTERNAL part, which carries a hash and fails closed
when the bytes change. The two are different promises and must not be
confused.

Not permitted: absolute paths, `..`, home expansion, host-specific roots. A
reference that resolves on only one machine is not a reference.

For references spanning repositories, identify the repository unambiguously
and group paths under it, using the smallest stable representation available
in context, consistently.

**Authoring gap, recorded rather than worked around.** Protocol 9 and
`baton_core` store multiple inline leaves happily. The released CLI exposes
one inline `--body` plus external parts, so an agent using the CLI cannot
author a references part today. The CLI is frozen for this stage. The
repeatable general-part authoring surface is a requirement of the
CLI-to-core adoption stage, and the convention becomes routinely usable when
that lands.

## 2. One live wait per active turn

Baton is vendor-neutral and stays that way. There are no Baton-to-model
bridges: the number of adapters would scale with the number of model runners,
and none of them belong in a portable protocol.

- While an agent is actively assigned, keep its turn alive around exactly ONE
  foreground `wait`.
- Delivery returns to the LIVE turn. Resolve the claim, re-arm, continue in
  the same turn.
- **Never end a turn leaving a detached `wait` behind.** It can claim mail
  without waking the model: terminal output does not itself wake an idle
  agent, and the claim is then stranded -- held, invisible, and blocking the
  sender.
- If the agent is intentionally idle, poll with read-only `scan` or a generic
  host heartbeat. Never leave a claim-producing orphan waiter.
- Waking is a RUNNER concern, not protocol behaviour. A future standard runner
  signal can improve idle wakeups without changing anything here.

This was written after exactly that failure: a detached background `wait`
claimed a message, the turn ended, and the claim sat unanswered while six more
queued behind it.

## Baton as the primary channel, from the commit onward

Slawomir's notice, recorded verbatim because it changes who an agent is
talking to:

> baton will be the primary means of commuication - don't bother waiting for
> your console/prompts to be answered. Baton is the way to communicate going
> forward. This is approved when we commit this work.

**Not in force yet**, by its own terms: it takes effect when this work is
committed, and committing is Slawomir's. Until then a console prompt is still
a live channel.

What it means afterwards: an agent does not block on the terminal for an
answer it could ask for through the mailbox. A question goes to the
participant who can answer it, as a directed message with a real subject, and
the agent goes on working or waits on `wait` -- not on a prompt nobody is
watching. The terminal remains where a human standing in front of one can
still see and steer, but it stops being the thing an agent depends on.

This is also the reason the console exists. A protocol whose primary channel
is the mailbox needs the human to be a first-class participant in it, rather
than someone who reads agent traffic over a shoulder.

### The reader must not truncate

Found the hard way in the same exchange. A notice is delivered ONCE, and a
receipt then exists; there is no second read. An agent that prints a delivered
notice through a formatter which elides -- as mine did, at 400 characters --
has destroyed the only copy it will ever have, and `see`, `dump` and
`materialize` will not give it back. See `work/finding-cli-read-authority`.

Print a delivered notice in full, or write it to a file, before doing anything
else with it.
