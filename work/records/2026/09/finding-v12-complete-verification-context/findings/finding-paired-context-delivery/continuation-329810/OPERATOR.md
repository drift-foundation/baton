# Owner operations — W321776 continuation packet

**Nothing below has been executed against the selected root.** Every command is
labelled with who runs it and what it does. The preparation steps were exercised
once into the throwaway root `/tmp/w321776-preflight-329810` and the results are
in `PREFLIGHT.json`; the **selected** root is untouched, no Job is submitted, no
engine or container was invoked, no provider was contacted and no credential was
read.

Selected identities:

| element | selection |
| --- | --- |
| declared base | `bbdacb5d38f6cf2d2461e9da103d28f9ab30cc6c` (this tree's committed HEAD, compared twice this claim) |
| run identity | `paired-context-w321776-329810` |
| selected root | `/home/sl/baton-instances/paired-context-w321776-329810` (does not exist; `stage` refuses reuse) |
| worker image | `baton-v12-claude-worker:w239528-244216`, config digest `sha256:c862c055c6430addc918ca078a9e4d55f6bd8173ed9c9878a8ad9d6cad334ca2` — existing, unchanged, **not rebuilt** |
| manager runtime | `/home/sl/baton-runs/managed-correction-236087/build/stack/out/distro`, binary `sha256 04aa459a…`, build commit `1e576ff2` |
| manager source | 112 files from `v12/python/{src/baton_v12,tools}` **at the declared base**, staged into the root's own `code/` |
| supervisor | `work/records/2026/09/finding-v12-single-implementation-proof/baseline.py` at the declared base (`c1b0a10e…`), with `baseline_bindings.py` and `prepare_instance.py` |
| launch envelope | `baton.dogfood-task/2`, `source_root` `source`, `source_profile` `git-line` |
| terminal policy | `report-and-hold`; one implementation invocation, no automatic retry |

## Step 0 — read-only input check (anyone, any time)

```
python3 -B /home/sl/src/baton/work/records/2026/09/finding-v12-complete-verification-context/findings/finding-paired-context-delivery/continuation-329810/verify-inputs.py
```

Opens no store and writes nothing. It verifies every pinned input against the
tree, the declared base's own bytes for each restored path, the bootstrap
binary, and that the task carries the exact load command for the exact
`restore.py` bytes. **Run this first**; a drifted input means this packet is
describing something that is no longer there.

## Step 1 — stage (owner)

```
python3 -B <packet>/prepare.py stage --root /home/sl/baton-instances/paired-context-w321776-329810
```

Creates the root `0700`, refuses an existing one, writes the base's manager and
supervisor source into it, and emits `bootstrap-inputs.json` and `stage.json`.
Starts nothing.

## Step 2 — bootstrap this instance's own authority (owner)

```
cd /home/sl/baton-instances/paired-context-w321776-329810/code/v12/python
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/home/sl/baton-instances/paired-context-w321776-329810/code/v12/python/src:/home/sl/baton-instances/paired-context-w321776-329810/code/v12/python \
python3 -B -m tools.bootstrap \
  --inputs /home/sl/baton-instances/paired-context-w321776-329810/bootstrap-inputs.json \
  --destination /home/sl/baton-instances/paired-context-w321776-329810/instance \
  --distro /home/sl/baton-runs/managed-correction-236087/build/stack/out/distro \
  --no-repositories
```

The supported bootstrap. `--no-repositories` is deliberate: this instance binds
no Job and configures no execution capacity until `bind` runs.

## Step 3 — bind (owner)

```
python3 -B <packet>/prepare.py bind --root /home/sl/baton-instances/paired-context-w321776-329810
```

Composes the packet documents, writes them under `<root>/packet/`, then proves
them: `held_packet` re-pins every artifact the packet binds — including each of
the 13 `fixture.files`, so a drifted preserved buffer refuses here rather than
inside a turn — and `verify_imported_sources` proves this process is running the
staged code and not some other checkout. Ends with
`PREPARED.json: state prepared-not-executed`. **No Job is submitted.**

## Step 4 — start (OWNER'S ACT, NOT AUTHORIZED BY THIS PACKET)

The reviewer's return states plainly: *no launch authorized*. The start command
is recorded so the owner does not have to reconstruct it, and it is the owner's
decision to run it after this packet passes independent review:

```
# from <root>/packet/commands.json, "start"
/usr/bin/python3 -B <root>/supervisor/baseline.py \
  --packet <root>/packet/PACKET.json \
  --incarnation paired-context-w321776-329810
```

`commands.json` also carries the read-only `status` invocation and records
`submission_owner: "start; do not also submit manually"`. SIGINT/SIGTERM
requests the supervisor's bounded cancellation and accounting; a held outcome is
**not** proof of cessation.

Before starting, the owner must confirm the credential profile this packet
names resolves in their **own** private registry
(`/home/sl/.baton/credential-sources.json`, slot `claude`, reference
`w202663-development`). This packet reads no credential and carries no bearer.

## Step 5 — after the run (owner, then an independent reviewer)

The retained proposal is immutable and is **not** an accepted candidate. An
independent reviewer consumes it through v11 after exact runtime cessation;
there is no automatic integration and no self-acceptance. A failed or partial
run is preserved and reported with its evidence rather than retried silently.

## Two things the owner should decide before step 4

1. **The bounds may be too small.** `LIMITS-CHECK.json` records the tension:
   this packet carries the accepted W321780 table (900s turn, 1500s total), and
   the comparable implementation Job in this campaign (W321528) selected 3600s
   with a 4200s total and still spent its turn. A paired two-materializer change
   is larger than that slice. Raising an accepted bound is the owner's act, so
   it is flagged and not raised.
2. **W325695 overlaps.** It owns the verifier-descriptor-in-descendant-processes
   defect and touches worker and test paths; it is currently open and unclaimed
   at `baton.decide`. The task text forbids redesigning the verification
   environment or altering `TMPDIR` to force a green run, but concrete disjoint
   ownership or serial selection between the two is a coordination decision, not
   something this packet may assert.
