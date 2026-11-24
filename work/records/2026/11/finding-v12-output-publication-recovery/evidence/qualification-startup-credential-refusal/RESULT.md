# Startup credential-preflight correction

Owner selected direct correction in this context. Two files changed: single_worker.py now skips provider construction only for the validated publication role; test_publication_recovery_execution.py exercises pooled production/default credential construction and retains the missing-provider-registry refusal.

Before: two new tests ran, one reproduced the exact installed refusal and the negative case passed. After: both pass. The fixture also contains an integration worker, so the positive assertion accounts for three credential providers, not the two provider roles in the live qualification instance.

Focused complete modules: 454/454 passed, zero failures/errors/skips, 151.341s. Prepared interpreter, disk-backed fixtures, fake engine only. No live calls, containers, build or protected Git mutations. Source hashes remained unchanged through verification. Retained log, ledger, source identity and patch are adjacent.

Existing worker images remain applicable: no worker/image bytes changed. Host packaging is next: python3 /tmp/baton-w385695-rebuild.py. That script verifies the corrected 50-path source identity and runs one build plus the packaging gate. No source acceptance by an independent context is claimed for this coordinator correction.

Correction to prior operator advice: supported bootstrap cannot upgrade runtime in place; one-operand bootstrap changes configuration only. Preserve qualify-w385695-560eaa89-1 and use a new qualification destination for the corrected runtime. The existing images are reusable; the two scripted qualification producers will be created in that fresh instance. No expensive model work is lost or repeated.
