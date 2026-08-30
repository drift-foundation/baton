# Finding: injected worker agents still require the scripted default

**Status:** corrected and independently signed off; awaiting operator closure

**Canonical Baton Work:** `W39770`

**Discovery context:** W39357's real Claude adapter image

## Observed — 2026-08-29

`v12/worker/baton_worker.py:main` documents and accepts an `agent=` injection
seam, but imports `ScriptedAgent` unconditionally before deciding whether the
caller supplied an agent. A provider image that ships its injected adapter but
not the unused scripted fixture therefore fails at process startup with
`ModuleNotFoundError: No module named 'scripted_agent'`.

W39357 temporarily copies `scripted_agent.py` into its Claude image. That is an
explicit stopgap and not the correction: every future provider image would
otherwise have to ship the same unused default.

## Confirmed by independent review — 2026-08-29

The current source is exactly the reported path:

```python
def main(argv=None, stdin=None, stdout=None, agent=None, place=LAUNCH_DOCUMENT):
    from scripted_agent import ScriptedAgent
    return serve(stdin or sys.stdin.buffer, stdout or sys.stdout.buffer,
                 agent or ScriptedAgent(), place)
```

This has two independently observable failures:

1. the unconditional local import raises before an injected adapter can start
   when the provider image omits `scripted_agent.py`; and
2. the truthiness fallback replaces an explicitly supplied falsey adapter with
   `ScriptedAgent`, even though only `None` means no injection.

The reference `v12/worker/Dockerfile` deliberately ships the scripted agent,
so deferring the import to the `None` branch preserves its ordinary entrypoint.
W39357's `Dockerfile.claude` separately names its copy as a stopgap and has a
guard that requires deliberate removal once this seam is corrected.

## Proposed boundary

Load and construct the scripted default only when `agent is None`. A small
lazy helper or an inline `None` branch is sufficient; the important property
is that neither the import nor construction occurs on the injected branch.
Preserve the reference image's default behavior and retain an explicitly
injected falsey agent rather than silently selecting the default.

The W39357 stopgap and its guard should be removed only after the seam itself
is corrected and the provider image proves it no longer carries
`scripted_agent.py`.

## Acceptance

- `main(agent=injected)` starts without `scripted_agent` being importable.
- `main(agent=None)` retains the scripted reference behavior.
- A supplied falsey agent is not replaced by the default.
- The real provider image removes the scripted-agent stopgap and keeps its
  no-secret build and runtime gates green.
- Focused worker tests cover import timing and both branches without requiring
  a container engine.

## 2026-08-29 — corrected

`main` no longer imports or constructs the fixture on the injected branch:

```python
def _scripted_default():
    from scripted_agent import ScriptedAgent
    return ScriptedAgent()


def main(argv=None, stdin=None, stdout=None, agent=None,
         place=LAUNCH_DOCUMENT):
    return serve(stdin or sys.stdin.buffer, stdout or sys.stdout.buffer,
                 _scripted_default() if agent is None else agent, place)
```

Both observable failures the review separated are closed by that one line.
**Where the import lives decides what an image has to carry**, which is why it
moved into the branch rather than staying at the top of the function with a
conditional around its use. And `agent is None` replaces `agent or`, because
only `None` means nobody injected one: an agent defining `__bool__` or
`__len__` is an ordinary object, and a seam that silently substituted the
fixture would run somebody else's agent under the caller's assignment.

The reference image is unchanged: its recipe ships `scripted_agent.py` and its
entrypoint supplies no agent, so it takes exactly this branch and gets exactly
the object it got before.

## Closure ruling — 2026-08-29

The corrected injection seam is the subject of W39770 and is independently
accepted. Removal of `Dockerfile.claude`'s temporary `COPY scripted_agent.py`
and its now-ineffective guard remains explicit integration work in W39357.
That transfer does not reopen the corrected seam and is not a reason to keep
W39770 active.
