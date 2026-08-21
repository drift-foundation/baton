# Cutover: schema-27 authority with a separate interactive Prompt

This is the operator checklist for the combined W1477/W1594 rollout. It
creates one immutable release and one fresh authority. It does not update,
copy, or migrate an existing Baton database.

## Inputs and hard stop

Choose absolute paths and export them before doing anything mutable:

```bash
REPOSITORY=/absolute/path/to/baton/source
RELEASE=/absolute/path/to/new/immutable/v11-release
NEW_HOME=/absolute/path/to/new/coordination-home
WORKSPACE=/absolute/path/to/baton/source
CODEX=/absolute/path/to/codex
CODEX_HOME=/absolute/path/to/codex-home
RUNTIME=/absolute/path/to/new/runtime
CLAUDE_AGENT=/absolute/path/to/claude-agent-acp
CLAUDE_POLICY=/absolute/path/to/claude-policy-root
CLAUDE_CONFIG_DIR=/absolute/path/to/claude-config-directory
GEMINI=/absolute/path/to/gemini
GEMINI_POLICY=/absolute/path/to/gemini-policy/deny-git-mutations.toml
GEMINI_PROJECT=deployment-owned-google-cloud-project
```

`RELEASE` must not exist because deployment publishes an immutable directory.
`NEW_HOME` must be a new empty coordination home. Stop if either resolves to
an existing release or authority. In particular, do not copy an old
`work.sqlite3`, authority UUID, accepted config, generated policy, lifecycle
state, or runtime directory. Schema 27 intentionally refuses a schema-26
database; durable repository dossiers, not database copying, carry the
historical decisions into the new authority.

The candidates are under `evidence/schema-27-fresh/`. The sibling historical
candidate directory is superseded evidence and is not an installation source.

## Build the release, scaffold, and render generation 1

Run the reviewed complete gate first. From `REPOSITORY`:

```bash
just test-v11
just deploy-v11 "$RELEASE"
mkdir -p "$NEW_HOME" "$RUNTIME"
"$RELEASE/bin/baton" init directory="$NEW_HOME"
AUTHORITY_UUID=$(jq -er '.instance.authority_uuid' "$NEW_HOME/baton.json")
```

Render the config candidate with the UUID minted by this `init`. The `prompt`
role and `baton.prompt` participant are therefore present in generation 1,
before the database exists:

```bash
CANDIDATES="$REPOSITORY/work/records/2026/08/finding-interactive-prompt-participant/evidence/schema-27-fresh"
jq --arg uuid "$AUTHORITY_UUID" --arg repository "$REPOSITORY" --arg release "$RELEASE" --arg home "$NEW_HOME" '
  def replace($from; $to): split($from) | join($to);
  walk(if type == "string" then
    replace("{{fresh-authority-uuid}}"; $uuid)
    | replace("{{repository-root}}"; $repository)
    | replace("{{release}}"; $release)
    | replace("{{home}}"; $home)
  else . end)
' "$CANDIDATES/baton.template.json" > "$NEW_HOME/baton.json.staged"
install -m 600 "$NEW_HOME/baton.json.staged" "$NEW_HOME/baton.json"
```

Render the lifecycle and dispatcher inputs from the same release and home.
Only the lifecycle-owned `{{context.*.threadId}}` and `{{render.*}}`
references remain after these commands:

```bash
jq --arg repository "$REPOSITORY" --arg release "$RELEASE" --arg home "$NEW_HOME" --arg workspace "$WORKSPACE" --arg runtime "$RUNTIME" --arg codex "$CODEX" '
  def replace($from; $to): split($from) | join($to);
  walk(if type == "string" then
    replace("{{repository}}"; $repository)
    | replace("{{release}}"; $release)
    | replace("{{home}}"; $home)
    | replace("{{workspace}}"; $workspace)
    | replace("{{runtime}}"; $runtime)
    | replace("{{codex}}"; $codex)
  else . end)
' "$CANDIDATES/infra.template.json" > "$NEW_HOME/infra.json"

jq --arg release "$RELEASE" --arg home "$NEW_HOME" --arg codex_home "$CODEX_HOME" --arg runtime "$RUNTIME" '
  def replace($from; $to): split($from) | join($to);
  walk(if type == "string" then
    replace("{{release}}"; $release)
    | replace("{{home}}"; $home)
    | replace("{{codex-home}}"; $codex_home)
    | replace("{{runtime}}"; $runtime)
  else . end)
' "$CANDIDATES/codex-event-bridge.template.json" > "$NEW_HOME/codex-event-bridge.template.json"

jq --arg release "$RELEASE" --arg home "$NEW_HOME" --arg workspace "$WORKSPACE" --arg runtime "$RUNTIME" --arg claude_agent "$CLAUDE_AGENT" --arg claude_policy "$CLAUDE_POLICY" --arg claude_config "$CLAUDE_CONFIG_DIR" '
  def replace($from; $to): split($from) | join($to);
  walk(if type == "string" then
    replace("{{release}}"; $release)
    | replace("{{home}}"; $home)
    | replace("{{workspace}}"; $workspace)
    | replace("{{runtime}}"; $runtime)
    | replace("{{claude-agent}}"; $claude_agent)
    | replace("{{claude-policy}}"; $claude_policy)
    | replace("{{claude-config-dir}}"; $claude_config)
  else . end)
' "$CANDIDATES/acp-claude.template.json" > "$NEW_HOME/acp-claude.template.json"

jq --arg release "$RELEASE" --arg home "$NEW_HOME" --arg workspace "$WORKSPACE" --arg runtime "$RUNTIME" --arg gemini "$GEMINI" --arg gemini_policy "$GEMINI_POLICY" --arg gemini_project "$GEMINI_PROJECT" '
  def replace($from; $to): split($from) | join($to);
  walk(if type == "string" then
    replace("{{release}}"; $release)
    | replace("{{home}}"; $home)
    | replace("{{workspace}}"; $workspace)
    | replace("{{runtime}}"; $runtime)
    | replace("{{gemini}}"; $gemini)
    | replace("{{gemini-policy}}"; $gemini_policy)
    | replace("{{gemini-project}}"; $gemini_project)
  else . end)
' "$CANDIDATES/acp-gemini.template.json" > "$NEW_HOME/acp-gemini.template.json"
```

Inspect the rendered files before activation. No deployment token may remain;
the context/render tokens named above must remain for lifecycle rendering.
Confirm that all preexisting kinds and Routes still match the candidate and
that `prompt` is absent from every Route handler list. Confirm the Claude and
Gemini adapter, provider, permission-mode, and policy values against the
deployment-owned inputs; Baton does not infer or supply them.

## Activate, generate policy, and start

The approver accepts the fresh proposal exactly once:

```bash
"$RELEASE/bin/baton" --participant baton.slaw activate directory="$NEW_HOME"
```

Generate a new policy from this release binary and this accepted config using
`evidence/schema-27-fresh/POLICY.md`. Do not append or copy an earlier policy.
Then start the fresh backend from the source checkout:

```bash
just start "$NEW_HOME"
just status "$NEW_HOME"
```

The lifecycle must mint separate `prompt`, `reviewer`, and `tuner` contexts.
It starts exactly one Work-readiness producer for `baton.codex`, exactly one
for `baton.tuner`, and none for `baton.prompt`.

## Acceptance and interactive attachment

Record these checks against the fresh paths:

```bash
jq -e '.contexts | keys | sort == ["prompt", "reviewer", "tuner"]' "$NEW_HOME/run/infra-state.json"
jq -e '[.contexts[].threadId] | length == 3 and (unique | length == 3)' "$NEW_HOME/run/infra-state.json"
jq -e '[.services[] | select(.participant == "baton.prompt")] | length == 0' "$NEW_HOME/infra.json"
jq -e '[.services[] | select(.participant == "baton.codex")] | length == 1' "$NEW_HOME/infra.json"
jq -e '[.services[] | select(.participant == "baton.tuner")] | length == 1' "$NEW_HOME/infra.json"
jq -e '[.services[] | select(.participant == "baton.claude")] | length == 1' "$NEW_HOME/infra.json"
jq -e '[.services[] | select(.participant == "baton.gemini")] | length == 1' "$NEW_HOME/infra.json"
"$RELEASE/bin/baton" --config "$NEW_HOME/baton.json" --participant baton.slaw runtime
```

The runtime inventory must map each participant to its one minted thread:
`baton.prompt` to `prompt`, `baton.codex` to `reviewer`, and `baton.tuner` to
`tuner`. The inventory must also retain one `baton.claude` ACP runtime and one
`baton.gemini` ACP runtime, each using its own rendered configuration and
per-start state directory. A missing, duplicated, or cross-mapped session
fails the rollout.
When the managed reviewer claims its first fresh review assignment, compare
that Work's Handler with `runtime`: both must identify the reviewer context
while Prompt remains independently usable.

Attach the human TUI only to the prompt locator:

```bash
PROMPT_THREAD_ID=$(jq -er '.contexts.prompt.threadId' "$NEW_HOME/run/infra-state.json")
codex resume --remote ws://127.0.0.1:4500 "$PROMPT_THREAD_ID"
```

Never attach the interactive TUI to `.contexts.reviewer.threadId`, and never
arm a Baton readiness consumer for `baton.prompt`.
