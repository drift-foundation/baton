# Plan

**Status:** queued behind W2; no deletion is authorized yet.

1. Inventory every live v10 process, readiness source, configuration reference, executable/alias, deployed release, mailbox/data path, repository implementation, test, and active instruction.
2. Separate executable fallback material from durable historical evidence, and present the exact cleanup targets for Slawomir's approval.
3. Re-prove v11-only human, Codex, and ACP operation, including restart and recovery, immediately before cutover.
4. Stop all v10 consumers, verify none remains, then perform only the approved bounded cleanup.
5. Verify no active command, alias, configuration, documentation, or monitor can select v10; restart all v11 participants and run the final coordination trial.
6. Record what was removed, what historical material remains, and the evidence that fallback is impossible.

## Child tracks

- Runtime/source removal — `work/records/2026/08/finding-v10-runtime-removal/`
- Deployment/configuration/data retirement — `work/records/2026/08/finding-v10-deployment-data-retirement/`
- README/documentation/architecture picture — `work/records/2026/08/finding-v11-public-documentation-cutover/`
- v11 operating guide — `work/records/2026/08/finding-effective-baton-v11/`

All four remain blocked on W2 and require their own implementation and review disposition. W99 closes only after every child closes.
