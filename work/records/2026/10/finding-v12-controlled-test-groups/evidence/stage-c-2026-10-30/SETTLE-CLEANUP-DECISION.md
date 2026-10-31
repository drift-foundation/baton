# Decision packet: `workspaces.settle_cleanup`'s unread `connection` (B2 Case H)

Prepared by K (copilot under owner claim E384905) for Slawomir, as review
2026-10-31T03:05:05Z asked: evidence, recommended semantics, alternative, exact
text and compatibility, tests. This packet prepares a decision; it changes no
atomicity and no specification. Nothing below is implemented.

## The fact and the evidence

`settle_cleanup(control, connection, assignment_id, admitted, what)`
(`workspaces.py`) never reads `connection`. Its docstring states the contract:
"Close the admission IN THE ENDING'S OWN TRANSACTION, atomically with it ...
`connection` is the caller's open one, so this writes through `_record` rather
than `transact` -- pure database work under a lock the caller already holds".

Transaction and caller evidence (read from the current tree):

- `ControlStore.transact` (`store.py`): `connection = self._connection;
  connection.execute("BEGIN IMMEDIATE")` ... `SAVEPOINT act` ...
  `result = action(connection)` ... `COMMIT`. The callback receives the store's
  ONE connection object.
- `ControlStore._record` writes `INSERT INTO operations ...` through
  `self._connection` -- the same object -- so a `_record` call made inside an
  `action` callback is inside the caller's open transaction by construction.
- The only caller: `intake._settle(store, connection, attempt_id, ...)` at
  `intake.py:5558`, reached from `intake.py:1435` as
  `lambda connection: _settle(store, connection, attempt_id, receipt, ...)`
  inside `store.transact(...)`. `_preserved_ending` and
  `_settle_recordless_cleanup` take the same `connection` and the pattern is the
  same there.
- Inventory: the operand is a stated row ("an unread operand reaches no effect";
  STAGE_C_STATED) and the function's two other operands are owned
  (`assignment_id` identity, `what` label).

So the contract HOLDS today, but by the store's structure (one connection), not
by anything `settle_cleanup` checks: a caller that invoked it outside a
transaction, or against another store's connection, would still write -- through
`control._connection`, autocommitted -- and the docstring's atomicity would be
false without anything refusing.

## Recommended semantics (option 1): prove the contract at the door

Keep the parameter and make it a proof: refuse unless `connection is
control._connection and connection.in_transaction`. The first clause binds the
act to the store the record is written to; the second
(`sqlite3.Connection.in_transaction`) proves the caller is inside an open
transaction -- which, with `BEGIN IMMEDIATE`, is the write lock the docstring
claims. The write stays through `control._record` (keeps the durable-secret
walk; no duplicated INSERT). Refusal vocabulary: `ContractRefusal("integrity",
"schema", f"{what}'s cleanup settlement must run inside the ending's own
transaction on this store's connection; ...")`.

- Exact text affected: `settle_cleanup`'s docstring gains one sentence ("the
  connection is checked to be this store's open transaction"); no DESIGN.md
  change (W270664 F2 already states the atomicity; this enforces it). The
  inventory row for `connection` moves from stated to layer-owned by a new rule
  in `settle_cleanup` (probe: a foreign `sqlite3.connect(":memory:")` connection
  refuses; the store's connection outside a transaction refuses).
- Compatibility: the one caller already satisfies both clauses; no record shape
  changes; no replay change.
- Decisive tests: (a) `_settle` path unchanged (existing intake ending tests);
  (b) direct call with a foreign connection refuses before any write; (c) direct
  call with the store's connection outside `transact` refuses; (d) inside
  `store.transact` succeeds and the settlement record is committed with the
  ending.

## Alternative (option 2): remove the parameter

Drop `connection` from `settle_cleanup`, `_preserved_ending` and
`_settle_recordless_cleanup`'s signatures and let the docstring say "called
only from an ending's `transact` callback". Smaller, but the contract then
rests on call-site discipline alone and the inventory loses the row rather
than owning it. Not recommended: the whole point of B2 Case H was that an
unread operand hid a claim nobody checks.

## Rejected: write through the parameter

`connection.execute("INSERT ...")` directly would bypass `_record`'s
`check_no_durable_secret` walk and duplicate the journal's INSERT in a second
place. No.

## What this packet does not do

It does not change atomicity, the ending's transaction shape, record kinds or
replay. It needs the owner's selection between option 1 and option 2; K
implements the selected one as a bounded correction with the tests above.
