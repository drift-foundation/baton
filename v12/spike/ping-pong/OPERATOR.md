# W17110 — proof complete; development fixtures retained

**Updated 2026-08-27, after both trials succeeded.** This file has trailed the
Work twice now: it said no provider had been nominated after one was staged,
and then directed two retries after both had already returned the pong. Each
time an operator reading it would have acted on a state that no longer existed.

## Where it stands

**Both real agents returned the correlated exact `pong`**, in a real container
each, against the staged read-only credential, with enforced clean teardown and
no provider text in either report.

    Claude   satisfying
    Codex    satisfying

Independent proof sign-off is complete. The approver has chosen to retain the
two exact staged credential files for future trials on this private development
box, so no operator cleanup remains before terminal closure.

## Current credential state

The exact files below may remain as volatile, operator-managed development
fixtures. They stay owner-only (`0400`) and are mounted read-only only for an
explicit trial. They are not copied into images, results, logs, or Baton state.

    /run/baton/credentials/claude
    /run/baton/credentials/codex

This retention is a private-box exception, not a production lifecycle rule.
Credentials can expire, so every later trial still runs `preflight.py` and
refreshes or restages an unusable entry.

## Optional withdrawal

If the operator later wants to remove the fixtures, use only these bounded
commands:

    sudo unlink /run/baton/credentials/claude
    sudo unlink /run/baton/credentials/codex
    sudo rmdir  /run/baton/credentials
    sudo rmdir  /run/baton          # only if it is now empty

**No recursive deletion is authorized and none is written here.** `rmdir`
refuses a directory that is not empty, which is the point: if anything else is
in there, it is not this spike's and this spike does not remove it.

`/run` is a tmpfs on most systems, so the staging normally does not survive a
reboot. Neither persistence nor withdrawal is a W17110 closure condition.

## Re-staging, if a later round ever needs it

Everything below is kept for that case and for the record of how the approved
layout was built. **It is not a current instruction.**

## Why the obvious thing does not work

Your own runtime credentials exist:

    /home/sl/.claude/.credentials.json   1000:1000  0600
    /home/sl/.codex/auth.json            1000:1000  0600

Both spike images run as **uid 65532**. A bind mount preserves host ownership
rather than translating it, so mounting either of those as they stand hands the
runtime a file it cannot open. `preflight.py` reports this as `readable_by_container_uid: false`.

**But that is the HOST's view of the numbering, and it is not always the
container's.** On this machine the same file reads as uid 65534 from the host
and uid 65532 from inside a container. So readiness is decided by a probe
container that asks whether the configured identity can open the exact path,
never by the host-side model — and separately by whether every ancestor is
traversable, which a bind mount would otherwise carry the container past.

## How the provider was staged, for reference and for re-staging

Copies you are content to expose to a container, owned by the identity that has
to read them. **Nothing here reads or prints a credential.**

    sudo install -d -m 0711 /run/baton /run/baton/credentials
    sudo install -o 65532 -g 65532 -m 0400 \
        ~/.claude/.credentials.json /run/baton/credentials/claude
    sudo install -o 65532 -g 65532 -m 0400 \
        ~/.codex/auth.json          /run/baton/credentials/codex

The carrier directories are **traverse-only** and root-owned; the two entries
are owned by the container identity at `0400`. Preflight requires exactly that
and does not require the carrier to be listable — `r` on a directory is
permission to read the names, and no trial needs the names.

Then confirm the machine agrees before running anything:

    python3 preflight.py          # exits 0 only when both paths are usable

Then the two trials, in the order the ruling fixes — Claude first, so its result
can refine shared mechanics without erasing the independent Codex outcome:

    python3 trial.py claude --credentials /run/baton/credentials/claude
    python3 trial.py codex  --credentials /run/baton/credentials/codex

Each prints one JSON report and exits non-zero unless the trial is satisfying.
A report carries no provider text: identities, exit states, a digest of the
answer, byte counts, and one word from a closed failure vocabulary.

**`/run` is a tmpfs on most systems, so this does not survive a reboot.** That
is a feature for a spike: the exposure ends when the machine does.

## Withdrawing it — see the optional procedure above

The exact `unlink`/`rmdir` commands are in "Optional withdrawal" above, so
there is one copy of them and not two that can drift apart.

**Corrected 2026-08-27 by W17110's eighth review:** this section used to say
`sudo rm -rf /run/baton/credentials`, and the approved decision authorizes no
recursive deletion — only unlinking the two exact entries and removing the
directories once empty. An operator would have run that on my say-so.

## Option 2 is gone — closing as a partial was superseded

**Superseded 2026-08-27** by the ruling in `FINDING.md`: *"The earlier option to
close or park W17110 as a useful partial result is superseded. W17110 is the
campaign's live proof gate and remains open until both a real Claude container
and a real Codex container return the correlated exact `pong`."*

A categorized provider failure is valuable evidence and may create follow-up
Work. It does not discharge this one. So there is no decline path here any
more: what the operator supplies is a provider that lets the trials run.

## What is not on the table

Moving the agent onto the host, weakening the container's isolation, or
substituting a credential nobody nominated. The ruling forbids the first two by
name, and the third is the same decision by a quieter route.
