# Schema-27 fresh-authority candidates

These are input templates for the combined W1477/W1594 rollout. They are not
an in-place update and are not directly runnable until an operator substitutes
the documented values.

- `baton.template.json` preserves every existing kind and Route, adds the
  unrouted `prompt` role and `baton.prompt` participant, and stays at
  generation 1. Replace `{{fresh-authority-uuid}}` with the UUID minted by
  `init`, `{{repository-root}}` with the absolute checkout path, and every
  `{{release}}` and `{{home}}` occurrence with the new immutable release and
  fresh coordination home.
- `infra.template.json` is the `conf/infra.example.json` contract with
  deployment-owned locators expressed as `{{repository}}`, `{{release}}`,
  `{{home}}`, `{{workspace}}`, `{{runtime}}`, and `{{codex}}`. Render those
  from the fresh inputs while preserving its lifecycle-owned context/render
  references.
- `codex-event-bridge.template.json` is the shipped dispatcher contract with
  deployment-owned locators expressed as `{{release}}`, `{{home}}`,
  `{{codex-home}}`, and `{{runtime}}`. Lifecycle rendering replaces only its
  three `{{context.*.threadId}}` references.
- `acp-claude.template.json` and `acp-gemini.template.json` preserve both live
  managed implementation runtimes. Baton paths, workspace, and per-start
  state derive from the fresh rollout. Adapter/provider and prohibition-policy
  inputs remain separate and explicit; they are never copied from Baton.
- `POLICY.md` gives the only policy-generation sequence. The policy is derived
  from the new release binary and accepted fresh config; no prior rule file is
  copied.

The files under sibling `generation-3/` are retained chronological evidence
only. They name the old authority and must never be installed.
