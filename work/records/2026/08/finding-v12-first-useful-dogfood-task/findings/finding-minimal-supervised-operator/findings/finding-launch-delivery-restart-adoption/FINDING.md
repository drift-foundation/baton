# Adopt launch delivery for restarted cleanup

W47225, child of W39358's `finding-minimal-supervised-operator`.

## Operational finding: this dossier did not exist at the implementation claim

The Work's binding resolved to
`work/records/2026/08/finding-v12-first-useful-dogfood-task/findings/finding-minimal-supervised-operator/findings/finding-launch-delivery-restart-adoption`
and nothing was there. Reported rather than worked around, per standing role
policy. The Work's contract was legible in full from its own thread (seq
47225), and this record is created at the implementation claim on the
precedent W43975 set when its decomposition minted a Work without one.

## The defect

W39358's fresh-process narrow handoff retry reconstructed its cleanup adapter
with `launch_delivery=None`, even though the ordinary attempt had materialized
a live launch root. After the retried pass, `authorize_cleanup` could remove
the runtime while `OciAdapter._launch_ended` reported `not-delivered` -- so the
launch root stayed on disk with nothing that would ever come back for it.

The launch component had `materialize` and `discard` and no way to hold a
delivery it had already made. A restarted process therefore had no honest
option: `materialize` refuses an existing root by design.

## The boundary

**Pinned: adoption, not reconstruction.** A deployment that built its own
`LaunchDelivery` from a path would be minting the typed capability the adapter
trusts out of bytes nobody proved -- exactly the caller-selected locator the
fixed target exists to take away. So the proving lives in the component that
owns the layout, and what crosses back is the same typed object `materialize`
returns.

**Pinned: fail closed on every disagreement.** The root, the document's name,
the file type, both modes this manager itself established, the byte ceiling
and the document's own closed contract are each proved.

**Pinned: absent is not a fault.** An attempt whose root does not exist adopts
`None`, because an attempt may have had no delivery -- and answering `None` is
what lets a caller tell that apart from a delivery it failed to prove. A root
that EXISTS and is not the one this manager wrote is a refusal rather than a
repair.

## 2026-08-30 — independent revalidation of the first adoption slice

**Observed:** the first implementation holds document member names and schema,
not member values or the exact values this attempt launched with. It also
accepts extra root entries that `discard` will later delete. Three additive
witnesses in `review-2026-08-30T15-05-35Z.md` make those gaps executable.

**Clarified:** absence remains ordinary for the generic launch component. It
is a contradiction for W39358's fresh-process handoff retry, because that path
exists only for an attempt whose runtime started after launch materialization;
the deployment must require a non-null adoption there.

## 2026-08-30 — independent outcome

Signed off in `review-2026-08-30T15-26-50Z.md`. Adoption is bound to exact
canonical authored bytes and a closed one-entry root through descriptor-
relative no-follow reads. W39358 applies the started-attempt absence refusal.
The generic seam is complete; its parent's real retry/removal gate remains
parent Work rather than an open child requirement.
