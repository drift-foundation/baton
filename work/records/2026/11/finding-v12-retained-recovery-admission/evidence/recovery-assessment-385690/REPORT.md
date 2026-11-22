# W385624 retained-output recovery assessment — E385690 / M385688

2026-11-22, baton.codxpc. Assessment complete; Stage1-B candidate remains unreviewed. No implementation repeated, product edit, test run, live launch, old-store mutation, cleanup or protected Git mutation.

## Proven retained candidate and immediate review route

Candidate `5bc260b6dcbe970c8729424fa826b88dbc1a9d0f`, direct parent/base `ce6e1b2bf12519a84a3792f06562b7727dfe3021`. All 16 hashes in `../output-limit-recovery-20261122/manifest.json` match. The bundle verifies against its prerequisite. Reconstructed it in an independent bare repository by fetching the exact base from the main repository read-only, then the retained bundle. Compared all 31,734 tracked archive entries (path/type/mode/size/content or symlink target) to `git archive` of the bundle candidate: identical. Changed paths match all 30 result.json paths (12 v12 paths, 18 dossier paths). Extracted the validated archive with the data filter into confined scratch. No linked worktree, shared Git metadata, push or main-index write.

Reconstruction took 10.780 seconds; `reconstruct.py`, `git-reconstruction.log`, `RESULT.json` and `candidate-tree.json` retain reproducible proof. Tree inventory SHA256 `7ea90c89fe8c4f3b019d68580723e1f80fc2002c85bc40d975bd15b2ec635777`. Review workspace: `work/scratch/w385624-recovery-385690/candidate`; independent Git objects: sibling `objects.git`. Scratch is rebuildable, not the sole evidence copy. Required source, bundle and archive remain in the earlier durable dossier. Off-machine backup/checkpoint remains owner-owned; local preservation does not prove off-machine durability.

**Concrete route now:** coordinator routes W385624 to an independent reviewer through the existing v11 claim/pass protocol, binding the above candidate, base, tree inventory and original proposal hashes. Reviewer reads the reconstructed source and retained evidence and performs focused verification if assigned. This proceeds without implementation redispatch, importing the candidate or pretending native custody succeeded. It is independent source review, not completion of the failed native Job. Native automatic publication/review continuation is unavailable today.

Read-only candidate inspection (supported now):

```bash
git -C /home/sl/src/baton/work/scratch/w385624-recovery-385690/objects.git diff --stat ce6e1b2bf12519a84a3792f06562b7727dfe3021 5bc260b6dcbe970c8729424fa826b88dbc1a9d0f
```

## Failure and supported operations

The retained `proposal/result.json` reports provider exit0 and required verifier exit0. Outer verification log records 63/63 in 2.813s, zero failures/errors/skips. These are inherited execution evidence, not tests rerun or independent acceptance. Candidate's internal COUNTS/REPORT retain separate group results, failures/skips and incomplete tools-pure run; their baseline/environment classifications have NOT been independently accepted here. Do not collapse those results into an all-green candidate. Full substantive review remains outstanding.

Proposal four files total 1,147,926 bytes. `role_contract.py:99,202,413` supplies AND exact-validates 1,048,576 for every output, including proposal. `pool.py` composes these role descriptors. Worker `baton_worker.py:1631` measures the actual tree and refuses on overflow; `handle` calls `agent.work`, then `answered`/measurement, then `publish_completion` (around1950–1990). There is no post-agent publication-only operation. File exchange terminal is faulted/output, answers describe only, and has null disposition/manifest digest. `receipt.json` is command acceptance, NOT result custody. Manager `exchange.py:1393` validates null success fields on fault; `output.py:254` requires an observed terminal disposition before freezing, and `_check_limits` checks BOTH tree and artifact size against the original declaration. Raising a producer constant cannot change this admission's immutable input or supply its missing completion.

Current command inventory and candidate were inspected:

- `manager fresh-attempt` carries the original specification into a new attempt. It repeats implementation and retains old selected bounds; it is not publication recovery.
- `manager serve --once` reconciles known durable state; it is not owner-authorized publication under a changed limit.
- `tools.next_run recover` reports consumed runs without replay (or releases never-consumed reservations); it does not publish this candidate.
- Stage1-A `failure_analysis.py:433,468` requires verification-failed and frozen custody. This failure has successful verification and no custody. Retained Stage1-B's `recovery-item/recovery-decide` operates on that analysis/frozen-result lineage, not arbitrary unpublished output; Stage1-C execution is also separately undelivered. Do not use the unreviewed candidate to recover itself.
- **Supported resource-only path:** installed `manager settlement-preview`, `settle-stopped`, `settlement-status`. They retain bytes and record failed-stopped, leaving `result_consumption=unresolved`. They neither publish nor review. Read-only preview was run through the installed qualified executable; `settlement-preview.json` records eligible, trusted runtime quiescent, reserved=false, state=not-selected at19:22:29.082Z. No settlement executed. This is stronger current evidence than the earlier Docker snapshot, but not a committed release or custody receipt.

Supported commands, only if the owner selects retain-only resource settlement (not necessary to begin isolated source review, and not a workaround for publication):

```bash
/home/sl/baton-instances/native-w385624-admission-1/distro/baton-v12-stack manager settlement-preview --instance /home/sl/baton-instances/native-w385624-admission-1/instance.json --job w385624-native-admission-1 --stage w385624-native-admission-1/implementation --episode 1 --operation-id w385624-output-recovery-preview-385690
```

The exact request from the observed preview is retained in `settlement-request.json`. Execution revalidates exclusion and exact identities; a later refusal is preserved, not bypassed:

```bash
/home/sl/baton-instances/native-w385624-admission-1/distro/baton-v12-stack manager settle-stopped --instance /home/sl/baton-instances/native-w385624-admission-1/instance.json --document /home/sl/src/baton/work/records/2026/11/finding-v12-retained-recovery-admission/evidence/recovery-assessment-385690/settlement-request.json
/home/sl/baton-instances/native-w385624-admission-1/distro/baton-v12-stack manager settlement-status --instance /home/sl/baton-instances/native-w385624-admission-1/instance.json --document /home/sl/src/baton/work/records/2026/11/finding-v12-retained-recovery-admission/evidence/recovery-assessment-385690/settlement-request.json
```

No exact native resume command can truthfully be supplied: **missing capability is owner-authorized revalidation and publication of retained unpublished output into new accountable custody followed by linked independent review, without invoking implementation or falsifying the original terminal.** Do not change an old manifest, replay worker work, directly record a fabricated freeze, trim the reviewed proposal, or invoke fresh-attempt to hide this gap.

## Smallest separate delivery boundaries (recommendations, not new assignments)

1. **Proposal cap revision:** select a new role/template descriptor revision with proposal-only104857600 bytes. Existing exact revisions remain valid and unchanged; unrelated output byte limits,100-entry ceiling, links/media and other declarations remain unchanged. The shared MAX_OUTPUT_BYTES constant cannot simply become100MiB because that silently widens every output. Update producer and exact validator together, compose the selected revision, verify real admitted manifest and worker/manager enforcement at old/new boundary. Wire outputConstraints already permits100MiB (`max_bytes` maximum9007199254740991); no worker wire-schema enlargement needed. Qualification/build and selection apply to future admissions only. Distinct finite Work; no need to mix this with Stage1-B semantic review.
2. **Retained output-publication recovery:** a separate coupled outcome, owner inspect/approve → manager durable recovery intent → exact retained-byte revalidation and new custody → linked review handoff, with no provider implementation invocation and no repeated successful verification while exact evidence is valid. Reuse exchange identity, measurement, output/sealing owners, retained-candidate validation, owner authorization and manager stage admission. Must supply a supported CLI and actual production composition, not a library utility or receipt-writing script. Keep original failure and admission immutable, bind old attempt/command/input/output/candidate/verifier/context, selected limit descriptor and review profile/stages, new operation/lineage and bounded clocks. Verify writer cessation through host owner APIs and refuse unknown/changed bytes, stale authority, cancellation, replay collision, double collection/review and restart at every external-effect cut. Exercise real CLI through custody and review admission with fake provider boundary and zero implementation calls. Review uses existing substantive consumer only after valid custody. A new recovery execution may need fresh authority; never publish as the dead original generation. Valid source-level review may proceed independently but does not itself satisfy native recovery.

Shared ownership: cap revision owns role_contract/template producer composition and their tests. Recovery owns owner/manager recovery composition plus publication/sealing/exchange changes actually needed; serialize any shared descriptor or manager entry paths. Stage1-B candidate bytes remain pinned; W385625 retains its Stage1-C verification loop. Coordinator should create/bind separate Work and graph relationships before assigning those changes. No new unbound dossier or graph mutation made here.

## Normative amendment to pin before recovery implementation

Proposed bounded addition beside REC-8 and ART-8: “After completed implementation with retained output but failed output publication, the owner may authorize an exact corrective publication disposition. The manager must preserve the original admission, ending and evidence, validate retained identity/content and positive cessation, and append accountable recovery lineage under separately selected finite limits. It must resume publication/collection and independent review without redispatching implementation; still-valid successful verification is preserved. A stopped generation cannot publish as current. Unknown or invalid custody, bytes, authority, execution state or evidence must hold explicitly. Replay/restart must not duplicate publication, review or external effects. Changing a bound never rewrites a prior admitted manifest.”

Owner intent and100MiB selection are already pinned in FINDING; this assessment does not silently expand verification-only REC-8 or edit DESIGN. The separate recovery Work should pin the concrete amendment before coding. Remaining decision is delivery selection: immediate independent source review in parallel with the separate recovery capability, versus waiting for that capability to complete automatic native review. Neither requires another implementation of Stage1-B. Current assignment ends with this assessment and exact retained checkpoint, not acceptance of Stage1-B or completed native recovery.
