"""Claim-244098 dossier entries and the product-change evidence."""
import hashlib
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[4]

BEFORE = {
    "v12/worker/claude_agent.py":
        "abdf903da3c767f3fe9babf84e4499f455da968a61ee3c975b9899988354bb4d",
    "v12/python/tests/manager/test_claude_context.py":
        "9ccc49a24914d87258a04371402662363b7a9c64444236712d5f0b1607f0e498",
    "v12/python/tests/manager/test_claude_agent.py":
        "43bfd0e9ab321d1491702540cd5473b9455a73f07e5c9fefc0b39b469f523bbd",
}

PROGRESS = """
## 2026-09-23 -- baton.claude, claim 244098, the custody mode

Owner reroute 244096 selects the remaining custody-mode correction. The
decision was recorded in FINDING and the three paths pinned BEFORE any edit, as
that reroute requires (`pin_244098.py`). No live run, no deployed
provisioning, no image rebuild, no recovery, no reviewer stage, no resume, no
closure. Nothing chmods the retained evidence.

**The manager's checks are preserved exactly.** `context_delivery._private`,
`_state`'s link and special-file refusals and the credential-slot symlink rule
are untouched. The defect was never that the check was wrong; it was that the
deployment handed the provider a process that creates world-readable
directories and then asked the manager to accept them.

**Established rather than assumed**, which the reroute asks for explicitly.
`subprocess.run(..., umask=0o077)` was exercised against a real child: an
`os.makedirs` tree, an `os.mkdir` with an EXPLICIT `0o755`, and a file all came
out `0o700`/`0o700`/`0o700`/`0o600`. `mkdir` applies `mode & ~umask`, so a
child under this mask cannot create a group- or other-readable directory even
when it asks for one, and the mask is inherited by its descendants. The
`umask` operand is `Popen`'s own and is applied after fork without
`preexec_fn`, which matters because the provider spawn already runs beside a
reader thread and `preexec_fn` is documented unsafe with threads.

The observed evidence is consistent with exactly this: the seven non-private
directories are all `0o755`, which is `0o777 & ~0o022`, and the two private
ones are the CLI asking for something stricter. **The one residual risk is
stated rather than hidden**: `chmod` is not masked, so a provider that made a
directory permissive after creating it would still be refused -- which is the
right outcome, is its own finding if it ever happens, and is why the check is
not weakened.

**Only the provider child.** A mask on the whole worker would also narrow what
the adapter writes into the shared private line, whose group access the
deployment configures on purpose. `PROVIDER_UMASK` is applied to the provider
spawn and to nothing else, and a focused case asserts no other child's mask
moved.

**The fixture stops compensating, which is the deterministic proof.**
`tests/manager/test_claude_context.py`'s fake provider had always chmodded its
two state parents to `0o700` -- the fixture-only repair that is exactly why no
deterministic test ever saw this. It now creates `memory`, `backups`,
`shell-snapshots`, `sessions` and `session-env` the way a real CLI does and
chmods nothing. All 81 context checks still pass, which means the adapter's
mask is what makes them compliant; remove the mask and they fail on a layout
the fixture never touches.

`TheRealLayoutIsCompliantBecauseOfTheMaskNotARepair` makes that unmissable:
every directory under the context home is private, the observed layout is the
one created, the manager's own `_state` -- the function that refused the live
run -- accepts it, and the context generation actually seals (`status: ready`,
which the live run never reached). **Negative custody coverage is preserved**:
`ACustodyModeTheRealProviderProduces` still drives a whole run whose home is
made readable after the turn and still expects the stall, and a fifth case
chmods the sealed home and asserts `_state` refuses with the live run's exact
message.

Verification: 143 focused deterministic checks, measured 26.850900484991143s,
receipt `verification-8.json` with `verification-8.log`; 4 are new. Product
suites: `test_claude_agent` 224, `test_claude_context` 81,
`test_review_driver` 164 -- 469 together in 59.258s, no failure or skip.

Cumulative measured for W239528: 558.956385128s (through claim 243990) +
26.850900485 + 25.560063872 + 59.258 + 38.230 + 14.917 + 7.197 (claim 244098)
= **730.969349485s**.

State: awaiting independent review.
"""

PLAN_DONE = """
## Done under this claim

1. Decision recorded and paths pinned before any edit (`pin_244098.py`).
2. `claude_agent.PROVIDER_UMASK = 0o077`, applied to the provider spawn alone
   through `Popen`'s own `umask` operand.
3. The fixture's permission repair removed and the real extra directories
   created, so the deterministic path proves the correction instead of hiding
   the need for it.
4. Four new checks: the operand at the adapter boundary, no other child's mask
   moved, a real child under that mask, and the whole layout accepted with the
   generation sealed. Negative custody coverage preserved and extended.

Verification: 143 dossier checks, 26.850900484991143s, receipt
`verification-8.json`; 469 product checks in the three affected suites.

## What an operator still needs

The corrected adapter is worker-image code. A live run on it needs an image
built from this `claude_agent.py` -- **not done here and not authorized here**;
`OPERATOR-SUCCESSOR-243284.md`'s standing warning is unchanged until that
image exists and the packet binds it.
"""

OWNERSHIP = """
## Claim 244098 -- the custody mode, fixed at creation

Added: `pin_244098.py`, `records_244098.py`,
`PRODUCT-CHANGE-244098.json`, `verification-8.json/.log`.

Edited: `test_no_progress.py`, `PLAN.md`, `PROGRESS.md`, `FINDING.md`, this
file.

PRODUCT paths edited, pinned before the first edit:

    v12/worker/claude_agent.py                      PROVIDER_UMASK
    v12/python/tests/manager/test_claude_context.py the fixture repair removed
    v12/python/tests/manager/test_claude_agent.py   the focused adapter case

The three paths accepted under claim 242687 are unchanged and still carry their
accepted after-hashes. No custody check was weakened. No retained evidence was
chmodded, moved or deleted.
"""


def sha(path):
    reading = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            reading.update(block)
    return reading.hexdigest()


def main():
    (HERE / "PRODUCT-CHANGE-244098.json").write_text(json.dumps({
        "schema": "baton.single-implementation-product-change/1",
        "work": "W239528", "claim": 244098, "participant": "baton.claude",
        "pinned_before_editing": "PLAN.md, by pin_244098.py",
        "paths": {one: {"before": was, "after": sha(ROOT / one)}
                  for one, was in BEFORE.items()},
        "decision": ("the manager's ownership, mode and symlink checks are "
                     "PRESERVED; the provider execution path is corrected to "
                     "create compliant private directories"),
        "established_not_assumed": (
            "subprocess.run(..., umask=0o077) exercised against a real child: "
            "makedirs tree 0o700, explicit mkdir(0o755) -> 0o700, file 0o600. "
            "mkdir applies mode & ~umask and the mask is inherited."),
        "residual_risk": (
            "chmod is not masked, so a provider that made a directory "
            "permissive AFTER creating it would still be refused by the "
            "unchanged manager check -- the right outcome, and its own "
            "finding if it ever happens"),
        "not_changed": [
            "context_delivery._private and _state -- the checks stand",
            "the retained live evidence -- never chmodded",
            "the three paths accepted under claim 242687",
        ],
        "still_needed_for_a_live_run": (
            "a worker image built from this claude_agent.py; not done here "
            "and not authorized here"),
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    progress = HERE / "PROGRESS.md"
    if "claim 244098" not in progress.read_text(encoding="utf-8"):
        progress.write_text(
            progress.read_text(encoding="utf-8").rstrip("\n") + "\n" + PROGRESS,
            encoding="utf-8")
    plan = HERE / "PLAN.md"
    body = plan.read_text(encoding="utf-8")
    old = "## Not in scope\n"
    if "Done under this claim" not in body.split("# Historical", 1)[0]:
        plan.write_text(body.replace(old, PLAN_DONE + "\n" + old, 1),
                        encoding="utf-8")
    owner = HERE / "OWNERSHIP-239528.md"
    if "Claim 244098" not in owner.read_text(encoding="utf-8"):
        owner.write_text(
            owner.read_text(encoding="utf-8").rstrip("\n") + "\n" + OWNERSHIP,
            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
