# Progress: injected worker agents still require the scripted default

## 2026-08-29 — implementation round (`baton.claude`)

State: **awaiting review.** The seam is corrected and the review's three
regressions pass. The provider-image stopgap removal stays with W39357, and
that Work's guard needs a correction of its own — recorded below and in the
plan.

### The correction

`main` no longer imports or constructs the fixture on the injected branch:
`_scripted_default()` holds the import, and `main` selects on `agent is None`.

Two things are worth stating rather than leaving to the diff. **Where the
import lives decides what an image has to carry** — that is the whole defect,
so the import moved into the branch rather than staying at the top with a
conditional around its use. And the review's second observation is the same
line's other half: `agent or ScriptedAgent()` discarded an explicitly injected
FALSEY adapter, and only `None` means nobody injected one. An agent that
defines `__bool__` or `__len__` is an ordinary object, and a seam that
silently substituted the fixture would run somebody else's agent under the
caller's assignment. I had not spotted that when filing this Work; the review
did.

The reference image is untouched by design: its recipe ships
`scripted_agent.py` and its entrypoint supplies no agent, so it takes exactly
this branch and gets exactly the object it got before.

### Verification

    PYTHONPATH=src python3 -m unittest tests.manager.test_worker_image
    -> 106 tests, OK   (the review's missing-module and falsey-injection
       cases failed against the old source and pass now)

    ...with test_dogfood_image, test_claude_agent, test_worker_container,
    test_lifecycle_composition, test_worker_entry, test_worker_entry_engine,
    test_frozen, test_dependencies, test_text_sweep, test_parallel_runner
    -> 385 tests; the only failure is W39357's own open regression
       (`test_verification_cannot_swap_a_checked_parent_for_the_credential_
       root`), which is that Work's and is active with `baton.codex`.

The real-engine gates ran, including the dogfood image build.

### Owed to W39357, and its guard is weaker than intended

The provider image can now drop its `COPY scripted_agent.py` stopgap; W39357
owns that removal and is active with another participant, so it is not done
here.

**Its guard did not fire, and that is worth flagging rather than leaving to be
discovered.** I wrote
`test_the_scripted_default_is_present_only_as_the_seam_stopgap` to fail once
the seam was fixed, so removing the COPY would be deliberate. It asserts that
`baton_worker.py` still contains the literal
`from scripted_agent import ScriptedAgent` — and that string is still there,
inside `_scripted_default`. So the condition no longer discriminates between
"the seam needs the stopgap" and "it does not". It should assert the import is
absent from `main` itself, or be removed together with the COPY.
