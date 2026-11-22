# Joined integration result

Native candidate7d686bf0 on retainedf13e0b12/original72e1093d combined with
accepted main heavy-profile checkpoint5d5e79a4. Native verdict accepted;
one test-only composition correction35de2ca2 independently accepted by K in
review-2026-11-22T17-27-08Z.md (M385670). Exact imports and modes recorded.
The three heavy-profile files remain unchanged.

First combined run388 cases:387 pass,1 stale exhaustive-profile assertion.
After exact accepted test delta import:388/388 pass,0 failures/errors/skips,
23.277 seconds, prepared interpreter via just test-one. Modules:
test_retained_failure_analysis, test_job_control, test_sweep, test_delegation,
test_documents, tools.test_parallel_runner. Disk roots were
/var/tmp/baton-w385623-integration. Logs retain both outcomes. No broader
coverage or container execution claimed. git diff --check passed.

New product/test files use0644; pre-existing modes preserved. Original import
stopped on umask0664 for a new file and resumed after complete byte revalidation;
see import.json. Native PLAN/PROGRESS are preserved under retained-records,
without replacing host coordination history. No Git index/history mutation.

Ready for owner checkpoint of the ten product/test paths plus this dossier.
Packaged qualification follows that checkpoint. Native coverage limitations
recorded in FINDING remain; Stage1-B/C are not delivered by this result.
