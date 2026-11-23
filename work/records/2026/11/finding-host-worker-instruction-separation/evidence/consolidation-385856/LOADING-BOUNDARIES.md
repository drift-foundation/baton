# Instruction loading audit and bounded delivery proposal

Status: static source/configuration audit and policy candidate; worker delivery is
NOT implemented or qualified. No live provider call, Docker operation, build,
install, protected Git mutation or new agent context was used.

## Observed host chain

The root source is 51,628 bytes, 745 lines. Both inspected Codex homes
(`/home/sl/.codex` and `/home/sl/.codex-pushcoin`) have no `AGENTS.override.md` or
`AGENTS.md` and no explicit project-document budget/fallback configuration.
The current tool environment has no CODEX_HOME override. Root/cwd and the
`v12/`, `v12/python/`, `v12/worker/`, `docs/`, `tools/` paths have no additional
AGENTS/override files. The proposed root is below the default 32,768-byte project
budget. HOST-INTEGRATION.md is an explicit read-when-selected guide, not an
additional automatic instruction file. V12-WORKER-INSTRUCTIONS.md is not an
AGENTS filename and does not auto-select worker execution for a host source edit.

The official [Codex discovery guide](https://developers.openai.com/codex/guides/agents-md/)
describes global guidance followed by project-root-to-cwd files, override precedence
and a 32 KiB default bound. Nested files do not avoid that shared bound. This
candidate uses no nested AGENTS selector. Static inventory establishes the known
file-chain budget; it does not prove unseen launcher-injected instructions or
provider behavior. The original automatically truncated payload is not silently
claimed to have been refreshed in this running conversation. Import/restart or
explicit reread is needed before the new bytes govern a subsequent host session.

Host Claude is 2.1.330. Its user `~/.claude/CLAUDE.md` is 471 bytes (no imports),
with no project/ancestor CLAUDE file found on the checked paths. Current documented
Claude discovery can load AGENTS in that situation, but that is version-dependent.
Global user instruction bytes stay outside this candidate and were not copied or
altered. Auto-memory/managed deployment configuration is not fully inventoried;
no assertion of the entire live Claude system prompt is made.

## Observed native path and concrete gap

`v12/worker/Dockerfile.claude` pins Claude 2.1.247, not the host's version.
The official [Claude memory guide](https://code.claude.com/docs/en/memory) says
direct AGENTS loading requires 2.1.277 or later. Do not assume newer host behavior
or current documentation proves image behavior. No image was started here.

`claude_agent.py:_provider` uses a closed argv: `claude --print
--dangerously-skip-permissions --output-format json`, optionally model and session
or resume operands, and the task prompt. It sets cwd to the private candidate (or
OUTPUT_ROOT for contextual turns). `_prepared_home` supplies a private home and
credential path; it does not import host policy deliberately. No worker-policy
text, instruction-file selector, append-system prompt or explicit discovery
exclusion is added by this path. Source project files can still be discovered
according to the pinned CLI's rules. Arbitrary source text asking the model to
read root AGENTS is also possible. No new policy file changes these facts.

Implementation `_prompt` and host `provider_context.context_prompt` are byte-matched;
contextual argv/prompt digests are validated before invocation. Review, analysis,
clarification/response and continuation have additional prompt paths. Changing
only `_provider` or only the implementation prompt would break agreement or leave
roles uncovered. A policy revision must be bound in admitted execution identity
and preserve old admissions and retained context compatibility/refusal semantics.

There is no production Codex adapter at the audited base. W385830 is preparing it;
its CLI selection is 0.169.0. The inspected host reports that version, but a host
executable is not a qualified worker image. An exact native Codex loading claim
therefore cannot yet be verified on an existing production path.

## Minimal proposed delivery delta (not yet selected/implemented)

Deliver the reviewed worker document as an immutable execution input outside the
source repository, and bind its content digest together with the provider command
configuration. Select worker context explicitly in execution preparation, never
by `v12/AGENTS.md`, source cwd, replacing tracked source files or a model guess.
Keep the original task and candidate identities unchanged.

For Claude, pair the worker text delivery with explicit exclusion of the host-only
root instruction document. Preserve applicable project coding/test guidance and
selected task constraints; do not globally disable project guidance, hooks,
credentials or skills as a shortcut. `--bare` is not a neutral solution: current
CLI help changes authentication and more than instructions. Current docs expose
`claudeMdExcludes` and append-system-prompt delivery; qualify the exact selected
CLI's supported behavior before relying on those knobs. On the old image, direct
AGENTS is not documented as supported; explicit worker delivery remains necessary.
Do not import the host global CLAUDE file into a native provider home.

For Codex, the proposed adapter must explicitly compose a worker execution policy
and applicable source/task guidance. `project_doc_max_bytes=0` by itself is NOT a
complete design: it can discard needed project rules. Neither adding a fallback
filename nor placing a nested override prevents ancestor text loading. A supported
execution-specific loader/selector must exclude host-only policy while retaining
shared/project instructions and binding their bytes. Do not replace the model's
entire base instructions merely to append this policy. If the pinned CLI cannot
provide that selection without source mutation, report the capability gap and
select the exact adapter composition rather than silently dropping instructions.

This is a finite remaining integration decision/qualification task, not authority
to invent flags. W385830 ownership coordination was posted as M385858 in T385853
with include=baton.impl. No runtime/provider paths have been edited here.

## Required deterministic delivery proof

After ownership and the supported selector are settled, use the real preparation,
provider argv/environment and context-digest builders with a recording fake provider:

1. Host editing both root and v12 source receives host policy; no worker auto-load.
2. Every native role receives the exact worker-policy digest and selected project/
   task instructions; a host-only sentinel is absent from its composed instructions.
3. Cover fresh implementation, independent review, analysis, clarification response,
   continuation and context restore; matching host/worker prompt and argv digests.
4. No source/candidate bytes or protected Git metadata change merely to select
   instructions. Private HOME/config cannot import unrelated host instructions.
5. Missing, changed, oversized or unsupported policy/selector refuses before provider
   execution. Old admitted/context identities are not silently reinterpreted.
6. Byte-budget accounting covers the complete selected chain, including global,
   overrides, project/nested guidance and explicit appended policy, with no silent
   truncation. Required task constraints survive the selection.

Use the prepared interpreter and focused tests; anticipated groups are manager-pure
(provider/context) and tools-pure (composition), exact selection after the bounded
implementation is chosen. Real vendor discovery must be observed through a
supported non-model diagnostic or exact-version source/fixture; a fake provider
that merely echoes adapter inputs does not certify proprietary CLI discovery.
No full suite, live provider, image build/qualification or install is selected here.

## Acceptance disposition

The editorial candidate and rule matrix are reviewable now. Overall Work remains
unfinished until the selected delivery proof succeeds or the owner explicitly
decomposes it with a recorded dependency and joined acceptance consumer. There is
no decomposition implied by this document and no claim that W385830 already owns
the remaining proof. The immediate continuation is to settle the supported native
instruction selector with K and coordinate exact shared-file ownership, then
implement/verify that bounded delta or install an explicit decomposition gate.
