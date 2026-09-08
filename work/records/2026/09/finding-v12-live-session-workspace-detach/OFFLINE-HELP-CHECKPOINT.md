# Help visibility and actual initialization — W106673

Candidate under claim 107495, responding to M107492. The latest retained probe
passed exact version and help-command execution, then refused at the all-flags-
visible check. It did not attempt streaming initialization.

The missing installed flag names are **not recoverable from the retained
artifacts**: neither the help output nor its per-flag map was saved on failure.
The input audit records the readable result/registration and reviewed staged
script hash. No fresh runtime observation or guessed missing-name diagnosis is
claimed. Missing max-turns/max-budget-usd in the new tests is synthetic input.

## Proposed correction and acceptance boundary

evidence/real_session_preflight_help.py is a separate candidate preserving both
earlier probes and their manifests. It stores every fixed FLAGS name with a
boolean help-substring observation and derives missing_help_flags in fixed order.
These fields now cross both success and validated failure boundaries. Null means
help was not observed; an empty missing list means all listed names were seen.
Unknown names, non-boolean values or inconsistent missing-name lists refuse.

This proposes one explicit acceptance change: the all-help-visible requirement
no longer gates the idle initializer. Successful help output is a useful
inventory, not evidence that an omitted option is rejected by the parser. After
recording that inventory, the candidate must pass the exact same initialize argv,
control correlation, idle process continuity and container checks. Failed
initialization remains failure even if every flag appears in help. An idle pass
does not claim live behavior of the flags whose names are visible.

The unchanged initialize argv includes --print, --input-format, --output-format,
--verbose, --tools, --setting-sources, --strict-mcp-config and --mcp-config.
A successful correlated answer demonstrates that this exact invocation reached
initialization; it does not independently prove every option's behavioral effect.

The result explicitly retains unexercised_flags:

- --resume
- --session-id
- --max-turns
- --max-budget-usd
- --model
- --dangerously-skip-permissions

These flags were in the old help requirement but never in its initialize argv.
Their actual behavior remains a gate for the subsequent live package. Resume,
session continuity, model identity, tool policy and limits are not accepted by
their help visibility or this idle probe. The USD3 cap remains unverified.
No model/user frame, credential, workspace, image acquisition or namespace
operation is added, and the existing runtime posture is unchanged.

This acceptance change is a proposal for independent review and owner
disposition, not an executed workaround or permission to drop live requirements.

## Exact proposed next operator invocation

After independent review and separate owner execution disposition:

    /usr/bin/python3 /home/sl/src/baton/work/records/2026/09/finding-v12-live-session-workspace-detach/evidence/real_session_preflight_help.py --operator

Only the source basename differs from the previous operator invocation. The image,
container create/stop calls, clean environment, flags and actual initialize argv
are unchanged. Local Docker authority remains required; managed agents received
no new execution authority. The printed temporary root, registration, result and
container identity must be retained. A new result will identify exact missing
help names even if later initialization fails. No blind rerun was performed.

## Verification and evidence

Six new mocked tests and all four unchanged original local tests pass. Tests
cover failure-field retention through Docker exit1, unobserved versus absent
help, exact field validation, successful initialization despite synthetic help
omissions, and continued refusal when initialization actually fails.

AST comparison verifies unchanged original tests/assertions, initializer
correlation, container checks, command capture, Docker wrapper, constants,
actual initialize argv and Docker create/stop calls. Both prior manifests still
match every bound artifact. The changed all-help-visible gate is explicitly
listed as the proposed acceptance delta rather than hidden in preservation claims.

evidence/real-session-help-manifest.json binds this document, new probe/tests,
incremental patch, retained input audit and validation records. Review returns
to baton.ops before another operator run. The full real-session experiment
remains open, and M107362's approved existing credential delivery remains resolved.
