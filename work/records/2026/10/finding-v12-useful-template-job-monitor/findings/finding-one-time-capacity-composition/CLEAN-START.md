# Reproducing this preparation from a clean start

Review 2026-10-27T18-27-26Z [R3]: *"A reviewer should not have to patch the
script to reproduce its published command."* Nothing below reads a hidden
file, needs an environment variable, or asks you to perform a step by hand.
There is no `/tmp/distro.txt`.

Nothing is ever removed. **What each command writes is not uniform, and the
earlier version of this page said it was** — review 2026-10-27T23-11-07Z was
right that "writes only into a directory the invocation itself created" is
false for two of the commands below. The accurate split:

| command | writes |
|---|---|
| `capacity.py preflight` | **nothing**, unless `--evidence <dir>` is given |
| `capacity.py materialize` | **only** a directory it creates itself (`mkdtemp` under the scratch root, or `--into <a path that must not exist>`) |
| `capacity.py compose` | **nothing**, unless `--evidence <dir>` is given. It *reads* a proposal set and reports the files it opened under `effects.read`. |
| `proposed_grants.py` (publish) | **into this record**: `proposed-grants/` by default, or wherever `--into` names. This is the publisher; writing is its job. |
| `proposed_grants.py --verify` | **nothing** |
| `prove_capacity.py`, `prove_guide_contract.py`, `prove_custody.py` | only directories they create under the scratch root, plus `--evidence <dir>` where given |

`--evidence <dir>` writes wherever you point it, **including inside this
record** — that is how the `evidence/claim-*/` directories were made. Every
command reports those writes in its own `effects.wrote`; none is hidden.

## Prerequisites — all two of them

1. This checkout at the selected revision `42bed8bb04a53380e565b1a63fb2bc702677f0d0`.
   `preflight` refuses if the checkout is elsewhere, and so does `compose`.
2. A disk-backed scratch root that already exists. The bound finding names
   `/var/tmp/baton-w257624`; any existing directory works via `--scratch`.
   Nothing here creates the scratch root: inventing one is the operator's
   decision, not this preparation's.

No container engine, no credential provider, no network and no build.

## The three entrypoints

```sh
cd work/records/2026/10/finding-v12-useful-template-job-monitor/findings/finding-one-time-capacity-composition

# READ-ONLY. Creates nothing, extracts nothing, removes nothing. Reports the
# selection, the archive identity, the derived paths and -- before anything is
# done -- the operator grants this preparation cannot resolve.
python3 capacity.py preflight

# Extracts the retained runtime into a directory it CREATES with mkdtemp and
# uniquely owns, verifying the archive sha256 AND the extracted folder digest.
# It retains what it made. `--into <path>` is refused if the path exists.
python3 capacity.py materialize

# Emits the two-lane bootstrap document for a MINTED identity. Writes nothing;
# reads nothing but the checkout. The uuid is read back from
# <destination>/authority-identity.json after the mint; `compose` refuses
# anything that is not 32 hex characters.
python3 capacity.py compose --minted-uuid <minted> --destination <dest>
```

### Binding a proposal set — the set and the task must match

A proposal set is composed **for one task**. The format addendum changes the
task, which changes the rendered role instructions, so the default set and the
formatted set are **different sets**. `compose` holds the set's inventory to
the task it is binding, so the two forms below are the two that work, and they
pair a set with its own task:

```sh
# THE DEFAULT SET, with the default task. Succeeds.
python3 capacity.py compose --minted-uuid <minted> --destination <dest> \
    --proposed-grants

# THE FORMATTED SET, with the formatted task. Succeeds.
python3 capacity.py compose --minted-uuid <minted> --destination <dest> \
    --grants-from proposed-grants-format --proposed-format
```

Both write nothing. Each reports the eight files it opened — the inventory and
the seven artifacts — under `effects.read`, and both still answer
`preparation_is_complete: false`.

**Mixing them is refused, on purpose.** This is *not* a usable command and an
earlier version of this page wrongly advertised it as one:

```sh
# EXPECTED REFUSAL (exit 2): the default set against the formatted task.
python3 capacity.py compose --minted-uuid <minted> --destination <dest> \
    --proposed-grants --proposed-format
```

    refused: the published proposal set at …/proposed-grants was composed for
    task digest c21e6b93bfe199eb (proposed_format=False) and this composition
    is binding task digest cb7001c74de828ab (proposed_format=True). Their role
    instructions differ, so these are different sets. Publish the one you want
    and point at it … Nothing was written.

`prove_custody.py` drives all three of these — both successes and this
refusal — so the page and the commands cannot drift apart silently.

Every entrypoint also accepts `--evidence <dir>` and then writes `<verb>.json`
there. That write goes wherever you point it, **including inside this
record**, and is reported in `effects.wrote`.

## The seven proposed policy artifacts

```sh
python3 proposed_grants.py                    # publishes proposed-grants/
python3 proposed_grants.py --verify           # READ-ONLY: set vs inventory
python3 proposed_grants.py --print-rendered   # and the two role prompts

# the format-selected variant is a DIFFERENT SET -- its role instructions
# differ -- so it is published explicitly, somewhere of its own:
python3 proposed_grants.py --proposed-format --into proposed-grants-format
```

**This is the publisher, so writing is its job — and it writes into this
record**, at `proposed-grants/` or wherever `--into` names. What it will not
do is write over a set composed for a *different* task: that is refused by
name, with the remedy. Composition is the other side of the split: `compose`
*reads* a published set, holds every file to that set's own `INVENTORY.json`,
and writes nothing.

Two sets are published in this record, with distinct identities: the default
`proposed-grants/` and `proposed-grants-format/`. Only `role_instructions`
differs between them, because only the role prompts depend on the task text.

Each set's seven artifacts: five are **reused** from content that already
exists at the selected revision
— the product's own two prompt composers rendered for this task, the worker
image recipe, `ARGV_POLICY`/`ENVIRONMENT_POLICY`, the reviewed manifest's
source consumption, the reviewed worker's credential profile. Two are
**authored** from documented deployment values because the product ships no
such document: the resource policy and the network policy. Every one carries
`status: "proposed-not-granted"` and `authorized_by: null`.

**None of them is a grant.** Binding a set is an opt-in, and with all seven
bound `preparation_is_complete` is still `false` — the accounting just moves
those members from `unresolved-grant` to `proposed-grant`, each naming the
artifact and what it still needs: an owner's selection. Current inventory
digests, neither granted: default
`6ae52f7b2b796fe1bae8323155513fb8f751e182f4a48a0dffbb577243284add`,
formatted `e57d3ed180400a12b8fd4992cd1eafdae894101d4f93fe18415585bfd7fb9a18`.

## The joined proof

```sh
python3 prove_capacity.py                       # materializes its own runtime
python3 prove_capacity.py --distro <folder>     # reuses a verified one
python3 prove_capacity.py --evidence evidence/<claim>
```

Eleven steps: mint only → readback → compose → ONE destination install →
`DeploymentDerivation` → ordinary `manager create` → the refusals (stale
source, *malformed* authority identity, wrong retained artifact, occupied
materialization target, a moved manifest member against the seal) →
`preflight` writes nothing, **measured** by digesting the whole child
directory either side of the call → a **well-formed** foreign authority
identity offered to a freshly minted instance and to `create` → the whole
chain again with the seven proposed artifacts bound READ-ONLY, in both
variants, plus the refusal when one set is bound to the other's task → **the
custody guard over the whole run**, digesting every file under the child
directory before anything happens and again at the very end.

`--distro` no longer leaves the named folder to the installer: it is measured
with `instance.manifest` and held to the retained archive's recorded folder
digest first, and refused if it does not match.

Exit 0 means every step reached its expected outcome. The answer carries
`not_established`, which says plainly what was *not* shown.

## The task's verification contract

```sh
python3 prove_guide_contract.py
```

Eighteen cases. It reproduces the inherited pilot contract's **false success**
(exit 0 with the deliverable absent), then drives fourteen refusals — two of
them by this build's own parsers — and three passes.

**The six headings are a selection, not the parent's criteria.** By default
there is no format gate at all, and a differently organised guide covering the
same ground *passes* — case
`differently_organised_guide_passes_by_default`. With `--proposed-format` the
same file is refused, and the task's own instructions carry the addendum that
announces exactly what will be checked. The earlier claim that USEFUL-JOB.md
enumerates those headings was inaccurate and is withdrawn.

`fixtures/qualifying-TEMPLATE-JOBS.md` is a **verification fixture, not the
deliverable**. Writing `v12/TEMPLATE-JOBS.md` is the Job's own work.

## The custody guard over the public commands

```sh
python3 prove_custody.py
```

`prove_capacity.py`'s step 11 guards one invocation of itself. This guards the
commands as a **set** — eleven public subprocess runs including both opt-ins
in both orders and two whole proofs, then the three custody refusals — and
digests the child directory and the published inventory around all of it.
Nothing appears, vanishes or is rewritten, and every claim binding's proposal
digests still hold.

The defect it exists for was an ordering effect: `compose` used to publish,
so whichever variant ran last silently won.

## What a clean start will NOT give you

`preparation_is_complete` is **false**, by design and in every answer —
with the proposal bound as well as without it. Seven operator grants in the
input manifest have no owner selection; `provenance.members` names each one,
what it names, and what it still needs. This is a reusable preparation with a
real connected proof and a concrete proposal to decide on — not a finished
operational configuration.

`compose_capacity.py` is superseded and its entrypoint refuses. Its body is
retained as a record of the attempt.
