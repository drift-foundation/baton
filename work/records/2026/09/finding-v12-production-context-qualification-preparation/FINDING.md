# V12: Prepare production context qualification packet

Work: 2b077949-W177936. Consumer: W161234, contributing to W2.

## 2026-09-15 — owner-selected parallel preparation

Slawomir confirmed the three-task proposal with "I agree with the plan". Owner approved this preparation on 2026-09-15. Assign baton.codex source/nonsecret-evidence-first preparation for W161234 production context qualification: pinned one-shot Claude CLI at /output, minimal credential-free saved-state layout, actual terminal conversation/model/success fields, and protected custody readable under actual Docker manager/runtime UIDs. Reuse W106673 evidence; distinguish confirmed facts from gaps. Produce exact smallest remaining experiment, acceptance evidence and proposed paths; no live model, actual engine execution, tests, installation, implementation or production enabling. Incoming release candidate reviews take priority; return baton.ops with complete packet or concrete missing evidence. Own only this new dossier.

This is preparation for existing required outcomes, not a new release gate. W61599 retains first shared serving-file ownership; W161234 B waits for its independently reviewed final candidate and file release. No backlog copy, authority cutover or v13 expansion.

## Required inputs

- baton:work/records/2026/09/finding-v12-correction-restart-proof/PLAN.md
- baton:work/records/2026/09/finding-v12-correction-restart-proof/EXECUTION-B-177536.md
- baton:work/records/2026/09/finding-v12-correction-restart-proof/HANDOFF-B-177536.md
- baton:work/records/2026/09/finding-v12-context-reuse-design/DESIGN.md
- baton:work/records/2026/09/finding-v12-live-session-workspace-detach/review-2026-09-07T20-20-41Z.md

## 2026-09-15 — owner reassigns all three preparation packets to Claude

Slawomir subsequently directed: "let's have Claude work on the prep-work, claude is nearly done with her work and she can jump on that". This explicitly supersedes the Codex/tuner assignments in the preceding three-packet selection. Assign W177936, W177937 and W177938 to baton.claude, serially after the current W61599 implementation handoff: production context qualification first, viewer activity connection second, final correction/restart C proof packet third. Do not interrupt or release Claude's W61599 claim. If W61599 returns for an in-scope correction, complete that release work before further preparation. Codex remains available for independent reviews.

The preparation-only scope, durable dossier ownership and acceptance boundaries remain unchanged. No implementation, tests, live provider/actual engine execution or production enabling is added. W161234 B still awaits W61599's independently reviewed shared-file release. Priority selects qualification ahead of the other two; the two remaining low-priority items retain their creation order and explicit serial instruction.

## 2026-09-15 — Claude prepares; tuner implements downstream work

Slawomir added "tuner can do the work" after assigning the preparation packets to Claude. The working division is Claude for W177936/W177937/W177938 preparation and baton.tuner for downstream implementation once the concrete packet is selected and required inputs/file ownership are ready. This clarifies the prior assignment; it does not move the three preparation Works back to tuner. Each preparation handoff must recommend the exact tuner execution scope and evidence references. W161234 B still follows W61599 independently reviewed shared-file release. Preparation-only authority remains unchanged; this role selection is not a claim, an unbounded implementation assignment or authorization for a live qualification experiment.

## 2026-09-15 — preparation complete (claim 178367)

Two facts from this round change the shape of the remaining work and are worth
keeping beyond the packet.

**The argv half was already qualified, by an artefact the design did not cite.**
`work/records/2026/09/finding-v12-live-session-workspace-detach/evidence/offline-transport-pass-2026-09-07.json`
is an operator-run offline probe inside the pinned image — no credential, no
network, no model call — and it records `--session-id`, `--resume` and `--model`
as present in the installed 2.1.247 help, with `--max-turns` absent. So no help
or version probe needs repeating. The same artefact is explicit that visibility
is not behaviour: it carries `restore: "unproved"`, `session_continuity:
"unproved"` and `real_turns: 0`, and `OFFLINE-HELP-CHECKPOINT.md` states the rule
in terms.

**The accepted restoration evidence cannot certify the production profile for a
reason that is a list rather than a caveat, and the sharpest item is one line.**
Every retained behavioural observation of this CLI was made in `stream-json`
mode, and the two facts the production receipt must carry — the conversation
identity and the actual model — were both read from the `system`/`init` frame.
One-shot `--output-format json` emits no such frame. Of fourteen dimensions
compared between that experiment and the current production `_provider`, three
transfer: the credential arrangement, the CLI build and the runtime uid.

**And the custody question was not open.** Manager-owned roots readable and
writable across the real Docker manager/runtime identities is an already-shipped,
already-measured arrangement — fixed uid 65532 plus `--group-add` of the
configured workspace group, `0o2770` setgid directories so worker-created entries
return in the manager's group, and `0o640` for a file the runtime must read. It
has three shipped instances and a real-daemon proof in W105706, closed
satisfying. What remains inside it is one small behavioural unknown: whether this
CLI will use a group-writable, setgid HOME at all.

Deliverables: `PACKET.md`
`sha256:be5076943897be157240c8cd48af1db754a61d102030d830d895a8f1b2d8de86`,
`BASELINE-177936.json`
`sha256:f2f0b8abed95ad4f0e55387e23dba960fefd8f047df9429c23235276473e949e`,
and `HANDOFF.md`. All five required inputs were present and readable.
Preparation only; new measured verification 0 s.

## 2026-09-15 — owner178575 selects tuner fixture preparation, claim178579

Owner178575 selects PACKET sections5–8 and image
sha256:979f11d53433f2930d69b70d81e265332547895cbd674e3e8b190cafb236243f
for qualification only. This supersedes the preparation stop and pending image
choice for this bounded fixture; no production deployment or live execution is
selected. W61599 correction was handed off at178569 before this claim. Tuner
owns only this dossier, including evidence/qualification-fixture.py, its worker
helper, offline tests, manifest, exact operator recipe and evidence. Return
baton.feat focused fixture review then baton.ops live-run decision. No product
edits, broad suites, build/pull, live models or actual engine operations.

BASELINE-178579.json revalidates every prior input by hash. W61599 claude_agent
bytes changed under tuner correction178427; its provider argv/environment
contract is unchanged, and no accepted-final product qualification is asserted.

Preparation clarifications, explicitly superseding inconsistent packet phrases:
- The selector flag and prompt change; UUID/model stay fixed. It is not a
  one-operand argv difference. Hash both prompts separately.
- Two user-turn CLI invocations do not mean two provider API calls. Internal
  model/tool calls and billing are not hard-bounded by this fixture. Retain
  180s per invocation/600s overall, no --max-turns or unselected argv expansion.
- The known credential symlink is excluded without reading its target; any
  unexpected credential-shaped entry refuses capture/promotion. The literal
  demand to reject every credential-looking entry would reject the required link.
- Raw arbitrary member/path names can carry private data. Public export carries
  known field names and only exact pinned session/model values; other names are
  represented by digests/counts. Full relative metadata stays protected.
- The subset is selected before turn2 by an exact bounded shape: one observed
  project directory beneath .claude/projects and its exact expected UUID.jsonl,
  no other session or nested files. The project key is observed, not inferred
  from /output. Additional required entries produce failure, never adaptive copy.
- The group grant mechanism is established, but actual CLI-created modes may
  deny manager reading. This fixture will not normalize protected state or
  weaken permissions to make qualification pass. Such a failure is evidence
  against this instance and its claimed sufficient custody arrangement.
- Host collection and artifact verification happen only after positive stopped
  inspection with PID0 and receipt consumption; the supervisor captures bounded
  terminal projection before exiting. This replaces the ambiguous pre-stop
  host listing instruction and avoids a mutable-state capture.

All generated context files remain private opaque bytes. The fixture never
claims universal credential detection within provider-created transcripts.

## 2026-09-15 — fixture178579 complete; live qualification still unselected

The dossier now contains the bounded two-turn controller, closed contract and
in-image supervisor, with manifest `26a0f74254f88d49e02420c05b242c3349dc6b30b567666928be7290019ded2f`.
OPERATOR-178579.md is the exact proposed command and remaining live question.
This completes only owner178575 preparation; it supersedes the older current
action wording that fixture composition and qualification image choice were
still pending. Original PACKET.md/HANDOFF.md bytes remain chronological evidence.

Twenty-two offline tests pass against the final candidate, including shutdown
receipt ordering, private-field projection, UID/GID/mode capture, exact subset
selection, no-widening refusals, uncertain cleanup, lost-create recovery, and
bounded local process cleanup. Four measured iterations total 1.054891332s.
No actual engine, model, credential source or protected live transcript was used.
The model/modelUsage field mapping and one-file state layout are explicit
qualification hypotheses; fake fixtures do not establish them for the CLI.
Independent fixture review goes to baton.feat, then baton.ops decides the exact
live run. Production enabling and acceptance remain separate.

## 2026-09-15T14:36:52Z — independent fixture review requests R1/R2

baton.codex claim178808 reviewed exact manifest
26a0f74254f88d49e02420c05b242c3349dc6b30b567666928be7290019ded2f.
review-2026-09-15T14-36-52Z.md SHA256
e1107c43c598da0e8f9b20ca2679efa7ecc8b7c8b4df0709eb972c40de92a231 and
review-evidence-178808.json SHA256
847f3f96ab2adc0e6be57dc0e46e6127d620b24bc0163a60e8bc7b92e4c2e180 bind the
concrete review. The26 inventoried inputs matched before and after execution;
all22 original focused offline tests passed independently. Two additional probes
confirmed fixture gaps, with no actual controller/engine/provider admission.

R1: reconstruction creates a manager-owned0640 session file, readable but not
file-writable by the selected different runtime UID65532. The same-UID fake
reports qualified while masking this difference. This is confirmed metadata;
actual Claude failure is not asserted, since a writable parent permits replacement
and the CLI write strategy remains unobserved. Resolve the intended writable-use
mode (new copies only) or explicitly select the narrower read-only input meaning
before treating a result as qualification of the accepted writable-use profile.

R2: an existing export root does not refuse run admission. The offline probe
reached controller-process construction and created the other fixed markers;
the export directory is only created after the live work in the actual path.
Reserve/check all fixed identities before any controller/credential admission,
without repairing foreign paths, and add negative coverage for every root.

This supersedes awaiting-review as the current action. Return baton.ops for
bounded correction disposition before live selection; no automatic implementation
or live run is authorized here. Positive shutdown/order, closed projection and
bounded-pipe observations remain recorded, but fixture acceptance is withheld.
Measured reviewer supervisor0.26373039101599716s, no timeout, no test threads,
owned process group absent. Author1.0548913319944404s remains separate.

Canonical W161234 at snapshot178831 is active with tuner claim178810 after
owner178645 shared release, so the handoff's pending-shared-release language is
historical. This review does not interrupt B or add a gate/consumer edit. G1–G6,
production enabling and live-result acceptance remain unqualified/separate.
No product/test-candidate/PROGRESS/Git edits, live credentials, protected live
transcripts, actual engine, model, build/pull, installation or broad suite.


## 2026-09-15 — advance W177936 with bounded R1/R2 correction by Claude

Slawomir asks to advance W177936. At snapshot178870 the fixture review requests two bounded corrections; tuner is actively implementing W161234 B and Claude is free. Assign baton.claude the correction, without interrupting B. This supersedes the prior tuner-only preparation/correction scheduling and pending correction selection; the selected qualification-only image, two-turn experiment bounds and separate live-run decision remain unchanged.

Read review-2026-09-15T14-36-52Z.md (SHA256 e1107c43c598da0e8f9b20ca2679efa7ecc8b7c8b4df0709eb972c40de92a231). R1: new reconstructed per-use session working-copy files must be writable by the selected runtime UID through the configured supplementary group; use a distinct working-copy creation mode0660 with other access absent. Do not change immutable source snapshots, observed CLI-created state, credentials, request files or existing protected objects. Add focused effective owner/group access checks instead of relying on a same-UID fake alone. R2: reserve/refuse all three fixed run, volatile and export roots before controller/credential/engine admission; preserve existing foreign paths and partial-preflight accounting, with one negative case per root.

Own only this dossier's evidence/qualification-fixture.py, evidence/qualification_contract.py if needed, evidence/test_qualification.py, updated manifest/operator packet and attributable progress/candidate/evidence records. Keep the qualification worker unchanged unless the exact R1/R2 correction demonstrably requires it and the reason is recorded. Revalidate current candidate first. Run focused offline tests and R1/R2 checks only, bind fresh candidate hashes and cleanup evidence, then baton.feat independent review and baton.ops for the exact live-run decision. Routine R1/R2 corrections may return to this same scope without a new architecture cycle; no scope expansion.

No live provider/engine, image build/pull, product edit, broad suite, baseline repair or production enabling is authorized. The real CLI write strategy remains unobserved; R1 fixes the known working-copy permission mismatch, not a claimed observed vendor failure. Preserve old evidence and measured/estimated history. This assignment adds no gate to W161234 B.

## 2026-09-15T14:51:59Z — independent acceptance of correction178875

baton.codex claim178923 accepts the corrected offline fixture bound by manifest
73fe32b941b2c82bc0f7bc87a4fa512854dfd64b17b4c8656752607f45dc0481.
The append-only review is review-2026-09-15T14-51-59Z.md, SHA256
2995243fa8353018fc5ee89171146f40cf6e1a30db4c09a01044064873b1c022;
review-evidence-178923.json has SHA256
44a161d9fc0d7d21959b3b429ad5450f95133283e9f145c7fc1cf92c8b7829b1.
All six candidate files matched their inventory before and after verification;
retained base and candidate bytes were checked independently.

R1 and R2 are resolved. Reconstructed per-use state is created0660, request
objects remain0640, and the controller probe preserved source metadata and
copied bytes. Every fixed root is reserved before controller construction;
negative tests cover existing roots and partial reservation cleanup. The older
OPERATOR-178579.md sentence grouping reconstructed files under0640 is explicitly
superseded by its Correction178875 section and owner178872's0660 ruling.

All29 focused offline tests passed independently with an additional controller
metadata check. The reviewer supervisor measured0.41404445900116116s, with no
timeout, live test threads or remaining owned process group. This is fake-engine
and filesystem evidence, not an actual runtime UID or vendor CLI execution.
Author correction verification0.2638512429839466s remains separately attributed;
negative-probe iteration durations are unknown. Prior author and reviewer costs
remain preserved in the review. No broad suite or baseline investigation ran.

This acceptance supersedes pending R1/R2 correction and fixture review as the
current action. Return to baton.ops for owner selection of the exact live command
and claimant. No live execution or production enabling occurred or is authorized
by this review; G1–G6 provider facts remain unqualified and live-result acceptance
remains separate. This adds no dependency or interruption to W161234 B.

## 2026-09-15T15:08:40Z — operator's failed live result; assessment before correction

Slawomir supplied the failed result of the exact OPERATOR-178579.md command,
authorized the read-only diagnostic and asked to advance W177936. This records
observed execution, not a retroactive claim or invented approval receipt. At
snapshot179060 Work remained unclaimed at baton.ops, episode178960.

Public evidence is retained in operator-result-2026-09-15T15-08-40Z/:
- qualification.json SHA2567ac89dac9d7e1457b553b761d406187958866d5c7bbe373280834753ddf5ecfc;
- PROVENANCE.json SHA25627649d4ddfcfaba5b9f20e79e84a2011433bef4a8cc3899b048189b64d02f368;
- diagnostic.json SHA2562695e882e7192e724a6ad8124e8d15f8ebe268b02ce07dc813788b37ae7977ee;
- diagnostic.py is the exact read-only metadata/byte-comparison tool.

The export hash matches its provenance and names accepted manifest73fe32b941b2c82bc0f7bc87a4fa512854dfd64b17b4c8656752607f45dc0481.
No private prompts, transcripts, credentials, arbitrary filenames or artifact
contents were copied into this evidence. Original private run/markers remain.

**Observed:** initial-artifact failure at first-turn, elapsed8.666650786995888s.
One provider invocation is observed, exit0, terminal success and matching session
ID. The receipt records stopped PID0 and consumed shutdown before the artifact
check and confirms final container/network cleanup. No second turn, collection
or reconstruction occurred: this does not establish restoration failure.

**Confirmed by diagnostic:** only solution.py exists, a38-byte regular file.
Exact comparison fails; CRLF normalization does not resolve it; stripping outer
whitespace matches the expected bytes. Thus the immediate refusal is an outer-
whitespace mismatch. The exact-byte contract was not met and is not relaxed here.
Diagnostic UID/GID values (including65534) describe the prompt filesystem view;
do not equate them with actual Docker manager/runtime identities in the receipt.

**Separate evidence gap:** modelUsage is present but fails the expected singleton
model-key check; actual_model is null and model_fields is empty. The worker
projects anonymous stdout without retaining original provider JSON. This export
cannot distinguish wrong type, empty/multiple keys or another model name. Do not
infer the actual model or seek it by opening private session transcripts.

**Next:** managed independent result/provenance assessment, then a concrete
correction recommendation to baton.ops. Assess exact-byte fixture control versus
a narrowly specified outer-whitespace rule with negative coverage; recommend
minimal safe model-field diagnostics without exporting prose/private state or
silently accepting another model. Neither issue is yet independently classified
as a fixture defect. No fixture/product/test edits, tests, live provider/engine,
image work, private transcript/credential inspection, new run identity or rerun
is selected by this assessment. A subsequent candidate needs selection/review.

This supersedes pending first live-run selection as the current action. Preserve
earlier fixture acceptance and this failed outcome. G1 is partial; restoration
facts remain unobserved. No production enabling or new W161234 gate follows.

## 2026-09-15T15:16:11Z — independent result assessment, claim179084

review-2026-09-15T15-16-11Z.md assesses owner179075's supplied result without a
rerun, test or private inspection. review-evidence-179084.json SHA256
0426aaea3744868859c7e2637eae07b41f3d5bc07dd3131fbc5483c6a7471975 records18
public/candidate input hashes and14 matching static consistency checks. The
export/provenance and accepted178875 fixture bytes agree. Accept the evidence
as a failed first-turn result, not as production qualification. Cleanup is
confirmed by the retained receipt, not by a fresh engine observation.

**Confirmed refinement of the preceding diagnostic:** INITIAL is39 bytes with
only one outer whitespace byte, a final LF. Its stripped form is38 bytes; the
actual file is38 bytes and strips to that same form. Therefore actual already
equals INITIAL without its final LF. The mismatch is exactly the missing final
newline. This follows from the public diagnostic and source constants; no private
file was reopened. The exact-byte guard correctly refused the selected contract.

**Proposed, not selected:** accept solution.py in both turns either exactly as
the expected constant or with its single final LF absent. No other whitespace
normalization, code change, file-set change or continuity-token relaxation.
Record observed raw hashes rather than continuing to label constant hashes as
observed after normalization. The review enumerates focused positive/negative
coverage and the exact dossier-only correction paths.

**Confirmed diagnostic limitation:** model is absent and modelUsage is present
but does not match the expected singleton model key. The projection cannot tell
wrong type, empty, other singleton or multiple keys apart. No actual model is
established. Recommend bounded closed type/cardinality/expected-key diagnostics,
with no arbitrary names/values and no change to actual-model acceptance. The
original provider JSON was not retained; private state inspection is not a repair.

This supersedes pending independent assessment as the current action: return
baton.ops to select the concrete correction, followed by independent fixture
review and a separate live-run decision. No correction execution, tests, live
run, new run identity or marker reset is authorized by this assessment. Preserve
the failed result and prior acceptance. Operator elapsed8.666650786995888s;
new runtime verification0s; prior author/reviewer durations remain attributed
in the review. Restoration was not attempted; G1 is partial, G4/G6 first-use
only, G2/G3/G5 remain unobserved. No production enabling or W161234 gate.

## 2026-09-15 — owner179142 selects the bounded artifact/model correction (claim179146)

Slawomir selected the correction proposed by assessment179084 and routed it to
baton.claude: accept `solution.py` only as the expected bytes with or without
its single final LF, preserve every other byte, the file sets and the continuity
contract, export observed raw hashes and closed artifact diagnostics, and add
bounded model diagnostics without relaxing actual-model acceptance or exporting
private values. This supersedes pending correction selection as the current
action. Bases were revalidated before any edit: the four fixture files match
accepted manifest `73fe32b941b2c82bc0f7bc87a4fa512854dfd64b17b4c8656752607f45dc0481`
and OPERATOR-178579.md matches `e504579fb99ec837d5522a0184906fda3ffb01a3830cbe5e1274af800b5ba323`.

**THE ACCEPTANCE SUPERSESSION, PINNED BEFORE THE EDITS.** The selected artifact
contract for `solution.py`, in BOTH turns, is now exactly two forms: the expected
constant, or that same constant with its one final LF absent. This explicitly
supersedes the exact-final-LF requirement that FINDING's 178579 entry and
OPERATOR-178579.md stated, and it supersedes nothing else. `strip()`, Unicode
normalization, AST equivalence, CRLF conversion and general whitespace tolerance
are named and excluded: an extra final LF, any leading whitespace, horizontal
trailing whitespace, altered indentation, an altered multiplier, an added comment
and any extra or missing workspace entry all still refuse. **`continuity.txt`
keeps its exact token-plus-LF contract unchanged** — no observation in this
campaign supports moving it, and the failed run never reached it.

**Why the old guard was not a defect.** The exact-byte guard enforced the
contract that was selected, and the provider-created file did not meet it. The
change is a fixture acceptance decision about a formatting sensitivity that is
irrelevant to this experiment's multiply-by-two/three and continuity question; it
is not a bug fix, and it does not convert the failed run into a pass. That run
remains a failed first-turn qualification.

**A constant is not an observation.** The old export named `sha(INITIAL)` and
`sha(CORRECTED)` as `initial_artifact_sha256`/`corrected_artifact_sha256`. That
was harmless only while equality was exact. Under a two-form rule a constant
digest under an observed-sounding name would be a false record, so expected and
observed are now separately named and the observed raw digest, byte length and
`exact`/`missing-final-lf` classification are exported BEFORE any refusal.

**Model diagnostics record the reason, not the model.** `modelUsage` was present
and failed its exact singleton-key predicate; `model` was absent. Wrong type,
empty object, another singleton key and multiple keys are indistinguishable in
the retained projection, and the original provider JSON was never retained. The
correction adds closed type/cardinality/expected-key diagnostics and changes the
`actual_model`/`model_fields`/conflict predicate NOT AT ALL. Neither an
expected key inside a mixed object nor the matching `--model` argument qualifies
a model; missing, malformed, conflicting and other-only stay unqualified, and no
arbitrary key, value, usage payload, provider prose or raw JSON is exported.

Scope: dossier only — `evidence/qualification_contract.py`,
`evidence/qualification-fixture.py`, `evidence/test_qualification.py`, the
manifest and OPERATOR-178579.md. The worker is unchanged; it forwards the closed
projection whole, so the new members reach the controller without a worker edit.
No product or consumer path, live execution, engine, model, credential use,
image work, marker reset or new run identity. The consumed fixed identity is not
reused: a future run belongs to a separately selected, digest-bound operator
packet. G1 stays partial with no accepted actual model, G4/G6 first-use only,
G2/G3/G5 unobserved, G7 qualification-only, G8 omitted. Production qualification
and enabling remain incomplete; W161234 B remains independent.

## 2026-09-15T15:39:27Z — independent correction review requests diagnostic R1

baton.codex claim179242 reviewed exact candidate179146/manifest
9a1ddd250da674e956c707f043830863d74db9074814b5050dff5d5c6c5b78ff.
review-2026-09-15T15-39-27Z.md requests one bounded correction before fixture
acceptance: consistent() does not cross-check singleton/cardinality/overflow or
known member presence. Four deliberately malformed records reach qualified
through the real controller with the fake engine, including expected-only with
two keys and overflow with count1. This is a diagnostic admission defect, not an
observed provider failure;80 real-projection comparisons preserve every old
acceptance field and produce coherent diagnostics.

The selected artifact change is correct: both solution forms, exact remaining
bytes/file sets/token, observed raw hashes and before-refusal records pass the
independent51-test suite. Preserve those results and accepted prior custody/root
behavior. Complete the finite diagnostic relationships and arm-level negatives
in the review within owner179142's selected contract/test/candidate scope;
actual-model acceptance and worker forwarding remain unchanged.

review-evidence-179242.json SHA256
63b0d980eaa412ffc888fb9932d347d7d940e40a0c5587cde08318a145b68364 binds19
matching current/candidate/base inventories and independent0.4640157849935349s
verification, no timeout/live test threads/owned group remaining. Four probes
observe the defect, not desired acceptance. Author main0.2638050550012849s is
separate; repeated positive/probe durations remain unknown and prior costs are
preserved in the review. No live execution or private inspection occurred.

This supersedes correction-in-progress/awaiting-review as the next action:
return baton.ops for bounded correction disposition before fixture acceptance
and the separate live-run decision. Preserve candidate179146 and failed live
evidence; no marker reset or new run identity. A mistaken evidence/OPERATOR
lookup was corrected to the readable dossier-root file. No required input remains
unreadable. Gaps and production qualification stay open; no W161234 interruption.

## 2026-09-15T15:39:27Z — review179242 requests diagnostic R1; owner179288 selects it (claim179295)

baton.codex reviewed correction179146 and **withheld fixture acceptance for one
bounded defect**, keeping the artifact half. Read
review-2026-09-15T15-39-27Z.md SHA256
`de5c4a2b5131c80739201ebe05eabbe80804f35d1eaa3f6cffe6749d3777cb63` and
review-evidence-179242.json SHA256
`63b0d980eaa412ffc888fb9932d347d7d940e40a0c5587cde08318a145b68364`. Slawomir
routed the correction to baton.claude within the owner179142 scope. All nine
reviewed inputs were revalidated at their recorded hashes before any edit.

**THE DEFECT IS MINE AND IT IS REAL.** `consistent()` validated the diagnostic
members' types, ranges and boolean identity, and the verdict relationships — and
then did not check that the members agree with **each other**. Four malformed
terminal records reached `qualified` through the actual controller and arm:
`expected-only` with count2; `expected-only` with count8 and capped; count1 with
capped; and `modelUsage` reported as `expected-only` while the closed `members`
list says the field was absent. I reproduced all four before touching anything,
plus four more the review's correction names — `empty-object` with capped,
`expected-plus-other` with count1, `other-only` count1 with capped, and a `model`
diagnostic of `expected` for a field absent from `members`. **A guard that
type-checks a vocabulary without relating its terms is not a guard**: a record
could claim a singleton and report two keys, or claim overflow at one key, and
still be admitted as an internally consistent qualification report.

**Scope.** This is a malformed-worker-record admission gap, not a claim that the
pinned provider produced these contradictions and not a change to actual-model
extraction — the review's own 80-vector matrix found the unchanged worker
projection coherent throughout. It matters because the whole point of the
diagnostics is to be a strict closed boundary.

The correction completes the finite relationships inside the selected contract:
`missing` means the known member is absent and every other diagnostic means it is
present, for both `model` and `modelUsage`; `empty-object` is count0 uncapped;
`expected-only` is count1 uncapped; `other-only` has a positive count;
`expected-plus-other` has at least two; and `capped` requires exactly the cap and
a shape that can hold more than one key. `MODEL_KEY_CAP` stays 8, the strict
int/bool checks stay, the `model_fields`/verdict checks stay, and **the original
actual-model predicate is untouched**. No model acceptance is relaxed, no
unknown model name is inferred and no validation redesign is attempted.

**Retained from the review as accepted:** the two-form artifact acceptance is
implemented precisely in both turns, the provider workspace is never rewritten,
other whitespace/code/entry-set differences still refuse, `continuity.txt` keeps
token-plus-LF, expected and observed hashes are separate with the observed raw
length/hash/form recorded before refusal, and the workspace events and token
diagnostics carry no token digest or content. The 0640→0660 supersession, the
fixed-root admission checks and the consumed run identity are all unchanged.

Scope: `evidence/qualification_contract.py` and `evidence/test_qualification.py`,
plus a fresh manifest, operator packet, candidate and evidence. The worker stays
unchanged; the arm already calls `consistent()`. No live execution, new run
identity, marker reset, product or consumer edit, or interruption to W161234 B.
The prior failed live run remains failed; G1 partial without an accepted actual
model, G4/G6 first-use only, G2/G3/G5 unobserved, G7 qualification-only, G8
omitted. Production qualification remains incomplete.

## 2026-09-15T15:53:41Z — independent acceptance of correction179295

baton.codex claim179346 accepts fixture manifest
3d5684edae17c296827db26c2a1dcffbf5173d719ddb80fe8e5f1e25f6f98741 under
owner179288/179142. review-2026-09-15T15-53-41Z.md resolves diagnostic R1:
shape/count/overflow/expected-key/member relationships are now enforced together.
All four original malformed records refuse at the first arm before restoration.
The actual-model predicate and previously reviewed artifact behavior are unchanged.

Independent60-test suite passes, plus80 projection comparisons and four original
fault rechecks. review-evidence-179346.json SHA256
ecbbd4b85309fd011af2a0bbc35bbf29185a087177e5354ee40b39d2b60a6fd6 binds19
matching current/candidate/base checks and fixed post-run hashes. Measured
0.4139386789756827s, no timeout/live test threads/remaining owned group. Author
main0.2636633020010777s and all historical costs remain separately attributed.
No live provider/engine, protected data, marker or product change occurred.

Evidence note: the author reused evidence/probes-179146.json for the current12
probes. The old7 results remain in unchanged EVIDENCE-179146.json, whose hash
was rechecked, and the current12 are in EVIDENCE-179295.json. Use those immutable
claim records for historical attribution; future standalone probe reports should
use fresh claim-specific paths. This is not an additional acceptance gate.

This supersedes pending R1 correction/review as the current action. Return
baton.ops for a separate concrete live-run decision, including its selected
claimant and fresh digest-bound identity/packet. Do not reuse consumed roots;
fixture acceptance authorizes no rerun or marker reset. The failed live result
and incomplete provider gaps remain unchanged; production qualification/enabling
are still due. No W161234 gate or interruption follows.

## 2026-09-15T18:04:42Z — owner advances fresh-identity preparation

Slawomir asks to advance W177936 after the proposed fresh-identity preparation
handoff. At snapshot180070 it remains unclaimed at baton.ops and Claude has no
claim, with a current idle runtime report. Assign baton.claude the bounded
preparation previously proposed: a fresh qualification identity and exact
manifest-bound operator command from accepted correction179295, manifest
3d5684edae17c296827db26c2a1dcffbf5173d719ddb80fe8e5f1e25f6f98741 and
review-2026-09-15T15-53-41Z.md.

This supersedes the prohibition on preparing a new identity in owner179288's
completed correction scope, and pending identity-preparation selection. Own only
this dossier's necessary identity bindings, manifest/operator packet and fresh
candidate/evidence records. Revalidate accepted bytes first; retain accepted
behavior, selected image, two user turns,180s per invocation and600s overall,
strict model/artifact/continuity/custody/shutdown rules. Preserve all consumed
roots, markers and old evidence. Prepare proposed fresh paths without launching
the fixture or reserving live resources. Verification and independent review
are limited to the changed identity bindings and their existing consumers;
reuse applicable accepted evidence, with no architecture restart or broad suite.

Publish exact fresh candidate hashes and a copyable Python-file command, then
baton.feat reviews the bounded delta and returns baton.ops for the separate
concrete live-run selection and executor. No live model/engine, image work,
credential/private transcript access, marker reset, production enabling or
product/consumer change is selected. W161234 remains independently scheduled.

## 2026-09-15T18:05:50Z — fresh identity180078 prepared (claim180078)

Owner reroute180071 selected the bounded fresh-identity preparation. All nine
accepted inputs were revalidated at their recorded hashes first, including
manifest `3d5684ed…` and OPERATOR-178579.md `fb872f80…`.

**THE CONSUMED IDENTITY IS RETIRED, NOT RESET.** Run179075 took all three fixed
roots of the 178579 identity, and the fixture refuses a taken root rather than
repairing it — which is the accepted behaviour and the reason a rerun needs a new
name. The 178579 roots keep their original 09:02 timestamps and their evidence,
and a test now asserts that **nothing executable in the fixture or the contract
can name them**, asserted over comment-stripped source so the history can still
be explained where it cannot run. The fresh identity is `180078`; its three roots
were confirmed free and **none was created** — this preparation reserves nothing.

**THE MANIFEST NOW BINDS THE IDENTITY, NOT JUST THE BYTES.** `audit` requires the
manifest's `run_identity`, `private_root`, `credential_copy_root` and the new
`export_root` to equal the roots this fixture would actually reserve. Before
this those fields were decorative: an approved manifest could have named one
identity while the code took another and the digest would still have verified.
Changing any one of the four alone now refuses with `manifest-constants`. The
export root is derived from the run root in **one** place, used by both `audit`
and `run`, because a second copy of that derivation is exactly how a declared and
a reserved name drift apart.

Delta: `evidence/qualification-fixture.py`, `evidence/test_qualification.py`, the
manifest and the operator packet. **`qualification_contract.py`,
`qualification_worker.py` and `verify-offline.py` are byte-identical to accepted
correction179295**, so the image, the two user turns, 180s per invocation, the
600s envelope and the artifact, continuity, custody, shutdown and model-acceptance
behaviour all carry over unchanged and reuse that acceptance.

Verification 67 tests (60 before, 7 added), OK, 0.26378964600735344 s, exit0, no
timeout, owned process group positively absent — receipt
`evidence/identity-180078.json`. Fifteen reversal probes, each failing exactly
where it should, including one that puts the consumed identity back and one that
lets the manifest declare an identity the code does not take. Deliverables:
`EVIDENCE-180078.json`, manifest
`5e789f4e3115b5eb9a7623772adf0a17aac3e45135afaa65bc11a35eb30e951f`,
OPERATOR-178579.md `f3cc23c44c15c0553df742f70bdc2cca352037c67e6fe60f469596df0b98b435`
and `candidate-180078/`.

**THIS PREPARES AN IDENTITY; IT DOES NOT AUTHORIZE A RUN.** No live model,
engine, credential, network or image operation; no root reserved; the fixture was
never launched; no marker reset; no product or consumer edit. Selecting the run,
its executor and the moment remains a separate baton.ops decision. G1 partial
without an accepted actual model, G4/G6 first-use only, G2/G3/G5 unobserved, G7
qualification-only, G8 not composed. Production qualification remains incomplete;
W161234 stays independently scheduled.

## 2026-09-15T18:17:18Z — independent identity180078 delta acceptance

Claim180134 accepts the exact identity delta in review-2026-09-15T18-17-18Z.md: manifest5e789f4e3115b5eb9a7623772adf0a17aac3e45135afaa65bc11a35eb30e951f, current operatorfe63a4f11a3a3b7ea480d70e2a72793ed8f90cc9fab1bee62214ede80c4d6589. This explicitly supersedes the stale operatorf3cc23c4 locator above.67 offline tests and four matching-digest identity/root negatives plus four stale-digest refusals pass. Twenty inventory checks match; seven current hashes unchanged;0.41391784299048595s, no timeout/live threads/owned group. Review evidence561ba87e0d46e8c46c19923d753ae84875fe33ca5cb8055c8fbe06ef3e417eb8. Contract/worker/supervisor and acceptance predicates unchanged.

Provenance correction: the blanket claims that no fresh root was ever created/reserved are superseded by the authors disclosed probe incident in EVIDENCE-180078 and PROGRESS: a mutation briefly created the real empty export directory, which the author removed; no live provider invocation is reported. Current paths are unreserved, not historically never-created. Reviewer checked only root metadata in its managed view: consumed /tmp roots unchanged and proposed /tmp roots absent; old/new /dev/shm paths are not visible, so host volatile availability and all-three-root preservation are not independently corroborated. Actual executor uses existing exclusive preflight. No reviewer path repair, reservation or private content access.

Operational finding: candidate-179295/OPERATOR-178579.md is absent. Its historical hash exists in prior review, but no retained operator byte delta can be verified there. Complete current operator independently read and matching current snapshot accepted as a fresh document. Its final180078 section governs current paths and digest; digest is byte selection, not owner permission. Reused probe filename history remains in claim-specific EVIDENCE records. These are evidence clarifications, not another correction gate.

Return baton.ops for separate exact live-run selection and executor; command in the review. G1 partial/model unknown, G4/G6 first-use only, G2/G3/G5 unobserved, G7 qualification-only, G8 omitted; qualification incomplete. No W161234 dependency or interruption. New reviewer0.41391784299048595s, cumulative reviewer1.969647156976862s; author and unknown probe costs remain separate.

## 2026-09-15T18:29:34Z — operator identity180078 failed at collection

Slawomir reports executing the accepted manifest5e789f4e3115b5eb9a7623772adf0a17aac3e45135afaa65bc11a35eb30e951f command and receiving failed/cleanup_confirmed=true. baton.prompt read and preserved the two closed public export files under operator-result-2026-09-15T18-29-34Z/. This explicitly supersedes the prior pending-live-run action: identity180078 is consumed; do not rerun it or reset any markers.

Observed: one provider invocation, exit0, successful terminal result and matching session. Initial solution.py is exact39bytes with matching expected/observed hash. Stage=collection, failure_code=unclassified, elapsed14.50469564498053s. No second arm or restoration success is recorded. Cleanup is confirmed by the exported receipt, including container shutdown and network cleanup; this is receipt evidence, not an independent new engine inspection.

The model diagnostic now establishes model member absent, modelUsage expected-plus-other with exactly2 keys, expected key present and no cap. Actual model remains null under the accepted strict predicate. This does not establish the other key's identity or function and does not justify relaxing model acceptance. It is separate from the unclassified collection failure.

The public export does not retain an exception class, errno or failing collection step. Static source places inventory/subset/reconstruction within this stage; the exact cause remains open. No private transcript/state/credential content or raw path inventory was inspected. No rerun, tests, product/fixture correction, marker repair or model-policy change was performed.

Next: bounded independent assessment through baton.feat using this public evidence, accepted candidate and source. Diagnose what can be established without live execution; if a metadata-only diagnostic is needed, specify exact paths/fields and avoid private contents. Recommend the smallest closed error diagnostic/correction and any model-evidence disposition separately. Return baton.ops for concrete scope selection; preserve accepted contracts and W161234 independence.

Public evidence hashes:
- qualification.json: `7cdfea126a0f80654fa569c8e7964ec5a0810712f096cca0e374c178578ea981`.
- PROVENANCE.json: `b6dcdcc92a5d06398f4d69b248f0ad3d3e43e94ec39634d4566a63643803aa51`.

## 2026-09-15T18:36:00Z — independent collection-failure assessment180244

review-2026-09-15T18-36-00Z.md completes owner180241's public-evidence/source
assessment. AUDIT-180244.json confirms16 hashes and both provenance links;
current seven files match accepted candidate180078. Exact initial artifact and
one successful CLI turn are established by the export. No second arm is
recorded. Cleanup is supported by exported receipts only. Qualification remains
failed, and the consumed identity cannot be reused or reset.

Confirmed diagnostic defect: qualification_contract.failure_code collapses
ordinary exceptions and unregistered Refusal values to unclassified without a
collection step, class or errno. Source places the failure between first-home
inventory and subset-reconstructed event, including that event's own write.
Inventory, subset, private-layout save, destination preparation, copying and
restored inventory are all possible; absence of the later public fields does
not prove no partial reconstruction exists. Host access to UID65532-created
state is a plausible permissions hypothesis, not a confirmed cause.

The review proposes exact fixed-path lstat metadata and, only if still needed,
a bounded no-content directory walk in the original operator view. It also
names the smallest future closed step/category/errno fixture correction and
focused deterministic fault cases, preserving acceptance and custody. Neither
proposal was executed or grants authority. No content, private-path metadata,
tests, fixture/product edits, engine/provider call or marker operation occurred.
The inventory script's initially wrong operator-file locator was corrected to
the existing readable dossier-root file; no required input remains unreadable.

Model member absent plus exactly two usage keys including expected leaves G1
unqualified. The other key's identity/function is not recoverable from this
closed export; collection metadata cannot settle it. No model relaxation or
extra provider run is recommended in the collection scope. G4/G6 first-use
only; G2/G3/G5 unobserved; G7 qualification-only; G8 not composed. W161234 stays
independent.

Return baton.ops for diagnostic/correction selection. This explicitly
supersedes pending independent assessment, not the failed run or its evidence.
New test runtime0s; reviewer cumulative1.969647156976862s unchanged. Operator
14.50469564498053s and previous author/operator/unknown probe costs remain
separate. Exact detailed scope, limitations and proposed paths are in the review.

## 2026-09-15T18:41:03Z — owner180325 selects the fixed-path metadata diagnostic (claim180339)

Slawomir selected **only the first proposal** in `review-2026-09-15T18-36-00Z.md`:
the fixed-path metadata inspection of the consumed 180078 tree, delivered as one
standalone Python file for the **original operator host**. Pinned before any
file was written.

**Explicitly not selected by this assignment, and not prepared here:** the
review's optional bounded no-content traversal of `use-1/home` and `use-2/home`
— it is conditional on the fixed metadata leaving inventory permissions
unresolved, and directory enumeration of a private tree needs its own concrete
selection — and the separate closed collection step/category/errno fixture
correction. Neither is started; both remain available for later selection.

**Why the host and not here.** The review is explicit that a managed sandbox's
mount and PID view is not equivalent to the operator's. This context reports
uid1000 with groups {1000, 65534}, which is a different identity from the one
that ran the collection; reading the tree from here would answer a question
nobody asked. **The diagnostic is therefore written, verified against a synthetic
tree, and handed over — the private tree is not inspected in the managed
context.**

What the diagnostic reports: the operator's real and effective UID/GID and
supplementary groups as **numbers only** — no `pwd`/`grp` lookups, because account
names are arbitrary strings — and for each of the eleven fixed operands under
`/tmp/baton-w177936-qualification-180078` its state, type, UID, GID, numeric
mode, link count and closed errno category from the review's enum.

**No contents, no hashes, no link targets, no exception strings, no tracebacks,
no discovered filenames.** Every operand label is a constant in the source, so
nothing the filesystem contains can become a label. The script never opens a
regular file, never lists a directory, never calls `readlink` and never writes.

**No component is followed, not just the last one.** Plain `lstat` protects only
the final component: if `use-1/home` were a symlink, `lstat` on
`use-1/home/.claude` would silently report a different location. Each operand is
walked component by component through `O_PATH|O_NOFOLLOW|O_DIRECTORY` descriptors,
so a symlinked intermediate is **refused** instead of quietly succeeding. **The
refusal is `ENOTDIR` on Linux, not `ELOOP`** — `O_DIRECTORY` is consulted first —
and my synthetic-tree test failed the first time for exactly that reason: the
guard worked and my assertion named the wrong code. Both codes are inside the
review's closed enum, so the operator sees a refusal either way; I am recording
the correction because "surfaces as ELOOP" would have read as a defect against
real output.

**Identity180078 stays consumed.** Metadata inspection cannot convert its result
into success, and no repair, chmod, chown, marker reset, alternate identity,
fixture rerun or new run identity is prepared or authorized. Both consumed root
sets — 180078 and 178579 — are preserved untouched. The strict model predicate is
unchanged: `modelUsage` remains expected-plus-other with two keys and G1 stays
unqualified. G4/G6 first-use only, G2/G3/G5 unobserved, G7 qualification-only,
G8 not composed. W161234 remains independent.

## 2026-09-15T18:50:49Z — operator fixed-path metadata result

Slawomir reports running diagnostic-180078.py from the original operator terminal
and supplies its JSON. Preserved as
operator-result-2026-09-15T18-29-34Z/metadata-180078-operator-reported.json.
This is a normalized transcription of user-supplied JSON (terminal wrapping
removed), not original stdout bytes or a new independently executed inspection.

Normalized evidence SHA256: `237d34b173cea22c7686e5c5d9dad66bf25f1e1e5d057e6b5ba7e77434109ffd`.

Observed in the supplied result: real/effective UID and GID1000, supplementary
group1001 present. Root is UID1000/GID1000 mode0700; use-1, home and .claude are
UID1000/GID1001 mode2770. projects is UID65532/GID1001 mode2755. All five fixed
directories returned metadata without error. private-layout.json and its tmp
sibling, use-2 and its three listed descendants are absent (ENOENT).

Inference: the reported identity has read/search permission by the mode bits
on these checked directories. These results do not establish actual readability
of their contents, ACL/policy behavior, or permissions on unlisted descendants.
No persistent layout or destination-home checkpoint is present; assuming the
retained tree has not changed, the failure preceded successful layout save and
destination-home setup. Source inventory reads/hashes admitted regular files
apart from .claude.json and the excluded credential link, so an inaccessible
nested file remains a possible source of the unclassified exception. This is
not evidence of an actual EACCES or a specific failed path. Model qualification
remains separately open; these observations do not identify the other usage key.

Proposed next step: the review's already specified bounded metadata-only home
walk, prepared as one standalone operator Python script. At most1024 entries
per home, depth8, 20s wall bound, no-follow directory descriptors, aggregate
counts only by type/UID/GID/mode/operator read-search mode bits; stop at links
and credential-shaped entries, no regular-file opens, contents or discovered
names/hashes/sizes/mtimes. Report coverage, truncation and closed errors honestly.
This broader metadata inspection is proposed, not executed or selected by the
operator's fixed-path result. No permission repair, fixture change, new identity
or live rerun follows automatically. Preserve both consumed identities.

## 2026-09-15T18:52:18Z — owner180411 selects the bounded metadata-only walk (claim180413)

Slawomir selected the review's **second, conditional** proposal now that the
fixed-path result is in: one standalone operator script performing a bounded
metadata-only walk of `use-1/home` and any existing `use-2/home`. Pinned before
implementation.

**The fixed-path result narrowed the interval, and the walk is aimed at what is
left.** `private-layout.json`, its tmp sibling and every `use-2` operand are
absent, so — assuming the retained tree is unchanged — the run stopped **before**
the private-layout save and before destination-home creation. That leaves first
inventory and subset selection. `inventory` reads and hashes every admitted
regular file except `.claude.json` and the excluded credential link, so **a
nested file the collector could not open is the one hypothesis the fixed paths
could not test**: they showed the five top directories are mode-permitted for the
reported identity, and said nothing about descendants.

**What the operator's own result already shows.** Identity uid/gid 1000 with
group 1001 present. The three manager-created directories are `0o2770` uid1000
gid1001. **`use-1/home/.claude/projects` is uid65532 gid1001 mode `0o2755`** —
provider-created, group read and search but **not** group write. That is the
boundary where the runtime's own files begin, and it is exactly where the walk
starts to matter.

**Bounds, as selected:** at most 1024 entries per home, depth 8, 20 s wall time,
no-follow directory descriptors throughout. It exports **aggregate counts only**,
grouped by type, uid, gid, mode and whether POSIX mode bits permit the reported
operator identity to read and to search. It stops at links and credential-shaped
entries without opening or following them, never opens a regular file, and emits
no discovered name, path hash, size or mtime. Truncation, depth limiting,
timeout, traversal errors and incomplete coverage are reported explicitly rather
than left to be inferred from a short list.

**`use-2/home` is absent and that is not an error.** The script reports it absent
and walks only what exists, because the owner's wording is "any existing".

**What it still cannot do.** POSIX mode bits do not account for ACLs, namespaces
or other policy, so a permitted classification is not proof of readability and a
denied one is not proof of the actual failure. The original exception was never
retained — `failure_code` collapsed it to `unclassified` — so no metadata
inspection can recover it; that needs the separate closed-diagnostics fixture
correction, which remains unselected. **A permission or copying change still
requires its own bounded rationale and must not be bundled with a guess.**

Identity180078 stays consumed; no repair, chmod, chown, marker reset, identity
switch, fixture rerun or new identity follows. Both consumed root sets stay
untouched. The strict model predicate is unchanged and G1 stays unqualified; the
walk cannot identify the other `modelUsage` key. Verified synthetically here; the
private tree is not inspected from the managed context. W161234 independent.

## 2026-09-15T19:10:55Z — operator walk establishes a retained-tree access failure

Slawomir supplied the original-operator walk-180078.py result. Its normalized
JSON is preserved under operator-result-2026-09-15T18-29-34Z/
walk-180078-operator-reported.json. This transcribes user-supplied output with
terminal wrapping removed; it is not original stdout bytes or an independently
executed inspection by baton.prompt.

Normalized evidence SHA256: `d399a3a6705b3453007e6ff83aecb8ec23ce2704a3fb1e49ccc1adfabb62e3fb`.

Observed: operator real/effective UID/GID1000 with supplementary group1001.
First home has11 observed entries, depth4, no entry/depth/time bound reached,
and one actual opendir:EACCES. Coverage is incomplete because of that error.
Aggregates include one UID65532/GID1001 directory0700 and three regular files
UID65532/GID1001 mode0600, all mode-classified unreadable by the operator;
the directory is also unsearchable. Four runtime directories2755 and one file0644
are mode-readable; one link was not followed. Second home remains absent.

Confirmed as operator-reported evidence: an actual directory access denial now
exists in the retained tree, and observed runtime-owned modes exclude the host
collector identity despite group1001 membership. Setgid parent inheritance did
not ensure group-readable descendants. The read-only walk did not open any
regular file, so their actual read outcomes remain untested. The aggregate does
not identify which directory produced EACCES, whether the blocked directory
contains the selected session, or which original collection operation failed.
The original exception remains lost; these findings strongly support collection
identity/custody incompatibility without recovering that exception.

This supersedes the earlier purely hypothetical permission concern: directory
access failure is observed, while attribution to the exact original substep
remains an inference. No further general metadata discovery is proposed now.
Recommend a bounded collection/custody correction proposal based on this actual
runtime0700/0600 behavior, preserving minimal credential-free session selection,
shutdown/identity/custody checks and the consumed evidence. Do not chmod/chown
or reset either consumed tree. Do not infer broad permission relaxation or an
identity switch is already selected. Include the previously proposed closed
collection step/category/errno diagnostics so future failure evidence is useful.
Prepare exact source/test boundaries and verification, then owner selection of
the concrete correction; no live rerun or fresh identity is implied by this result.
Model qualification remains separately open; no model predicate change follows.
W161234/C1/C2 remain independent.

## 2026-09-15T19:12:33Z — owner180530 selects a bounded collection/custody correction proposal (claim180537)

Slawomir asked for the smallest collection/custody correction, as a **concrete
proposal with exact paths and verification** — not an implementation. Pinned
before writing. Delivered as `CORRECTION-PROPOSAL-180537.md`.

**One inference in the walk result is worth stating precisely, because the fix
depends on it.** The runtime created *both* permissive and restrictive objects:
four directories at `0o2755` and a file at `0o644` alongside one directory at
`0o700` and three files at `0o600`. A single umask cannot produce both, so the
restrictive modes are **explicitly requested, not umask-derived** — and the
`0o700` directory carries gid1001 with **no setgid bit**, which a child of a
setgid parent would have inherited. Something chmodded it after creation.

**That kills the smallest-looking fix.** Setting a umask for the container would
have been a one-line change, and it cannot work: umask only removes bits, never
adds them, so an explicit `0o600` stays `0o600`. I checked this before proposing
it rather than after.

**What the evidence actually establishes.** Setgid gave group *ownership* —
everything is gid1001 — and setgid never gives group *permission bits*. That is
the same distinction the accepted R1 correction turned on at 178875, arriving
from the other direction: there the manager had to make a file the runtime could
write; here the runtime makes files the manager cannot read. The host collector
is uid1000 in group1001 and is excluded by mode from one directory and three
files, with one real `opendir:EACCES` recorded.

**What it does not establish, and the proposal does not assume:** which directory
produced the EACCES, whether it contains the selected session, whether the three
`0o600` files include it, or which original collection operation failed. The
original exception is still lost. The proposal is therefore written to be correct
whichever of those is true, and it says so.

Scope of the proposal: dossier fixture paths only, with the closed collection
step/category/errno diagnostics included as owner180530 requires, so the next
failure produces usable evidence instead of `unclassified`. No implementation, no
further private-tree exploration, no consumed-tree repair, no chmod or chown of
either consumed tree, no live rerun, no fresh identity, no identity switch
assumed already selected, and no model-acceptance change. Both consumed root sets
stay untouched. Model qualification remains separately open and G1 unqualified.
W161234, C1 and C2 remain independent.

## 2026-09-15T19:18:49Z — proposal revision 2 after owner180577 found two defects (claim180580)

Owner180577 returned revision 1 with two defects. **Both are real and both are
mine.** Revision 2 is `CORRECTION-PROPOSAL-180537.md` sha256
`e4495ee4bd65dd6c28a511449c9703b90932e3f9e96af2150895e01ecd64d31f`, superseding
`3e18b5e5…` in place, with the defects described in its §2 rather than quietly
repaired.

**D1 — my P1b would have made three absence claims vacuous.** I wrote that an
unreadable entry should be "recorded closed instead of raising" without asking
what the fixture asserts from directory listings. It asserts three *negatives*:
`unexpected-credential-entry` home-wide, `project-key-ambiguous`, and
`foreign-session-state`. **An unenterable directory hides exactly the names those
claims are about**, so my tolerance would have turned "no foreign session and no
credential-shaped entry" into "we did not look" — while the export still reported
the checks as passed. That is the vacuous-assertion failure this campaign has
caught twice before, and I introduced it.

The rule follows from what each claim reads, and the distinction is the fix: all
three are **name-based**, and a name is visible from the parent listing. So an
unreadable **regular file** is safe to record closed — only its digest is lost —
while an unenterable **directory** must refuse, with a new registered code. The
tolerance is now exactly as wide as the evidence stays sound.

**D2 — my P1a did not distinguish the turns and aimed at the accepted R1 object.**
Turn 2's home is **manager**-reconstructed; its restored session file is created
`0o660` and owned by uid1000, which R1 established at 178875 as the writable
working copy. A turn-agnostic "relax the project directory and the session file"
pointed a chmod at that object. It would have failed as EPERM rather than
silently corrupting the contract — uid65532 cannot chmod a uid1000 file — so the
damage was bounded, but the intent was wrong and the contract violation real.
Revision 2 confines P1a to **turn 1** and to **runtime-owned** objects, and every
check is made through the same no-follow descriptor that is then `fchmod`ed, so
there is no window between checking and changing.

**One thing revision 2 says that revision 1 should have.** If the blocking
`0o700` directory is not the project directory, the correction does **not** make
the run pass: P1a relaxes two named objects and P1b then refuses at
`state-coverage-incomplete`. That is still progress — the export names the step
and errno instead of `unclassified` — but it is a refusal, and a proposal that
implied otherwise would have been selling a guess. Widening P1a to relax every
runtime-owned directory would make the run pass and qualify nothing; it stays
rejected, and collecting as uid65532 stays the deferred larger candidate that
these diagnostics would justify.

Still a proposal: no implementation, private-tree inspection, consumed-tree
repair, chmod or chown of either consumed tree, live rerun, fresh identity or
model-acceptance change. Both consumed root sets keep their timestamps; the
accepted fixture is untouched at manifest `5e789f4e…`; G1 stays unqualified;
W161234, C1 and C2 independent.

## 2026-09-16T00:29:25Z — owner182261 selects revision 2 for implementation (claim182264)

Slawomir selected `CORRECTION-PROPOSAL-180537.md` revision 2
(`e4495ee4bd65dd6c28a511449c9703b90932e3f9e96af2150895e01ecd64d31f`) for bounded
implementation, restating the four constraints that the two returned defects
produced: preserve turn-2 restored `0o660` state, **require complete directory
coverage and readable selected state**, retain the no-follow ownership/type
checks, and keep the closed failure diagnostics. Pinned before any edit; all
seven accepted inputs revalidated at their recorded hashes first.

Implemented in the six named paths only: `evidence/qualification_worker.py`
(P1a), `evidence/qualification_contract.py` (P1b and P1c),
`evidence/qualification-fixture.py` (P1c), `evidence/test_qualification.py`, the
manifest and `OPERATOR-178579.md`.

**The coverage rule is the load-bearing part, and it is a refusal rather than a
tolerance.** Only unreadable *file contents* are tolerated; unreadable
*structure* never is. A failed `scandir` **or a failed per-entry `stat`** refuses
with `state-coverage-incomplete`, because both hide names, and all three of the
fixture's absence claims — credential-shaped entries home-wide, exactly one
project directory, no foreign `.jsonl` — are read from names. The stat case
matters concretely: a `0o600` directory is readable, so `scandir` succeeds and
the failure lands on each child's `stat`, which is exactly the shape the operator
walk observed.

**The selected session must be genuinely readable.** An unreadable non-selected
file is recorded `content: unreadable:<errno>` and the run continues; the
selected one refuses at `subset` with its own code rather than surfacing later as
a digest mismatch.

**P1a stays where only the owning identity can act.** Turn 1 only, runtime-owned
only, with type, uid and gid verified through the same `O_NOFOLLOW` descriptor
that is then `fchmod`ed. Turn 2 performs no mode change at all, so the
manager-owned `0o660` restored working copy accepted at R1 is untouched.

No live rerun, fresh identity, product expansion, model-acceptance change or
consumed-tree repair. Both consumed root sets keep their timestamps. G1 stays
unqualified. W161234, C1 and C2 independent.

## 2026-09-16T00:41:09Z — independent review182326 requests R1–R3

review-2026-09-16T00-41-09Z.md withholds correction182264 acceptance.
All85 supplied tests pass independently,21 current/candidate/base byte checks
match and source is unchanged, but six synthetic publication cases establish
the selected pre-mutation and exact-object boundaries are incomplete.

R1: final-component O_NOFOLLOW does not protect the parent chain. A symlinked
projects parent redirects chmod outside HOME; swapping the project pathname
after its descriptor check redirects the selected file to a decoy. A hardlinked
selected file also changes its outside alias. R2: foreign/nested sessions and
a credential-shaped entry still allow publication/mode changes, contrary to
proposal §3a/§7.4 refusal-before-change. Later inventory refusal is too late to
prevent those effects. R3: inventory converts causal EACCES into a plain
state-coverage-incomplete Refusal, so the diagnostic records errno none. The
promised eight-step operation-level fault matrix is absent; current helper and
vocabulary checks do not exercise it. Exact repros and bounded fixes are in the
review, including preserving no-follow descriptor ancestry and all preflights
before fchmod, single-link selection, closed causal errno and targeted tests.

Evidence review-probes-182326.json SHA256
03e90f511d4a73c6779a1a376d22e8e4d698bf08d4e5657ea97a15d82dd0ff67;
suite receipt evidence/review-182326.json SHA256
6b418b3070bd4fcd8065f1fd0fb573f52c1178462d6c542c3ce19cd8a39599a5.
Suite0.3137755789794028s, no timeout/group remaining; probes0.0010939929634332657s,
no children, owned temporary trees cleaned. New reviewer0.31486957194283605s,
cumulative2.284516728919698s; author/operator costs separate. All probes use
synthetic same-UID trees, no real private state or credential/engine/model use.

Evidence clarification explicitly supersedes the new claim that a stat failure
on a0600 directory was the operator observation: preserved walk180078 instead
reports opendir:EACCES and a runtime-owned0700 directory. The stat case is an
additional synthetic regression. Collection failure belongs to identity180078,
not the earlier run179075 initial-artifact failure. Mixed modes alone also do
not establish a chmod call; differing requested creation modes can share a
umask. The restrictive-mode limitation remains, but the exact creation call is
not established by aggregate metadata.

Return baton.ops for the bounded correction and fresh candidate review. This
supersedes pending independent review; candidate182264 and all older evidence
remain. Preserve turn2/restored0660, coverage refusal and strict acceptance.
No new identity/live run/consumed-root repair or product expansion selected;
G1 and remaining gaps unchanged; W161234/C1/C2 remain independent.

## 2026-09-16T01:57:00Z — owner proceeds with R1–R3 correction

Slawomir directs "W177936 is next" after the W161234 joined closeout handoff.
baton.prompt re-read canonical state and review182326: the Work is unclaimed
at baton.ops, candidate182264 remains unaccepted, and R1–R3 remain pending.
Select baton.claude to complete those corrections within the already selected
revision2 worker/contract/controller/test and manifest/operator/evidence paths.
This supersedes pending correction disposition; no new architecture or live
experiment scope is selected.

Binding review: review-2026-09-16T00-41-09Z.md SHA256
 a47b7cb76bafdd774cd21f5d95e4fb4266835f133af2164583aabbf0950d549e.
R1 binds full no-follow ancestry, enumeration, selection and mutation to verified
descriptors, refuses multi-link selected files, and uses type-safe nonblocking
opens. R2 completes all selected bounded name/type/ownership/shape checks before
any fchmod, including foreign/nested sessions and credential-shaped entries.
R3 carries only closed causal errno through coverage refusal and adds actual
operation-level eight-step fault coverage, canary exclusion and real worker
publication in composed synthetic tests. Include the review's wrong-UID case
and correct its named historical attribution errors explicitly.

Preserve turn2 no-op/restored0660, complete structure refusal, minimal selected
state, strict model/artifact/continuity predicates and all failed evidence.
Revalidate current bytes and reproduce the exact review cases offline; produce
fresh digest-bound candidate and focused verification, then baton.feat independent
review and baton.ops. No private-tree access, consumed-root repair, live provider
or engine, fresh run identity, product expansion or W161234 dependency. No further
owner approval is needed for ordinary in-scope correction/test iterations.

## 2026-09-16T01:57:30Z — review182326 requests R1–R3; owner182768 selects the correction (claim182771)

baton.codex withheld fixture acceptance on manifest `3b0020ba…`. **All three
defects are real and all three are mine**, and each is a case where the boundary
I wrote was narrower than the boundary I claimed. The review's own bytes were
revalidated before any edit.

**R1 — my no-follow bound one component, not the path.** `_owned` opened absolute
paths with `O_NOFOLLOW` on the *final* component only, and `publish` reopened the
session by pathname rather than relative to the project descriptor it had just
verified. Three consequences the reviewer demonstrated: a symlinked
`.claude/projects` publishes an object **outside HOME**; a rename-and-replace
between the check and the second open changes an unrelated decoy; and a
hardlinked session is chmodded through its alias, which the manager's later
hardlink refusal cannot undo because the mode change already happened. I had
written "nothing can be swapped between check and change" — true of each single
descriptor, and not true of the *path*, which is what matters.

**R2 — I changed forbidden layouts before refusing them.** `publish` checked one
directory and the expected filename and nothing else, so an extra foreign JSONL,
a nested session, or an `oauth-token` entry each still published and still moved
`0600→0640`. The proposal's own §3a says these must "refuse and relax nothing".
Later inventory refusal does not repair a mode change that already occurred.

**R3 — my coverage refusal threw away the errno it was raised for.** `inventory`
caught the `OSError` and raised a plain `Refusal(...) from None`, so
`failure_detail` reported `known-refusal` / `errno: none` — and the test I wrote
asserted `none` while its name claimed the errno was retained. A test that
asserts the bug is worse than no test. The packet promises a named step **and
errno** for exactly this failure.

**Three evidence attributions corrected, keeping the history.** The operator walk
reports **`opendir:EACCES` on a runtime-owned `0o700` directory** — not a stat
failure on a `0o600` directory; that second shape is a useful synthetic
regression and I had presented it as the observed result. The collection failure
is identity **180078**; 179075 was the earlier initial-artifact failure. And
mixed permissive/restrictive modes do **not** by themselves prove a `chmod`:
different requested creation modes share one umask. The part that survives is the
part that matters — **an explicitly requested `0o600` cannot be made
group-readable by loosening umask** — so the conclusion that a umask change
cannot fix this stands, while "something chmodded it" was more than the metadata
supports.

Corrected within the already selected paths, preserving turn-2 no-op, the
restored `0o660` contract, complete-structure refusal and every strict contract.
No private-tree inspection, consumed-root repair, live execution, fresh identity,
product expansion or model-policy change.

## 2026-09-16T02:11:27Z — independent review182843: R1/R2 incomplete; R3 verified

review-2026-09-16T02-11-27Z.md withholds fixture acceptance of manifest
f6b954ccb2e68bca9d44d0afdfdca1a3b18ff25f2ac96cb630463b1f405e06ba.
All95 supplied tests pass independently and21 current/candidate/base checks
match. The author's bound log also reports95; new summaries saying94 need an
explicit correction. Source remains unchanged.

Observed R1 continuation: _survey closes inspected directory descriptors and
then resolves the target again. Replacing the surveyed project with another
regular directory before that second open publishes an unsurveyed decoy and
changes its selected file0600 to0640; the original stays0600. Observed R2
continuation: HOME/cache and HOME/.claude/cache are not traversed, so nested
oauth-token entries allow publication; an extra non-session symlink is also
ignored. Subsequent inventory refuses, after the selected mode has changed.
These contradict the selected exact-object and full before-mutation preflight.

R3 is verified: the real coverage seam preserves distinct EACCES/EIO/ENOENT
causes without canary leakage, the operation-level fault matrix runs, and the
composed fake engine invokes actual worker publication. Preserve these changes
and the working direct invalid-layout, UID/GID, hardlink and symlink guards.
Finish R1/R2 under existing owner182768 scope; no new selection is needed for
ordinary correction iterations. This explicitly supersedes all-corrections-
complete as the current disposition for candidate182771.

Evidence review-probes-182843.json SHA256
bbec4eab4baeec83579f965739fc967f747cb3a01945a9983bc095900863be3f;
suite evidence/review-182843.json SHA256
83131cb5c84f87c22064a6ed5897724067a5ce9e65d552f2338057db7e2f24b8.
Suite0.3137830900377594s, no timeout and group absent; ten synthetic publication
cases plus three diagnostic checks0.0028731600032188s, no children and temporary
trees cleaned. New reviewer0.3166562500409782s, cumulative2.601172978960676s;
author0.3638601779821329s and prior author/operator costs separate.

The review records a corrected optional manifest locator mistake; the actual
required manifest was read and no required input remains unreadable. Current
inventory source still contains the superseded stat-case operator attribution,
which should match the corrected opendir:EACCES history. No private/live roots,
credentials, engine/model, consumed-root repair or fresh identity were used.
Both consumed identities and qualification gaps remain unchanged. Return ops
for bounded continuation, then independent review; W161234/C1/C2 stay independent.

## 2026-09-16T02:18:53Z — R1/R2 still incomplete; owner182904 selects completion (claim182906)

Review182843 verified R3 — distinct EACCES/EIO/ENOENT causes, the operation-level
eight-step matrix and the real `worker.publish` composition — and found **R1 and
R2 still incomplete**. Both findings are right, and both are the same mistake
repeated: I fixed the case the previous review demonstrated instead of the class
it belonged to.

**R1 — I retained nothing.** I made the survey walk descriptors and then, at the
end, **reopened the targets by path**. So the swap simply moved later: replace
the project directory with a regular decoy *after* the survey and the chmod lands
on an unsurveyed file while the original stays `0o600`. Verifying through a
descriptor is worthless if the descriptor you verify is not the one you change.
The targets are now the descriptors the walk itself opened, held through
selection and mutation.

**R2 — my "home-wide" survey was not home-wide.** It descended only into
`.claude` and the `.claude/projects` chain, so a credential-shaped entry under
`HOME/cache` or `HOME/.claude/cache` was never seen, and unselected invalid types
elsewhere were ignored — each publishing before the manager's later inventory
refused. The preflight now descends the whole home under the existing entry and
depth bounds and applies the same type rule the manager's inventory applies,
while still never opening credential or configuration contents.

**Two evidence corrections.** An `inventory` source comment still called the
`0o600`/stat seam the observed operator shape; the observed result is
`opendir:EACCES` on a runtime-owned `0o700` directory. And my summaries said
**94** tests where the bound log says **95** — the count I had been discounting
was the audit case, which passes once the manifest is rebound. Both corrected
wherever they appear.

Preserved: verified R3, turn-2 no-op, the restored `0o660` contract, complete
structure refusal and every strict contract. No live run, fresh identity,
consumed-root repair, product expansion or model-policy change.


## 2026-09-16T02:31:07Z — independent review182947 accepts fixture correction182906

review-2026-09-16T02-31-07Z.md accepts manifest
eaa757a494ec6dc10db5e1a5cd67a88d52710affd912a947f7a41482d3fad99d
for the selected offline correction. All21 current/candidate/base checks and
seven current modes match; independent98 tests pass. The post-survey regular
directory replacement probe changes only retained original objects, leaving
the decoy0700/0600. Both skipped-cache credential cases and an unrelated symlink
now refuse before mode changes. R3 closed causal errno remains verified.
This supersedes pending correction/review as the current disposition; prior
R1/R2 findings and evidence remain history.

Evidence: evidence/review-182947.json and review-probes-182947.json, exact hashes
and boundary explanations in the review. New reviewer0.3164290550048463s;
cumulative W177936 reviewer2.9176020339655224s. Author/operator costs separate.
No live/private-tree work, new identity or consumed-root repair. Return ops for
qualification disposition: both identities consumed, G1 still unqualified,
G4/G6 first-use only, G2/G3/G5 unobserved, G7 qualification-only, G8 not composed.
A new live run requires separately selected fresh identity and rebound packet.
W161234/C1/C2 remain independent; this acceptance does not close qualification.

## 2026-09-16T02:54:46Z — fixture accepted; owner183105 selects a fresh identity (claim183114)

Review182947 **accepted candidate182906** at manifest `eaa757a4…` — for the
selected offline fixture correction only, not for live qualification and not for
a rerun of a consumed identity. Owner183105 selected the next bounded step: a
fresh unused run identity and a newly digest-bound operator packet, plus a
statement of what remains unqualified.

**The fresh identity is `183114`.** Both earlier identities are consumed:
`178579` by the initial-artifact failure and `180078` by the collection failure.
All six of their roots keep their original timestamps, nothing executable can
name either, and neither is repaired. The three `183114` roots were confirmed
free and **none was created** — this preparation reserves nothing.

**The remaining questions are stated rather than implied**, because the accepted
fixture answers none of them:

- **G1 is partial and the model is still unqualified.** Run180078's `modelUsage`
  held **exactly two keys, one of them the expected model**, with no direct
  `model` member — `expected-plus-other`, which the strict predicate correctly
  refuses. The other key's identity and purpose are **unknown and not
  recoverable**: the raw terminal document is read from an anonymous bounded pipe
  and never retained. No fixture change can answer it; only a run that retains
  more, which is a separate selection with its own privacy question.
- **G2, G3 and G5 remain unobserved.** No `--resume` turn has ever run, so
  restoration from a manager-rebuilt home is still the one thing this campaign
  has never done.
- **G4 and G6 have first-use evidence only** — one `cwd` and one HOME mode
  observation, from turns that did not reach a second arm.
- **The custody correction is offline-verified, not field-verified.** The
  publication and coverage rules are exercised by same-UID synthetic fixtures;
  no two-UID or live-provider observation supports them yet. That is precisely
  what a `183114` run would test first.
- **G7 stays the qualification-only image selection and G8 is not composed.**

Preserved unchanged: the accepted behaviour, the image, the strict model
predicate, the artifact and continuity contracts, the two-turn shape, 180 s per
invocation and the 600 s envelope. No live execution, production enabling,
consumed-root repair or model-policy change.


## 2026-09-16T03-01-11Z — review183137 accepts fresh-identity packet183114

review-2026-09-16T03-01-11Z.md accepts manifest
dd28498767bbcaf0eeb1552549f39228c555069b6c48e939abec136fa7df2779 for separate
operations selection. All21 byte checks and seven modes match; independent98
offline tests pass. AST comparison isolates the executable change to the identity
constant; both consumed identities refuse in all four declared identity/root
fields, and wrong digests refuse. Accepted R1/R2/R3 bytes and limits unchanged.

Clarifications: four candidate paths changed, not the summary claim of three;
the evidence table is correct. New identity cannot recover the old mixed-model
key; any future run still independently faces the unchanged strict predicate.
The author reports fresh paths free at preparation; this review does not certify
host-global absence or timestamps. Exclusive execution-time reservation remains
required. No roots reserved, live run, private-tree access or production enabling.

New reviewer 0.32552685303380713s; cumulative 3.2431288869993296s, author/operator costs separate.
Return ops for separate live-run selection. Both old identities remain consumed;
G1 unqualified, G2/G3/G5 unobserved, G4/G6 first-use, G7 qualification-only,
G8 not composed; W161234/C1/C2 independent. This supersedes pending review as
the current action, preserving prior history.


## 2026-09-16T03:05:02Z — operator run183114 failed at worker publication

baton.prompt read and preserved the operator's public export byte-for-byte in
operator-result-183114/qualification.json and PROVENANCE.json. Verified the
qualification hash against the exported provenance:
qualification SHA256 008b79672a42b8d5a6c95a1cb7ce28bf91b4950846ee26dbed0d0f300da71707;
PROVENANCE SHA256 152a38d35be35228cadb01617a75a6f3f56609a4a5c41ea5a7b5ccba53c3aa5a.
This is inspection of operator-produced evidence, not independent execution.

Observed: reviewed manifest dd28498767bbcaf0eeb1552549f39228c555069b6c48e939abec136fa7df2779;
stage first-turn; provider_started true; failure_code publish-shape; known-refusal,
no causal errno or substep. Elapsed18.80640551802935s. First container reported
exited with PID0/running=false and its shutdown receipt consumed. Cleanup
confirmed for both turn slots and network. One arm is exported; no second
turn/restoration occurred. Identity183114 is now consumed; preserve all three
consumed identities and their roots. No rerun or repair is selected.

Source observation: qualification_worker.py uses publish-shape for multiple
walk bounds, metadata/listing/credential-link failures, credential-name checks
and project/session cardinality checks. The exported code cannot select which
branch failed. main calls publish before recording provider exit/terminal and
its exception handler replaces the result; this run therefore supplies no
terminal-model or artifact acceptance evidence. Container exit0 alone does not
establish provider success. Do not infer a specific forbidden entry, permission
failure or model outcome. Prior model evidence remains separate.

Recommended next action (not yet selected): bounded source/public-evidence
diagnosis and a concrete minimal diagnostic/correction proposal through the
managed reviewer. Preserve strict publication/model checks. No private-tree
inspection, credentials, live execution, fresh identity or product enabling.
Operator still holds the Work and must pass it explicitly for that next scope.
This supersedes awaiting-run disposition; offline candidate acceptance remains
history and production qualification is unfinished.


## 2026-09-16T03:07:02Z — owner selects one complete offline correction/review cycle

Slawomir agreed to stop live reruns until the fixture provides useful diagnostics
and to let Claude/reviewer handle ordinary corrections directly. Exact bounded
selection: OFFLINE-CORRECTION-CYCLE-183114.md. Implement closed publication-branch diagnostics, preserve
validated prior terminal observations on failure, add focused faithful offline
regressions and complete independent acceptance. Preserve all strict gates and
existing evidence; no private inspection, actual-engine/model execution, fresh
identity or production enabling. The old precise publish-shape cause remains
unknown unless evidence establishes it.

This supersedes the previous reviewer-proposal-only recommendation and routine
ops-return correction cadence for this cycle. Canonical Work is still held by
baton.slaw; the operator must pass it to baton.impl. No claim or assignment was
performed by baton.prompt. Return ops only on complete independent acceptance
or a real scope/authority decision.

## 2026-09-16T03:07:51Z — owner-confirmed offline correction cycle (claim183197)

Review183137 accepted candidate183114 and the operator ran it. **It failed at
first turn with `publish-shape` and nothing else**, after the provider had
started and exited; cleanup confirmed, 18.80640551802935 s, no second turn.
Owner pass183193 selects `OFFLINE-CORRECTION-CYCLE-183114.md`
(`54e00a9b5892b123e3703024088695b90702e70ad58bc7e13b18b9a44d2a6727`): stop live
reruns until failures produce useful information, and exchange ordinary
corrections directly between impl and feat.

**Both defects the export exposes are mine, and they are the same shape as the
ones this campaign keeps finding.**

**The publication refusal is one code for seventeen different checks.** I
collapsed bounds, traversal failures, credential-link and name checks, type
checks, project and session shape, ownership, alias and the chmod itself into
`publish-shape`/`publish-type`, so the export can say a run refused and not which
question it answered. That is the same "a bare code is not evidence" failure that
`unclassified` had at the collection boundary, reintroduced one layer up.

**And the validated terminal observation was thrown away by a later failure.**
`publish` ran *before* `c.projection`, so a publication refusal discarded a
provider exit and a terminal record that were already available — the run cannot
even say whether the provider's answer was well-formed. Ordering that made the
observation depend on an unrelated later step was a mistake.

Both corrections are bounded by the cycle: closed check and errno vocabulary,
no raw paths, names, prose, credential or configuration contents or transcripts;
a preserved observation **stays a failed arm** and bypasses no publication,
shutdown or qualification gate; malformed or missing terminal data stays
explicitly unobserved.

**What this cycle cannot do, stated plainly.** The 183114 export cannot identify
which branch actually fired, and no synthetic reproduction recovers that run's
cause or its terminal response. The diagnostics make the **next** failure
informative; they do not explain this one. All three identities — 178579, 180078
and 183114 — stay consumed, and an old manifest is not rerunnable because the
diagnostics improved.

Preserved: R1 retained descriptors with alias/type/UID/GID checks, R2 complete
bounded preflight before mutation, R3 causal diagnostics, turn-2 restored `0o660`,
the strict model/artifact/continuity acceptance, the image and the run limits.
No live run, private-tree inspection, fresh identity or consumed-root repair.

**One summary correction from review183137, kept rather than quietly fixed:** my
183114 progress note said "three files changed" when **four** did — the operator
packet is a candidate file too, and my own evidence table listed all four. The
undercount was in the prose only.


## 2026-09-16T03-18-48Z — independent review183243 requests two bounded corrections

review-2026-09-16T03-18-48Z.md withholds acceptance of manifest
c5b325cd3b083b0ba5fd8952c48bbd27ff1efa67e0e27c326434e95c35901cc6. All21 byte checks
and seven modes match;109 supplied offline tests pass, but independent probes
reproduce two gaps. R1/P1: the failed-arm terminal validator omits six normal-path
field checks; synthetic canaries in each reach the exported failed arm. Use full
shared terminal validation and paired negative cases; make malformed publication
diagnostic types refuse predictably rather than raising TypeError. R2/P2:
target fstat exceptions still produce unclassified/publication-null and lose
their errno; wrap that operation and cover actual operation failures.

Valid observation retention and no-second-arm behavior work and must remain.
Synthetic probes do not identify run183114's live cause. Evidence and exact
hashes are in the append-only review and review-probes-183243.json.
New reviewer0.37555032497039065s; cumulative3.61867921196972s; author/operator costs separate.
Source unchanged. No live/private-tree work, new identity or root repair.

Next is direct baton.impl correction under OFFLINE-CORRECTION-CYCLE-183114.md
and pass183193, then fresh candidate and independent review; no ordinary ops
approval hop. This supersedes all-corrections-complete as current disposition.
All three identities stay consumed and all qualification gaps remain unchanged.


## 2026-09-16T03-26-33Z — review183295 verifies prior fixes; one validator continuation remains

review-2026-09-16T03-26-33Z.md withholds candidate183267 acceptance solely
for R1/P2 malformed-container handling. The original six-field canary leak is
fixed, publication diagnostic types refuse correctly, and R2 target-fstat causes
are preserved. Valid prior observations still survive without admitting turn2.
114 tests pass;21 byte checks and seven modes match.

The new shared valid_terminal still constructs sets from unvalidated list
elements and passes untyped model diagnostics into membership checks.
Four malformed shapes through both controller paths produce unclassified/other
instead of a registered terminal refusal. No canary escapes and no second arm
starts. This inherited type assumption must be completed in the shared validator;
exact minimal correction and32-case evidence are in the append-only review.
Do not reopen verified R2 or weaken good-case preservation.

New reviewer0.38589503295952454s; cumulative4.004574244929245s; author/operator costs separate.
Continue directly baton.impl under pass183193 and the selected offline cycle,
then fresh candidate to reviewer. No live/private-tree work, new identity or
consumed-root repair. All three identities and qualification gaps unchanged.
This supersedes the two-outstanding-findings state: only this R1 continuation
remains, while prior evidence is preserved.


## 2026-09-16T03-32-44Z — review183339 accepts completed offline correction cycle

review-2026-09-16T03-32-44Z.md accepts candidate183316 manifest
d101f1ec1c3dac410e0551cb5beaf2ed60cf0ecce21aca33674e3da233eba7fa.
All21 byte checks and seven modes match.116 focused offline tests and32
independent probes pass. The shared validator now names malformed terminal
refusals on both paths; six-field leak closure, publication diagnostic type
refusals, target-metadata errno and valid observation preservation remain verified.
All findings from review183243 and continuation183295 are resolved for this cycle.

New reviewer0.3859800400095992s; cumulative4.390554284938844s; author/operator costs separate.
Exact evidence hashes and scope are in the review. Current candidate unchanged;
PROGRESS remains implementer-owned. No live/private-tree work, new identity,
root repair or production enabling. Old run183114 cause remains unknown.

Return baton.ops with accepted offline completion under pass183193. This
supersedes the pending implementation correction; no correction remains for
this selected cycle. All three identities stay consumed, including183114 still
named by the fixture; a future live experiment needs separate justified selection
and fresh bound identity. G1 unqualified; G2/G3/G5 unobserved; G4/G6 first-use;
G7 qualification-only; G8 not composed. W161234/C1/C2 remain independent.

## 2026-09-16T03:35:40Z — offline cycle accepted; owner183369 selects one diagnostic experiment (claim183372)

Review183339 **accepted candidate183316** as complete for
`OFFLINE-CORRECTION-CYCLE-183114.md`: every finding from review183243 and
continuation183295 is resolved, and no implementation correction remains for the
selected offline cycle. Owner183369 selected the next bounded step — a fresh
digest-bound identity and operator packet for **one** diagnostic qualification
experiment.

**The fresh identity is `183372`.** Three are now consumed: `178579` by the
initial-artifact failure, `180078` by the collection failure, `183114` by the
publication failure. All nine of their roots keep their timestamps, nothing
executable names any of them, and none is repaired. The three `183372` roots were
confirmed free and **none was created**.

**The experiment has exactly two outcomes worth having, and both are useful.**
Run183114 refused at `publish-shape` and the export could not say which of
seventeen checks answered; the accepted cycle fixed that. So this run either

- **names the actual publication check** — with its closed errno where an
  operation failed, and the validated terminal observation retained alongside it,
  so for the first time a publication failure says what the provider answered; or
- **publishes successfully and reaches restoration** — which would be the first
  `--resume` turn this campaign has ever run, and the first evidence for G2, G3
  and G5.

A failure that names its branch is a **result**, not a wasted run. That is the
whole point of the cycle the owner confirmed: stop rerunning until failures
produce useful information, then run once.

**What it still cannot do.** It cannot recover run183114's cause — that export
cannot identify the branch, and no later run explains an earlier one. It cannot
settle the model: run180078's `modelUsage` had exactly two keys including the
expected one, and the other is unrecoverable from a document never retained. And
the custody correction remains offline-verified; this run is the first thing that
would test it with two real identities rather than same-UID fixtures.

Preserved unchanged: strict model, artifact and continuity acceptance, the image,
the two-turn shape, 180 s per invocation and the 600 s envelope, retained
descriptors, before-mutation refusal, R3 collection diagnostics and turn-2
restored `0o660`. No agent live execution, consumed-root repair or production
enabling.


## 2026-09-16T03-41-10Z — review183394 accepts identity183372; clarifies experiment claims

review-2026-09-16T03-41-10Z.md accepts manifest
cefaf7bfa518874a082d9867c464f3629819828ef940cad5e8db0a74afb91945 and exact operator
command for operations selection.116 offline tests,21 byte checks,7 modes and14
negative identity/digest audits pass. Executable delta is only IDENTITY; accepted
contract/worker unchanged. No run or reservation performed by reviewer.

Clarification superseding literal preparation wording: the two outcomes are
objectives, not exhaustive outcomes. Publication success does not guarantee
restoration/resume: remaining shutdown/artifact/collection/copy gates may refuse.
Retained terminal facts require a valid available projection. Old model keys and
run183114 cause remain unrecoverable, but a future run can yield its own strict
model evidence. Run183114 already attempted real two-UID publication; SUCCESSFUL
custody/restoration remains unproved. This is the first run with enhanced
diagnostics, not the first real custody attempt. No executable change needed.

Root absence is author-reported at preparation, not reserved or independently
certified host-global absence. Operations still uses exclusive reservation.
All three old identities consumed; no repair. G1 unqualified; G2/G3/G5 unobserved;
G4/G6 first-use; G7 qualification-only; G8 not composed. W161234/C1/C2 separate.

New reviewer0.37552333099301904s; cumulative4.766077615931863s; author/operator separate.
Next baton.ops with exact command for execution decision, no agent live run or
production enabling. This supersedes pending identity review as current action.


## 2026-09-16T03:46:34Z — run183372 failure and operator host authentication diagnosis

baton.prompt preserved the public export byte-for-byte at operator-result-183372/.
qualification SHA256 a2de4c40f86e174b6c8f67bdfe79332362fd247d865e4db920fb17100ddb7165, verified against PROVENANCE;
PROVENANCE SHA256 73bea11e1eef59184f7f841d9e677c5f5df5de8b2a795502836682e8fb371726.
Not independent live execution. Operator claim183431 remains held by baton.slaw.

Observed: first-turn failure after provider start, provider_exit1, projected
is_error=true, matching session, no actual model, empty modelUsage. Despite
subtype=success, exit1/is_error=true do not meet provider success. Publication
refused publish-shape with check=credential-link and errno=other. Source maps
this combination to the post-provider os.readlink failure at the expected
credential link; it is not evidence of a specific errno or replacement type.
The pre-provider readlink check passed. No permission change or second turn was
reached on this path. Shutdown receipt consumed; cleanup confirmed for both
turn slots and network. Elapsed1.693677491042763s. Identity183372 is consumed
alongside178579/180078/183114. No retry or root repair.

Operator separately reports the host CLI pong command failed with:
"Failed to authenticate: OAuth session expired and could not be refreshed".
Exact supplied text is in host-auth-operator-reported.txt. This confirms an
authentication failure for that host invocation. A relationship to the fixture's
provider failure/credential-link change is plausible, not established causation.
Do not claim this explains all previous failed runs or successful restoration.

Next immediate recommendation: restore authentication interactively in the
operator host CLI using its supported auth login command; establish host health
before selecting another qualification experiment. No login, credential reads,
private-tree access or additional model calls were performed by baton.prompt.
The current fixture identity remains consumed even after authentication repair.
This supersedes awaiting-run disposition, not accepted offline fixture evidence.


## 2026-09-16T03:50:35.728956+00:00 — direct owner-selected fresh identity after host auth recovery

Operator reports pong received after restoring host authentication and explicitly
requests fresh identity preparation directly, without Baton ceremony. baton.prompt
prepares identity20260916T035035Z from reviewed manifest cefaf7bfa518874a082d9867c464f3629819828ef940cad5e8db0a74afb91945.
Scope: identity/root rebinding and corresponding fixture-test constants only;
no provider behavior, acceptance, credentials, image, permissions or run-limit
change. Preserve old bytes in identity-preparation-20260916T035035Z/. No new claim or independent
review is asserted. Static executable comparison and offline package audit
verify this mechanical preparation. No live run is performed. Previous identity
183372 is consumed; preserve all earlier roots. Execution still exclusively
reserves the new roots; preparation does not certify host-global absence.


## 2026-09-16T03:53:07.322472+00:00 — post-authentication run20260916T035035Z: publication succeeds, inventory EACCES

Operator-produced public export preserved byte-for-byte in operator-result-20260916T035035Z/.
qualification SHA256 58408c2ea88711eb033bf645775cb9e73f2813ddb1a9f12c35732ec527285d06, verified against exported provenance;
PROVENANCE SHA256 1804c7ebf4344a5bef3044d683e9095c436b0659202b99ccb4a438714432ee9d. No independent live execution.

Observed: provider exit0, success terminal with is_error=false and matching
session; exact39-byte initial artifact matches expected digest. Worker reports
selected project/session publication modes02750/0640. First runtime stopped with
shutdown receipt consumed. Collection fails at source-inventory with
state-coverage-incomplete, closed cause EACCES. No second turn or restoration.
Cleanup confirmed; elapsed6.432271532015875s. This supports successful first-turn
publication after operator-reported host auth recovery, not successful complete
manager collection. The inaccessible entry/operation is not identified.

Model remains unqualified: direct model missing; modelUsage expected-plus-other,
exactly2 keys with expected key present. Do not infer the other key's identity or
purpose, or relax the strict predicate. This observation is separate from the
collection refusal and repeats the earlier mixed-usage shape.

Source-confirmed boundary mismatch: qualification_worker.publish changes only
the selected project/session, while qualification_contract.inventory requires
complete home-wide directory listing/stat coverage as manager UID1000 after the
runtime UID65532 has stopped. Successful selected publication cannot establish
manager access to all other directories. The precise offending entry remains
unknown; do not claim a particular directory caused EACCES.

Recommendation: stop identity-only live retries. Resolve the collection/custody
boundary with a bounded offline two-identity reproduction and a concrete design
that preserves complete coverage, credential exclusion and shutdown-before-copy.
Do not broadly chmod HOME, skip unreadable structure or inspect private roots as
an implicit workaround. Model evidence also needs an explicit resolution.
This is a proposed next scope, not authorization for privileged execution or
new product semantics. No further run, private read or credential access performed.
All five identities178579/180078/183114/183372/20260916T035035Z are consumed.
This supersedes the prepared/unconsumed status for20260916T035035Z; old evidence remains.


## 2026-09-16T03:56:43.607333+00:00 — owner selects bounded offline custody correction

Slawomir confirms "let's proceed - we need to assign to worker?" after the
post-authentication collection failure. Select Claude implementation and direct
independent review/correction cycle under OFFLINE-CUSTODY-CORRECTION-20260916.md. Resolve collection/custody
within existing invariants, pin concrete design before implementation, exercise
faithful offline manager/runtime boundaries, and preserve strict model refusal.
No private inspection, live engine/model, fresh identity or permission broadening.
Return only accepted completion or a real scope/authority decision. This
supersedes recommendation-only status; operator still holds Work until pass.

## 2026-09-16T04:00:34Z — the custody/collection mismatch, and the design (claim183524)

Run 20260916T035035Z: provider exit 0, successful terminal and session, exact
initial artifact, publication `0o2750`/`0o640`, consumed shutdown — then
`source-inventory` `state-coverage-incomplete`, cause **EACCES**, as the manager.
Cleanup confirmed, 6.432271532015875 s, no second turn.

**The correction cycle paid for itself.** Run183114 said `publish-shape` and
nothing else; this one names its step, its refusal and its errno, and carries the
provider's answer alongside. That is the difference between a wasted run and a
result.

**The mismatch is structural and it is mine.** Publication relaxes exactly two
objects while `inventory` demands **whole-HOME** name and type coverage under a
different UID. Those two rules cannot both hold over a home whose other
directories the CLI creates `0o700`. I built each half against its own review and
never checked them against each other.

### The design: publish traversal, not contents

**Name and type coverage needs `r-x` on directories. It does not need `r` on
files.** `scandir` needs read on the directory; `entry.stat` needs search on the
directory; neither opens a file. And P1b already records an unreadable *file* as
`content: unreadable:<errno>` and continues — only unreadable *structure* refuses.

So the runtime, which owns its state, publishes **traversal**: every
runtime-owned directory in the home becomes `0o2750` — group read and search,
setgid preserved, no world access — while **every file keeps the mode the CLI
gave it**, except the one selected session at `0o640`. The manager can then see
every name and type it must check, and can read exactly one file: the one it is
entitled to copy.

**This is not the broad HOME chmod the selection forbids.** No file content
becomes readable that was not already; `.claude.json`, every other session and
every cache file stay exactly as the CLI left them. Nothing is skipped, nothing
extra is copied, and no model, artifact or continuity gate moves.

Every bounded invariant is kept: complete required name/type coverage, credential
exclusion, no foreign or nested session acceptance, exact selected-state custody,
no symlink or hardlink escape, descriptor identity across checks and mutation,
original runtime exclusion before manager copy, turn-2 restored `0o660`, and no
second turn on a failed first arm. **All mode changes still happen only after the
complete preflight**, on descriptors the survey itself opened, so the directory
count is bounded by its own closed check rather than by the file-descriptor limit.

**The model gap is untouched and unresolved.** `expected-plus-other` with two
keys is observed **again**; the strict predicate refuses it, as it should. The
other key's identity remains unknown and unrecoverable from a document that is
never retained. This custody correction is not model or production qualification
and does not change model policy or raw-output retention.

All five identities — 178579, 180078, 183114, 183372 and 20260916T035035Z — are
consumed. No live run, fresh identity, private-root inspection or consumed-root
repair.

## 2026-09-16T04:19:10Z — owner deferral applied to the current handoff

Reviewer baton.codex, claim183638, records the controlling owner ruling in
baton:work/records/2026/08/finding-v12-isolated-agent-workers/OWNER-FRESH-ATTEMPT-RECOVERY-20260916.md
and T177936 message183568. Production session reuse is optional, deferred and
nonblocking for minimum v12. This explicitly supersedes continuation183521,
OFFLINE-CUSTODY-CORRECTION-20260916.md's active execution/routing instruction,
and the later author handoff's instruction to continue direct correction review.
Historical technical findings and proposals are preserved, not erased.

review-2026-09-16T04-19-10Z.md records preservation and return to baton.ops for
parking. Candidate183524 remains unreviewed and unaccepted. Its manifest,
EVIDENCE-183524.json and operator-packet hashes match the handoff; no fixture,
test, snapshot, operator command, PROGRESS or product path was edited. Claude's
implementation claim ended at183579. The current review owns disposition
records only and selects no further implementation writer.

The retained author receipt reports offline exit0/no timeout/process group
absent and0.36381306999828666s. Its120 tests/46 probes and simulated-identity
limitations remain author evidence, not independent acceptance. No reviewer
verification process was started. New test/provider/engine spending0s; prior
reviewer4.766077615931863s and separate author/operator histories remain intact.

All five identities178579/180078/183114/183372/20260916T035035Z remain consumed.
Production profile/actual OCI context execution remain refused; model identity
and custody/restoration remain unqualified. No rerun, fresh identity, private
inspection, root repair, predicate relaxation or enabling is selected. W2's
separate readiness recommendation and W161234/C1/C2 acceptance do not accept
these partial bytes. Preserve open Work identity; ops parking is next, not a
satisfying closure. A future continuation requires explicit new selection.

## 2026-09-21T06:32:41Z — owner: first priority after v12 passes the cutoff

Recorded by baton.prompt from the owner's statement: "if v12 makes the cutoff that will be first to work on". The selected first follow-up is production session reuse for review-feedback correction: an independent review remains a separate execution, while its feedback returns through a newly scheduled implementation execution that resumes the original implementer's Claude conversation. Preserve context across correction rounds; measure token/cache/time effects rather than promising cache savings.

This establishes conditional first priority for existing W177936 and supersedes an unspecified later ordering, not the Sep16 minimum-release deferral or failed qualification evidence. Work stays parked until the owner accepts the v12 cutoff result and continuation is routed explicitly. Revalidate the retained candidate, model identity, custody/restoration and current runtime before implementation; no live qualification, enabling or automatic retry is authorized now. This is not an automatic verifier-to-Claude loop, and does not merge reviewer and implementer sessions.
