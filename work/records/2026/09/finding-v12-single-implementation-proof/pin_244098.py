"""Record the custody decision and PIN the paths, BEFORE implementation.

Owner reroute 244096: "Record the decision before implementation."
"""
import hashlib
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[4]

PINNED = ("v12/worker/claude_agent.py",
          "v12/python/tests/manager/test_claude_context.py",
          "v12/python/tests/manager/test_claude_agent.py")

FINDING = """
## 2026-09-23 -- OWNER: the custody mode is fixed at creation, not at the check

Owner reroute 244096, recorded here BEFORE implementation as it requires:

    "Owner selects the remaining custody-mode correction. Record the decision
     before implementation: preserve private-context ownership, mode and
     symlink checks; make the provider execution/delivery path create
     compliant private directories. Establish whether restrictive creation
     permissions solve the observed CLI behavior; do not assume or
     blanket-chmod retained evidence. Reproduce the real directory layout
     deterministically without fixture-only permission repairs, preserving
     negative custody coverage. Keep scope within the separate implementation
     baseline."

**The manager's checks are not weakened.** `context_delivery._private` keeps
refusing any custody directory whose owner differs or whose mode carries group
or other bits, `_state` keeps refusing a link or special file, and the
credential slot keeps having to be exactly the expected symlink. The defect was
never that the check was wrong; it was that the deployment handed the provider
a process that creates world-readable directories and then asked the manager to
accept them.

### What the evidence shows

Seven directories under the live context home carry `0o755` --
`.claude/backups`, `projects`, `session-env`, `session-env/<conversation>`,
`shell-snapshots`, `projects/-output` and `projects/-output/memory`. Two carry
`0o700`: `.claude` and `.claude/sessions`. `0o755` is exactly `0o777 & ~0o022`,
the ordinary umask default; the two private ones are the CLI asking for
something stricter. Nothing in the evidence is a directory that could only be
`0o755` through an explicit `chmod`.

### What was ESTABLISHED, not assumed

`subprocess.run(..., umask=0o077)` was exercised against a real child under
this interpreter (3.13.7):

    0o700  dir   a          (os.makedirs)
    0o700  dir   a/b
    0o700  dir   a/b/c
    0o700  dir   d          (os.mkdir with an EXPLICIT 0o755)
    0o600  file  f

`mkdir` masks its mode argument, so a child under `umask 0o077` cannot create a
group- or other-readable directory **even when it asks for one**, and the mask
is inherited by its descendants. The `umask` operand exists on `Popen` from
Python 3.9 and is applied in the child after fork without `preexec_fn`, which
matters here because the provider spawn already runs beside a reader thread and
`preexec_fn` is not thread-safe.

**The one residual risk, stated rather than hidden**: a provider that
explicitly `chmod`s a directory permissive AFTER creating it would defeat a
umask, because `chmod` is not masked. The retained evidence does not show that
-- every non-private mode is exactly the umask default -- and the manager's
unchanged check would refuse it, which is the right outcome and would be a
separate finding. This correction is therefore necessary, sufficient for the
behaviour actually observed, and honest about what it does not cover.

### Where it goes, and where it deliberately does not

**Only the provider child.** A umask set at worker entry would also apply to
everything the adapter writes into the shared private line, whose group-based
access the deployment configures on purpose; narrowing that would be a
different change with different consequences. The provider is the only party
that creates the context home's directories, so it is the only party whose
creation mask moves.

### What the retained evidence is NOT

Nothing chmods `/home/sl/baton-runs/single-implementation-success-239528/`. The
owner said not to blanket-chmod retained evidence and that is a record of what
a real run produced; repairing it would destroy the only proof of the
behaviour this correction addresses.

### And the fixture stops compensating

`tests/manager/test_claude_context.py`'s fake provider has always chmodded its
two state parents to `0o700` -- the "fixture-only permission repair" that is
exactly why no deterministic test ever saw this. With the creation mask
corrected, the repair is unnecessary and is removed, so the fixture's child
creates its directories the way a real one does and the adapter's umask is what
makes them compliant. `ACustodyModeTheRealProviderProduces` is preserved
unchanged as the negative coverage: a home that is NOT compliant must still be
refused.
"""

PLAN = """# Current action -- the custody mode, fixed at creation

## Active -- claim 244098, baton.claude

Owner reroute 244096. The decision is recorded in FINDING before any
implementation, as that reroute requires: the manager's ownership, mode and
symlink checks are PRESERVED, and the provider execution path is corrected to
create compliant private directories.

## PINNED PRODUCT OWNERSHIP -- pinned BEFORE the first edit

%s

The change: the provider child is spawned with `umask=0o077`, so every
directory it or its descendants create is private and every file is
owner-only. `mkdir` masks its mode argument, so this holds even for an explicit
permissive mode. Only the provider child is affected; a umask at worker entry
would also narrow what the adapter writes into the shared private line, whose
group access the deployment configures deliberately.

Test paths are covered by the standing test-change authority (AGENTS.md, owner
ruling 2026-09-13) and are recorded here as that ruling requires.

## Steps

1. Record the decision and this pin. (done -- `pin_244098.py`)
2. Correct the provider spawn.
3. Remove the fixture's permission repair so the deterministic path proves the
   correction rather than hiding the need for it; PRESERVE the negative
   custody coverage unchanged.
4. Reproduce the real fourteen-entry layout deterministically and assert the
   manager's own `_state` accepts it under the corrected mask and refuses it
   without.
5. Successor artifacts and exact bounded commands; independent review.

## Not in scope

Weakening any custody check. Chmodding retained evidence. Any live run,
deployed provisioning, image rebuild, recovery, reviewer stage, resume or
closure.

---

"""


def sha(path):
    reading = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            reading.update(block)
    return reading.hexdigest()


def main():
    pins = "\n".join(f"    {one}\n        {sha(ROOT / one)}" for one in PINNED)
    finding = HERE / "FINDING.md"
    if "the custody mode is fixed at creation" not in \
            finding.read_text(encoding="utf-8"):
        finding.write_text(
            finding.read_text(encoding="utf-8").rstrip("\n") + "\n" + FINDING,
            encoding="utf-8")
    plan = HERE / "PLAN.md"
    body = plan.read_text(encoding="utf-8")
    if "claim 244098" not in body:
        head = body.split("\n", 1)[0]
        plan.write_text((PLAN % pins) + body.replace(
            head, "# Historical action" + head.split("action", 1)[-1], 1),
            encoding="utf-8")
    print(pins)
    print("recorded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
