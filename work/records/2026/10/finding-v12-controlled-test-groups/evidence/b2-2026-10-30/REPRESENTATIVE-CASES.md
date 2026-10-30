# Representative boundary-inventory cases for independent review (owner M384894)

Prepared by K (interactive copilot under the owner-held claim E384883) on
2026-10-30. This is K's classification with evidence; it is NOT independent
acceptance. Every claim below names a file:line and, where a runtime behaviour
is claimed, a reproduction in `representative-reproductions.log` (R-numbers),
run on the prepared interpreter from `v12/python` with `PYTHONPATH=src`.

Categories used, as the owner asked: (i) genuinely absent validation;
(ii) validation performed elsewhere (a private helper, an inline check, or a
constructor the manager controls); (iii) inventory attribution limitation.

## 1. What the three big lists are made of

Measured over the 646 "caller" entries of the 696 unowned receiving entries
(`unowned-caller-candidates.txt`, `boundary-inventory-lists.json`), by reading
each public function's AST for how it uses the parameter:

| how the parameter is used in its function | entries | category |
|---|---|---|
| passed to a module-private helper `_xxx(...)` that validates it | 364 | (ii)/(iii) |
| passed to a private method `self._xxx(...)` | 38 | (ii)/(iii) |
| passed to a named validator (`check_workspace_storage`, `nominate_source`) | 5 | (ii)/(iii) |
| checked inline (`type(x) is`, `isinstance`, `x not in CONSTANTS`, `.startswith`) | 66 | (ii) |
| forwarded to another call (no visible validation at this site) | 90 | needs reading |
| used with no visible validation anywhere in the function | 81 | (i) candidates |
| never referenced in the body | 2 | dead parameter |

The 190 "boundary calls attributed to no entry" are the OTHER SIDE of the same
fact: they are `boundaries.<kind>(value, label)` calls inside exactly those
private helpers (`attempts._committed_record`, `custody._reconciled`,
`exchange._instant`, `failure_cause._committed`, `intake._abandon_fence_operation_id`,
`interrogation._diagnostics`, …; `representative-code-paths.txt` §D shows each
helper with its callers). The inventory follows only the helpers listed in
`COOPERATIVE_FORWARDERS` / `_through_helpers`; these newer helpers are not
listed, so their validation is invisible to it at both ends.

The 266 "owned, never probed" entries are owned (the inventory found the
validator) and simply have no probe written; they do not indicate missing
validation.

## 2. Representative cases

### Case A — provider_context.admit_context_use(control, jobs, authority, *, attempt_id, writer_id, profile_digest)
- Code: `provider_context.py:757-758` — `_text(attempt_id); _text(writer_id); _hash(profile_digest)`;
  `_text` is `provider_context.py:63-67` (`boundaries.identity(value, "provider context identity")` + bound);
  `_hash` is `provider_context.py:70-73`.
- Reproduction: R1 `attempt_id=123` → `ContractRefusal(integrity, schema): provider context identity is durable text`;
  R10 `_hash("nope")` → refusal.
- Classification: `attempt_id`, `writer_id`, `profile_digest` are (ii)+(iii): validated through a private helper the inventory does not attribute.
- Contrast: `jobs`, `authority` (store capabilities) — R2 `jobs=None` → `AttributeError: 'NoneType' object has no attribute 'replay'`. No typed-capability ownership at the crossing. Category (i) — but the catalog already treats the injected store `control` the same way (declared operand, no `boundaries.capability`), so whether a store capability must be owned by `boundaries.capability` is a specification question for the owner.

### Case B — launch.launch_document(..., job_execution=None, provider_context=None)
- Code: `launch.py:500-513` — `_job_execution(job_execution)` (`launch.py:362`, W156162: every member required) and `_context_delivery(provider_context, ...)` (`launch.py:1007`).
- Reproduction: R3b `job_execution="bad"` → `ContractRefusal(integrity, schema): a launch document value is durable text`.
- Classification: (ii)+(iii).

### Case C — failure_cause.record_and_raise_cessation_intent(store, attempt_id, *, component, …)
- Code: `failure_cause.py:457` `component=_component(component)`; `_component` at `failure_cause.py:329-335` refuses a name outside `COMPONENTS`.
- Reproduction: R4b `_component("bad")` → refusal naming the closed set. (R4 with `store=None` escapes earlier at the store, before the component is read — the store precondition precedes it.)
- Classification: (ii)+(iii).

### Case D — exchange.activity_identities(delivery, *, session) and context_delivery.configure_context_storage(…, excluded_roots, runtime_uid)
- Code: `exchange.py:1124-1126` `if type(delivery) is not ExchangeDelivery: _untrusted(...)`; `context_delivery.py:77` `if type(excluded_roots) is not list or not excluded_roots: refuse`.
- Reproduction: R5 → `ContractRefusal(policy, denied)`; R6 → `ContractRefusal(refused, precondition): storage exclusion roots must be explicit`.
- Classification: (ii) inline checks not routed through `boundaries`; the inventory cannot see them by design (it looks for the layer). Whether inline exact-type checks satisfy PLAN 4bz is a rule question for the owner.

### Case E — attempt_logs.AttemptLogs.place(self, stream) and attempt_logs.named(stream)
- Code: `attempt_logs.py:164-165` `named(stream)`; `named` at `attempt_logs.py:253` applies `attempt_log_format.named`'s rule.
- Reproduction: R7 `named("../x")` → `ContractRefusal(policy, denied): '../x' is not a stream this delivery names`.
- Classification: (ii)+(iii).

### Case F — documents.abandon_intent(**members) and 29 sibling emitters
- Code: `documents.py:800-808` → `_emit("attempt.abandon-intent", members)` (`documents.py:651`), the module's one schema-validating emitter.
- Classification: (iii): one private helper owns every emitter's `members`; the inventory does not attribute `_emit`.

### Case G — custody.adopted_directory_custody(..., prepared_store=None)
- Code: `custody.py:2316` `_recorded_store(store, prepared_store)` (`custody.py:2378`).
- Reproduction: R9 refuses earlier at the custodian image identity (the probe never reaches `prepared_store`); the helper exists in code.
- Classification: (ii)+(iii), with the note that reaching it needs a composed world.

### Case H — workspaces.settle_cleanup(control, connection, assignment_id, admitted, what)
- Code: `workspaces.py:2745-2804`. `connection` appears ONLY in the docstring ("the caller's open transaction connection"); the body writes through `control.operation_record(...)` and `control._record(...)` (lines 2755, 2775, 2785 of the function) and never touches `connection`. Caller: `intake.py:5547` inside the ending's `store.transact(...)`.
- Reproduction: R8 `connection=None` → refused for want of the admission (`admitted`), i.e. the parameter is never read.
- Classification: dead parameter AND a docstring contract ("NO NESTED TRANSACTION … `connection` is the caller's open …") that the body does not honour through the parameter. Whether `control._record` already rides the same open connection is a store-internals question. K did NOT change this one: it touches transaction semantics. Owner/independent decision requested.

### Case I — the two `port` entries owned twice (intake discharge gates)
- Code: `intake.py:1591-1595` (`discharge_quiescence_gate`) and the twin at 3516ff: `boundaries.capability(getattr(port, "satisfy_gate", None), "the authority session's gate discharge")` then `_require_participant(port, ...)`.
- Second owner: `CONSTRUCTED_BY["port"] = "authority_port.py:AuthorityPort.__init__"` (`test_boundary_inventory.py:3188`): every caller `port` is already owned where the manager constructs it.
- Classification: (ii) validated elsewhere → the discharge gates' capability check is a blanket revalidation that PLAN 4bz forbids. Two honest resolutions: remove the two redundant `boundaries.capability(getattr(port, ...))` calls (product), or record a justified exception for `satisfy_gate` (a method added later, W119548, that an older port might lack). Owner decision; K changed nothing.

### Case J — injected: authority_port.AuthorityPort.claim answer members (13 entries, 36 unprobed)
- Code: `authority_port.py:457-468`: `answer = self._session.claim({...})`; `taken = boundaries.document(answer, "the claim answer's result", ...)`; `self._decided(taken, scope, role, ...)` owns the decision members.
- Classification: the envelope is owned; `claim.claim_event`, `claim.decision.grant`, `claim.decision.policy_generation` are members the inventory sees read without a per-member owner → needs reading of `_decided` (private method) — (iii) likely, possibly (i) for members used raw.

### Case K — adopted: provider_context._history / _qualified read `operations` by `control._connection.execute("SELECT operation_id FROM operations …")`
- Code: `provider_context.py:576`, `provider_context.py:280`.
- Classification: (i) candidates: raw SQL reads not through `boundaries.row`/a canonical decoder, in a module that otherwise owns everything through `_text`/`_hash`. Also an architectural question: the module reaches `control._connection` directly instead of a store method.

## 3. What this means for the campaign estimate

The 696/190/266 counts overstate missing runtime validation. On the evidence
above, most of the receiving entries are validated by private helpers or
inline checks the inventory cannot attribute (categories ii/iii), the 190
unattributed calls are those same helpers seen from the other side, and the
266 probes are test authoring over already-owned entries. The genuine (i)
candidates are the 81 "no visible validation" caller entries, the 31 injected
and 19 adopted entries, each of which still needs reading one by one.

## 4. Proposed bounded repair slices (not authorized; for owner selection)

| slice | outcome | depends on | files (overlap) | acceptance evidence |
|---|---|---|---|---|
| S1 helper attribution | the inventory follows the named private validating helpers (one justified entry per helper, each reviewed as a real owner); expected to clear most of the 364+38+5 entries and the 190 orphans together | — | tests/manager/test_boundary_inventory.py only | `just test-group scans`: the two lists shrink by exactly the attributed entries; no product change |
| S2 inline checks | owner rule: route the 66 inline checks through `boundaries` (product) OR declare them STATED with reason (test); K recommends the owner picks per kind | S1 | product modules named per entry + the inventory | `just test-group scans` + the modules' own groups |
| S3 genuine gaps | per-entry decisions over the 81 + 31 + 19 candidates: add ownership at the crossing or justify; includes Case K's raw SQL reads and Case A's store capabilities | S1 (to see the true residue) | provider_context, workspaces, oci, source_boundary, store, authority_port, exchange, context_delivery | focused module groups + `scans` |
| S4 probes | author the probes for owned entries (per module) | S1 | tests/manager/test_boundary_inventory.py | `EveryProbeProvesItArrived` green |
| S5 two product questions | Case H (`settle_cleanup connection`) and Case I (`port` revalidation) | owner decision | workspaces.py / intake.py | module groups |

Overlap note: oci.py, launch.py and exchange.py are dirty candidate bytes of
other Work; any S2/S3 edit there must be sequenced after those candidates land
or coordinated with their authors.
