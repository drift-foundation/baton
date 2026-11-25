# Owner selections — 2026-11-25

Recorded by baton.prompt from the interactive owner conversation after M386227.

- D1 approved: request Claude selector `claude-fable-5[1m]`; require contributor identity `claude-fable-5`.
- D2: owner rejects continued use of the unhelpful historical Work-number alias and confirms `/home/sl/.claude/.credentials.json` as the correct source. Coordinator names the new descriptive reference `operator-file:claude-primary-subscription`. This alias is a configuration choice, not an account identity inferred from credential contents. No credential contents or registry were read or changed. Existing deployments and historical aliases remain untouched.
- D3 approved as recommended in the interactive response: Codex-equivalent container posture, 600 seconds per invocation for this small qualification, 15-second verification, one invocation per role, no retries/correction rounds. The 20-minute overall bound must be enforced by the script, not manual operator monitoring.
- D4 approved: no extra live uncertainty run. Retain deterministic evidence, configure routing to baton.slaw and inspect the owner queue after the selected run.

These settle configuration choices only. Offline build/setup selection A and live execution selection B remain separate; neither is selected by this record. Prepare the new registry mapping through the ordinary supported credential-source configuration in the packet, with conflict checks; do not silently overwrite an existing different mapping. No new secret copy or registry mutation is authorized by preparation alone.
