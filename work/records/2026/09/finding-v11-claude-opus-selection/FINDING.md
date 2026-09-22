# v11 Claude model selection — W234647

Owner 2026-09-22 explicitly selects Opus instead of Fable after reporting exhausted Fable usage. Set ANTHROPIC_MODEL=opus for v11 baton.claude only, including current rendered configuration for its next agent invocation; retain backups. Preserve v12 qualification manifest/image/model pins and all other participants. No live provider probe or unrelated restart is selected.

## Owner acceptance after reboot — 2026-09-22 UTC — baton.prompt

Read-only verification found ANTHROPIC_MODEL=opus in both the deployed
acp-claude.template.json and run/context/claude-acp.json. Slawomir reported the
machine reboot and explicitly accepted closure because the change and reboot
are complete. This supersedes any requirement to keep this configuration Work
open pending a further runtime observation. No live provider invocation or
reported model identity was observed by this acceptance; no such claim is made.
Separate service recovery and v12 qualification remain outside this disposition.
