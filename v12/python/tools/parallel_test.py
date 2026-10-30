"""W9707 — run the safe v12 source tests across the host's available CPUs.

`work/records/2026/08/finding-v12-parallel-test-runner/`.

The canonical `just test` recipe runs ONE `unittest` process over the whole
source tree. On the 16-core/32-CPU development host that measured 423.54s
elapsed against 422.65s user: one CPU, all of it, for seven minutes, while the
other thirty-one idled. The baseline is
`evidence/serial-pure-baseline-2026-08-25.txt`.

WHAT THIS IS NOT. It is not `pytest -n`, and it is not a shell fan-out over the
module list. Parallelism here is a property of the HARNESS and never of the
product: nothing under `src/` learns that it might be run concurrently. Every
shard is a fresh interpreter, which is most of the safety proof — module
`sys.path` and environment state, live-secret registries, SQLite handles, mocks
and worker-entry counters cannot cross a process boundary. The rest of the
proof is the registry below, which is EXPLICIT and FAILS CLOSED: a test module
that belongs to no registry stops the runner rather than being guessed into
the parallel phase.

WHY CLASSES AND NOT MODULES. A module-level partition was measured and
rejected: the baseline showed `test_boundary_inventory`'s whole-universe scans
dominating the wall clock, so a module fan-out would have kept exactly one long
pole and bought much less than it looks like it would. The ordinary shard is
therefore one concrete `TestCase` class, and the two aggregate scan classes are
split one test METHOD per shard. That split is safe to state as a rule because
the two selected aggregate classes have no shared class/module fixtures.
Other class fixtures remain intact; supervised engine fixtures are never shards.

COMPLETION ORDER NEVER DECIDES PRESENTATION. The parent drains every scheduled
shard before it prints anything about results, then reports in sorted shard
order. A run whose shards finish in a different order every time still produces
byte-identical stdout, which is what makes `jobs=1` and `jobs=32` comparable at
all. Durations and live progress go to stderr, where they cannot make stdout
nondeterministic.

THE PARENT NEVER IMPORTS A TEST MODULE. Collection happens in disposable child
interpreters that report exact `unittest` ids back as JSON; the parent only
ever partitions strings. A test module with an expensive or side-effecting
import therefore costs the parent nothing and cannot contaminate it.

W168703 classifies separately supervised tests without granting execution.
Default/all refuses until their acceptance is explicitly composed. Use an
explicit parallel or serial phase for scoped results; serial still includes
engine workloads. Supervised entries are metadata, never commands or receipts.
Collectors may import inert fixture definitions, but cannot select their tests.
"""

import argparse
import io
import json
import os
import pathlib
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest

HERE = pathlib.Path(__file__).resolve()
ROOT = HERE.parents[1]

# -- the registries ----------------------------------------------------------
#
# Registries are written by hand and their COMPLETENESS is checked
# mechanically, so a new module is a loud failure rather than a silent
# assumption. `tests/tools/test_parallel_runner.py` owns that check.

PARALLEL_MODULES = ("tests.tools.test_stack",
                    # W183883. The prepared-environment checks: the one command
                    # that reaches an index is injected, so they need no
                    # network, Docker, engine or serial resource either.
                    "tests.tools.test_environment",
                    # W183883. The one-time deployment setup: a real Authority,
                    # which is a self-contained durable store, and no Docker,
                    # engine, network or serial resource.
                    "tests.tools.test_bootstrap",
                    # W183883. The deployed instance selector: a stand-in
                    # runtime of ordinary files, no build, no Docker, engine,
                    # network or serial resource.
                    "tests.tools.test_instance",
                    # W183883. The REAL one-folder bundle: subprocesses of the
                    # built command and digests of a copy of it. No Docker,
                    # engine, network or serial resource -- and it SKIPS with
                    # the exact build command when there is no bundle, because
                    # a check that cannot be answered must not answer.
                    "tests.tools.test_packaging",
                    # W183883. The application version and the captured build
                    # stamp: pure formatting and a substituted repository tool,
                    # so no Docker, engine, network or serial resource -- and
                    # no version-control operation at all.
                    "tests.tools.test_version",
                    # W183883. The stack lifecycle checks: pure, no Docker,
                    # engine, network or serial resource, so they shard.
                    "tests.authority.test_assignment",
                    "tests.authority.test_boundary",
                    "tests.authority.test_catalog",
                    # W16823's closed claim result and its schema-4 boundary.
                    # PARALLEL: every case owns a disposable authority under
                    # its own temporary directory and shares no file with
                    # anything else.
                    "tests.authority.test_claim_result",
                    "tests.authority.test_contract",
                    "tests.authority.test_identity",
                    "tests.authority.test_operations",
                    # W16821's principal/scope seam.  PARALLEL: every case owns
                    # a disposable authority under its own temporary directory
                    # and shares no file, port or engine with anything else.
                    "tests.authority.test_principal_scope",
                    "tests.authority.test_session",
                    # W29400's Work-label authority model. PARALLEL: every
                    # case owns a disposable authority under its own temporary
                    # directory and shares no file with anything else.
                    "tests.authority.test_work_labels",
                    # W29401's exposure revalidation. PARALLEL: a disposable
                    # authority per case and no engine, image or container --
                    # and deliberately small, because v12 has no CLI or
                    # protocol host for the rest of that cut to land in.
                    "tests.authority.test_work_label_exposure",
                    "tests.authority.test_store",
                    "tests.manager.test_attempts",
                    "tests.manager.test_boundary_inventory",
                    "tests.manager.test_canonical",
                    "tests.manager.test_contracts_inventory",
                    "tests.manager.test_dependencies",
                    "tests.manager.test_diagnostic_rendering",
                    # W34998's failed-start destroy provider. PARALLEL: a
                    # recording fake engine and this suite's own temporary
                    # roots; no daemon, image or container anywhere in it.
                    "tests.manager.test_failed_start_destroy",
                    "tests.manager.test_refused_session_cleanup",
                    "tests.manager.test_custody",
                    "tests.manager.test_frozen",
                    "tests.manager.test_handshake",
                    "tests.manager.test_credentials",
                    "tests.manager.test_intake",
                    "tests.manager.test_launch",
                    # W81857's durable per-attempt file exchange, at both of
                    # its ends. PARALLEL: every case owns one temporary launch
                    # home and one disposable control store, and the worker
                    # half patches the two container root CONSTANTS onto the
                    # module for the life of one case -- which is process
                    # state, and every shard is a fresh interpreter.
                    "tests.manager.test_exchange",
                    "tests.manager.test_sealing",
                    "tests.manager.test_interrogation",
                    "tests.manager.test_manifest_rules",
                    "tests.manager.test_oci",
                    # W110934: the fenced integration mount boundary. PARALLEL
                    # rather than serial: it owns disposable coordinator and
                    # manager stores, a private delivery root and its own
                    # canonical target tree, and it starts no engine -- the
                    # run seam is a recorded callable.
                    "tests.manager.test_oci_integration",
                    "tests.manager.test_offers",
                    "tests.manager.test_output",
                    "tests.manager.test_pod",
                    # W16823's principal-aware manager context. PARALLEL: an
                    # injected fake session and a disposable control store per
                    # case, and no engine, image or container anywhere in it --
                    # the label cases compare the manager's own derivation
                    # rather than asking a daemon what is running.
                    "tests.manager.test_principal_context",
                    # W32649's cross-attempt runtime lane. PARALLEL: a
                    # disposable control store per case and an injected fake
                    # session and adapter; the one threaded case races three
                    # managers over ITS OWN store file and touches no engine,
                    # image or container.
                    "tests.manager.test_runtime_lane",
                    "tests.manager.test_secrets",
                    "tests.manager.test_sessions",
                    "tests.manager.test_store",
                    "tests.manager.test_text_sweep",
                    "tests.manager.test_validate",
                    # W39357's real Claude worker adapter. PARALLEL: the
                    # provider is an INJECTED process-running capability, so
                    # no provider, credential, network or daemon is reached --
                    # every case runs against a per-case temporary tree with
                    # the workload's root constants patched onto the module.
                    "tests.manager.test_claude_agent",
                    # W38956's Docker worker-entry transport. PARALLEL: the
                    # positive cases run the image's own program in a THREAD
                    # over a private pipe pair with the worker's root
                    # constants patched to a per-case temporary directory, and
                    # the negative ones drive a composed peer. No daemon, no
                    # image and no container -- `exec_vector` is asserted as a
                    # composed vector, and whether an engine applies it is the
                    # serial gates' question.
                    "tests.manager.test_worker_entry",
                    "tests.manager.test_worker_image",
                    "tests.manager.test_workspaces",
                    # W39358's dogfood operator halves. PARALLEL: the facade
                    # delegates to an injected object, the staging and the two
                    # protocol documents are pure functions over a temporary
                    # directory, and the one case that reaches the manager
                    # calls `compose_input_root` over that same private root.
                    # No daemon, no image, no credential and no shared name.
                    "tests.tools.test_dogfood_operator",
                    # W52821's user-scoped credential source. PARALLEL: no
                    # authority, no engine, no image, no network, no provider,
                    # no worker and no real credential. Every case owns a
                    # disposable private tree, its own registry, its own
                    # reader, its own credential home and its own attempt ids;
                    # the one concurrent case runs TWO complete contexts
                    # through a barrier inside its own two temporary homes,
                    # which is exactly the shape a global lock, cache or
                    # singleton in the reader would break.
                    #
                    # IT DOES REACH THE MANAGER PACKAGE, and that is the
                    # correction rather than a widening: review
                    # 2026-09-01T13-04-03Z [P1] found the suite asserting the
                    # reader's place in the deployment against stand-ins it
                    # defined itself, so the seam cases now drive the real
                    # command and the real `CredentialHome`. What they touch
                    # is `credentials.resolved_delivery`, one materialization
                    # per case under this case's own temporary home, and the
                    # process-wide live-secret registry -- which every case
                    # releases before it ends, and which is per-process and
                    # therefore still not shared with anything running beside
                    # this module.
                    #
                    # AND IT REACHES IT UNCONDITIONALLY. Review
                    # 2026-09-01T13-57-01Z [P1]: the seam imports sat behind
                    # `except Exception` and became a module-wide skip, so the
                    # shard could report this module green in a tree where the
                    # manager or the command did not import at all. Both are
                    # module-scope imports now, exactly as every other entry
                    # in this phase takes its own -- a shard that cannot
                    # import them FAILS rather than passing quietly.
                    "tests.tools.test_user_credentials",
                    "tests.tools.test_parallel_runner",
                    "tests.tools.test_worker_image_build",
                    # W71875's persistent Job manager. APPENDED rather than
                    # inserted, so no existing member moves. Every case owns a
                    # disposable temporary directory holding its own Job store
                    # and its own Worker Manager control store, drives a strict
                    # in-process fake session, and starts no container, builds
                    # no image and touches no shared artefact -- which is what
                    # this phase is for.
                    "tests.job_manager.test_delegation",
                    "tests.job_manager.test_documents",
                    "tests.job_manager.test_ending",
                    "tests.job_manager.test_exchange",
                    "tests.job_manager.test_launch",
                    "tests.job_manager.test_recovery",
                    "tests.job_manager.test_restart",
                    "tests.job_manager.test_scheduling",
                    "tests.job_manager.test_status",
                    "tests.job_manager.test_store",
                    "tests.job_manager.test_submission",
                    "tests.job_manager.test_sweep",
                    "tests.job_manager.test_tool",
                    # W316918's final-allocation settlement. PARALLEL on the
                    # same rule as the block above: one disposable temporary
                    # root per case holding its own Job store, a strict
                    # in-process fake deployment, and no container, image,
                    # engine, network or shared artefact at all.
                    "tests.job_manager.test_final_allocation_release",
                    # W76207's production one-worker composition. PARALLEL:
                    # real stores and filesystem material are confined to one
                    # temporary root per case; the OCI boundary is a recording
                    # callable, so no daemon, image, credential or network is
                    # shared or reached.
                    "tests.tools.test_single_worker",
                    # W103083: the standalone stage deployment, and W119114's
                    # composed one-Job lifecycle inside it. STILL PARALLEL,
                    # and the reason is narrower than it was: the OCI boundary
                    # is a recording callable, so no daemon, image, container,
                    # credential or network is reached. What the lifecycle
                    # cases DO start is real version control and real worker
                    # and provider children, and every one of them runs inside
                    # that case's own temporary root with no ambient
                    # configuration -- so nothing is shared with another shard.
                    "tests.tools.test_stage_execution",
    # W110935: the integration worker's additive provider wrapper. PARALLEL:
    # every case owns one temporary root, the process seam is a recording
    # callable and no provider, credential, engine or network is reached.
    "tests.manager.test_integration_worker",
    # W110935: the integration image's recipe and the layout it copies.
    # PARALLEL, and it is the deterministic half on purpose: it reads the
    # recipe and stages the exact file set that recipe copies into one
    # temporary directory per case, then imports it with a child interpreter.
    # No engine, daemon, image, container, network, credential or shared name
    # -- building or selecting an artefact is a deployment act and this suite
    # deliberately performs neither.
    "tests.manager.test_integration_image",
    # W112630: the immutable integration evidence bundle. PARALLEL, and it
    # starts nothing: the version control is a deterministic read-only runner
    # over real temporary files, the bundle is published into one disposable
    # root per case, and the real admission world it drives is the same
    # in-process one `tests.integration.test_driver` already runs here.
    "tests.tools.test_integration_bundle",
    # W110774: the production integration runtime port. PARALLEL, and it
    # starts nothing: the engine is a recording callable no case reaches, the
    # manager/offer/attempt owners are real but live in one disposable store
    # per case, and the canonical target is a temporary directory this module
    # provisions and removes. No daemon, image, container, network or
    # credential -- selecting or starting a runtime artefact is a deployment
    # act and this suite deliberately performs neither.
    "tests.tools.test_integration_worker",
                    # W71917's source/workspace boundary. PARALLEL: every case
                    # owns one temporary root holding its own nominated source,
                    # workspace store and control store, and the module-level
                    # patches it makes -- `os.lstat`, `os.statvfs`,
                    # `workspaces.mount_table`, `source_boundary.MOUNTINFO` --
                    # are process state, which a fresh shard interpreter does
                    # not share. It reads `/proc/self/mountinfo`, which is this
                    # process's own view and not a shared artefact, and the one
                    # case that would create a mount namespace is gated on an
                    # actual `unshare` capability probe and skips without it.
                    # No daemon, image, container, credential or shared name.
                    "tests.manager.test_source_boundary",
                    # W61984's quiescent-assignment finalization. PARALLEL: a
                    # disposable control store under this suite's own temporary
                    # directory, an injected fake session, and no agent call,
                    # runtime-stop call, daemon, image or container -- the
                    # module exists precisely because finalization takes
                    # neither capability. The restart case reopens THIS case's
                    # own store file.
                    #
                    # REGISTERED BY W71917 AND NOT OWNED BY IT. This module was
                    # added at `fda9cf6` without a registry entry, so the
                    # completeness gate refused the whole runner for every
                    # caller until now -- which is the gate working, and is
                    # also why the broad sweep could not be run at all. The
                    # classification above is read off the suite's own fixture;
                    # W61984's record owns the module.
                    "tests.tools.test_quiescent_assignment_finalization",
                    # W71918's checkpoint profile and persistent review-cycle
                    # suites. PARALLEL: each case owns disposable source,
                    # checkout, workspace-storage and control-store roots. The
                    # profile suite's real Git case uses only its private
                    # repository; the review-cycle suite uses in-process fake
                    # profiles and authority ports. Neither reaches a daemon,
                    # image, container, credential, network, or shared name.
                    "tests.manager.test_checkpoint_profiles",
                    "tests.manager.test_review_cycles",
                    # W71878's target-global integration coordinator.
                    # PARALLEL: every case owns one coordinator database under
                    # its own temporary root, and the store is the ONLY thing
                    # any case touches -- no Git, no working tree, no
                    # Authority session, no daemon, image, container,
                    # credential, network or shared name, because the module
                    # under test is the seam that owns none of those.
                    #
                    # The cases that use two connections -- the threaded
                    # grant race, and the interleaving that proves one proof
                    # observes one snapshot -- open both against THEIR OWN
                    # database file inside the case, and close both there.
                    "tests.integration.test_coordinator",
                    # W101490's generic integration runtime boundary. PARALLEL
                    # for the same reason: each case owns one coordinator
                    # database under its own temporary root, and the module
                    # under test composes documents rather than starting
                    # anything -- no runtime, no daemon, image, container,
                    # credential, network or shared name.
                    "tests.integration.test_runtime",
                    # W101491's candidate admission, at K's request under the
                    # obligation on that Work: the tuner owns the leaf and this
                    # registry is a shared boundary it is not permitted to
                    # change.
                    #
                    # PARALLEL, on the same evidence as its two siblings and
                    # checked rather than inherited from them. Every case owns
                    # one coordinator database under its own temporary root;
                    # the Authority, Job store and manager it admits against
                    # are in-process fakes rather than real stores; and it
                    # reaches no daemon, image, container, credential, network
                    # or shared name. Its one threaded case races two
                    # connections to ITS OWN database file to prove a
                    # concurrent exact admission returns one entry and one
                    # rank, and both are opened and closed inside that case.
                    "tests.integration.test_admission",
                    # W101492's fenced integration assembly. PARALLEL on the
                    # same evidence, checked rather than inherited: each case
                    # owns one coordinator database, one control store and one
                    # launch root under its own temporary directory, and the
                    # model is an in-process port that writes the durable
                    # result file a container would. Nothing here starts a
                    # runtime or reaches a daemon, image, container,
                    # credential, network or shared name.
                    "tests.integration.test_execution",
                    # W101493's operator-held recovery leaf, at the tuner's
                    # request under the obligation on that Work: the tuner owns
                    # the leaf and this registry is a shared boundary it is not
                    # permitted to change.
                    #
                    # PARALLEL, checked here rather than inherited from the
                    # fixture it composes. Its cases build on
                    # `test_execution`'s `ExecutionCase`, so each owns one
                    # coordinator database, one control store, one launch root
                    # and one DISPOSABLE TARGET directory under its own
                    # `tempfile.TemporaryDirectory`; the identifiers it repeats
                    # (`integration-attempt`, `integration-lease`) are rows in
                    # that private database rather than names in any shared
                    # namespace. Neither the module under test nor the suite
                    # reads an environment variable, changes the working
                    # directory or the umask, opens a socket or a subprocess,
                    # or reaches a daemon, image, container, credential,
                    # network or shared name -- the leaf holds an interruption
                    # and starts nothing. Confirmed by running both of its
                    # classes as eight concurrent processes, all passing.
                    "tests.integration.test_recovery",
    # W168703: reviewed per-case roots/stores and deterministic external
    # boundaries. Some cases run local Git/Python; class processes isolate
    # imports and mocks. The dossier records leaf ownership and conditions.
    "tests.integration.test_managed_execution",
    "tests.integration.test_managed_storage",
    "tests.integration.test_reconciliation",
    "tests.job_manager.test_execution_limits",
    "tests.job_manager.test_managed_integration_capacity",
    "tests.manager.test_execution_limits",
    "tests.manager.test_reconciliation_task",
    "tests.manager.test_reconciliation_worker",
    "tests.manager.test_runtime_deadline_engine_budget",
    "tests.manager.test_runtime_deadlines",
    "tests.tools.test_execution_limits",
    "tests.tools.test_job_viewer",
    "tests.tools.test_live_ab",
    "tests.tools.test_managed_integration",
    "tests.tools.test_managed_preparation",
    "tests.tools.test_scheduler_trace",
    "tests.tools.test_stage_execution_hardening",
    "tests.tools.test_stage_execution_status_hardening",
    "tests.tools.test_standalone_ab",
    # W384870. The modules found registered nowhere by the 2026-10-29 baseline
    # audit, each read before classification: none reaches a daemon (every
    # `docker` word in them is a fake engine or a planted secret), none builds
    # an image, none shares a name; class fixtures stay within one class
    # shard. So they SHARD. The engine-owning modules remain the serial
    # registry below, unchanged.
    "tests.authority.test_dossier",
    "tests.job_manager.test_creation",
    "tests.job_manager.test_fresh_attempt",
    "tests.job_manager.test_native_permission",
    "tests.job_manager.test_native_stop_restart",
    "tests.job_manager.test_role_capability",
    "tests.job_manager.test_role_contract",
    "tests.job_manager.test_serving_renewal",
    "tests.job_manager.test_store_readonly",
    "tests.job_manager.test_templates",
    "tests.manager.test_adapter_declaration",
    "tests.manager.test_attempt_failure_cause",
    "tests.manager.test_attempt_logs",
    "tests.manager.test_authoring_enforcement",
    "tests.manager.test_authoring_manager_guard",
    "tests.manager.test_authoring_shutdown_deadline",
    "tests.manager.test_claude_context",
    "tests.manager.test_dogfood_entry",
    "tests.manager.test_fixture_dispatch",
    "tests.manager.test_importing_fixture",
    "tests.manager.test_integration_generation",
    "tests.manager.test_maintenance",
    "tests.manager.test_proposing_fixture",
    "tests.manager.test_provider_context",
    "tests.manager.test_provider_context_delivery",
    "tests.manager.test_stopped_settlement",
    "tests.manager.test_verification_context",
    "tests.manager.test_verification_views",
    "tests.manager.test_verifier_topology",
    "tests.manager.test_w197661_verifier",
    "tests.manager.test_worker_packaging",
    "tests.tools.test_accepted_base",
    "tests.tools.test_attempt_diagnostics",
    "tests.tools.test_attempt_logs_command",
    "tests.tools.test_connected_creation",
    "tests.tools.test_connected_startup",
    "tests.tools.test_correction_restart",
    "tests.tools.test_creation_ports",
    "tests.tools.test_disposition_command",
    "tests.tools.test_dossier_command",
    "tests.tools.test_dossier_recovery",
    "tests.tools.test_fresh_retry_line_recovery",
    "tests.tools.test_job_task_delivery",
    "tests.tools.test_joined_workflow",
    "tests.tools.test_managed_apply",
    "tests.tools.test_next_run",
    "tests.tools.test_next_run_flow",
    "tests.tools.test_next_run_managed",
    "tests.tools.test_next_run_recovery",
    "tests.tools.test_operator_verification_view",
    "tests.tools.test_packaged_creation",
    "tests.tools.test_pool",
    "tests.tools.test_retry_task_lineage",
    "tests.tools.test_startup_prerequisites",
    "tests.tools.test_stopped_settlement_command",
    "tests.tools.test_stopped_settlement_joined",
    "tests.tools.test_worker_visibility",
    # W384870 review R2: the content-bound source identity `test-all` records.
    # Pure: a disposable git repository per case, no engine, no network.
    "tests.tools.test_source_identity")

SUPERVISED_MODULES = ({
    "module": "tests.manager.test_runtime_deadline_engine",
    "work": "W32577",
    "supervisor": "baton:work/records/2026/08/finding-v12-local-oci-negative-race-endings/findings/finding-v12-runtime-deadline-cleanup/engine-gate.py",
    "reason": "Requires the reviewed supervisor, preloaded immutable image and reserved cleanup; ordinary execution is not selected.",
},)

# W384870 R2 -- the INPUTS OUTSIDE `v12/` that the supported run consumes.
#
# The source identity a run reports (`tools/source_identity.py`) hashes the
# changed bytes under `v12/`; `HEAD` binds the committed rest. But the suite
# also EXECUTES, IMPORTS and READS files that live in Work records: the
# reviewed supervisor, the captured image contexts a fixture puts on its import
# path, the proposed contracts the role tests validate, the manifest vectors
# and schemas. HEAD binds their committed versions only; an edited or untracked
# input at one of these paths would otherwise change what a run tested without
# changing its identity. So they are DECLARED here, by exact path, and the
# identity hashes their bytes as they are in the checkout (tracked, modified or
# untracked alike; gitignored files such as `__pycache__` excluded). A declared
# input that is absent refuses the identity, and therefore the run.
#
# Declare the file or the smallest directory actually consumed -- an import
# path is a directory, a document is a file -- never a whole dossier: the
# records also hold the evidence runs produce, and that is exactly what must
# stay OUT of the identity. `tests.tools.test_parallel_runner` sweeps the test
# tree for record paths and fails when one is neither declared here nor
# listed there as synthetic; the supervisor is derived from SUPERVISED_MODULES
# above, not repeated.
_LAUNCH_MISMATCH = "work/records/2026/09/finding-v12-worker-launch-version-mismatch"
_WORKER_CONTRACT = ("work/records/2026/08/finding-v12-isolated-agent-workers/findings/"
                    "finding-v12-worker-contract/findings")
_ADMISSION_PLAN = ("work/records/2026/10/finding-v12-workflow-fragility-assessment/findings/"
                   "finding-template-adapter-admission-plan")
CONSUMED_INPUTS = (
    # import paths and executed programs
    {"path": _LAUNCH_MISMATCH + "/instance-201492/context/worker",
     "consumers": ("tests.manager.test_importing_fixture", "tests.manager.test_fixture_dispatch")},
    {"path": _LAUNCH_MISMATCH + "/instance-201492/context/Dockerfile.fixture",
     "consumers": ("tests.manager.test_fixture_dispatch",)},
    {"path": _LAUNCH_MISMATCH + "/instance-201492/verify_lifecycle.py",
     "consumers": ("tests.manager.test_w197661_verifier",)},
    {"path": _LAUNCH_MISMATCH + "/instance-201492/compose_lifecycle.py",
     "consumers": ("tests.manager.test_w197661_verifier (imported by verify_lifecycle)",)},
    {"path": _LAUNCH_MISMATCH + "/instance-200564/context/worker",
     "consumers": ("tests.manager.test_proposing_fixture",)},
    {"path": "work/records/2026/09/finding-v12-single-implementation-proof/baseline.py",
     "consumers": ("tests.manager.shutdown_fixture", "tests.manager.test_authoring_enforcement",
                   "tests.manager.test_authoring_manager_guard")},
    # documents read
    {"path": _LAUNCH_MISMATCH + "/instance-200564/bootstrap_inputs.json",
     "consumers": ("tests.manager.test_importing_fixture",)},
    {"path": _LAUNCH_MISMATCH + "/instance-200564/install_inputs.json",
     "consumers": ("tests.manager.test_importing_fixture",)},
    {"path": _LAUNCH_MISMATCH + "/instance-200564/task.json",
     "consumers": ("tests.manager.test_proposing_fixture",)},
    {"path": _ADMISSION_PLAN + "/CAPABILITY.synthetic.json",
     "consumers": ("tests.job_manager.test_role_capability",)},
    {"path": _ADMISSION_PLAN + "/ROLE-CONTRACT.proposed.json",
     "consumers": ("tests.job_manager.test_role_contract",)},
    {"path": _WORKER_CONTRACT + "/finding-worker-control-api-manifests/evidence/vectors.json",
     "consumers": ("tests.manager.verification_fixtures and the manifest, workspace, secrets, image, "
                   "container, output, driver, stage-execution, review-driver and next-run cases",)},
    {"path": _WORKER_CONTRACT + "/finding-worker-control-api-manifests/schema/worker-control-1.0.schema.json",
     "consumers": ("tests.manager.test_frozen",)},
    {"path": _WORKER_CONTRACT + "/finding-acp-agent-boundary/schema/agent-session-1.0.schema.json",
     "consumers": ("tests.manager.test_frozen",)},
    {"path": ("work/records/2026/08/finding-v12-isolated-agent-workers/findings/"
              "finding-v12-assignment-state-machine/evidence/test_assignment_state_model.py"),
     "consumers": ("tests.authority.test_catalog",)},
    {"path": "work/records/2026/09/finding-v12-deterministic-scheduler-stress/trace-160959-composed.json",
     "consumers": ("tests.tools.test_correction_restart",)},
)


def consumed_inputs():
    """Every repository-relative input outside `v12/` the supported run consumes: the
    declared paths plus each supervised module's supervisor, sorted, unique."""
    found = {entry["path"] for entry in CONSUMED_INPUTS}
    for entry in SUPERVISED_MODULES:
        prefix, _, relative = entry["supervisor"].partition(":")
        if prefix == "baton":
            found.add(relative)
    return sorted(found)

STATUS_EVIDENCE_MODULE = "tests.tools.test_stage_execution_status_hardening"
STATUS_EVIDENCE_VARIABLE = "BATON_STATUS_HARDENING_EVIDENCE"

# ONE AT A TIME, IN THIS ORDER, AND NEVER BESIDE THE PARALLEL PHASE.
#
# `test_worker_container` builds THIS repository's worker image, owns the
# suite-global `baton-w6633-test` names and is the only source module with
# class fixtures. `test_oci_engine` drives a real Docker daemon and
# PULLS the pinned base into the shared image store when it is absent; its own
# comments record a full run where an unconditional pull changed what the image
# gate resolved between two builds. Running either concurrently with anything —
# including the other — puts two suites in disagreement about one daemon's
# artefacts, which is not a result about either of them. The image gate runs
# first because it produces the artefact; the engine gate then observes a store
# nobody else is still writing to.
# `test_lifecycle_composition` (W6636) is serial for BOTH reasons at once: it
# builds this repository's worker image AND drives a real daemon through the
# manager's whole ordered lifecycle, including a case that asks the engine
# whether exactly one container carries an assignment's labels. A concurrent
# suite creating or removing containers makes that count a fact about the run
# rather than about the manager. It runs LAST, because it observes both
# artefacts the two before it produce.
# W26283 adds the fourth: `test_output_custody_engine` runs the reference
# worker for real and then seals what it wrote, so it owns containers and the
# built image exactly as the three before it do. It runs after
# `test_worker_container`, whose image gate is what produces the artefact it
# depends on being buildable at all.
# W32382 adds the sixth for the same two reasons as the third: it drives a
# real daemon through the manager's negative and race endings and asks the
# engine how many containers carry an assignment's labels. A concurrent suite
# creating or removing containers makes that count a fact about the run. It
# runs beside `test_lifecycle_composition`, whose fixture it subclasses.
# W33935 adds the eighth: `test_input_delivery` builds the worker image and
# starts real containers over the manager's own composed argv, so it owns the
# same two artefacts the seven before it do. It runs beside
# `test_lifecycle_composition`, whose engine fixture it reuses.
# W34998 adds the ninth: `test_failed_start_destroy_engine` builds this
# repository's worker image and creates real containers to remove them, so it
# owns the same two artefacts the eight before it do. It runs after
# `test_worker_container`, whose image gate produces the artefact it needs.
SERIAL_MODULES = ("tests.manager.test_worker_container",
                  "tests.manager.test_failed_start_destroy_engine",
                  "tests.manager.test_oci_engine",
                  "tests.manager.test_lifecycle_composition",
                  "tests.manager.test_negative_race_endings",
                  "tests.manager.test_ended_runtime_adoption",
                  "tests.manager.test_output_custody_engine",
                  "tests.manager.test_credentials_engine",
                  "tests.manager.test_refused_session_engine",
                  "tests.manager.test_custody_engine",
                  "tests.manager.test_input_delivery",
                  # W39356's real-engine transport gate, APPENDED rather than
                  # inserted: the image gate stays first and no existing
                  # member moves. Serial for the reason every other engine
                  # gate is -- it inherits W6636's class fixture, builds the
                  # reference image, starts real containers under one
                  # assignment's labels and drives `docker exec` against them,
                  # and one of its cases removes a container and asks the
                  # daemon about it.
                  "tests.manager.test_worker_entry_engine",
                  # W39357's no-secret dogfood image gate. SERIAL because it
                  # BUILDS an image -- with networked npm and Debian installs
                  # -- and then starts throwaway containers from it. It is the
                  # only gate in this registry whose build needs egress; the
                  # containers it then runs are all `--network none`.
                  "tests.manager.test_dogfood_image",
                  # W44716's abandonment gate, APPENDED for the same reason
                  # the two before it were: no existing member moves. Serial
                  # because it builds the reference image, starts real
                  # containers, and then asks the daemon whether a RUNNING
                  # container was removed -- a question a concurrent suite
                  # could answer for it.
                  "tests.manager.test_abandoned_attempt_engine",
                  # W39358's whole-arc gate, and the heaviest in this
                  # registry: it builds the dogfood image and then runs the
                  # composed arc over a real container, asking the daemon
                  # afterwards whether the runtime is gone.
                  "tests.tools.test_dogfood_arc_engine",
                  # W39358's public-retry gate: it derives an image from the
                  # reference worker and runs real containers through the
                  # documented commands.
                  "tests.tools.test_dogfood_retry_engine",
                  "tests.manager.test_private_line_access_engine",
                  # W116014: register the two stage drivers conservatively.
                  # Their composed fixtures have not been certified parallel;
                  # neither module requires a live model.
                  "tests.integration.test_driver",
                  "tests.job_manager.test_review_driver")

# The two whole-universe scans from the baseline. Split one test method per
# shard; every other class ships as one shard.
METHOD_SPLIT = ("tests.manager.test_boundary_inventory.EveryReceivingEntryHasOneOwner",
                "tests.manager.test_boundary_inventory.EveryProbeProvesItArrived")

# -- W384870: the logical test groups, an EXACT PARTITION by module -----------
#
# A group is a scheduling and repair unit, never a second execution registry:
# the parallel/serial/supervised registries above still decide HOW a module
# runs, the group decides which `test-group` selects it. Every module on disk
# belongs to exactly one group, checked mechanically beside the registry
# check, so `test-all` iterating the registries once schedules every test id
# exactly once and a `test-group` never runs an id twice across groups.
#
# Four groups are carved out explicitly; the rest follow their package.
GROUP_MODULES = {
    # The serial engine gates that own a daemon, built images or shared names.
    "manager-engine": ("tests.manager.test_worker_container",
                       "tests.manager.test_failed_start_destroy_engine",
                       "tests.manager.test_oci_engine",
                       "tests.manager.test_lifecycle_composition",
                       "tests.manager.test_negative_race_endings",
                       "tests.manager.test_ended_runtime_adoption",
                       "tests.manager.test_output_custody_engine",
                       "tests.manager.test_credentials_engine",
                       "tests.manager.test_refused_session_engine",
                       "tests.manager.test_custody_engine",
                       "tests.manager.test_input_delivery",
                       "tests.manager.test_worker_entry_engine",
                       "tests.manager.test_dogfood_image",
                       "tests.manager.test_abandoned_attempt_engine",
                       "tests.manager.test_private_line_access_engine",
                       "tests.tools.test_dogfood_arc_engine",
                       "tests.tools.test_dogfood_retry_engine"),
    # Run only through its reviewed supervisor.
    "supervised": ("tests.manager.test_runtime_deadline_engine",),
    # The whole-universe scans: long poles whose registries every new module
    # touches.
    "scans": ("tests.manager.test_boundary_inventory",
              "tests.manager.test_dependencies",
              "tests.manager.test_contracts_inventory",
              "tests.manager.test_text_sweep",
              "tests.manager.test_source_boundary"),
    # The cases that examine a BUILT bundle and refuse to stand in for one.
    "tools-packaged": ("tests.tools.test_packaging",
                       "tests.tools.test_packaged_creation"),
}
GROUP_PACKAGES = {"tests.authority": "authority",
                  "tests.job_manager": "job_manager",
                  "tests.integration": "integration",
                  "tests.manager": "manager-pure",
                  "tests.tools": "tools-pure"}
GROUPS = ("authority", "job_manager", "manager-pure", "manager-engine", "integration",
          "tools-pure", "tools-packaged", "supervised", "scans")


def group_of(module, explicit=GROUP_MODULES, packages=GROUP_PACKAGES):
    """The ONE group a module belongs to, or a refusal."""
    owners = [name for name, modules in explicit.items() if module in modules]
    if len(owners) > 1:
        raise RunnerRefusal(f"{module} is carved into more than one group: {owners}")
    if owners:
        return owners[0]
    package = module.rsplit(".", 1)[0]
    if package in packages:
        return packages[package]
    raise RunnerRefusal(f"{module} belongs to no group; add it to a carved group or map its package")


# W384870: the proofs the owner classified OPTIONAL on 2026-10-29. A skip of
# any OTHER test is a required proof not run, and `--account` fails the run.
# Each entry is an exact test id and the reason the owner accepted.
OPTIONAL_SKIPS = {
    "tests.manager.test_source_boundary.CleanupNeverRemovesMaterialThisManagerDidNotCreate."
    "test_a_real_same_filesystem_bind_mount_is_refused":
        "needs a user namespace this host does not permit; the sibling case "
        "proves the same boundary",
    "tests.manager.test_source_boundary.TheWorkspaceIsStorageAndScratchIsBounded."
    "test_more_than_the_scratch_bound_really_fits_in_the_workspace":
        "host-capacity proof selected by BATON_V12_LARGE_WORKSPACE_PROOF=1",
}

# What a composed supervised step needs in the environment, by module. The
# supervised metadata itself stays the closed four-field shape above.
SUPERVISED_ENVIRONMENT = {
    "tests.manager.test_runtime_deadline_engine": ("BATON_W32577_IMAGE_DIGEST",),
}
SUPERVISOR_TIMEOUT_SECONDS = 200.0


class RunnerRefusal(Exception):
    """The runner refusing to run, rather than running something it guessed."""


class Interrupted(Exception):
    """A recorded signal, raised at a SAFE POINT rather than inside the handler.

    Review R4 (2026-08-25T16:49:30Z) is why this type exists. Acting on a
    signal from async context means acting at an arbitrary bytecode, and the
    scheduler has instants — between creating a shard process and recording it
    — where its own bookkeeping does not yet describe reality. A handler that
    cleaned up there cleaned up the wrong picture and left a whole shard
    running. So the handler now records and returns, and the loop decides when
    the picture is complete enough to act on.
    """

    def __init__(self, number):
        self.number = number
        super().__init__(f"signal {number}")


# -- pure decisions the parent makes, with no process and no filesystem -------


def resolve_jobs(override, detected, shards):
    """The bounded worker count: LOWER-ONLY against the DETECTED CPU count.

    The finding pins two caps and they compose in one order. The refusal is
    evaluated against `detected`, never against `shards`: binding the operator
    override to the shard count would refuse a legitimate lowering whenever the
    selection happened to be small, which would make `--jobs 8` mean different
    things on different days. The shard count then only avoids starting workers
    that would have nothing to run.
    """
    if detected < 1:
        raise RunnerRefusal(f"the host reports {detected} available CPUs")
    requested = detected
    if override is not None:
        text = str(override).strip()
        # Deliberately not int(text): int() accepts "  8\n", "+8" and "8_0",
        # and an operator who typed one of those did not mean this.
        if not text.isdigit():
            raise RunnerRefusal(f"jobs must be a whole number 1..{detected}; got {override!r}")
        requested = int(text)
        if requested < 1 or requested > detected:
            raise RunnerRefusal(f"jobs must be a whole number 1..{detected} "
                                f"(this host's available CPUs); got {requested}")
    return max(1, min(requested, shards)) if shards else 1


def partition(ids, method_split=METHOD_SPLIT):
    """Exact test ids -> deterministic shards, losing and duplicating nothing.

    A `unittest` id is `package.module.Class.method`, so the class key is the
    id with its last segment removed. The returned shards are sorted by label
    and each shard's ids are sorted, which is the whole of the presentation
    order: nothing downstream re-sorts by completion.
    """
    seen = sorted(ids)
    duplicates = sorted({one for one in seen if seen.count(one) > 1})
    if duplicates:
        raise RunnerRefusal(f"collection produced duplicate test ids: {duplicates[:5]}")
    split = set(method_split)
    classes = {}
    shards = []
    for one in seen:
        key = one.rsplit(".", 1)[0]
        if key in split:
            shards.append({"label": one, "ids": [one]})
        else:
            classes.setdefault(key, []).append(one)
    for key in classes:
        shards.append({"label": key, "ids": sorted(classes[key])})
    shards.sort(key=lambda shard: shard["label"])
    covered = sorted(one for shard in shards for one in shard["ids"])
    if covered != seen:
        raise RunnerRefusal("partitioning lost or invented test ids")
    return shards


# -- the suite under management ----------------------------------------------


class Suite:
    """One source tree, its execution and supervised registries.

    Parameterized rather than hard-coded so the runner's own regressions drive
    THIS code over disposable fake trees instead of a re-implementation of it.
    """

    def __init__(self, root, parallel, serial, method_split=METHOD_SPLIT,
                 tests_dir="tests", pythonpath="src", supervised=(),
                 groups=GROUP_MODULES, packages=GROUP_PACKAGES, group_names=GROUPS,
                 optional_skips=OPTIONAL_SKIPS):
        self.root = pathlib.Path(root)
        self.optional_skips = dict(optional_skips)
        self.parallel = tuple(parallel)
        self.serial = tuple(serial)
        self.supervised = tuple(supervised)
        self.method_split = tuple(method_split)
        self.tests_dir = tests_dir
        self.pythonpath = pythonpath
        self.groups = dict(groups)
        self.packages = dict(packages)
        self.group_names = tuple(group_names)

    # -- W384870: the group partition --------------------------------------

    def registered(self):
        return list(self.parallel) + list(self.serial) + [entry["module"] for entry in self.supervised]

    def group_of(self, module):
        return group_of(module, self.groups, self.packages)

    def check_groups(self):
        """Every registered module in exactly one KNOWN group, and nothing carved
        that the registries do not know."""
        registered = set(self.registered())
        for name, modules in self.groups.items():
            if name not in self.group_names:
                raise RunnerRefusal(f"group {name!r} is carved but not a known group")
            stray = sorted(set(modules) - registered)
            if stray:
                raise RunnerRefusal(f"group {name} names modules the registries do not: {stray}")
        for name in self.packages.values():
            if name not in self.group_names:
                raise RunnerRefusal(f"package group {name!r} is not a known group")
        for module in sorted(registered):
            self.group_of(module)

    def group_counts(self, ids):
        counts = {name: 0 for name in self.group_names}
        for one in ids:
            counts[self.group_of(module_of(one))] += 1
        return counts

    def restricted(self, group):
        """This suite scoped to ONE group; registries and checks unchanged."""
        if group not in self.group_names:
            raise RunnerRefusal(f"unknown group {group!r}; the groups are {', '.join(self.group_names)}")
        chosen = Suite(self.root,
                       [m for m in self.parallel if self.group_of(m) == group],
                       [m for m in self.serial if self.group_of(m) == group],
                       method_split=self.method_split, tests_dir=self.tests_dir,
                       pythonpath=self.pythonpath,
                       supervised=[e for e in self.supervised if self.group_of(e["module"]) == group],
                       groups=self.groups, packages=self.packages, group_names=self.group_names,
                       optional_skips=self.optional_skips)
        if not chosen.registered():
            raise RunnerRefusal(f"group {group} selects no module")
        return chosen

    # -- registry completeness, checked against the filesystem ---------------

    def discovered(self):
        """Every module `unittest discover` would find, WITHOUT importing one.

        The glob is `test*.py` because that is `unittest`'s own default
        pattern; matching `test_*.py` instead would let a `testthing.py` be
        discovered by the canonical gate and missed by this check, which is
        precisely the residue the registry exists to make impossible.
        """
        base = self.root / self.tests_dir
        found = []
        for path in sorted(base.rglob("test*.py")):
            relative = path.relative_to(self.root).with_suffix("")
            found.append(".".join(relative.parts))
        return tuple(found)

    def check_registry(self):
        for entry in self.supervised:
            if not isinstance(entry, dict) or set(entry) != {"module", "work", "supervisor", "reason"}:
                raise RunnerRefusal("supervised metadata requires exactly module, work, supervisor and reason")
            if any(not isinstance(value, str) or not value.strip() or value != value.strip() or any(ord(c) < 32 for c in value) for value in entry.values()):
                raise RunnerRefusal("supervised metadata fields must be nonempty text without surrounding whitespace or control characters")
            if not re.fullmatch(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+", entry["module"], flags=re.ASCII) or not re.fullmatch(r"W[1-9][0-9]*", entry["work"]):
                raise RunnerRefusal("supervised metadata requires a dotted module and Work ID")
            locator = entry["supervisor"]
            if not re.fullmatch(r"[a-z][a-z0-9_-]*:work/records/[0-9]{4}/(?:0[1-9]|1[0-2])/(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+\.py", locator) or any(part in (".", "..") for part in locator.split("/")):
                raise RunnerRefusal("supervised metadata requires a canonical repository supervisor locator")
        registered = list(self.parallel) + list(self.serial) + [entry["module"] for entry in self.supervised]
        repeated = sorted({one for one in registered if registered.count(one) > 1})
        if repeated:
            raise RunnerRefusal(f"modules registered more than once: {repeated}")
        found = set(self.discovered())
        unregistered = sorted(found - set(registered))
        if unregistered:
            raise RunnerRefusal("these test modules belong to no registry; add each to the "
                                "parallel, serial or supervised registry in tools/parallel_test.py after "
                                f"deciding what it owns: {unregistered}")
        missing = sorted(set(registered) - found)
        if missing:
            raise RunnerRefusal(f"these registered test modules are not in the tree: {missing}")

    def supervised_description(self):
        return "; ".join(f"{entry['module']} ({entry['work']}; {entry['supervisor']}; {entry['reason']})" for entry in self.supervised)

    def check_selection(self, phase, print_ids, with_supervised=False):
        if self.supervised and not with_supervised:
            if print_ids and phase != "parallel":
                raise RunnerRefusal("--print-ids requires explicit --phase parallel while supervised tests are uncomposed: " + self.supervised_description())
            if phase == "all":
                raise RunnerRefusal("all-source acceptance is uncomposed; supervised tests require separate selection: " + self.supervised_description())
        if with_supervised and phase != "all":
            raise RunnerRefusal("--with-supervised composes the whole run; it requires --phase all")
        if phase != "serial" and STATUS_EVIDENCE_MODULE in self.parallel and self.environment().get(STATUS_EVIDENCE_VARIABLE):
            raise RunnerRefusal(f"unset {STATUS_EVIDENCE_VARIABLE} before selecting {STATUS_EVIDENCE_MODULE}; shared evidence destinations are not supported")

    def check_collected_ids(self, ids):
        forbidden = sorted({test_id for test_id in ids for entry in self.supervised if test_id == entry["module"] or test_id.startswith(entry["module"] + ".")})
        if forbidden:
            raise RunnerRefusal(f"collection selected supervised-owned test IDs; no shards will run: {forbidden}")

    # -- children ------------------------------------------------------------

    def environment(self):
        """The child's import path, stated rather than inherited.

        The canonical gate is `PYTHONPATH=src python3 -m unittest ... -t .`, and
        `-m` is what puts the top-level directory on `sys.path` there. These
        children are started as a SCRIPT, whose `sys.path[0]` is the script's
        own directory instead — so the tree root is named explicitly here and
        the child resolves exactly the same two places the gate does. The
        packaging proof is unaffected: it is the `build` stage that runs with
        `PYTHONPATH=` from outside the tree, and nothing here touches it.
        """
        environment = dict(os.environ)
        places = [str(self.root)]
        if self.pythonpath:
            places.append(str(self.root / self.pythonpath))
        environment["PYTHONPATH"] = os.pathsep.join(places)
        return environment

    def spawn(self, argv, err):
        """One child, in ITS OWN SESSION so its descendants can be reaped.

        `start_new_session=True` makes the child a process-group leader, which
        is what lets an interrupt kill the tests the child itself started
        rather than orphaning them. A test that spawns real processes — and
        several of these do — would otherwise survive the runner.

        Its stderr goes to ITS OWN FILE rather than a pipe. A pipe would be a
        64KiB deadlock waiting to happen: several of these modules emit
        ResourceWarnings, and a parent that only drains the pipe after `wait()`
        hangs forever the first time one of them is chatty. A file per shard is
        also why there is no shared log path to interleave.
        """
        handle = open(err, "wb")
        try:
            return subprocess.Popen([sys.executable, str(HERE)] + argv, cwd=str(self.root),
                                    env=self.environment(), stdout=subprocess.DEVNULL,
                                    stderr=handle, start_new_session=True)
        finally:
            handle.close()


class Run:
    """One invocation: its children, its disposable result root, its cleanup."""

    # How long a terminated shard's own descendants get to honour SIGTERM
    # before the group is killed outright. Bounded on purpose: this path only
    # runs when a run is being abandoned, and an abort that hangs waiting to be
    # polite is an abort that gets killed harder from outside.
    GRACE_SECONDS = 3.0

    def __init__(self, suite, jobs_override=None, progress=sys.stderr):
        self.suite = suite
        self.jobs_override = jobs_override
        self.progress = progress
        self.detected = os.process_cpu_count() or 1
        self.result_root = None
        self.live = {}
        # Popen -> the process group id recorded when this runner created it.
        # Kept beside `live` rather than derived from it, because shutdown must
        # still be able to reach a group whose leader has already exited.
        self.groups = {}
        # Set by the signal handler and by NOTHING else; read only at safe
        # points. The handler never touches `live`, `groups` or `result_root`.
        self.pending_signal = None

    # -- lifecycle -----------------------------------------------------------

    def note(self, line):
        if self.progress is not None:
            print(line, file=self.progress, flush=True)

    def open_result_root(self):
        self.result_root = pathlib.Path(tempfile.mkdtemp(prefix="v12-parallel-test-"))
        return self.result_root

    def shutdown(self):
        """Terminate every runner-owned process GROUP, then reap, then drop the root.

        Review R1 (2026-08-25T16:21:40Z) found the ordering bug this now avoids.
        The previous version dropped a shard from `self.live` the moment its
        LEADER exited, and escalated only over what remained — so a descendant
        that ignores SIGTERM outlived the runner whenever its leader took the
        signal and died first, and the entry naming its group was already gone.
        A shard leader's death says nothing about what the tests it started are
        still doing.

        Two rules follow, and the order of the steps below is the whole fix:

        1. THE GROUP IS THE UNIT, AND ITS IDENTITY IS RECORDED AT SPAWN. Every
           group id in `self.groups` was captured when this runner created that
           group, so escalation never depends on a leader still being alive and
           never has to re-derive an id from a process that has exited.
        2. NOTHING IS REAPED UNTIL AFTER THE KILL PASS. An unreaped leader is a
           zombie, and a zombie's pid is still reserved — so its group id cannot
           be recycled onto an unrelated process group in the window between
           TERM and KILL. Reaping first is what would make the KILL pass a
           danger to somebody else's processes, which is exactly the boundary
           the review asked to keep.

        The cost is that an abort always spends the grace period rather than
        exiting the moment the leaders die. That is deliberate: a zombie leader
        remains a member of its own group, so "is this group empty?" cannot be
        answered by signalling it, and the alternative is a /proc scan that buys
        a couple of seconds on a path that only runs when a run is being
        abandoned.
        """
        groups = list(self.groups.values())
        for pgid in groups:
            self.signal_group(pgid, signal.SIGTERM)
        if groups:
            deadline = time.monotonic() + self.GRACE_SECONDS
            while time.monotonic() < deadline:
                time.sleep(0.05)
            # Every group, including those whose leader already exited.
            for pgid in groups:
                self.signal_group(pgid, signal.SIGKILL)
        for child in list(self.live):
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
            self.live.pop(child, None)
        self.groups.clear()
        if self.result_root is not None:
            shutil.rmtree(self.result_root, ignore_errors=True)
            self.result_root = None

    def record_signal(self, number, frame=None):
        """The whole of the asynchronous handler.

        It records and returns. It reads no scheduler state and mutates none,
        because it can run between any two bytecodes — including the two that
        register a freshly spawned shard. The FIRST signal is kept so the
        reported exit code does not depend on how many times somebody pressed
        Ctrl-C; a second one is deliberately not a fast path around cleanup.
        """
        if self.pending_signal is None:
            self.pending_signal = number

    def checkpoint(self):
        """A SAFE POINT: act on a recorded signal now that bookkeeping is true.

        Called only where `live` and `groups` describe every process this
        runner has actually created — never between a spawn and its
        registration, and never between a cleanup side effect and the state
        change that follows it.
        """
        if self.pending_signal is not None:
            raise Interrupted(self.pending_signal)

    def has_exited(self, child):
        """Has this leader exited? Asked WITHOUT reaping it.

        `Popen.poll()` cannot answer this question safely, and review R2
        (2026-08-25T16:30:55Z) is why: poll() reaps, reaping releases the pid,
        and a released pid takes the process-group id with it. Any cleanup done
        after that is either impossible or — worse — aimed at whatever process
        inherits the number next.

        `waitid` with `WNOWAIT` reports the exit and leaves the leader as a
        zombie, which is exactly the state `retire()` needs: dead enough to have
        a final status, undead enough that the group id still provably belongs
        to this runner.
        """
        try:
            return os.waitid(os.P_PID, child.pid,
                             os.WEXITED | os.WNOHANG | os.WNOWAIT) is not None
        except ChildProcessError:
            # Somebody already reaped it; treat it as finished rather than
            # spinning on a child that will never report again.
            return True

    def retire(self, child):
        """Finish one shard: kill what it left running, THEN reap it.

        The order is the whole of review R2's required correction, and it is
        unconditional rather than conditioned on the shard's verdict. A shard
        can fail an assertion and let its worker exit 1 perfectly normally
        while a process it started keeps running; the leader's clean exit says
        nothing about that. Deciding whether to clean up based on the verdict
        would also mean computing the verdict first, so cleaning up ALWAYS is
        both simpler and strictly stronger than what the review asked for.

        SIGKILL with no grace period, deliberately: this shard is over. Its
        descendants are not being asked to wind down mid-run — they are already
        orphans of a finished shard, and the acceptance boundary says none may
        survive. The graceful TERM-then-grace path stays where it belongs, in
        `shutdown()`, where a run is being abandoned while shards are still
        legitimately working.

        The leader is still an unreaped zombie at the moment of the signal, so
        the group id cannot have been recycled onto anybody else's processes.
        Only after the group is cleared is the leader reaped and its ownership
        identity released.

        EVERY STATE MUTATION HERE FOLLOWS ITS SIDE EFFECT, which is review R3
        (2026-08-25T16:39:27Z). This method can be interrupted at any line: the
        SIGINT handler runs `shutdown()`, and `shutdown()` can only clean up
        what is still registered. The previous version popped the group BEFORE
        signalling it, so an interrupt landing in that window found nothing to
        signal and exited 130 with the descendant still running. The window was
        tiny and entirely real. The order below leaves no instant at which a
        descendant is both alive and untracked:

            groups[child] still set   -> shutdown() TERM/grace/KILLs the group
            signal issued, entry gone -> the group is already dead; a later
                                         handler has nothing left to do
            live[child] still set     -> shutdown() still reaps the leader
        """
        pgid = self.groups.get(child)
        if pgid is not None:
            # The side effect FIRST, while the group is still registered.
            self.signal_group(pgid, signal.SIGKILL)
            # Safe to forget only now: the fatal signal has been delivered, so
            # an interrupt from here on has nothing left to kill — and holding
            # a PGID past its leader's reaping is the reuse hazard R2 forbids.
            self.groups.pop(child, None)
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass
        return child.returncode

    def group_of(self, child):
        """This child's process group, recorded while it is certainly alive.

        `start_new_session=True` makes the child its own group leader, so the
        group id IS the child's pid; `getpgid` is asked anyway and the pid is
        the fallback, because reading it back is what proves the child really
        got its own group rather than inheriting the runner's.
        """
        try:
            return os.getpgid(child.pid)
        except (ProcessLookupError, PermissionError):
            return child.pid

    def signal_group(self, pgid, which):
        """Signal ONE group this runner created. Never anything else."""
        try:
            os.killpg(pgid, which)
        except (ProcessLookupError, PermissionError):
            # The group is already empty. That is the goal, not a failure.
            pass

    # -- the bounded scheduler -----------------------------------------------

    def drive(self, work, jobs, label):
        """Run `work` items at most `jobs` at a time, and DRAIN THEM ALL.

        A failing item never abandons its siblings: the phase's verdict is
        decided after everything scheduled has finished, because a partial
        parallel result is not comparable with the serial baseline it has to
        stand against.
        """
        queue = list(work)
        total = len(queue)
        for index, item in enumerate(queue):
            item["err"] = self.result_root / f"{label.replace(' ', '-')}-{index:05d}.err"
        done = []
        started = 0
        while queue or self.live:
            while queue and len(self.live) < jobs:
                item = queue.pop(0)
                item["started"] = time.monotonic()
                child = self.suite.spawn(item["argv"], item["err"])
                # REGISTRATION IS NOT INTERRUPTIBLE WORK (R4). A signal landing
                # anywhere in here is only recorded, so these two lines always
                # complete and the checkpoint below sees the real picture.
                self.live[child] = item
                self.groups[child] = self.group_of(child)
                started += 1
                self.note(f"[{label}] start {started}/{total} {item['label']}")
            # Safe point: everything spawned above is registered. This is also
            # the check that covers an IDLE scheduler, since the sleep path
            # below comes straight back around to it.
            self.checkpoint()
            finished = [child for child in self.live if self.has_exited(child)]
            if not finished:
                time.sleep(0.01)
                continue
            for child in finished:
                # The child stays registered in `live` ACROSS retirement (R3):
                # an interrupt part-way through must still find a leader to
                # reap. It is released only once retirement has returned.
                item = self.live[child]
                item["returncode"] = self.retire(child)
                self.live.pop(child, None)
                item["stderr"] = item["err"].read_text(encoding="utf-8", errors="replace")
                item["elapsed"] = time.monotonic() - item["started"]
                done.append(item)
                # STDERR, and only stderr. A duration is the one thing about a
                # shard that is different every run, so putting it in stdout
                # would cost the byte-identical comparison that makes jobs=1
                # and jobs=32 checkable against each other. It belongs in the
                # progress stream, where finding the long pole is what it is
                # for.
                self.note(f"[{label}] done  {len(done)}/{total} {item['label']}"
                          f" rc={child.returncode} in {item['elapsed']:.2f}s")
            # Safe point: every retirement above ran to completion, so no group
            # is half-released and no leader is half-reaped.
            self.checkpoint()
        return done


# -- collection ---------------------------------------------------------------


def collect(run, jobs, modules=None, label="collect"):
    """Exact test ids for every parallel module, gathered by child processes.

    W384870: the same child collection serves the serial and supervised
    registries when a run is ACCOUNTED, so the expected set is every id the
    tree declares and not only the parallel ones. Collection imports; it
    selects nothing to run.
    """
    root = run.result_root
    work = []
    for module in (run.suite.parallel if modules is None else modules):
        out = root / f"{label}-{module}.json"
        work.append({"label": module, "module": module, "out": out,
                     "argv": ["collect-one", module, str(out)]})
    done = run.drive(work, jobs, label)
    ids = []
    for item in sorted(done, key=lambda one: one["label"]):
        # The child's own recorded reason first: it names the import that
        # failed, where a returncode and a stderr tail often name nothing.
        if item["out"].exists():
            answer = json.loads(item["out"].read_text(encoding="utf-8"))
            if answer.get("error"):
                raise RunnerRefusal(f"collecting {item['label']} failed: {answer['error']}")
            if item["returncode"] == 0:
                ids.extend(answer["ids"])
                continue
        raise RunnerRefusal(f"collecting {item['label']} failed "
                            f"(rc={item['returncode']}): {item['stderr'].strip()[:500]}")
    return ids


# -- phases -------------------------------------------------------------------


def shard_work(run, shards, kind):
    work = []
    for index, shard in enumerate(shards):
        plan = run.result_root / f"{kind}-{index:05d}.plan.json"
        report = run.result_root / f"{kind}-{index:05d}.report.json"
        plan.write_text(json.dumps({"ids": shard["ids"], "report": str(report)}), encoding="utf-8")
        work.append({"label": shard["label"], "ids": shard["ids"], "report": report,
                     "argv": ["run-shard", str(plan)]})
    return work


def harvest(item):
    """One shard's structured outcome, or a synthetic one if it never wrote it.

    A child that is killed, faults in the interpreter or dies before writing
    its report is a FAILURE of that shard and says so. Treating a missing
    report as an absence of failures is how a runner reports green for tests it
    never actually ran.
    """
    if item["report"].exists():
        answer = json.loads(item["report"].read_text(encoding="utf-8"))
        answer["label"] = item["label"]
        answer["returncode"] = item["returncode"]
        if item["returncode"] != 0 and answer.get("ok"):
            answer["ok"] = False
            answer["errors"] = list(answer.get("errors", [])) + [
                {"id": item["label"], "trace": f"shard reported success but exited {item['returncode']}"}]
        return answer
    trace = item["stderr"].strip() or f"the shard process exited {item['returncode']} without a report"
    return {"label": item["label"], "ids": item["ids"], "ran": 0, "ok": False,
            "failures": [], "skipped": [], "expected_failures": [], "unexpected_successes": [],
            "errors": [{"id": item["label"], "trace": trace}],
            "returncode": item["returncode"]}


def present(results, heading, out):
    """The deterministic half of the output: sorted, and free of durations."""
    print(f"--- {heading} ---", file=out)
    for answer in results:
        verdict = "pass" if answer["ok"] else "FAIL"
        count = answer["ran"]
        print(f"[{verdict}] {answer['label']} ({count} tests)", file=out)
    broken = [answer for answer in results if not answer["ok"]]
    if broken:
        print(f"--- {heading}: failures ---", file=out)
        for answer in broken:
            for kind in ("errors", "failures"):
                for one in answer.get(kind, []):
                    print(f"=== {kind[:-1].upper()}: {one['id']} ===", file=out)
                    print(one["trace"].rstrip(), file=out)
    ran = sum(answer["ran"] for answer in results)
    failures = sum(len(answer.get("failures", [])) for answer in results)
    errors = sum(len(answer.get("errors", [])) for answer in results)
    skipped = sum(len(answer.get("skipped", [])) for answer in results)
    ok = all(answer["ok"] for answer in results)
    print(f"[{heading}] {len(results)} shards, {ran} tests, {failures} failures, "
          f"{errors} errors, {skipped} skipped -> {'OK' if ok else 'FAILED'}", file=out)
    return {"shards": len(results), "ran": ran, "failures": failures, "errors": errors,
            "skipped": skipped, "ok": ok}


# -- W384870: exact test-identity accounting and the composed supervised step --


def module_of(test_id):
    """`package.module.Class.method` -> `package.module` (also for `setUpClass (x.y.Z)`)."""
    text = test_id.split(" (")[0]
    parts = text.split(".")
    if len(parts) >= 2 and parts[-2][:1].isupper():
        return ".".join(parts[:-2])
    return ".".join(parts[:-1]) if len(parts) > 1 else text


FIXTURE_EVENT = re.compile(r"^(setUpClass|tearDownClass|setUpModule|tearDownModule) \(")


def is_fixture_event(test_id):
    """`setUpClass (pkg.mod.Class)` and its kin: an outcome of a FIXTURE, not of a test."""
    return bool(FIXTURE_EVENT.match(test_id))


def base_id(test_id):
    """FALLBACK ONLY, for a report entry that carries no structural `parent`.

    A subtest id carries ` [message]` and/or ` (member=...)`; the accounted
    identity is its test. The runner's own reports bind the parent
    structurally (`subject_of`), so this text rule is reached only for a
    report produced by something else. A fixture event's parenthesis names the
    class or module it belongs to and is kept whole.
    """
    if is_fixture_event(test_id):
        return test_id
    for marker in (" [", " ("):
        if marker in test_id:
            test_id = test_id.split(marker)[0]
    return test_id


def subject(entry):
    """(accounted id or None, is_fixture) for one report entry, structure first."""
    if "parent" in entry:
        return entry["parent"], bool(entry.get("fixture"))
    if is_fixture_event(entry["id"]):
        return None, True
    return base_id(entry["id"]), False


def account(collected, reports, optional=OPTIONAL_SKIPS):
    """collected == executed, every executed id with exactly one outcome.

    Nothing here trusts a count: `passed` is DERIVED from the ids that ran
    minus the ids that did anything other than pass, and the run is OK only
    when passed plus OPTIONAL skips is exactly the collected set.
    """
    expected = set(collected)
    owners = {}
    failed, errored, expected_failures, unexpected = set(), set(), set(), set()
    skipped, fixture_skipped, fixture_errors = {}, {}, {}
    stray_errors = []
    for answer in reports:
        for one in answer.get("executed", []):
            owners.setdefault(one, []).append(answer["label"])
        for one in answer.get("failures", []):
            parent, fixture = subject(one)
            if fixture or parent is None:
                fixture_errors[one["id"]] = one["trace"].rstrip().splitlines()[-1][:200] if one["trace"].strip() else ""
            elif parent not in expected:
                stray_errors.append(one["id"])
            else:
                failed.add(parent)
        for one in answer.get("errors", []):
            parent, fixture = subject(one)
            if fixture or parent is None:
                fixture_errors[one["id"]] = one["trace"].rstrip().splitlines()[-1][:200] if one["trace"].strip() else ""
            elif parent not in expected:
                stray_errors.append(one["id"])
            else:
                errored.add(parent)
        for one in answer.get("skipped", []):
            parent, fixture = subject(one)
            if fixture or parent is None:
                fixture_skipped[one["id"]] = one["reason"]
            else:
                skipped[parent] = one["reason"]
        expected_failures.update(base_id(one) for one in answer.get("expected_failures", []))
        unexpected.update(base_id(one) for one in answer.get("unexpected_successes", []))
    executed = set(owners)
    duplicates = sorted(one for one, labels in owners.items() if len(labels) > 1)
    unaccounted = sorted(expected - executed)
    uncollected = sorted(executed - expected)
    optional_skipped = {one: why for one, why in sorted(skipped.items()) if one in optional}
    required_skipped = {one: why for one, why in sorted(skipped.items()) if one not in optional}
    # A class-level skip the owner classified optional (by its fixture id)
    # makes the tests it never started OPTIONAL too, by the class prefix.
    optional_fixtures = {one for one in fixture_skipped if one in optional}
    optional_prefixes = tuple(one[len("setUpClass ("):-1] + "." for one in optional_fixtures if one.startswith("setUpClass ("))
    not_started_optional = sorted(one for one in unaccounted if one.startswith(optional_prefixes)) if optional_prefixes else []
    unaccounted = sorted(set(unaccounted) - set(not_started_optional))
    for one in not_started_optional:
        optional_skipped[one] = "not started: " + fixture_skipped[next(f for f in optional_fixtures if one.startswith(f[len("setUpClass ("):-1] + "."))]
    required_fixture_skips = {one: why for one, why in sorted(fixture_skipped.items()) if one not in optional}
    passed = sorted(executed - failed - errored - set(skipped) - expected_failures - unexpected)
    ok = not (failed or errored or duplicates or unaccounted or uncollected or required_skipped
              or required_fixture_skips or fixture_errors or unexpected or stray_errors)
    ok = ok and set(passed) | set(optional_skipped) == expected
    return {"collected": sorted(expected), "executed": sorted(executed), "passed": passed,
            "optional_skipped": optional_skipped, "required_skipped": required_skipped,
            "fixture_skipped": dict(sorted(fixture_skipped.items())), "fixture_errors": dict(sorted(fixture_errors.items())),
            "failed": sorted(failed), "errors": sorted(errored), "stray_errors": sorted(stray_errors),
            "expected_failures": sorted(expected_failures), "unexpected_successes": sorted(unexpected),
            "duplicates": duplicates, "unaccounted": unaccounted, "uncollected": uncollected, "ok": ok}


def present_accounting(ledger, out):
    print("--- accounting ---", file=out)
    for one, why in ledger["optional_skipped"].items():
        print(f"[optional skip] {one}: {why}", file=out)
    for one, why in ledger["required_skipped"].items():
        print(f"[REQUIRED SKIP] {one}: {why}", file=out)
    for one, why in ledger["fixture_skipped"].items():
        print(f"[FIXTURE SKIP] {one}: {why}", file=out)
    for one, why in ledger["fixture_errors"].items():
        print(f"[FIXTURE ERROR] {one}: {why}", file=out)
    for kind in ("duplicates", "unaccounted", "uncollected", "stray_errors", "unexpected_successes"):
        for one in ledger[kind]:
            print(f"[{kind.upper()}] {one}", file=out)
    n, p, k = len(ledger["collected"]), len(ledger["passed"]), len(ledger["optional_skipped"])
    print(f"collected {n}, executed {len(ledger['executed'])}, passed {p}, optional skipped {k}, "
          f"required skipped {len(ledger['required_skipped'])}, failed {len(ledger['failed'])}, "
          f"errors {len(ledger['errors'])}, fixture skips {len(ledger['fixture_skipped'])}, "
          f"fixture errors {len(ledger['fixture_errors'])}, duplicates {len(ledger['duplicates'])}, "
          f"unaccounted {len(ledger['unaccounted'])}", file=out)
    print(f"[accounting] passed {p} + optional skipped {k} = {p + k} of collected {n} "
          f"-> {'OK' if ledger['ok'] else 'FAILED'}", file=out)


def resolve_supervisor(locator, root):
    """`baton:work/records/...py` -> the file, under THIS checkout's repository root."""
    prefix, _, relative = locator.partition(":")
    repository = pathlib.Path(root).resolve().parents[1]
    if prefix != "baton":
        raise RunnerRefusal(f"supervisor locator root {prefix!r} is not this repository")
    path = (repository / relative).resolve()
    if repository not in path.parents or not path.is_file():
        raise RunnerRefusal(f"supervisor {locator} is not a file under {repository}")
    return path


def supervise(run, entry, index, ids, retain, out):
    """ONE supervised module through its reviewed supervisor, as one report.

    The supervisor owns the body and the cleanup; this runner owns the
    accounting: the module's collected ids are executed only when the
    supervisor exits 0 and its body ran every one of them to OK.
    """
    missing = [name for name in SUPERVISED_ENVIRONMENT.get(entry["module"], ()) if not os.environ.get(name)]
    if missing:
        raise RunnerRefusal(f"supervised {entry['module']} needs {missing} in the environment")
    supervisor = resolve_supervisor(entry["supervisor"], run.suite.root)
    home = pathlib.Path(retain) if retain else run.result_root
    run_dir = home / f"supervised-{index:02d}" / "run"
    run_dir.parent.mkdir(parents=True, exist_ok=False)
    command = [sys.executable, "-W", "error", str(supervisor),
               "--python", sys.executable, "--run-dir", str(run_dir)]
    print(f"[supervised] {entry['module']} via {entry['supervisor']} ({entry['work']})", file=out)
    started = time.monotonic()
    trace = ""
    try:
        completed = subprocess.run(command, cwd=str(run.suite.root), env=run.suite.environment(),
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   timeout=SUPERVISOR_TIMEOUT_SECONDS)
        returncode = completed.returncode
        trace = completed.stdout.decode("utf-8", "replace")[-4000:] + completed.stderr.decode("utf-8", "replace")[-4000:]
    except subprocess.TimeoutExpired as expired:
        returncode = -1
        trace = f"supervisor exceeded {SUPERVISOR_TIMEOUT_SECONDS}s: {expired}"
    elapsed = time.monotonic() - started
    body = run_dir / "body.log"
    body_text = body.read_text(encoding="utf-8", errors="replace") if body.exists() else ""
    ran = re.search(r"^Ran (\d+) tests? in", body_text, re.M)
    # `unittest` prints its verdict line after `Ran N tests`; the body may
    # print its own evidence afterwards, so the verdict is searched for, not
    # assumed to be the last line.
    verdict = re.search(r"^OK(?: \(.*\))?$", body_text[ran.end():], re.M) if ran else None
    body_ok = bool(ran) and int(ran.group(1)) == len(ids) and verdict is not None and "skipped" not in verdict.group(0)
    ok = returncode == 0 and body_ok
    run.note(f"[supervised] done {entry['module']} rc={returncode} in {elapsed:.2f}s")
    answer = {"label": entry["module"], "ids": list(ids), "executed": list(ids) if ok else [],
              "ran": int(ran.group(1)) if ran else 0, "ok": ok, "failures": [], "skipped": [],
              "expected_failures": [], "unexpected_successes": [], "returncode": returncode,
              "errors": [] if ok else [{"id": entry["module"],
                                        "trace": f"supervisor rc={returncode}; body:\n{body_text[-3000:]}\n{trace}"}]}
    return answer


def main(argv=None, suite=None, out=sys.stdout, progress=sys.stderr):
    parser = argparse.ArgumentParser(prog="parallel_test",
                                     description="Run the safe v12 source tests across available CPUs.")
    parser.add_argument("--jobs", default=None,
                        help="lower the worker count; a whole number from 1 to the host's "
                             "available CPUs. Omitted means all of them.")
    parser.add_argument("--phase", choices=("all", "parallel", "serial"), default="all",
                        help="explicit scoped phase; all (default) refuses while supervised acceptance is uncomposed")
    parser.add_argument("--print-ids", action="store_true",
                        help="print scoped collected IDs without running them; supervised entries require explicit --phase parallel")
    parser.add_argument("--root", default=None, help=argparse.SUPPRESS)
    parser.add_argument("--group", default=None,
                        help="W384870: run exactly one logical group (" + ", ".join(GROUPS) + ")")
    parser.add_argument("--account", action="store_true",
                        help="W384870: exact test-identity accounting; collected ids must equal executed ids, "
                             "and any skip outside the optional registry fails the run")
    parser.add_argument("--with-supervised", action="store_true",
                        help="W384870: compose the supervised registry through its reviewed supervisor (requires --phase all)")
    parser.add_argument("--keep-going", action="store_true",
                        help="W384870: run the serial and supervised phases even after a failed parallel phase")
    parser.add_argument("--summary", default=None,
                        help="W384870: write the JSON accounting ledger to this path")
    parser.add_argument("--retain", default=None,
                        help="W384870: keep supervised run directories under this directory instead of the disposable result root")
    options = parser.parse_args(argv)

    if suite is None:
        suite = Suite(options.root or ROOT, PARALLEL_MODULES, SERIAL_MODULES, supervised=SUPERVISED_MODULES)
    run = Run(suite, options.jobs, progress=progress)

    previous = {}
    for number in (signal.SIGINT, signal.SIGTERM):
        previous[number] = signal.getsignal(number)
        signal.signal(number, run.record_signal)

    def phases():
        nonlocal suite
        suite.check_registry()
        suite.check_groups()
        if options.group:
            suite = run.suite = suite.restricted(options.group)
            print(f"[group] {options.group}: {len(suite.parallel)} parallel, {len(suite.serial)} serial, "
                  f"{len(suite.supervised)} supervised modules", file=out)
        suite.check_selection(options.phase, options.print_ids, options.with_supervised)
        if suite.supervised and not options.with_supervised:
            print(f"[scope] {options.phase} only; supervised not selected: {suite.supervised_description()}", file=out)
        run.open_result_root()
        # Collection is bounded by the same worker count, and by the module
        # count rather than the shard count that does not exist yet.
        jobs = resolve_jobs(options.jobs, run.detected, len(suite.parallel))
        ids = collect(run, jobs) if options.phase != "serial" else []
        suite.check_collected_ids(ids)
        shards = partition(ids, suite.method_split) if ids else []
        expected = list(ids)
        supervised_ids = {}
        if options.account and options.phase != "parallel" and suite.serial:
            serial_ids = collect(run, resolve_jobs(options.jobs, run.detected, len(suite.serial)),
                                 modules=suite.serial, label="collect-serial")
            suite.check_collected_ids(serial_ids)
            expected.extend(serial_ids)
            print(f"[collect-serial] {len(suite.serial)} serial modules -> {len(serial_ids)} tests", file=out)
        if options.with_supervised:
            for entry in suite.supervised:
                found = collect(run, 1, modules=(entry["module"],), label="collect-supervised")
                supervised_ids[entry["module"]] = found
                expected.extend(found)
            print(f"[collect-supervised] {len(suite.supervised)} supervised modules -> "
                  f"{sum(len(v) for v in supervised_ids.values())} tests", file=out)
        reports = []
        stopped = False

        if options.print_ids:
            for one in sorted(ids):
                print(one, file=out)
            return 0

        summaries = {}
        if options.phase != "serial":
            jobs = resolve_jobs(options.jobs, run.detected, len(shards))
            print(f"[collect] {len(suite.parallel)} parallel modules -> {len(ids)} tests "
                  f"in {len(shards)} shards", file=out)
            print(f"[parallel] jobs={jobs} (available CPUs {run.detected})", file=out)
            done = run.drive(shard_work(run, shards, "parallel"), jobs, "parallel")
            results = sorted((harvest(item) for item in done), key=lambda one: one["label"])
            reports.extend(results)
            summaries["parallel source"] = present(results, "parallel source", out)
            if not summaries["parallel source"]["ok"] and not options.keep_going:
                # The canonical gate's fail-fast ORDERING, preserved: a broken
                # source phase does not get to spend a Docker daemon's time.
                # W384870: the accounting below still runs, so the ids that
                # never executed are named rather than merely implied.
                print("[summary] parallel source FAILED; the serial registry did not run", file=out)
                stopped = True
        if options.phase != "parallel" and not stopped:
            serial = [{"label": module, "ids": [module]} for module in suite.serial]
            print(f"[serial] {len(serial)} source modules, one at a time", file=out)
            done = run.drive(shard_work(run, serial, "serial"), 1, "serial")
            results = sorted((harvest(item) for item in done), key=lambda one: one["label"])
            reports.extend(results)
            summaries["serial source"] = present(results, "serial source", out)
        if options.with_supervised and suite.supervised and not stopped:
            results = [supervise(run, entry, index, supervised_ids[entry["module"]], options.retain, out)
                       for index, entry in enumerate(suite.supervised)]
            reports.extend(results)
            summaries["supervised source"] = present(results, "supervised source", out)
        line = " | ".join(f"{name}: {one['ran']} tests, "
                          f"{one['failures'] + one['errors']} failed, {one['skipped']} skipped"
                          for name, one in summaries.items())
        ok = all(one["ok"] for one in summaries.values())
        if not stopped:
            print(f"[summary] {line} -> {'OK' if ok else 'FAILED'}", file=out)
        if options.account:
            ledger = account(expected, reports, suite.optional_skips)
            ledger["groups"] = suite.group_counts(expected)
            ledger["phases"] = summaries
            ledger["ok"] = ledger["ok"] and ok
            print("[groups] " + ", ".join(f"{name}={count}" for name, count in ledger["groups"].items()), file=out)
            present_accounting(ledger, out)
            if options.summary:
                pathlib.Path(options.summary).write_text(json.dumps(ledger, indent=1, sort_keys=True) + "\n",
                                                         encoding="utf-8")
            ok = ledger["ok"]
        return 0 if ok else 1

    try:
        code = phases()
    except RunnerRefusal as refusal:
        print(f"[runner] refused: {refusal}", file=out)
        code = 2
    except Interrupted as stopped:
        run.note(f"[runner] signal {stopped.number}; terminating "
                 f"{len(run.live)} live shards")
        print(f"[runner] interrupted by signal {stopped.number}", file=out)
        code = 128 + stopped.number
    finally:
        # RECORDING STAYS ARMED THROUGH CLEANUP, and the handlers are restored
        # only afterwards. Restoring first would give a signal arriving during
        # `shutdown()` the caller's default disposition — which for SIGINT
        # raises KeyboardInterrupt straight through the middle of the bounded
        # cleanup, abandoning the kill pass and the result root. The review's
        # rule is that a second signal need not bypass bounded cleanup; this is
        # what makes that true rather than merely intended. The signal is not
        # lost: it is recorded, and the check below reports it.
        try:
            run.shutdown()
        finally:
            for number, handler in previous.items():
                signal.signal(number, handler)

    # A signal recorded but never reached by a checkpoint — one that arrived
    # while the last phase was finishing, or during cleanup itself — must not
    # be silently converted into a successful exit (R4). A run that already
    # FAILED keeps its own code: the failures are the more informative answer,
    # and 1 is not a success being papered over.
    if code == 0 and run.pending_signal is not None:
        print(f"[runner] interrupted by signal {run.pending_signal} during cleanup",
              file=out)
        code = 128 + run.pending_signal
    return code


# -- the child modes ----------------------------------------------------------
#
# Both run in a fresh interpreter with the source tree's own PYTHONPATH. This
# is the ONLY place a test module is ever imported.


def collect_one(module, out):
    answer = {"module": module, "ids": [], "error": None}
    try:
        suite = unittest.TestLoader().loadTestsFromName(module)
        for test in iterate(suite):
            name = type(test).__name__
            if name in ("_FailedTest", "ModuleImportFailure"):
                # Fail closed. A module that cannot be imported must not be
                # collected as "one test that will fail somewhere later".
                raise RunnerRefusal(f"{module} could not be loaded: {test.id()}")
            answer["ids"].append(test.id())
        # W384870: a `TestCase` imported into this module's namespace is
        # collected again under ITS OWN module's id, so the same test would run
        # twice and the accounting would see a duplicate. Name the cause here,
        # at the module that binds the stranger, rather than as a bare
        # duplicate downstream.
        foreign = sorted({one.rsplit(".", 1)[0] for one in answer["ids"] if not one.startswith(module + ".")})
        if foreign:
            raise RunnerRefusal(f"{module} binds test classes defined elsewhere, which unittest would run "
                                f"twice; import their module instead: {foreign}")
    except Exception as trouble:
        answer["error"] = f"{type(trouble).__name__}: {trouble}"
    pathlib.Path(out).write_text(json.dumps(answer), encoding="utf-8")
    return 0 if answer["error"] is None else 1


def iterate(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from iterate(item)
        else:
            yield item


class StartedResult(unittest.TextTestResult):
    """A TextTestResult that also remembers which test ids actually began."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.started = []

    def startTest(self, test):
        self.started.append(test.id())
        super().startTest(test)


def subject_of(test):
    """The STRUCTURAL identity of one outcome, never parsed from its text.

    W384870 review R1: a subtest's id is `parent [message] (params)`, and the
    first ledger recovered the parent by cutting the text at ` (` -- which left
    a message-only subtest failure under a synthetic id and its parent PASSED.
    `unittest` knows the parent: a `_SubTest` carries `test_case`; a fixture
    event (`setUpClass (pkg.Class)`) is an `_ErrorHolder` with no test behind
    it. Both facts are read from the objects, and the full id is kept beside
    them for the diagnostics.
    """
    case = getattr(test, "test_case", None)
    if case is not None:
        return {"id": test.id(), "parent": case.id(), "fixture": False}
    fixture = type(test).__name__ == "_ErrorHolder" or not hasattr(test, "_testMethodName")
    return {"id": test.id(), "parent": None if fixture else test.id(), "fixture": fixture}


def run_shard(plan_path):
    plan = json.loads(pathlib.Path(plan_path).read_text(encoding="utf-8"))
    # The runner's own text output is discarded on purpose: the parent presents
    # this shard from the STRUCTURED report below, in sorted order, so a stream
    # written at completion time could only reintroduce the nondeterminism the
    # whole design removes.
    loaded = unittest.TestLoader().loadTestsFromNames(plan["ids"])
    # W384870: the exact ids this shard STARTED, recorded by the result as each
    # test begins. Not the loaded plan: a class whose setUpClass skips or
    # errors starts none of its tests, and B0's first ledger counted those as
    # passed because it trusted the plan. `loaded` is kept for the record.
    loaded_ids = [test.id() for test in iterate(loaded)]   # before running: a run suite drops its tests
    result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0,
                                     resultclass=StartedResult).run(loaded)
    answer = {"ids": plan["ids"], "loaded": loaded_ids,
              "executed": list(result.started), "ran": result.testsRun, "ok": result.wasSuccessful(),
              "failures": [dict(subject_of(test), trace=trace) for test, trace in result.failures],
              "errors": [dict(subject_of(test), trace=trace) for test, trace in result.errors],
              "skipped": [dict(subject_of(test), reason=why) for test, why in result.skipped],
              "expected_failures": [subject_of(test)["parent"] or test.id() for test, _ in result.expectedFailures],
              "unexpected_successes": [subject_of(test)["parent"] or test.id() for test in result.unexpectedSuccesses]}
    pathlib.Path(plan["report"]).write_text(json.dumps(answer), encoding="utf-8")
    return 0 if answer["ok"] else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "collect-one":
        raise SystemExit(collect_one(sys.argv[2], sys.argv[3]))
    if len(sys.argv) > 1 and sys.argv[1] == "run-shard":
        raise SystemExit(run_shard(sys.argv[2]))
    raise SystemExit(main(sys.argv[1:]))
