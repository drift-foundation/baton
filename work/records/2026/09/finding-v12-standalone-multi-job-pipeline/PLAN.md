# Plan

1. [done] Pin the standalone multi-job milestone, minimal vertical-slice
   acceptance, explicit non-goals, and scheduled-test authority clarification.
2. [done, reviewer map 2026-09-02] Map the existing v12 components and open Work to the
   acceptance bullets. Reuse what exists; identify only missing composition.
3. [done, corrected decomposition 2026-09-02; bootstrap correction approved
   2026-09-03] Use W62098 as the confirmed decision/evidence input, not as a
   monolithic implementation assignment, and create bounded non-overlapping
   children:
   - W71875: persistent manager process plus submit/status control loop;
   - W76207: one-worker production deployment bootstrap, blocked on W71875
     and required by W71917;
   - W71917: immutable read-only source and disk-backed writable workspace;
   - W71877: concurrent implementation/review pool scheduling from reusable
     runtime profiles, with one logical worker identity and one live assignment
     per instantiated session, blocked on W71875 and W71917;
   - W71918: immutable review checkpoints and same-line corrections that
     preserve candidate workspace and preferred logical-worker affinity while
     distinguishing new assignments and runtime incarnations, blocked on
     W71875 and W71917;
   - W71878: serialized approved-proposal integration, blocked on W71875,
     W71918, and W71459; and
   - W71879: two-Job end-to-end demonstration, blocked on W71875, W71877,
     W71878, W71917, and W71918.
   Each child has its own FINDING, PLAN, PROGRESS, bounded acceptance, and
   explicit test-change authority. The one-worker bootstrap is the final
   v11-coordinated exception. W71917 is the first ordinary self-hosted v12
   execution; later leaves stay gated until their exact predecessors close.
4. [in coordination; gated by W71459] Incorporate the scheduled-test authority ruling into
   the integrator policy after W71459's current file ownership ends, or through
   W71459 itself. Do not race its active edits.
5. [pending vertical slice] Run two independent Jobs concurrently from one
   immutable baseline, including one changes-requested loop and one planned
   test edit, then integrate approved results serially without ordinary
   transition commands.
6. [pending assessment] Record measured latency, CPU utilization, failure
   containment, operator interventions, retained artifacts, and remaining
   hardening Jobs. Call the design promising only if the full slice completes.

W32577 deadline cleanup and other exhaustive hardening remain recorded but do
not precede this happy-path proof unless a measured failure makes one necessary.
