# Owner operations — W333486 execution packet

**Nothing below has been executed against the selected root.** Every command is
labelled with who runs it and what it does. The preparation steps were
exercised once into the throwaway root `/tmp/w333486-preflight-333504` and the
results are in `PREFLIGHT.json`; the **selected** root is untouched and does
not exist, no Job is submitted, no engine or container was invoked, no provider
was contacted and no credential was read.

Selected identities are in `PACKET.md`. In short: base
`bbdacb5d38f6cf2d2461e9da103d28f9ab30cc6c`, run
`attempt-diagnostics-w333486-333504`, selected root
`/home/sl/baton-instances/attempt-diagnostics-w333486-333504`, existing image
`baton-v12-claude-worker:w239528-244216`
(`sha256:c862c055c6430addc918ca078a9e4d55f6bd8173ed9c9878a8ad9d6cad334ca2`,
not rebuilt), manager runtime
`/home/sl/baton-runs/managed-correction-236087/build/stack/out/distro`.

Let `<packet>` be
`/home/sl/src/baton/work/records/2026/10/finding-v12-attempt-failure-diagnostics/execution-333504`
and `<root>` be `/home/sl/baton-instances/attempt-diagnostics-w333486-333504`.

## Step 0 — read-only input check (anyone, any time)

```
python3 -B <packet>/verify-inputs.py
```

Opens no store and writes nothing. It proves every pinned input against the
tree, the declared base's own bytes for all 112 manager files and 3 supervisor
files, the bootstrap binary, that the task and the sealed gate name the same
two new modules, and that neither module the turn must create already exists.
Measured 0.108s. **Run this first**; a drifted input means this packet is
describing something that is no longer there.

Two of the seven task inputs — this dossier's `FINDING.md` and `PLAN.md` — are
the reviewer's to own. If a review appends to either before you start, this
check refuses. The correct response is to have the packet **re-sealed at the
new bytes**, not to edit a pin.

## Step 1 — stage (owner)

```
python3 -B <packet>/prepare.py stage --root <root>
```

Proves every base byte **before** creating anything, then creates the root
`0700`, refuses an existing one, writes the base's manager and supervisor
source into it, and emits `bootstrap-inputs.json` and `stage.json`. Starts
nothing. A refused stage leaves the filesystem exactly as it found it.

## Step 2 — bootstrap this instance's own authority (owner)

```
cd <root>/code/v12/python
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=<root>/code/v12/python/src:<root>/code/v12/python \
python3 -B -m tools.bootstrap \
  --inputs <root>/bootstrap-inputs.json \
  --destination <root>/instance \
  --distro /home/sl/baton-runs/managed-correction-236087/build/stack/out/distro \
  --no-repositories
```

The supported bootstrap. `--no-repositories` is deliberate: this instance binds
no Job and configures no execution capacity until `bind` runs. It generates
**this instance's own** authority uuid — the one in `PREFLIGHT.json`
(`f72d08c1…`) belongs to the throwaway preflight and is not a proposed
production identity. Expect your composed packet digest to differ from the
preflight's for the same reason: `bind` derives the Work id from the authority
uuid (`uuid[:8] + "-W1"`) and that travels into the submission. The pinned,
stable half is the input side, which `verify-inputs.py` and `held_packet`
check.

## Step 3 — bind (owner)

```
python3 -B <packet>/prepare.py bind --root <root>
```

Composes the packet documents under `<root>/packet/`, then proves them:
`held_packet` re-pins every artifact the packet binds — including each of the
seven `fixture.files`, so a drifted document refuses here rather than inside a
turn — and `verify_imported_sources` proves this process is running the staged
code and not some other checkout. Refuses a root that already holds a composed
packet. Ends with `PREPARED.json: state prepared-not-executed`. **No Job is
submitted.**

## Step 4 — start (OWNER'S ACT, NOT AUTHORIZED BY THIS PACKET)

The reviewer's current position is that no launch is authorized. The command is
recorded so you do not have to reconstruct it, and selecting this run is your
decision after this packet passes independent review:

```
# from <root>/packet/commands.json, "start"
/usr/bin/python3 -B <root>/supervisor/baseline.py \
  --packet <root>/packet/PACKET.json \
  --incarnation attempt-diagnostics-w333486-333504
```

`commands.json` also carries the read-only `status` invocation and records
`submission_owner: "start; do not also submit manually"`. SIGINT/SIGTERM
requests the supervisor's bounded cancellation and accounting; **a held outcome
is not proof of cessation.**

Before starting, confirm the credential profile this packet names resolves in
your own private registry (`/home/sl/.baton/credential-sources.json`, slot
`claude`, reference `w202663-development`). This packet reads no credential and
carries no bearer.

## Three things to know before step 4

1. **An unchanged host lease may stop this turn at 900 seconds.** This base
   does not carry sibling W333485's renewal correction — that is the very
   defect this campaign is correcting. The packet requests a 3600-second
   provider turn and `tokens.LIFETIME_SECONDS` is still 900 with
   `renewals=0`, which is exactly how the native pilot was terminated at 903s.
   No long-run claim is made and no bypass is attempted. `TASK.md` instructs
   the turn to preserve a partial candidate and account for it honestly if that
   happens — and such a termination would itself be further evidence for this
   Work, reportable through the correction it is asking for.

2. **The verification ceiling is 30 seconds and is not this packet's to set.**
   The composer fixes it at 30 in both places it appears
   (`baseline_bindings.py:345` and `:522`), with no compose parameter. The nine
   existing gate modules measure 11.83s, leaving ≈18.17s for the two the turn
   must write. `LIMITS-CHECK.json` reports what the generated documents say
   rather than what prose wishes.

3. **Two test modules are excluded from the gate and both already fail at this
   base**, for reasons that predate this Work: `tests.manager.test_boundary_inventory`
   (328 tests, 28 failures, 1 error, 49.469s on base bytes) and
   `tests.tools.test_packaging`'s subcommand case, which holds the source
   command table against the **installed bundle** — and that bundle was built
   at `1e576ff2`, before `record` and `disposition` joined the table, so it
   fails on this host today with `'disposition' not found`. Any future Work
   that adds a packaged subcommand hits the same case. `PACKET.md` records both
   so neither is attributed to this candidate.

## Step 5 — after the run (owner, then an independent reviewer)

The retained proposal is immutable and is **not** an accepted candidate. An
independent reviewer consumes it through v11 after exact runtime cessation;
there is no automatic integration and no self-acceptance. A failed or partial
run is preserved and reported with its evidence rather than retried silently.
The parent W325959 consumes this result jointly with W333485, and the human Git
checkpoint the parent PLAN carries remains pending.

## Retained temporary paths

Left in place for you rather than removed, because a managed turn does not
issue a destructive shell command merely to tidy its own reproduction. None is
the selected root; none holds a credential or a submitted Job.

- `/tmp/w333486-preflight-333504` — the exercised preparation root
- `/tmp/w333486-probe-drift` — the staged-but-unbound root the drift probe used
- `/tmp/w333486-base-probe` — a clean `git archive` export of the declared base,
  used for the gate measurements
