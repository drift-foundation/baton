# The authoring vehicle this packet binds

Recorded by `baton.claude`, claim334663. The prerequisite that held
`../execution-333707` is **closed**: owner close334628 satisfied W333735 after
independent acceptance
(`decisions/enforcement-review.md`) and integration
(`decisions/enforcement-integration.md`), and the human checkpoint is
`a9f4fa4da2323a357ae15aefbc5d7d22d41487b6` — this packet's declared base.

`../execution-333707`'s `HOLD.md` is therefore **historical**. It is preserved
unchanged and must not be read as current: its blocker is resolved, and its
packet still pins the old unenforced supervisor, so that packet remains
unlaunchable regardless.

## What changed in the vehicle

The supervisor's missing expiry pass is no longer worked around — it is
replaced by a separate accepted controller, `tools/authoring_enforcement.py`
(439 lines, new at this base), pinned here as
`sha256 2da6eb36b398d730…` and present among this packet's **113** pinned
manager files (112 before).

Read read-only this claim, against the committed bytes:

- The controller owns **its own connections and cancellation adapter** in a
  separate thread (`Guard`), so a scheduler blocked in filesystem, provider or
  engine work cannot block the enforcement lane — which is exactly the
  falsified property.
- `supervise_process` holds the outer deadline and **never calls the authoring
  sweep or the cancellation engine**; the child is a separate process group
  bound to its controller by `prctl(PR_SET_PDEATHSIG)`.
- `verify_controller(packet)` resolves `__file__` inside
  `packet["manager_source"]["path"]` and requires the pinned digest. So the
  controller must be **run from the staged source**, and a packet that did not
  pin it refuses.
- Admission is once: `admit_child` refuses a second child under the same run,
  and recovery is cancellation-only — **not a fresh budget**.
- Success is not the controller's to grant: `report["state"]` reaches
  `completed` only when the workload supervisor itself exits 0 **and** every
  attempt is observed `absent` with its token returned.

## The start command is NOT the one the composer writes

This matters more than anything else in this document.

`baseline_bindings.py` is **unchanged** at this base — still
`sha256 09fbf3c59820231b7199e24aa1cf64eee93f6ea2e60f3477fed5ca909e5fc379` —
and its line 721 still composes

```json
"start": ["<python>", "-B", "<supervisor>/baseline.py",
          "--packet", "<run>/packet/PACKET.json",
          "--incarnation", "<run_id>"]
```

That is the **unenforced** path: the one whose `serve` call carries no reclaim
argument. So `<root>/packet/commands.json` — a document the accepted composer
generates — tells an operator to start exactly the vehicle the prerequisite
was opened to replace.

**Do not use `commands.json`'s `start`.** `prepare.py bind` writes its own
`AUTHORING-COMMAND.json` beside it carrying the enforced invocation and the
environment it needs, and `OPERATOR.md` records it. The correct form is

```
cd <root>/code/v12/python
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=<root>/code/v12/python/src:<root>/code/v12/python:<root>/supervisor \
BATON_V12_STAGE_EXECUTION_CONFIG=<root>/packet/deployment.json \
python3 -m tools.authoring_enforcement --packet <root>/packet/PACKET.json
```

This is reported, not patched. Correcting `baseline_bindings.py` would be host
product implementation, which this Work is not authorized to do and which
belongs to whoever owns that composer. It is raised here so review can
classify it: **a packet composed by the accepted composer still advertises the
unenforced start**, and every later authoring packet inherits that until the
composer is corrected.

## What the new vehicle does and does not promise about the lease

`tokens.LIFETIME_SECONDS` is still **900** and production renewal is still
W333485's unfinished work. The enforcement controller makes the initial
900-second lease **actually enforced** — it is no longer ignored — but it does
not extend it.

So the requested bounds (provider turn 3600s inside a 4800s total) are
**ceilings, not a promise of a 3600-second authoring run.** An authoring turn
on this base should expect its workspace generation to expire at 900 seconds
and be enforced, with the controller ordering cessation, retaining partial
output and reporting a held outcome. `TASK.md` requires the turn to preserve a
partial candidate and account for it honestly, and such a termination is
itself further evidence for this Work.

This supersedes two earlier statements of mine, both now withdrawn:

- `execution-333504/OPERATOR.md` claimed the native pilot's 903-second
  termination transferred to the authoring vehicle. It did not: that vehicle
  had no reclaim at all.
- `execution-333707/HOLD.md` said the lease was **unenforced** on that
  vehicle. True of that one, and no longer true here — which is the whole
  point of the prerequisite.

Both documents are preserved with their original wording; this is the
correction, in the packet that is current.

## Measured requirement for the gate

`tests.manager.test_authoring_enforcement` spawns a **real** supervisor
subprocess and resolves
`work/records/2026/09/finding-v12-single-implementation-proof` from
`Path(__file__).resolve().parents[4]` — the checkout root. Measured both ways
this claim against a clean export of the declared base:

- without that directory present: **33 tests, 1 error** (the child cannot
  import `baseline`, so the partial-output file is never written), 0.439s;
- with it present: **33 tests, all passing**, 2.194s.

The private git-line checkout at the base carries it, so the gate is sound
there. It is pinned in `read_from_checkout_at_base` and stated here so nobody
rediscovers it inside a provider turn.
