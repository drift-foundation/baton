# Register custody receiving boundaries in the shared inventory

W43977, child of W36540. No dossier was bound at the claim; the Work names
`work/records/2026/08/finding-v12-worker-custody-provider/PLAN.md` as its
owning evidence and the contract is complete in its own thread (seq 43977,
44029). This record is created at the implementation claim, beside its two
siblings, on the precedent W43975 set.

## What the inventory asked, and what the rescan found

The pinned research (parent PLAN, "W43977 enrichment") mapped the baseline and
warned that inventorying an intermediate API would create stale entries by
construction: W43974 was removing the free `name` operand and W43975 would add
the composition and adopted-state surface. Both have landed, so this rescans
the final source, as that research requires.

The scanner saw SIXTEEN caller crossings over `custody.py` before this round
added a public owner for the root kind; it sees SEVENTEEN over the patched
source, because `check_custody_root` is itself an entry. Of the sixteen, seven
were already owned — three by a layer validator at the entry itself, three by
`ControlStore.open` as a constructed capability, and the verb by
`check_custody_operation`. Nine were not.

## Pinned: two of the nine were an ownership GAP, not a registration gap

The research's own instruction is the rule here: *use delegated/constructed
ownership where the rule genuinely lives; do not copy validators into
`custody.py` merely to satisfy the table.* Applied honestly, it cuts both
ways — where no rule lives anywhere, the answer is not a table entry either.

- **`adopted_directory_custody` held neither its attempt nor its root kind.**
  It derives an operation identity from both, so an unheld identity looked one
  up for a name this manager never allocated. A read, but a read of somebody
  else's act. Both are held now, exactly as the composing sibling holds them.
- **The root kind had no owner anywhere.** It existed as the same inline `if`
  in three places — which is three places to edit and, in the inventory's own
  terms, a rule owned nowhere. `check_custody_root` is now its one named
  owner, in the shape `check_custody_operation` has had for the verb since
  W36540, and the three copies call it.

## Pinned: the remaining EIGHT are delegations, each to a real site

Seven crossings were unowned after the two gaps above were closed by holding
them; the eighth is `normalize_directory`'s root kind, which the extraction
turned from an inline copy into a delegation to the new owner. The registry
therefore contains eight custody delegations, not seven.


`custody_act` is a COMPOSER. It hands every operand to the private composer
that owns it and then to the engine port, and owning them again at that entry
would be a second spelling of five rules. `_custody_vector` performs the
durable lookup and the argv composition in ONE act — eleven review rounds went
into removing the interval between them — so it is also where the engine, the
image identity, the verb, the attempt and the root kind are held.

## 2026-08-30 — engine-answer member discovery is fixed; ownership remains local

**Confirmed.** Fixed-point origin propagation now carries the injected engine
answer through `EnginePort.__call__`'s branch join, and literal stream reads
make all four source-derived crossings visible: `run`, `run.status`,
`run.stdout`, and `run.stderr`. A reviewer-added universe regression pins that
discovery without declaring the entries in a table.

**Observed P0.** The envelope has its existing layer owner and probe; the
status and two stream members have neither. `boundaries.injected` was correctly
rejected as their owner because it requires non-empty durable text, while the
status is an integer and quiet engine streams are ordinarily empty.

**Confirmed correction boundary.** No new boundary-layer kind is required.
This inventory's `STATED_OWNERS` already represents exact local rules outside
the layer, including exact booleans and positive integer seconds in OCI.
`_status` owns the exact non-bool integer rule; `_stream` owns exact encodable
text while permitting empty text. The three discovered entries must name those
local owners and carry independent semantic witnesses. The wider global green
gate still awaits the scope ruling requested at Baton seq 48312.

## 2026-08-30 — resolved: all engine-answer members have honest owners

The three member gaps above are resolved through the inventory's stated-owner
path: status at `_status`, stdout and stderr separately at `_stream`. Each has
an independent witness which admits the ordinary zero/empty value and refuses
a value wrong only for that member. The custody slice is signed off. The
global-green acceptance question is deliberately not relabelled resolved; it
remains with the approver under the directed request at Baton seq 48312.

## 2026-08-30 — approver ruling supersedes the global-green acceptance

The approver answered the directed request at Baton seq 48776 and selected
option (b): W43977 closes on its independently complete custody/declaration
slice with all 25 affected-site witnesses passing. The earlier requirement
that this Work make the entire shared inventory module green is explicitly
superseded and is no longer an open W43977 gate.

The debt is not discarded. Parked W48697 is bound to
`work/records/2026/08/finding-v12-global-boundary-inventory-debt` and owns the
remaining nine modules plus the observed 131 unowned entries and 57 missing
probes. Its acceptance requires module-level child Works before
implementation. W39666 continues to own `worker_entry` separately.

Fresh closure verification passes all 65 stated-rule witnesses and all 117
custody tests. The custody/declaration slice has no remaining implementation
or review finding.
