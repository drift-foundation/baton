# W92 cutover runbook — manual steps after review sign-off

Everything below is HELD for Slawomir; the implementation returned for review
prepares it but performs none of it against production. The retired trial
(`/home/sl/baton-v11/`, schema 14, executable 948e92f) stays live and
untouched until step 5.

1. **Commit** the reviewed W92 tree (records/open layout, AGENTS.md policy,
   schema 15, projection 4.1, this dossier). The implementer drafts the
   message; Slawomir commits.

2. **Deploy the immutable schema-15 executable** from that commit, using
   the operator-facing recipe (run from the repository root) with one NEW
   exact immutable release directory derived from the commit:

       just deploy-v11 /home/sl/opt/baton/v11/<short-commit>

   Every `<deployed>` below means exactly that directory —
   `/home/sl/opt/baton/v11/<short-commit>` — holding bin/doc/conf/tmpl as
   the deployer ships them. `tools/deploy_work.py` stays internal.

3. **Initialize the fresh authority** — a NEW home, never the trial's:

       mkdir -p /home/sl/baton-v11-2
       <deployed>/bin/baton init directory=/home/sl/baton-v11-2
       # edit baton.json: teams/roles/routes/kinds, and a `roots`
       # section declaring the `baton` repository root WITH its explicit
       # absolute base, e.g. "baton": {"display": "Baton repository",
       # "base": "/home/sl/src/baton"} — baton.json is the single root
       # config (W4); no roots.json exists
       <deployed>/bin/baton activate directory=/home/sl/baton-v11-2

   No file from the schema-14 trial database is copied or migrated.

4. **Recreate the surviving Work** (5 items, INVENTORY.md §F: 4 open
   plus the parked TUI Work-search; W2, W4, W6, W9, W12, W13, W14,
   W19 and W84 were fixed pre-cutover and are not recreated):

       BW=<deployed>/bin/baton \
       CONFIG=/home/sl/baton-v11-2/baton.json \
       ROOT=baton sh work/records/2026/08/finding-recursive-target-graph/findings/finding-fresh-record-layout-cutover/scripts/recreate-work.sh

   (the canonical repository-relative path — the runbook runs from the
   repository root throughout; no hidden working directory)

   Effectively-once op-ids make a crashed run safe to rerun. Each item binds
   to the canonical umbrella record
   `work/records/2026/08/finding-recursive-target-graph`.

5. **Parallel trial, then retirement.** Exercise JSON, CLI and TUI against
   the fresh authority with reliable v10 wakeups. Only after Slawomir accepts
   it: retire the schema-14 trial authority. Its immutable messages keep
   their old `work/finding-*` path references as written history — nothing
   is rewritten.

Verified in preparation (2026-08-16, re-run after the W2, W4, W6, W9, W12, W13, W14, W19 and
W84 removals): the deployer suite passes on the schema-15 tree; the
recreation script ran end-to-end on a scratch schema-15 authority —
5 rows (4 open + 1 parked), concrete classifications, canonical
umbrella bindings — and replayed idempotently on rerun.
