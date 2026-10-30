# Managed controller policy preparation — claim339937

Scope: owner reroute339935 selects repair preparation and read-only boundary
validation, not a second authoring invocation. Reviewer owns this document and
`evidence/policy-339937/`; no installed policy, socket permissions, controller,
packet, implementation progress or sibling Work was changed.

## Confirmed installation and failure

Rendered dispatcher `/home/sl/baton-v11.14aecfb/codx-pc/run/context/dispatcher.json`
nominates `/home/sl/.codex-pushcoin/rules/baton-codx-pc.rules` for baton.codxpc.
Its infra.json launches Codex with CODEX_HOME=/home/sl/.codex-pushcoin and
ws://127.0.0.1:4502. Installed nominated policy SHA256:
`0e41ce0d35d5fb26984e6bce37bd8f9952cafb91d5fd90182b090817c73e9f81`.
It contains exact Baton operation prefixes and four direct Docker inspection
prefixes. It contains no enclosing Python controller rule. `static-checks.json`
records local installed `codex execpolicy check` results: direct image inspect
matches allow; exact selected env/Python controller has no match. This checks
the nominated file, not every active layer or effective runtime policy.

Existing actual codxpc subprocess evidence is execution-339894/RESULT.json:
Docker socket permission denied before manager creation. This explains why a
direct Docker check passed while the controller refused. Successful corrected
managed-boundary validation is still outstanding; rvpc must not impersonate
codxpc or create a hidden consumer. `/home/sl/.config/systemd/user` is absent;
the installed infra manifest, rather than an assumed systemd unit, supplies the
known lifecycle procedure. Process enumeration inside the sandbox did not prove
host process state.

## Minimal inspection-only operator change

The proposed separate rules file contains one full env/Python/-c prefix for a
read-only call through the staged held_packet, imported-source and controller
checks, then the actual baseline._engine_inspect / verify_worker_image path.
It neither opens the authority nor creates a manager/Job. SHA256:
`a6b0e95e3dedebcb316d8cc31f21430020c38d36b1d747a1e020ee42f9dbf34d`.
Static positive check allows it; changed code, changed packet and authoring
launch have no match. The inline code ignores extra argv. Do not generalize this
to a bare Python/env/bash rule. The rule still trusts the already reviewed
staged imported files: preserve/recheck their bytes; a pathname rule alone is
not immutable-code confinement.

Operator commands, from /home/sl/src/baton, after confirming codxpc has no active
claim/turn and selecting this deployment change:

```sh
cp --no-clobber work/records/2026/10/finding-v12-standard-next-run-path/evidence/policy-339937/inspection-only.rules /home/sl/.codex-pushcoin/rules/w339626-inspection-only.rules
cmp work/records/2026/10/finding-v12-standard-next-run-path/evidence/policy-339937/inspection-only.rules /home/sl/.codex-pushcoin/rules/w339626-inspection-only.rules
python3 tools/infra.py stop /home/sl/baton-v11.14aecfb/codx-pc
python3 tools/infra.py start /home/sl/baton-v11.14aecfb/codx-pc
python3 tools/infra.py status /home/sl/baton-v11.14aecfb/codx-pc
```

Stop if cmp differs; do not overwrite an unrelated existing rule. These commands
are proposed, NOT executed. The current manifest is version1, so drain and
stop-drained are unavailable. Plain stop is immediate and is safe only after
quiescence. Start mints a fresh mapped codxpc context and preserves the previous
locator as history; it must replace the old supervised stack, never run beside
it. No restart of rvpc or Claude is required. Keep W339626 blocked while this
happens so readiness cannot select a product start.

The official [Codex rules documentation](https://learn.chatgpt.com/docs/agent-configuration/rules)
describes startup loading of rules and prefix matching; reload requires restart.
The checker proves matching, not that the managed server loaded the rule.

Have the mapped codxpc context, under the operational prerequisite claim, issue
this exact standalone inspection command in the cwd recorded in commands.json:

```sh
env BATON_V12_STAGE_EXECUTION_CONFIG=/tmp/baton-standard-next-run-w339626-339782/packet/deployment.json PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/baton-standard-next-run-w339626-339782/code/v12/python/src:/tmp/baton-standard-next-run-w339626-339782/code/v12/python:/tmp/baton-standard-next-run-w339626-339782/supervisor /usr/bin/python3 -B -c 'import baseline; from tools.authoring_enforcement import verify_controller; p=baseline.held_packet('"'"'/tmp/baton-standard-next-run-w339626-339782/packet/PACKET.json'"'"'); baseline.verify_imported_sources(p); verify_controller(p); d=baseline.verify_worker_image(p,image_inspect=baseline._engine_inspect); print(d['"'"'Id'"'"'])'
```

Expected: exit0, image digest
`sha256:c862c055c6430addc918ca078a9e4d55f6bd8173ed9c9878a8ad9d6cad334ca2`,
no approval request and no Job/control database, authoring log or outcome. Capture
the actual tool result, context identity, command, return code and elapsed time.
Any refusal is an operational finding; do not retry with escalation. The probe
uses the same staged verifier and Python subprocess engine path, but does NOT
prove the launch command is authorized. Keep those two acceptance claims distinct.

## Launch authority remains a separate explicit decision

Do not install a launch rule merely to make this check pass. The selected full
controller prefix would authorize execution outside the sandbox, including its
children. Prefix rules also allow trailing arguments; authoring_enforcement.py
accepts --child-of/--lock-fd/--status-path, so a full visible command prefix does
not enforce exact arity or the parent-controller entry path. A broad Python
allow or granting Docker socket access to the whole sandbox is not a minimal
repair. The inspection-only rule intentionally leaves launch unmatched.

After inspection acceptance, owner must select either execution of the unchanged
reviewed ENFORCED-COMMANDS start in an authorized operator context, or an explicitly
accepted trusted managed entry boundary that pins command arguments and source
bytes. No new wrapper/product implementation is selected here. Operator execution
would be the existing isolated v12 controller, not direct host implementation.
Any second invocation still needs explicit selection under the original limits;
this report grants none. Do not call this operational prerequisite complete on
static checks alone or unblock product execution while launch authority remains
unresolved. Preserve the spent first attempt, lock inode and accepted packet.

## Delivery split

Separate operator installation/boundary validation from preparer product work:
the former owns installed rule/lifecycle changes, the latter retains isolated
v12 implementation and rapid-start acceptance. W339626 consumes joined acceptance.
Use an ops child and a real blocked-by edge; no other Work allocation changes.
This is an operational prerequisite within selected scope, not a new product or
specification decision. Reviewer evidence here stays append-only; an operational
executor appends its own receipt, never edits these static results.
