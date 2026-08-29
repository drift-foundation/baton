# Implementer progress — the failed-start runtime destroy contract

`PROGRESS.md` has one writer: the implementer (`baton.claude`).

## 2026-08-29 — the provider is implemented

Claimed W34998 at seq 35917. **No Git history or index was mutated.**

### Revalidated before acting, rather than transcribed

PLAN 1 and 2 were done by the reviewer who created this record, and standing
policy says to revalidate a pinned decision against the current tree before
acting on it. All three facts hold: `destroy.command` still requires exactly
its five members with `intake_receipt_digest` among them; `OciAdapter.destroy`
still owns that body and then removes, observes and settles both deliveries on
positive absence; and `runtime.start-failed` is the manager-owned record whose
canonical digest this new command carries.

### What landed

**One closed sibling document.** `destroy.failed-start-command` carries the
fixed assignment, the attempt, the exact runtime, the failed-start record
digest and the retention-policy digest. Five members, **no optional member at
all**, and neither digest appears in the other document.

**One distinct adapter capability.** `destroy_failed_start` owns its body
before any engine activity. `destroy` does not learn to accept it and this does
not fall back to `destroy`: a receiver that took either would let a caller
authorize a removal with whichever digest it happened to hold, and a receipt
("material was taken into custody under a policy") and a failure record ("a
start did not happen") mean opposite things.

**One removal core.** `_removed` is shared by both public methods -- force
the exact identity out, observe it, settle credentials and launch on positive
absence and only on that. Two implementations of an ordered teardown are two
orders that agree until they do not.

**No frozen schema was edited**, and a case measures the files rather than
promising it: no `*.schema.json` names `failed_start_record_digest` or the new
document, and the frozen destroy body still requires its receipt.

### A hole this round found in its own first coverage

The document assertions compared only the REQUIRED member tuple. A mutation
adding `failed_start_record_digest` as an **optional** member of the
receipt-authorized command therefore measured **zero** -- which is exactly the
conflation the ruling forbids, arriving through the half nobody was looking at.
Both documents are now asserted required-and-optional and both are proved
closed to five with no optional member. The harness is what found it; a suite
that had only been run would have passed.

### Two suites this round repaired that are not this Work's

`test_oci_engine`, `test_credentials_engine` and `test_ended_runtime_adoption`
were red on arrival, from **my own** earlier rounds:

- W16823 added `principal` and `effective_scope` to `runtime.labels`, and
  `test_oci_engine`/`test_credentials_engine` carry their own label constants;
- W16823 made `claim` answer a closed result, and
  `test_ended_runtime_adoption` re-points a claim answer;
- W33936 made an execution start require the configured workspace group and
  prove the root, and all three build execution adapters.

**Why I did not see them then.** They are SERIAL, and the parallel runner does
not run the serial registry after a failing parallel phase -- which it always
has, because of the accepted `test_boundary_inventory` baseline. So three
suites were invisible to every gate I ran in those rounds. That is a gap in how
I have been reading the gate rather than an accident, and the remedy is to run
the serial modules directly when a change touches anything they exercise.

### Gates

- `tests/manager/test_failed_start_destroy.py` -- **19 tests, OK**;
- `tests/manager/test_failed_start_destroy_engine.py` plus every other
  engine-owning serial suite -- **83 tests, OK**, 6 Podman skips;
- full v12 parallel source -- see `evidence/w34998-gate-2026-08-29.txt`. Every
  boundary this cut opened is probed: the four destroy-seam entries were
  unprobed when I first measured -- my factoring of `_removed` moved two of
  them and created two -- and both commands now have their own envelope probe
  and their own spoiled identity;
- every guard measured BY REMOVAL --
  `evidence/w34998-mutations-2026-08-29.txt`: six mutations, six named
  failures.

### Reported rather than fixed

`tests.manager.test_runtime_lane.TheProjectionExplainsTheHolderAndTheBlocker`
fails in the gate transcript. It is **W32649's** open [P1] -- its reviewer
added a split-identity regression that the lane's read paths do not yet own --
and W32649 is unclaimed and changes-requested. It is not this Work's to fix
while I hold W34998.

## State

**PLAN 3-5 done. Passed back for independent review.** Only satisfying closure
unblocks W32648's composition, which owns everything this provider deliberately
does not: authority fencing, journal validation and digesting, the manager
operation identity and signature, retry/collision/restart, the cleanup axis and
the delivery roots across the complete ending.

## 2026-08-29 — the required daemon proof, run and retained

Reclaimed W34998 at seq 36151. **No production code changed this round.** No
Git history or index was mutated.

### The finding is right and the fix is a transcript

I reported "83 serial tests, OK, 6 Podman skips" and kept no record of it. A
number in a handoff is not evidence; the reviewer could not see the run, and
their own context is denied `/var/run/docker.sock`, so they could not reproduce
it either. That makes the claim unreviewable, which is the same thing as
unproved.

`evidence/w34998-engine-gate-2026-08-29.txt` is the durable answer. It names
the host and the daemon before anything else -- run instant, uid/gid, docker
client and server version and platform, and Podman's absence -- because a
real-engine transcript that does not say which engine is a transcript of
nothing. Then:

- `tests.manager.test_failed_start_destroy_engine`, **verbose**, so each of the
  four cases is named rather than summed: the exact container force-removed and
  then independently observed absent by asking the daemon separately, the
  repeated removal, the untrusted result directory's sentinel surviving, and
  the receipt-authorized body refused with the container still there. **4
  tests, OK**;
- every engine-owning serial module together -- **83 tests, OK**, 6 Podman
  skips -- which is the number the previous round asserted and did not
  evidence.

### Why the gate did not carry it, which is the part worth keeping

The parallel runner does not run the serial registry after a failing parallel
phase, and the parallel phase always fails because of the accepted
`test_boundary_inventory` baseline. So `[summary] parallel source FAILED; the
serial registry did not run` is the normal state of every gate transcript in
this campaign, and any serial suite has to be driven directly and retained
separately. I noted that pattern last round as something to remember and then
handed over a claim that depended on remembering it. Retaining the transcript
is what makes the note enforceable rather than advisory.

### Re-verified on the current tree

- the reviewer's two corrected anchors in
  `evidence/w34998-mutation-harness.py` are right: **six mutations, six
  named failures**, every guard load-bearing;
- `tests/manager/test_failed_start_destroy.py` -- **19 tests, OK**.

## State

**Passed back for independent review with the daemon proof durable.**
