# Partial accounting implementation — owner150498, tuner150501

This package is NOT executable proof preparation and is NOT ready for acceptance.
There is no execution-review.json or selected-images.json. Run9 identity, task,
policy and recipe copies are historical baseline fixtures, not fresh inputs or
permission to use run9 again. Do not run deployment.py, operator-prepare.sh,
build_images.py or run.py against a live root.

New accounting.py implements the interval/clock core and a partial bound reader.
run.py integrates clocks, evidence and whole-run final-check guards. Missing public
read-only worker-manager capability acquisition prevents the live judge reader;
it explicitly refuses instead of borrowing or fabricating a WorkspaceGroup.
See ../ACCOUNTING-150501.md for exact missing contracts and remaining work.

Offline verification from the repository root:

    python3 work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/prepared-150501/verify_offline.py

It retains synthetic /tmp fixtures. 82 cases passed: prior63 plus19 new accounting
cases. Copied evidence/ files predate this change and describe prior packages;
current results and costs are only in ../evidence/accounting-150501/.
No image rebuild, product change, model execution or historical state repair.
