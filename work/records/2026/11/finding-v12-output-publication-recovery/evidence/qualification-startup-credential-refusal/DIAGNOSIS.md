# Installed qualification startup refusal

The owner-run producer-failure phase refused at startup on 2026-11-24T06:33:29Z. No qualification producer execution is proved. The supported status reports manager and publisher absent, with no published snapshot.

Confirmed source cause: tools/stage_execution.py operations_from invokes single_worker.worker_preflight for every worker. tools/single_worker.py worker_preflight unconditionally requires credential_sources when no injected credential_provider is supplied. The publication worker correctly has credential_slots=[], credential_profile={}, credential_sources=None. The two provider workers have the qualification-only registry configured. This is a product composition defect, not a missing operator credential selection.

Required correction: allow the credential-free publication worker through shared preflight without supplying or delivering credentials, preserving refusal for provider workers that require a registry. Add a focused composition regression using the production/default resolver path, not an injected credential provider. Rebuild and update the qualification runtime through supported installation before repeating startup. Existing source acceptance does not cover this new correction. Do not alter stored deployment fields or attach credentials to the publication role as a workaround.

Images, prepared Jobs, failed-start logs and retained evidence remain intact. No source edit, store mutation, rebuild or restart was performed during this diagnosis.
