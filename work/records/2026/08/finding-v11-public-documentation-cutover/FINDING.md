# Finding: rewrite public documentation for the v11-only architecture

## Context

Child of W99. The active README, user documentation, examples, and architecture picture must describe the certified v11 Work/Thread/Message model and its distribution/coordination layout without advertising protocol-10 launch or fallback paths.

Historical release records may continue to describe their historical release, but active guidance must be unambiguous.

## Revalidated public surface — 2026-08-17

### Active documents to rewrite or reconcile

- `README.md` is an 868-line protocol-10 product manual. Its model, quickstart,
  CLI, TUI, version layout, and storage sections describe directed mailbox
  messages, notices, `send`/`reply`, `baton-tui`, and protocol-10 deployment.
  Replace it with a concise v11 product entry point; do not line-edit the old
  manual into a hybrid.
- `docs/AGENTS-MAILBOX-PROTO.md` is entirely the protocol-10 agent contract,
  yet repository policy still requires agents to read this stable path. Keep
  the filename to avoid breaking participating repositories, but replace its
  content with the v11 claim/pass/request/obligation/Work contract.
- `docs/BATON-WORK.md` and `docs/BATON-SETUP.md` are the current v11
  distribution documents. Preserve their ruled detail, reconcile them against
  the final CLI grammar after the in-flight v11 batch, and add clear links from
  the new README rather than duplicating the whole operator contract.
- `docs/CODEX-APP-SERVER-EVENT-CONNECTIVITY.md` and
  `tools/codex-event-bridge/README.md` still present the combined
  `just codex-baton` protocol-10 monitor stack as normal operation. Rewrite
  them around a standalone loopback app server, the generic event dispatcher,
  and the separately launched v11 `codex-baton-bridge` readiness producer.
  They must not retain the v10 overlap procedure, stack-owned Baton config, or
  `baton-codex-monitor` vocabulary after W101 removes those paths.
- `tools/acp-baton-bridge/README.md` correctly describes the agent-neutral ACP
  boundary but contradicts itself about co-deployment and hard-codes obsolete
  projection majors. State that the ready ACP bridge co-deploys with the v11
  distribution, while agent adapters, sessions, credentials, and prohibition
  policy remain deployment-owned. Refer to the shared current envelope gate
  rather than freezing a projection number in prose.
- `docs/LEGACY-CUTOVER-ON-DEMAND.md` is live fallback guidance, not a release
  record. Remove it once the v11-only docs land.

`docs/EFFECTIVE-BATON.md` belongs exclusively to W104. W103 may link to the
W104 result but does not rewrite it. `docs/RELEASE*.md`, permanent finding
dossiers, review journals, and other explicitly historical evidence stay
byte-honest history and are excluded from active-guidance scans.

### Public architecture to show

The new README should show one small durable topology rather than reproduce
implementation internals:

```text
human TUI          agent JSON CLI
    \                  /
     protocol-11 baton
  baton.json + one SQLite authority
 Work graph / Threads / Messages / Events
             |
 configured repository roots -> permanent work/records dossiers

read-only wait -> external readiness adapters -> Codex app-server or ACP agent
```

The diagram must make three boundaries explicit: Baton is the coordination
authority, dossiers are referenced durable evidence rather than a competing
database, and model-specific readiness is external to Baton and never claims
or completes Work for the agent.

### Screenshot disposition

`assets/artwork/baton-tui.png` visibly depicts the retired v10 inbox
(`MESSAGES`, notice/reply glyphs, message claims, and the old detail pane).
It cannot remain in the v11 README. Replace it with a sanitized v11 Work-tree
and Work-detail image produced from a scratch authority, or remove the image
until such an artifact exists; never relabel the v10 pixels as v11. A new
image must omit host/user paths and show the current column/pane vocabulary.

### Vocabulary order

W103 uses the protocol's current `Thread` term. W3 intentionally waits for the
entire v10-retirement umbrella and will later perform the `Thread` to `Topic`
rename across product and docs. Making W103 depend on W3 would create a cycle
because W99 cannot close until W103 closes.

### Distribution boundary

The v11 release already ships `BATON-WORK.md` and `BATON-SETUP.md`. Add the
rewritten `AGENTS-MAILBOX-PROTO.md` to the immutable `doc/` assets so a team
can bootstrap agent policy from the same exact release as its CLI. The root
README, integration development documents, historical release notes, and
screenshots remain repository documentation rather than runtime inputs.

## Acceptance additions

- The root README's quickstart exercises only `just deploy-v11`, `baton init
  directory=...`, explicit config/participant selection, `activate`, and the
  v11 JSON/TUI surfaces. Examples use the strict `VERB key=value` grammar.
- Active docs contain no protocol-10 launch, mailbox, notice, `send`/`reply`,
  `baton-tui`, combined `codex-baton` stack, legacy alias, or fallback
  instruction. Explicitly historical release records are not rewritten to
  satisfy this scan.
- Every repository-local link from the README resolves, and every documented
  installed path exists in a scratch `just deploy-v11` distribution.
- The deployed `doc/AGENTS-MAILBOX-PROTO.md` is byte-equal to the rewritten
  source document and names protocol 11.
- Codex configuration examples validate against the post-W101 generic bridge
  schema; ACP examples and commands match the co-deployed release layout.
- Human review confirms the public architecture diagram and any TUI image do
  not depict the retired product or expose machine-specific data.

## Follow-up public positioning — 2026-08-18

**Confirmed by Slawomir.** The README leads with the one-line product promise
“Multiplex engineering work across people, agents, teams, and models.” Baton
must not present itself as an agent-only tool because humans participate in the
same authority and TUI.

The README also makes the integration boundary and its operational value
explicit:

- Baton ships a generic ACP JSON-RPC/stdio readiness bridge. Claude, Gemini,
  Grok, or another agent can participate when exposed through a conforming ACP
  adapter; naming examples does not move model-specific credentials, sessions,
  permissions, or adapter policy into Baton.
- Codex is supported separately through the dedicated app-server readiness
  bridge rather than being described as ACP.
- Model-neutral coordination is an operational hedge: a team can switch away
  from an unavailable provider or route suitable Work to another model/persona
  without replacing its authoritative Work graph or losing the handoff trail.

### Version-neutral architecture label

**Confirmed by Slawomir.** The README's “Shape of it” diagram names the durable
layer **Baton protocol authority**, not `protocol-11 baton authority`. The
diagram explains the product architecture and should not require editorial
changes merely because a later protocol release changes the current version.
Version-specific compatibility statements remain prose outside that durable
architecture label.

### User-facing architecture boundary

**Confirmed by Slawomir.** The “Shape of it” diagram omits `baton.json`,
SQLite, and the `wait` operation. Those are implementation and operator
details, not concepts that help a reader understand the product at a glance.
The diagram names persistent local dossiers directly and shows readiness
adapters leading to Codex or any ACP agent.
