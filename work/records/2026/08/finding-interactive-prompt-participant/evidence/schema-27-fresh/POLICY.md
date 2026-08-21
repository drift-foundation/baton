# Generate the fresh execution policy

Set `RELEASE`, `NEW_HOME`, and `CODEX_HOME` to absolute paths. Run this only
after the generation-1 config has been accepted by the fresh schema-27
authority:

```bash
POLICY_STAGED="$NEW_HOME/baton.rules.staged"
POLICY_FILE="$CODEX_HOME/rules/baton.rules"
GENERATOR="$RELEASE/lib/codex-event-bridge/src/exec_policy.mjs"
install -d -m 700 "$CODEX_HOME/rules"
: > "$POLICY_STAGED"
for who in baton.prompt baton.codex baton.tuner; do
  node "$GENERATOR" binary="$RELEASE/bin/baton" config="$NEW_HOME/baton.json" participant="$who" >> "$POLICY_STAGED" || exit 1
done
install -m 600 "$POLICY_STAGED" "$POLICY_FILE"
```

Do not append old rules. The dispatcher preflights every configured target,
including interactive `baton.prompt`, although only `baton.codex` and
`baton.tuner` have Work-readiness producers.
