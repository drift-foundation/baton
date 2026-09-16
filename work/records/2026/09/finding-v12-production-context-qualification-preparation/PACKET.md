# Production context qualification — preparation packet

Prepared by baton.claude, W177936 claim 178367, under owner reroute M177951.
**Preparation only.** No product or test file was edited, no test was run, no
live model or actual engine was invoked, nothing was installed and nothing was
enabled. All writes are inside this dossier.

**No protected or private material was opened.** Every fact below comes from
repository source or from retained nonsecret evidence already committed to this
tree. The protected W106673 originals under `/tmp` were not read, and no
credential, transcript, session file or provider prose was inspected.

This packet answers the question `DESIGN.md` §5 left open, as far as retained
evidence can answer it, and names exactly what is left.

> "For the pinned CLI/image, can one-shot open then restore at `/output`
> preserve the same actual conversation using only the selected credential-free
> project state, a fresh credential slot and fresh HOME configuration/cache;
> which exact bounded result fields prove session, terminal success and actual
> model?"

## 1. Headline

**Three of the four qualification topics are further along than the design
assumed, and one of them is already answered.** The fourth — the provider's
one-shot persistence and identity behaviour — is not answerable from anything in
this tree, and the reason is specific rather than general: **every retained
behavioural observation of this CLI was made in `stream-json` mode, and the two
facts the production path needs are carried by a frame that one-shot mode does
not emit.**

The smallest remaining experiment is therefore **one** two-turn qualification,
and its defining property is not restoration — that is already proved — but
**restoring from a reconstructed minimal home rather than a retained whole one.**

## 2. What is confirmed, and by what

### 2.1 The argv vocabulary is already qualified at the pinned image

`evidence/offline-transport-pass-2026-09-07.json`
(`sha256:1c8db12a082ceddfb1c01d89511446726f10faa3d3e93d6d548af33aa85cf9f9`)
in the W106673 dossier is an operator-run, independently observed offline probe
**inside image `sha256:979f11d53433f2930d69b70d81e265332547895cbd674e3e8b190cafb236243f`**,
with no credential, no network and no model call. It records
`version: "2.1.247 (Claude Code)"` and a per-flag help inventory:

| Flag | Present in the installed CLI's help |
| --- | --- |
| `--print`, `--output-format`, `--input-format`, `--verbose` | yes |
| `--session-id`, `--resume` | **yes** |
| `--model` | **yes** |
| `--dangerously-skip-permissions`, `--tools`, `--setting-sources`, `--strict-mcp-config`, `--mcp-config`, `--max-budget-usd` | yes |
| `--max-turns` | **no** — absent from help on this build |

**So no help or version probe needs to be repeated.** `--session-id`, `--resume`
and `--model` exist on the exact pinned build the design proposes to compose.

That same artifact is equally explicit about what it does **not** establish, and
`OFFLINE-HELP-CHECKPOINT.md`
(`sha256:3c58a5f48428234fee08c41a0dc75798d675ab62dd41fca06d4ce1e7df7def09`)
states the rule in terms: *"Successful help output is a useful inventory, not
evidence that an omitted option is rejected by the parser."* The artifact records
`restore: "unproved"`, `session_continuity: "unproved"`, `real_turns: 0` and
lists `--resume`, `--session-id` and `--model` under `unexercised_flags`.

**Help visibility is not behaviour, and this packet does not treat it as such.**

### 2.2 Protected custody under the real Docker manager/runtime identities is
### answered, and the mechanism is already in production

This is the topic the assignment names fourth, and it is the one that is
**confirmed** rather than open.

| Fact | Source |
| --- | --- |
| The execution container is fixed at `--user 65532:65532`, `--cap-drop ALL`, `--read-only`, `--security-opt no-new-privileges` | `oci.py` `RESTRICTIONS` (`sha256:b842e605671b222d467c8d5e6abdb13628946984d9a467372f01b4bec92fc9c1`) |
| The manager cannot `chown` to that uid and does not try. The grant is a **supplementary group**: `--group-add <configured workspace group>`, composed only for an `execution` posture, refused outright when unconfigured | `oci.run_vector` |
| Manager-owned roots the runtime must write are `0o2770` — group write **plus setgid**, so entries the worker creates inherit the directory's group and the manager can read them back | `workspaces.WORKSPACE_DIR`, `adopt_workspace_group` |
| A manager-owned file the runtime must **read** is `0o640` in that same group, with `other` empty — the W52800 ruling, found by a real failed attempt where `stat` succeeded and `open` did not | `credentials.VOLATILE_FILE`, `_reader_group` |
| The exchange event namespace already uses this same arrangement for a second, non-workspace manager-owned root | `exchange.materialize` → `workspaces.adopt_workspace_group` |
| The arrangement is **measured against a real daemon**, not argued: W105706 closed satisfying on accepted live runtime evidence with host group `baton-workspace` gid 1001 and image `sha256:0697b6595aff0af2a39a81d492223bf33cf69877426ec859fe1abb90abd617e4` | `work/records/2026/09/finding-v12-private-line-runtime-access/PLAN.md`, review-2026-09-07T12-52-22Z.md |

**The proposed `context_storage` is a new instance of an already-proved
mechanism, not a new mechanism.** `DESIGN.md` §4's `0700` manager parents plus
"the established dedicated runtime-identity/group access arrangement" is exactly
this, and it needs no separate custody experiment.

**One small behavioural sub-fact is genuinely open inside it**, and it is worth
naming because it is the class of thing that has cost this campaign three
attempts before: the per-use HOME is `0o2770`, group-writable and setgid, and
**some programs refuse to use a group-writable configuration or state
directory.** Whether this CLI does is unobserved. It is a one-line observation
inside the experiment of §5 and needs no run of its own.

### 2.3 The current production one-shot path, read from source

`v12/worker/claude_agent.py` at the bytes now in the tree
(`sha256:a6f934eaa5cf37fbed0ae7edc7f0521bb42566d4a0753cd939b4c148625b4529`).

**Provenance note, stated rather than assumed.** Those bytes are W61599's
candidate, passed for independent review at seq 178359 and not yet accepted.
`git diff HEAD` over that file is **199 insertions and no deletions**, and none
of `PROVIDER_PROGRAM`, `PROVIDER_ARGUMENTS`, `_closed_environment`,
`EPHEMERA_ROOTS`, `_checked_directory` or `_provider_diagnostic` appears on a
changed line. Every fact below therefore holds equally at the accepted baseline
`sha256:c7a2b746fbefc088a7670c6f1a3c6363d0faeadcb08d27c56c8f6819ae0f979c`.

| Fact | Where |
| --- | --- |
| `PROVIDER_ARGUMENTS = ("--print", "--dangerously-skip-permissions", "--output-format", "json")` — **no `--model`, no `--session-id`, no `--resume`, no tool or settings policy** | `claude_agent.py:211` |
| For the Git line profile the candidate **is** `OUTPUT_ROOT`, so the one-shot cwd really is `/output` | `work`, W105575 comment |
| The child environment is composed member by member and is exactly `HOME`, `PATH`, `PYTHONPYCACHEPREFIX`, `TMPDIR`, `XDG_CACHE_HOME`. `os.environ` is never consulted | `_closed_environment` |
| `XDG_CACHE_HOME` already points **inside per-turn scratch** and is discarded with it | `EPHEMERA_ROOTS` |
| `CLAUDE_CONFIG_DIR` is **not set**, so the CLI uses its own default relative to `HOME` | same |
| `_checked_directory` requires `HOME` to be **beneath this turn's scratch**, at mode `0700`, every component proved | `_closed_environment`, `_checked_directory` |
| `_prepared_home` creates `$HOME/.claude` at `0700` containing exactly one entry — the credential **symlink** to `/run/baton/credentials/claude` | `_prepared_home` |
| stdout is drained continuously, bounded at 64 KiB retained, parsed strictly (duplicate keys, `NaN`/`Infinity`, `RecursionError` all refuse) and then **discarded**; a status-0 turn parses nothing at all | `_ran_provider`, `_provider`, `_provider_document` |
| The fields this module already reads from a one-shot record are `type`, `subtype`, `is_error`, `terminal_reason`, `api_error_status`, `result` — pinned from the installed 2.1.247 authentication branch | `_provider_diagnostic`, `PROVIDER_OAUTH_EXPLANATION` |

`evidence/failure-reason-112817/transport-contract.json`
(`sha256:880a5bc279ac820cb1224f6c43f6e96ac92501d95120684306363553c1dcb2a9`)
independently binds `result.api_error_status` to the public SDK `ResultMessage`
type and records `selected_cli_field_emission_observed: false`. It is the
precedent this packet follows: an interface fact taken from a public source,
with the un-observed half said out loud.

### 2.4 The image pin

`v12/worker/Dockerfile.claude` pins `ARG CLAUDE_VERSION=2.1.247` and
`USER 65532:65532`, and builds `/home/nonroot/.claude` owned by that uid. The
recipe is explicit that **the artefact is selected by digest, not rebuilt**, and
that three inputs move between builds.

**This is a gap in the qualification, and it is an owner selection rather than
an experiment.** Two digests are live in this tree: `979f11d5…`, which carries
every retained CLI-interface and restoration observation, and `0697b659…`, which
superseded it for the private-line access proof and *not* for the detach
experiment. **No digest is currently selected for a context-qualified production
profile.** Whichever is selected, the §5 experiment must run on that one; retained
interface evidence transfers to `979f11d5…` only.

## 3. What the accepted W106673 evidence does and does not transfer

`review-2026-09-07T20-20-41Z.md`
(`sha256:d757acbe3bc1e82f65a4b3d4b21c7957e0b2159f62f5eb1933eeb3c4d8b2771f`)
accepts a real restored conversation: CLI 2.1.247, actual model
`claude-fable-5`, session `869bb45a-…` identical before and after, workspace
`[43, 11799375]` identical, CLI process replaced across two containers after
**confirmed** old-container shutdown, and a useful multiply-by-2 to multiply-by-3
correction verified by a token the reviewer never reopened.

**That conversation really was restored, and this packet does not propose
re-proving it.** What it cannot certify is the production profile, and the reason
is a list rather than a caveat. Reading the retained fixture source
`evidence/live_supervisor_result_diagnostics.py`
(`sha256:94c6dd20122131f2a67bcd00c50d55e94ac5b65f14d648f036d8532fcf0cca41`):

| Dimension | W106673, accepted | Production `_provider`, current source | Transfers? |
| --- | --- | --- | --- |
| Output mode | `--input-format stream-json --output-format stream-json --verbose` | `--print --output-format json` | **no** |
| Model attested by | the `system`/`init` **frame's** `model`, checked `== ACTUAL_MODEL` | one-shot mode emits no init frame | **no** |
| Session attested by | the `system`/`init` frame's `session_id`, plus per-turn result | — | **no** |
| Terminal success read from | `result` frame `subtype` and `is_error`, closed vocabulary | the same two are reachable; nothing else is read | partly |
| Conversation selector | `--session-id` / `--resume` composed | neither is composed at all | **no** |
| Model pin | `--model claude-fable-5[1m]`, observed `claude-fable-5` | **no `--model` argument exists** | **no** |
| cwd | `/session/work` | `/output` (Git line) | **no** |
| HOME | `/session/home`, **retained whole across containers** | fresh `scratch/home`, destroyed with the turn | **no** |
| Config dir | explicit `CLAUDE_CONFIG_DIR=$HOME/.claude` | unset; CLI default | **no** |
| Cache | `XDG_CACHE_HOME=/session/cache`, **retained** | fresh under scratch, **discarded** | **no** |
| Extra env | `DISABLE_AUTOUPDATER=1`, `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1` | neither | **no** |
| Tool / settings / MCP policy | `--tools Bash,Read,Write,Edit --setting-sources= --strict-mcp-config --mcp-config '{"mcpServers":{}}'` | none | **no** |
| Turn and budget bounds | `--max-turns 8 --max-budget-usd 1` | none | **no** |
| Credential | `$HOME/.claude/.credentials.json` symlink to the fixed read-only slot | **identical** | **yes** |
| CLI build | 2.1.247 | image pins 2.1.247 | **yes** |
| Runtime uid | 65532 | 65532 | **yes** |

Three rows transfer. **The two facts the production receipt must carry — the
conversation identity and the actual model — were both read from a frame that
`--output-format json` does not produce**, and the accepted review records the
model as observed at initialization rather than in a terminal document.

**No retained artifact in this tree contains a one-shot `--output-format json`
success record.** The only one-shot field set anything here has seen is the
2.1.247 *authentication-failure* branch pinned in `_provider_diagnostic`. So
whether a successful one-shot document carries a session or model member is
**unobserved in both directions** — this packet does not claim they are absent.

## 4. The gaps, stated exactly

**G1 — one-shot identity fields.** Which members a successful
`--print --output-format json` record carries on this build, and specifically
whether any of them attests the conversation UUID and the actual model. Nothing
retained observes this. *Blocks:* the receipt contract, the profile's
accepted-actual-model rule, and `DESIGN.md` §5's "which exact bounded field".

**G2 — `--resume` composed with one-shot JSON.** `--resume` and
`--output-format json` are each present in help; that they compose, and that a
resumed one-shot turn actually continues the conversation rather than starting a
fresh one under the supplied id, is unobserved. *Blocks:* the whole restoration
contract on the production path.

**G3 — the minimal credential-free state layout.** `DESIGN.md` §5 proposes
retaining only the project conversation subtree beneath `.claude/projects` for
the fixed cwd. The accepted experiment retained the **whole** `/session/home`
**and** a retained `/session/cache`, and deliberately exported no file layout.
So neither the project-key encoding for cwd `/output`, nor the file naming rule,
nor — critically — **sufficiency** is established. *Blocks:* what the manager
promotes into an immutable generation.

**G4 — cwd `/output`.** Every retained observation ran at `/session/work`. If the
project key is derived from cwd, `/output` produces a different key, and the Git
line profile makes `/output` the candidate tree itself. *Blocks:* the state
layout and the profile's fixed-cwd binding.

**G5 — fresh configuration and cache.** The production path gives the CLI a
fresh `XDG_CACHE_HOME` per turn and sets no `CLAUDE_CONFIG_DIR`; the experiment
retained both. Whether resume survives a cold cache and a reconstructed config
is unobserved. *Blocks:* "fresh HOME configuration/cache" in the design question.

**G6 — a group-writable, setgid HOME.** §2.2. One observation, no separate run.

**G7 — the selected image digest.** §2.4. An owner selection, not an experiment.

**G8 — the missing `--max-turns`.** Absent from help on this build while the
accepted experiment composed it. Not on the production path today and not a
blocker, but a profile that names it would be naming a flag this build's help
does not list. Recorded so it is not rediscovered.

## 5. The smallest remaining experiment

**One two-turn qualification, in one shape, answering G1–G6 together.** Splitting
it would not reduce it: G1 and G2 need a real turn, and G3–G5 are only decidable
by a second turn that succeeds from a *reconstructed* home.

**Its defining property is not restoration.** W106673 already proved restoration
by retaining a whole home. This experiment must prove restoration **from a home
the manager rebuilt out of a named, credential-free subset** — because that is
the only thing the design actually needs and the only thing still unknown.

### Shape

Two containers of the pinned, owner-selected image, the second created only
after **confirmed shutdown** of the first, reusing W106673's accepted
shutdown-receipt discipline rather than inventing another.

**Turn 1 — open.** Exactly the production argv plus the two composed operands:

```text
claude --print --dangerously-skip-permissions --output-format json \
       --model <pinned> --session-id <manager-minted uuid> <prompt>
```

cwd `/output`, `HOME` a per-use directory in the configured workspace group at
`0o2770`, `$HOME/.claude/.credentials.json` a symlink to the fixed read-only
slot, `XDG_CACHE_HOME`/`TMPDIR`/`PYTHONPYCACHEPREFIX` fresh, no
`CLAUDE_CONFIG_DIR`, nothing else in the environment. The prompt carries a
private token and asks for a small verifiable artefact, as W106673's did.

Capture, before the container is stopped: the **whole terminal JSON document's
member names and a closed projection of their values** (§6), the container exit
status, and a **relative path listing with per-file size and digest** of
everything the CLI created beneath `HOME` — **paths and digests only, never
bytes**.

**Between the turns — the act that makes this experiment worth running.** The
manager-side collector selects, from that listing, only the entries the proposed
`claude-project-session/1` layout names. It then builds turn 2's home as a
**fresh directory** containing only those entries, a fresh credential symlink and
nothing else: no cache, no config store, no debug log, no history, no
`.credentials.json`, no entry the layout does not name. Confirm the first
container is stopped and its shutdown receipt consumed.

**Turn 2 — restore.** The identical argv with `--resume <same uuid>` in place of
`--session-id`, cwd `/output`, the reconstructed home, a fresh credential slot
and a fresh cache. A fixed correction prompt that does **not** repeat the token,
exactly as W106673's did.

### What each gap gets from it

| Gap | Answered by |
| --- | --- |
| G1 | turn 1's captured member set and closed projection |
| G2 | turn 2 producing a completed turn bound to the same conversation |
| G3 | turn 2 succeeding from **only** the promoted subtree; the listing names the layout exactly |
| G4 | both turns run at `/output`; the listing shows the project key for it |
| G5 | turn 2's home has a fresh cache and no retained config |
| G6 | turn 1 running at all under a `0o2770` setgid HOME |

### Bounds and prohibitions

Two containers, **two user turns total**, one model call each. Per-turn ceiling
180 s, whole experiment inside 600 s including the ending, matching the accepted
W106673 envelope. No performance claim, no ratio, no cached-token savings, no
detach, no third turn "to be sure", no whole-home fallback, and **no unrecorded
retry**: a failed turn 2 is the answer that the selected layout is insufficient,
and it is reported as that rather than repaired by widening the copy until it
passes. If widening is proposed, the exact added entries and the reason go back
for selection before any rerun.

**This packet authorizes none of this.** It is a proposal for owner selection and
independent review, exactly as `DESIGN.md` §5 and `EXECUTION-B-177536.md` §7
require.

## 6. Acceptance evidence for that experiment

Nothing below may carry provider prose, transcript content, a credential, a
private token, a host path from inside the private roots, or a state file's
**bytes**.

1. **Provenance**, in W106673's form: image digest, CLI version read from the
   artefact, both container ids, labels, network, restrictions, the operator
   invocation and the fixture source digest.
2. **Both argv vectors, verbatim**, minus the prompt text, with the prompt's
   SHA-256 in its place. The two must differ in exactly one operand.
3. **Turn 1's terminal record, projected closed**: the sorted list of top-level
   member names; `type`; `subtype` classified over
   `{success, missing, known-nonsuccess, unknown, wrong-type}`; `is_error` over
   `{false, true, missing, wrong-type}`; the presence and **exact string value**
   of any member naming a session or a model; `api_error_status` if present.
   `RESULT-DIAGNOSTICS.md`'s vocabulary is reused rather than re-invented.
   **Unknown member names are listed by name and never by value.**
4. **Turn 2's same projection**, plus the equality of its conversation identity
   with turn 1's and with the manager-minted UUID.
5. **The `HOME` listing after turn 1**: relative paths, sizes, SHA-256s, file
   types. Any entry that is a symlink, device, socket or hardlink is named as
   such. **An entry whose name or path indicates a credential store refuses the
   whole capture** rather than being filtered out quietly.
6. **The promoted subset**, as the exact subsequence of (5) the layout selected,
   and the turn-2 home listing proving it contains that subset, one credential
   symlink and nothing else.
7. **Confirmed shutdown** of container 1 before container 2 is created, with the
   consumed receipt, in W106673's accepted form.
8. **The correction artefact's digest**, and an independent verifier's accept or
   reject of the private token — the token itself never leaving the fixture.
9. **Both container exit statuses and an independent engine observation** of
   stopped state, as `docker-inspect.json` carried for W106673.
10. **An explicit negative list**: every flag composed that this build's help did
    not list (today, `--max-turns`), and every field the design hoped for that
    turn 1's record did not carry.

**The qualification passes only if turn 2 completes, is bound to turn 1's
conversation, and its home was built from the promoted subset alone.** A turn 2
that completes from a retained whole home proves nothing this campaign does not
already have.

**A failed qualification is a result.** It selects a different layout or a
different mode; it is not a reason to relabel the deterministic profile as
production-qualified.

## 7. Proposed paths and change boundaries

**Nothing here is assigned by this packet.** These are proposals for owner
selection, and the serial order of §8 governs.

### Preparation and experiment artefacts — this dossier only

| Path | What |
| --- | --- |
| `work/records/2026/09/finding-v12-production-context-qualification-preparation/PACKET.md` | this document |
| `.../HANDOFF.md` | the handoff, linking this packet and its baseline |
| `.../BASELINE-177936.json` | the read-input hashes recorded at preparation |
| `.../evidence/qualification-fixture.py` *(proposed, absent)* | the supervisor/controller for §5, written and independently reviewed **before** any operator invocation, following W106673's fixture form |
| `.../evidence/qualification-manifest.json` *(proposed, absent)* | binds the fixture, its offline tests and the reviewed operator command |
| `.../evidence/qualification-export/` *(proposed, absent)* | §6's evidence, nonsecret only |

### Product paths this qualification would then unblock — **not this Work**

The profile constants it settles belong to slice A/B under W161234 and are
listed here only so the boundary is explicit:
`v12/python/src/baton_v12/worker_manager/provider_context.py` (the
`baton.claude-context-profile/1` values) and
`v12/worker/claude_agent.py` (the composed argv and the terminal parser).
**This packet proposes no edit to either**, and W61599 holds `claude_agent.py`
until its review completes.

### Explicit exclusions

No `Dockerfile.claude` edit, no image build or pull, no `DEPLOYMENT.md` change,
no schema number reserved, no `oci.py` user or root change, no chmod of a
protected root, no UID override, and no weakening of `_checked_directory` to
admit an arbitrary external HOME. `EXECUTION-B-177536.md` §7 names each of these
as a way to make a run pass without qualifying anything, and this packet keeps
all of them closed.

## 8. Serial handoff requirements

1. **W61599 first.** Its six source and five test paths, including
   `claude_agent.py`, are owner-selected ahead of this work (M177542), and its
   candidate is with `baton.feat` at seq 178359. No qualification artefact may
   edit those paths, and the argv/environment facts in §2.3 must be re-read
   against its accepted bytes before a profile is certified. §2.3 already records
   that its diff is purely additive and touches none of them.
2. **Owner selects the image digest** (G7) before the experiment is composed.
   Retained interface evidence binds to `979f11d5…` only.
3. **The fixture is independently reviewed before it is run**, and the operator
   invocation is a separate explicit approval — W106673's accepted discipline,
   which this packet does not relax.
4. **baton.tuner is the recommended execution claimant**, per this dossier's
   PLAN. Its scope is: compose the §5 fixture and its offline tests, produce the
   manifest, hand the exact operator command back for approval, and on results
   produce the §6 export plus a qualification record stating pass or fail per
   gap. **It is not authorized to certify a profile, edit a product path, or run
   the experiment on its own approval.**
5. **W161234 slice B still waits** on W61599's shared-file release and on this
   qualification for the production-enabled configuration; B's deterministic path
   does not need it and is not blocked by it.
6. **This is not a new release gate.** It completes an existing required outcome.
   No architecture review is reopened and no Work is reclassified.

## 9. What this preparation did not do

No product or test file edited. No test, probe, provider, model, engine, build,
installation or Git operation. **New measured verification: 0 s.** Source reads
and hash comparisons are preparation evidence, not executed acceptance.

Nothing protected was opened: no credential, no session file, no transcript, no
private workspace, and none of the W106673 originals. Every artifact cited is
already committed to this repository.

Two inputs named in FINDING.md — `EXECUTION-B-177536.md` and `HANDOFF-B-177536.md`
— were read at the hashes in `BASELINE-177936.json` and are consistent with this
packet; `EXECUTION-B` §7 independently reaches the same conclusion about what
W106673 does not certify, from the other side of the boundary.
