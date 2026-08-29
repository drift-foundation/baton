# Progress

`PROGRESS.md` has one writer: the implementer (`baton.claude`).

## 2026-08-28 — claimed, verified absent, and PARKED

Claimed W32391 at seq 32726. No repository state was mutated.

### The dossier asks the Route handler to park it, and I am the Route handler

`FINDING.md` is explicit: Podman is absent, this Work must remain parked until
a real compatible engine is available, and "a simulation or Docker alias
cannot satisfy it". `PLAN.md` item 1 is `[pending Route handler]` because the
reviewer who created the Work cannot set the implementer Route's phase.

That is the same shape as W16821: the correct action is not to implement, and
not to hand the Work back with a note, but to put the state ON THE LEDGER
where a later wake cannot walk past it.

### Absence verified rather than assumed

Checked before acting, because "the dossier says so" is not a current fact:

- `podman` and `podman-remote` are not on `PATH`;
- no binary at `/usr/bin/podman` or `/usr/local/bin/podman`;
- no socket at `/run/podman/podman.sock` or the per-user path;
- `systemctl --user is-active podman.socket` answers `inactive`;
- the package is available (`Candidate: 5.4.2+ds1-2`) and **not installed**.

So this is an environment fact, not a coverage decision, and installing a
daemon is an operator act rather than an implementer one.

### What was NOT done, deliberately

**No Docker substitution, and no `PodmanComposition` unskip.** The three
lifecycle modules already carry a Podman class that skips narrowly on
availability; that skip is the honest record of this exact state and making it
pass by pointing it at Docker would be the one thing the finding forbids by
name.

**No revalidation of the shared adapter contract.** PLAN item 2 asks for it,
and it is worth having against the engine that will actually run it — which
does not exist here yet.

## State

**Parked on the absence of a Podman engine, with the reason on the ledger.**
The acceptance and the confirmed boundary are the reviewer's and are
untouched. Ready to implement the moment a real Podman is present: the
lifecycle, negative/race and ended-adoption modules each already have a
Podman class, so certification is running them rather than writing them.
