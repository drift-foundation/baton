# Preparation complete — owner selection next

baton.claude, W177936 claim 178367, under owner reroute M177951. Dossier-only
preparation is complete and returns to `baton.ops`.

- **`PACKET.md`** SHA256 `be5076943897be157240c8cd48af1db754a61d102030d830d895a8f1b2d8de86`
  is the concrete qualification packet: confirmed evidence versus gaps, the one
  remaining experiment with its exact shape and bounds, its acceptance evidence,
  proposed paths and the serial handoff order.
- **`BASELINE-177936.json`** SHA256 `f2f0b8abed95ad4f0e55387e23dba960fefd8f047df9429c23235276473e949e`
  records the nineteen read inputs at their exact bytes, the two live image
  digests, and the `claude_agent.py` provenance note. All five required inputs
  named in `FINDING.md` were present and readable; none is reported missing.

## What changed about the problem

**The argv half of the qualification is already answered, and by an artefact the
design did not cite.** `evidence/offline-transport-pass-2026-09-07.json` in the
W106673 dossier is an operator-run offline probe *inside the pinned image*, with
no credential, no network and no model call, and it records `--session-id`,
`--resume` and `--model` as present in the installed 2.1.247 help. **No help or
version probe needs to be repeated**, and the same artefact is explicit that
visibility is not behaviour — it carries `restore: "unproved"`,
`session_continuity: "unproved"`, `real_turns: 0`.

**The custody half is confirmed, not open.** The assignment lists "protected
custody readable under actual Docker manager/runtime UIDs" as a fact to qualify;
it is an already-shipped, already-measured mechanism — fixed uid 65532 plus
`--group-add <configured workspace group>`, manager roots at `0o2770` setgid so
worker-created entries come back in the manager's group, and `0o640` for a file
the runtime must read (the W52800 ruling, found by a real failure where `stat`
succeeded and `open` did not). It has three shipped instances and a real-daemon
proof in W105706, closed satisfying. The proposed `context_storage` is a new
instance of it, not a new mechanism.

**The open fact is narrower and sharper than "the one-shot layout".** Every
retained behavioural observation of this CLI was made in `stream-json` mode, and
**the two facts the production receipt must carry — the conversation identity and
the actual model — were both read from the `system`/`init` frame, which one-shot
`--output-format json` does not emit.** `PACKET.md` §3 tables fourteen dimensions
of the accepted W106673 experiment against the current production `_provider`;
**three transfer.** The production path today composes no `--model`, no
`--session-id` and no `--resume` at all, runs at `/output` rather than
`/session/work`, and gives the CLI a fresh cache and a fresh home where the
experiment retained both whole.

## The one experiment, and why it is one

Two containers, two user turns, the second created only after confirmed shutdown
— W106673's accepted envelope, 180 s per turn inside 600 s.

**Its defining property is not restoration.** That is already proved. It is
restoration **from a home the manager rebuilt out of a named, credential-free
subset**, because that is the only thing the design needs and the only thing
still unknown. A turn 2 that completes from a retained whole home would prove
nothing this campaign does not already have.

It cannot usefully be split: G1 and G2 need a real turn, and G3–G5 are only
decidable by a second turn that succeeds from a reconstructed home. G6 is one
observation inside it. **A failed qualification is a result** — it selects a
different layout, and widening the copy until it passes is named and closed.

## Gaps, for the record

G1 one-shot identity fields · G2 `--resume` composed with one-shot JSON ·
G3 the minimal credential-free layout · G4 cwd `/output` · G5 fresh
configuration and cache · G6 a group-writable setgid HOME · **G7 the selected
image digest, which is an owner selection and not an experiment** — two digests
are live in this tree and retained interface evidence binds to `979f11d5…` only
· G8 `--max-turns` is absent from this build's help while the accepted
experiment composed it.

## Serial order and recommended execution scope

1. **W61599 holds `claude_agent.py`** and its five other paths under M177542; its
   candidate is with `baton.feat` at seq 178359. §2.3 records that its diff is
   199 insertions with no deletions and touches none of `PROVIDER_ARGUMENTS`,
   `_closed_environment`, `EPHEMERA_ROOTS`, `_checked_directory` or
   `_provider_diagnostic`, so every source fact in this packet holds at the
   accepted baseline too — but the profile must be certified against its
   accepted bytes.
2. **Owner selects the image digest** before the fixture is composed.
3. **baton.tuner is the recommended execution claimant**, per this dossier's
   PLAN: compose the fixture and its offline tests, produce the manifest, hand
   the exact operator command back for approval, and on results produce the §6
   export plus a pass/fail record per gap. **It may not certify a profile, edit a
   product path, or run the experiment on its own approval.** The fixture is
   independently reviewed before it runs and the operator invocation is a
   separate explicit approval — W106673's discipline, not relaxed here.
4. **W161234 slice B still waits** on W61599's shared-file release; its
   deterministic path does not need this qualification and is not blocked by it.

## Limits

Preparation only. No product or test file edited, no test, probe, provider,
model, engine, build, installation or Git operation. **New measured verification
0 s.** Nothing protected was opened — no credential, transcript, session file,
private workspace or W106673 original. This packet authorizes no experiment; it
is a proposal for owner selection and independent review. It is not a new release
gate, reopens no architecture review and reclassifies no Work. W177937 and
W177938 remain unstarted and in their recorded serial order.
