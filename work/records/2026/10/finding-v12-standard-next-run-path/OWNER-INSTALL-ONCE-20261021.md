# Owner confirmation — install once

Recorded by baton.prompt on 2026-10-21 from Slawomir's explicit confirmation in the interactive conversation.

Privileged account, credential, ACL, storage and narrow admission provisioning is one-time installation, handled by installation tooling. Routine starts, failures and retries must not require operator-authored shell/Python procedures or repeated account creation, credential copying, ACL setup or sudoers editing. Routine preparation remains input-only and at most 60 seconds; actual agent thinking and coding may take substantially longer.

The launcher must create and validate required output directories and other launch prerequisites before consuming a run selection. Provide supported recovery that preserves evidence and isolation without repeating installation. Completing another manual provisioning procedure is not product acceptance.

This supersedes any interpretation of historical W339972/W343989 procedures as the normal repeated workflow. Preserve those procedures and their results as historical evidence. Already-authorized v3 managed verification may finish. This ruling does not authorize arming, another live invocation, clearing consumed receipts or weakening isolation.

Queued product work: reconcile DESIGN and the task with this requirement before dependent implementation; include install-once, preflight and recovery behavior in fast-start acceptance. Further manual reprovisioning requirements are product defects, not routine operator steps.
