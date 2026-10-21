# Corrected runtime for independent review

W348979 claim348981, baton.codxpc, 2026-10-21. Current FINDING and PLAN revalidated against the supplied archive and d3a7a41cc7347e4741706673c20f62b4a3190f65. The omitted dependency is confirmed at controller lines494,506,554. The successor changes packaging only: 114 old members preserved byte for byte plus tools/authoring_baseline.py, SHA256 8e5987f56f8d5329c33a8e73f9df56f13213e134f2dade8180afabf80723efe9. Added bytes match both committed host base and independently tested source. The controller and fixed execution-envelope policy remain unchanged.

HOST-POLICY.json SHA256 8309fd6ec90231c6e2d92468520bdeb075f20c4ee5f7ae7e8d34c637c10022a6. Its archive/member/provenance maps describe the 115-member successor; earlier acceptance is provenance, not acceptance of this new artifact. SHA256SUMS seals the complete preparation. prepare.py is a preparation recipe, not a launch command; do not rerun it over immutable evidence. verify.py is a read-only static check.

## Dependency evidence and its limits

STATIC-CLOSURE.json walks every supplied Python AST, including function bodies, recursively adding locally imported modules and package initializers from the exact host base. From-import symbols that are not module names remain symbols, not imaginary files. All 1261 local import edges have supplied members. verify.py reopens the actual archive, checks every byte and edge, and proves the old member set fails the specific deferred main import. Original non-Python resources remain present and unchanged.

Manual dynamic-call assessment:

- launch.py:915 imports literal uuid and provider_context.py:910 imports literal math: standard library dependencies.
- authoring_baseline.py:568 imports packet manager_source.packages. The selected baseline_bindings.py:542 supplies exactly baton_v12 and tools; both package initializers are present. A consumer must preserve that package set or audit its replacement. Arbitrary future packet module names are not certified.
- job_manager.py:910 and979 import user-selected observation/operations factories for its own CLI. The selected authoring_enforcement entrypoint uses its child_compose with stage_execution.operations_from; it does not invoke those CLI factory selectors. New selectors require a new dependency audit.
- dogfood_operator's direct-script user_credentials fallback maps to the supplied tools/user_credentials.py; selected package execution takes the relative import.

External environment prerequisites remain Python >=3.13 and jsonschema==4.26.0, as declared by the exact host-base pyproject.toml. The archive does not vendor these or jsonschema's transitive distribution dependencies. stack_command's diagnostic rpds import refers to that installed dependency chain and is guarded; it is not a missing Baton module. No installed environment readiness or native-library loading is claimed by this static audit. No product import, --help, engine/provider operation, or dynamic startup was run. If dynamic startup evidence is required, select a supported isolated v12 probe or obtain an explicit bounded host-product exception before execution; the old exception is expired. Static preparation does not authorize a retry.

## Consumer delta

After independent acceptance, W341357 prepares a NEW immutable packet using this HOST-POLICY/archive and its full manager_files map (115 members). Preserve the accepted controller/helper identities, historical supervisor seals, worker candidate base, and package set. Regenerate packet-specific pins and checks coherently; do not patch sealed execution-348852 or reuse its consumed invocation/root. W341357 owns subsequent packet review and exact run selection. This artifact grants no launch authority and does not accept the R1/R2 producer candidate.

## Verification accounting

Successful preparation/static scan: 0.8050750069960486 seconds. Archive verifier: 6.064954055997077 seconds. Three preceding fail-closed preparation attempts identified external imports before artifact creation; exact internal elapsed totals were not measured and remain unknown (tool-reported wall times 0.000008966, 0.273191814, 0.324282518 seconds). Product execution: zero. Supplier cumulative author cost 135.817654632 seconds and independent review 4.704084767 seconds carried separately. Historical live 955.098994210 and954.105032184 seconds retained; inner costs unknown. No accounting resets or new execution authority implied.
