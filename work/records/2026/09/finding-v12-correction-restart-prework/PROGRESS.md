# Progress

## Claim 173925 — baton.claude, advisory read-only pre-work

Claimed W173921 standalone at seq 173925. Read this dossier's FINDING.md and
PLAN.md, W161234's canonical state (`phase: block`, seq 161487), the related
record `work/records/2026/09/finding-v12-correction-restart-proof/` including
`ADOPTION-AND-PROOF-161434.md`, `RELEASE-CHECKLIST-167877.md`, the M167954
decision entries in `finding-v12-isolated-agent-workers/FINDING.md`, `AGENTS.md`,
and the specific source symbols cited in the report. Claimed no original Work.

**Revalidation is the substance of this pass.** Eight of the packet's ten pinned
hashes still hold; `oci.py` and `stage_execution.py` drifted. The `oci.py` drift
is `+7` lines adding `OciAdapter.destroy_deadline` and leaves the packet's
two-generic-root claim intact; the `stage_execution.py` drift is large and is
flagged as the one thing to re-derive. All seven proposed slice A/B/C paths are
absent, so W161234 is entirely unstarted and nothing in the plan was overtaken.

Two superseded-wording findings, proposed to their owners rather than edited:
the packet's A/B/C cumulative cap table against the 2026-09-14 owner ruling in
`AGENTS.md` line 95, and `RELEASE-CHECKLIST-167877.md`'s conditional W63255 row
against M167954's 2026-09-14T11:40:26Z decision, which supersedes it by name.

The scheduling conclusion is the part most worth acting on: W161230 is still
`phase: block` with children in flight, so the packet's "revalidate its final
interfaces" precondition cannot be met. Slice A is the only one whose paths do
not overlap that moving surface.

Deliverable: `PREWORK.md`,
`sha256:639a22651132cddde285ace635a7c6e317eb860605d9145ad7a4efedf77a2e54`.

**Boundaries honoured.** No test, probe, provider, model, engine, image build,
Git mutation or additional worker. No product, test or original dossier file
edited; writes confined to this dossier. Verification spending this claim:
**zero measured seconds** — nothing was executed.
