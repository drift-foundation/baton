# Progress

`PROGRESS.md` has one writer: the implementer (`baton.claude`).

## 2026-08-28 — PLAN 1 done; blocked on the pending ruling

Claimed W32577 at seq 32804. **No production code was edited**, which the
bound record and thread both require. No Git history or index was mutated.

### The gate is explicit and I checked it rather than assumed it

`FINDING.md` carries an **Open decision**: an approver must confirm the
runtime deadline's authority meaning before implementation, because "the
missing product meaning must be ruled before tests or implementation guess
it". Thread message 32587 says it again in operational terms: *"do not edit
production until that ruling is pinned here. The impl Route owns any ledger
block needed when it claims."*

Approver obligation **M32585** is pending on parent W32382. It has not been
answered.

### PLAN 1: the non-equivalence, evidenced

The one thing worth having before the ruling is the evidence the ruling turns
on, and it is measured on the tree rather than transcribed:

- `interrogation.py` states the meaning in its own words — "A TIMEOUT IS AN
  OBSERVATION, NOT A CANCELLATION and not authority to discard work. It says
  this manager stopped waiting; it says nothing about whether the turn is
  still running or whether an answer is still coming."
- and it is **deliberately non-terminal**: "`timed-out` is NOT terminal on
  either axis: a model that answers afterwards is answering, and the axis has
  to be able to record that. An axis that made it terminal would turn the
  manager's patience into a decision about somebody else's turn."
- `schema.py:611` says the same about ownership — "`deadline_at` is the
  MANAGER's, not the adapter's. Timeout is an observation".

So the finding's claim holds exactly: reusing this field or its prose to
destroy an execution runtime would REVERSE a meaning the tree states three
times. There is no second candidate — `deadline_at` appears nowhere else in
`worker_manager`.

The other horn is equally closed: treating expiry as worker `cancelled` would
write a worker disposition the worker never produced, which is the defect
W32382's review already refused once in my own test.

### What was deliberately NOT done

**No production edit, no test, no pinned shape.** PLAN 2 is "obtain and record
the authority meaning", and every later item depends on it. Writing a seam now
would be choosing the ruling by implementing it — which is precisely what the
Open decision exists to prevent, and what the parent's review called out when
a test invented a disposition.

## State

**Blocked on approver obligation M32585, unclaimed.** Implementation-ready the
moment the meaning is pinned: PLAN 1's evidence is here, and PLAN 3's seam is
small once the ending is chosen — `request_cancellation` already owns
authority-before-destruction, exactly as it did for W32576's handshake refusal.
