# Correction plan: the v11 instance configuration boundary

**Plan only; Gate B remains stopped and no source changes until this is
reviewed.** Answers the 2026-08-14 supersession ("v11 requires an instance
configuration boundary") and the configuration-path clarification. The gap it
corrects is mine to own: Gate A shipped dynamic `register-*` commands and an
`--authority`/`--viewer` surface, which is identity-by-assertion and topology
discovered piecemeal — exactly what `baton.json` exists to prevent, and the
reported viewer-validation gap was this architecture gap wearing a small
symptom.

## 1. The v11 configuration schema

One strict JSON document, canonical deployment `mailbox/v11/baton.json`
(stable filename; the generation lives in the path as organization, never as
the handshake — the document itself declares its protocol and is validated):

    {
      "config_version": 1,
      "protocol_version": 11,
      "generation": 1,
      "instance": {"name": "drift-suite-v11"},
      "teams": {
        "lang": {
          "display": "Language",
          "members": {"ada":   {"display": "Ada",
                                "roles": ["rsrch", "rev"]},
                      "grace": {"display": "Grace",
                                "roles": ["impl"]}},
          "roles":   {"rsrch": {"display": "Research"},
                      "impl":  {"display": "Implementation"},
                      "rev":   {"display": "Review"}},
          "kinds":   {"bug":   {"display": "Bug intake",
                                "route": {"role": "rsrch",
                                          "handlers": ["ada"]}}}
        }
      }
    }

Validation at load, all of it before anything else runs:

- strict JSON: duplicate keys and unknown fields refused (the discipline
  every trust document in this project already follows);
- every team/member/role/kind handle passes the 6/6 wcwidth grammar — the
  Gate A validator moves from registration time to config time unchanged;
- `route.role` names a declared role; every `route.handlers` member holds
  that role; every kind has a route (an endpoint that resolves to nobody is
  refused at config time, not discovered at tag time);
- display names mandatory, free text.

The authority file sits beside the config (`mailbox/v11/work.sqlite3`),
located from the config's directory exactly as protocol 10 locates its
SQLite — no `--authority` flag survives.

## 2. Source of truth: the config is a proposal, the authority accepts it

Protocol 10's hard-won rule, carried over whole: editing the file changes
nothing the authority believes. `init` accepts generation 1; every later
change is accepted by an explicit audited transition (`accept_config`,
the v11 `regen`) which validates the document, records its digest and
generation, projects it into the identity tables, and writes one event.
`open` refuses when the file's digest is not the accepted one — a modified
config is a proposal awaiting acceptance, said in those words.

The Gate A tables (`teams`, `members`, `kinds`) stop being mutable registry
and become the projection of the accepted configuration. The registration
events in existing authorities remain readable history; the registration
COMMANDS are removed.

Continuity rules on acceptance, enforced against history:

- a kind removed from the config is RETIRED, never deleted; its name stays
  taken forever (Gate A's rule, now driven by config diff);
- a team or member removed must not strand anything: open Work whose
  `Current` endpoint or pending obligation resolves through a removed
  kind/handler refuses the acceptance and names the stranded records —
  the config cannot orphan responsibility that "no open work without a
  responsible endpoint" protects;
- handles never change meaning: a handle reused for a different display
  identity across generations is accepted (display is mutable); a removed
  handle reused for a NEW thing is refused, same reason kinds never return.

## 3. Generation and change lifecycle

`generation` increments by exactly one per acceptance; the acceptance event
records old/new generation, the new digest, and a structural diff summary
(added/removed/retired identities, route changes). Handler reassignment is a
config change like any other — one generation bump, one audited event —
which is deliberately heavier than a side-channel "swap handler" verb: route
responsibility moving without an audit trail is the defect the model calls
out ("reassigning a route... does not change history" — and history must
show the reassignment itself).

## 4. Route resolution and handler assignment

`team.kind` stays the public endpoint. Resolution happens AT USE, against
the currently accepted generation: tagging `@lang.bug` resolves to the
route's role and current handlers and records the resolved
(endpoint, role, handlers, generation) in the event, so later
reassignment never rewrites what an obligation meant when created.
Obligations continue to be OWED by the endpoint; the projection exposes the
current handler(s) alongside (the finding: the table shows the route,
detail may expose the handler). No dispatch pipeline appears anywhere —
a route is lookup, not workflow.

## 5. Participant validation — the reported gap, closed architecturally

The surface becomes `--config PATH --participant team.member` for CLI, JSON
and TUI alike. Opening validates, in order, before any output or curses:

1. config readable, strict-parses, schema-valid;
2. document protocol == client protocol (11) — mismatch refuses with both
   numbers, path evidence never substituting for the handshake;
3. authority present, its accepted digest == this config's digest, its
   authority uuid == the one recorded at init (config/authority pairs are
   not interchangeable);
4. `--participant` names a configured member — refusal before curses, the
   B1 xfail's expectation, now for the right reason.

One validated participant context flows through every read and transition;
`--viewer` disappears rather than becoming a synonym. Open-graph visibility
is untouched: this validates who is asking, never what they may see.

## 6. Initialization and failure modes

`baton-work --config ... init` creates the authority beside the config and
accepts generation 1. Every failure is a refusal naming the layer: missing
config / unparseable / schema / handle grammar / route incoherence /
protocol mismatch / digest mismatch ("edited but not accepted") / uuid
mismatch ("this authority belongs to another config") / unknown participant.
Each gets a test; none gets a traceback.

## 7. Migration of the Gate A surface and tests

Code (serial steps, each with evidence + break-sweep as before):

- **C1** config schema + strict loader + validation (pure; no authority);
- **C2** `init`/`accept_config` in the authority; registry tables become
  projection; continuity rules; open-time digest/uuid/participant checks;
- **C3** CLI surface: `--config`/`--participant`; `register-*`/`retire-kind`
  verbs removed; everything else unchanged in shape;
- **C4** resolution recording in tags/obligations + handler exposure in the
  projection;
- **C5** test migration: fixtures build config documents and `init`
  (the shared fixture becomes a config plus a script, closer to production
  shape); the handle-grammar vectors move to config-validation tests
  unchanged; the registration race test becomes a concurrent-acceptance
  test (same property: losers burn nothing); the soak seeds from config;
  scenario/parity/packaged switch flags; the B1 xfail flips to a passing
  refusal test;
- **C6** re-run B1–B3 on the corrected surface and re-submit Gate B
  evidence.

What deliberately does NOT change: the publication sequence, Work/edge/
message schema and transitions, readiness recomputation, tag cardinality,
the canonical projection's shape (one addition: current handler on
endpoint-bearing fields), the JSON envelope, pagination, purity. Gate A's
authority/transition evidence stands; what moves is who may speak and how
the cast is declared.

## Choices made here that review should confirm (none blocking, all cheap
## to reverse before C1)

1. handler reassignment requires a generation bump (no side-channel verb);
2. acceptance refuses configs that would strand open Work or pending
   obligations, naming them;
3. the authority file is always a sibling of the config (no override flag);
4. member roles live on the member (`"roles": [...]`) with route handlers
   validated against them, rather than roles listing members — same data,
   the shape that reads best in a config a human edits.

---

# Rev 2 — the four review corrections, before C1

## R-a. Acceptance without the open deadlock

Rev 1 had a hole: ordinary `open` refuses an edited config, but
`accept_config` must READ that edited config to accept it — refusing there
deadlocks every change. The v10 `regen` discipline, made explicit:

- **ordinary open** validates file digest == accepted digest and refuses
  otherwise ("edited but not accepted");
- **acceptance mode** (`accept_config`, and `init` as its generation-1 case)
  opens the AUTHORITY by the accepted state, reads the PROPOSAL file
  separately, and requires the proposal to declare
  `generation == accepted_generation + 1` explicitly — an edit that does not
  say it is the next generation is a mistake, not a proposal;
- acceptance itself is one write transaction, so two concurrent acceptances
  of generation N+1 serialize and the loser gets the ordinary
  race-refusal, burning nothing (the A1 property, reused);
- who may accept is a capability (see R-b), validated against the
  CURRENTLY ACCEPTED generation — the proposal cannot grant its own
  acceptor.

## R-b. Participants and routes as first-class schema objects

The vocabulary was implicit; now it is modeled. Two changes to §1:

- **`participants` is the identity surface**: a participant IS a configured
  `team.member`, and each member entry carries `capabilities` (as in v10:
  e.g. `"config"` for who may accept generations) alongside `display` and
  `roles`. The word "participant" appears in the schema documentation as the
  public identity term; `--participant` resolves against exactly this set.
- **`routes` is a named table per team**, not an attribute buried in kinds:

      "routes": {"intake": {"role": "rsrch", "handlers": ["ada"]}},
      "kinds":  {"bug": {"display": "Bug intake", "route": "intake"}}

  A route is addressable and reusable across kinds; a kind names its route;
  validation requires every kind's route to exist, every route's role to be
  declared, and every handler to hold the role. Resolution recording (§4)
  now records (endpoint, route, role, handlers, generation).

## R-c. Where the config–authority UUID binding lives

Stated precisely: the binding lives in the handshake record beside both
files — `mailbox/v11/WORK.json`, which `init` already writes read-only. It
gains one field:

    {"format": "baton.work-authority", "format_version": 1,
     "namespace": "v11", "protocol_version": 11,
     "authority_uuid": "<hex>"}

Open validates the triangle: WORK.json's uuid == the authority's meta uuid,
and the config's accepted digest == the authority's accepted digest. The
CONFIG file itself carries no uuid — it is a human-edited proposal and must
stay copyable between environments; the uuid pairs the DIRECTORY's authority
with its handshake, and a config dropped beside a foreign authority refuses
at the digest check with "this authority was initialized from a different
configuration lineage". The path stays organizational; the handshake stays
in documents.

## R-d. Versioned, documented surface changes

The projection version moves **1.0 → 2.0** (breaking), and the changes are
documented in the plan rather than discovered:

- envelope: `viewer` → **`participant`** (same position, same
  team.member string); requests carrying `--expect-projection 1.x` fail
  clearly, which Gate A already built and tested;
- every endpoint-bearing value in `detail`/`links`/`home` rows changes from
  the bare string `"team.kind"` to a structured object:

      {"endpoint": "lang.bug", "route": "intake",
       "role": "rsrch", "handlers": ["ada"]}

  resolved against the current generation at read time (history keeps the
  resolution recorded at event time);
- `obligations` rows gain the same structure for their endpoint;
- the TUI renders `endpoint` in the CURRENT/NEXT columns exactly as before
  (no visual change) and may expose role/handlers in detail — presentation,
  no semantics;
- CLI flags: `--authority`→`--config`, `--viewer`→`--participant`, and the
  removal of `register-*`/`retire-kind`, all listed in the C3 step and in
  the eventual release notes as breaking surface changes of the
  pre-release slice. Nothing deployed speaks projection 1.0, so no
  compatibility shim is built — stated so its absence is a decision.
