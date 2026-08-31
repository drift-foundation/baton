# The blocker, located and reproduced without a credential

`baton.claude`, 2026-08-31, attempt `attempt-w51487-run3`.

The credential was replaced from an authenticated host session (M52739) and
the attempt produced the **identical** result: `provider-failed`, status 1,
zero changed paths, the same custody content digest
`sha256:e002024b91fc1f643efeb954d1f7563c1838359fe6d24dc227846e4515f6c33c` as
run 2. So my previous round's inference — that the credential was being
rejected by the API — is **refuted**. Replacing it changed nothing.

Here is what is actually wrong.

## The provider is not failing to authenticate. It cannot read the file.

Credential-free probe, in the image, no credential mounted at all:

    claude --print --permission-mode acceptEdits 'hi'
    EXIT=1
    stdout: Not logged in · Please run /login

That is the exact signature of the attempt: exit 1, no API time. And the
argument is correct — the same probe with a deliberately invalid mode gives

    error: option '--permission-mode <mode>' argument 'bogusMode' is invalid.
    Allowed choices are acceptEdits, auto, bypassPermissions, manual,
    dontAsk, plan.

so `acceptEdits` is a valid choice. `claude_agent`'s own comment calls that
tuple "the single operand in this module a golden test cannot establish" and
asks the first live turn to prove it. **It is proven correct.** The argv is
not the problem.

## The delivered slot is mode 0600 and owned by the manager

`credentials.py` writes the attempt-scoped delivery with `VOLATILE_FILE =
0o600` under a `VOLATILE_DIR = 0o700` root, both owned by the manager's uid.
The execution container runs as the fixed uid **65532**. Reproduced with a
file of my own containing `{"not":"a credential"}` — no real material — mounted
exactly as the adapter mounts the slot:

    os.path.exists  -> True
    os.access R_OK  -> False
    open            -> PermissionError 13
    uid 65532, file uid 1000, mode 0o600

`os.path.exists` succeeds because a `stat` needs only search permission on the
parents; the read does not.

## Which is why nothing refused

`claude_agent._prepared_home` guards with

    if not os.path.exists(slot):
        raise TaskRefusal("this container has no credential at ...")

Existence, not readability. So the guard passes, the unreadable slot is
symlinked into the private home, the CLI reads it, gets `EACCES`, prints
"Not logged in" and exits 1 — and `_ran` sends both streams to `/dev/null`,
so all that survives is `status: 1`.

Every layer behaved exactly as written. No layer asked the one question that
mattered.

## This is W33935's defect a third time

The same shape has now been found three times in this campaign, each time
because a consumer running as uid 65532 was handed material owned by the
manager at an owner-only mode:

1. the two `/input` protocol documents at `0400` — fixed to `0444` by W33935;
2. the staged source TREE at `0600` — fixed by `_frozen_delivery` under
   W39358, found by the first real worker turn;
3. **the credential slot at `0600` — still broken, and found by this one.**

And the irony is exact: the frozen task this attempt exists to perform is
adding coverage for `preflight.py::_observed_readable` — W17110's probe that
runs a container as uid 65532 with the credential mounted and runs `test -r`.
The spike built a probe for precisely this failure. The manager's credential
home does not use it, and the worker does not ask it either.

## A remedy shape, proven credential-free

Not taken — `credentials.py` and `claude_agent.py` are not this Work's files —
but measured so the next Work does not have to guess.

The manager already gives the execution container the deployment's configured
workspace group as a supplementary group (`--group-add`, W33936). With the
same file at `0640` and that group:

    groups [1000, 65532] | access R_OK -> True | open -> ok

So the slot can be made readable by the container's fixed uid **without**
becoming world-readable, which matters more here than it did for `/input`:
this one is a bearer. `0444` would work and would be the wrong answer.

The second half belongs to the worker: `_prepared_home` should ask
`os.access(slot, os.R_OK)` — or simply open it — rather than
`os.path.exists`, so that an unreadable delivery is a typed refusal naming the
cause instead of a provider exit 1 whose diagnostic may not be published. That
is last round's [P1] in its most concrete possible form.
