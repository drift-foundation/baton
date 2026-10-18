# W321528 — honest retained-candidate and effective-timeout reporting

Implement in your isolated checkout at base 3dcf6dc4bcee97e932d17c93ac13c5811b3af188. No host edits,
live providers, Docker, timeout-policy changes, launcher redesign or integration.

Two observed defects: single-implementation-proof/baseline.py _proposals skips
noncompleted dispositions before reading frozen artifacts, so actual sealed failed
candidates are reported absent. v12/worker/claude_agent.py result publishers write
PROVIDER_SECONDS3600 even when _invoke runs with effective600/900 seconds.
Revalidate these paths and v12/DESIGN.md OBS-2 and DB-1/DB-4 before editing.

Required outcome: independently report execution disposition, validated retained
candidate availability/locator, verification state and acceptance state. A failed
attempt stays failed even when it retained a candidate. Validate artifact ownership,
manifest/reference/digest and declared base through existing owner APIs; malformed,
missing, foreign or mismatched evidence must not become a valid candidate claim.
Avoid filesystem access inside store transactions. Never invent acceptance or
formal verification, clear cleanup uncertainty, retry or import. Never expose
credentials or raw provider transcripts. Preserve historical evidence files.

Report actual effective provider timeout rather than the default constant for
all affected result publishers (Git-line, directory and review). Distinguish default
from explicit selection where supported by current bounded input. Prefer one
resolved source of truth for execution and reporting; do not alter timeout semantics.
Do not hardcode600/900 based on the two historic examples.

Suggested starting points: baseline._proposals/_workload/_attributions and
claude_agent._invoke and result publishers (currently seconds_bound at2123,2148,
2258). These are evidence locations, not an exclusive files-to-edit list. The
composer and old historical runs remain pinned; modifications to the supervisor
in this candidate are proposed future bytes, not a modification of the live runner.

Use deterministic replay/fake-provider tests. Cover successful candidate; failed
with candidate; failed without candidate; no frozen result; malformed/missing/foreign
custody or wrong base; unreadable observation; partial/absent verification and
unaccepted candidate; effective explicit and default bounds in affected publishers.
Keep failure and cleanup/uncertainty behavior intact. Outcome formatting must never
make retained artifacts count as successful completion merely because present.
Existing frozen_output_of/load_manifest and custody APIs should own validation;
locators alone and unchecked worker claims are insufficient evidence.

Focused verification imports test_baseline from its canonical dossier and five
claude_agent test classes (FailureIsHonest, ThePositiveTurnWritesTheDeclaredProposal,
ThePreparedLineTurnCommitsAndDeclaresItsObjects, NoUsableReportIsNoVerdictAtAll,
TheReviewTurnAuthorsAVerdictItDidNotDecide). Add required cases to these selected
suites so the frozen command covers them. Use Python3.13/jsonschema and complete
repository source. Tests use real private Git fixtures under their supported
boundary, fake engine/provider only; no live execution. If fixture context is
missing, report it rather than weaken assertions or silently skip cases.

STOP once required focused/affected checks pass. Do not discover the whole Python
tree, run a broad suite for reassurance, or start a test command longer than the
remaining provider time. W319114's second provider timed out after starting a
3000-second whole-tree command despite96 focused and978 affected tests passing.
Return promptly with a concise summary, exact tests/results and limitations so
adapter verification and artifact handback can execute. No self-approval. Retain
exact base/head/tree, complete paths and binary patch. On inability, return an
honest partial result; no automatic retry is selected.
