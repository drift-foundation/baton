# Provider account checks — W265097

## 2026-09-25 — confirmed owner interface and assignment

Owner requests one just task to check all configured Codex and Claude accounts, including multiple homes per provider. Owner rejects hardcoded personal home paths and approves assignment to Tuner. This supersedes the creation message reserving implementation to prompt and any primary interface requiring repeated per-account commands.

Selected primary interface: `just provider-checks` reads a user-local account list outside tracked source; an optional explicit configuration path is supported. Entries name provider, display label and optional provider configuration directory. No personal account inventory, absolute user paths or credentials belong in tracked source. Use HOME/XDG conventions for the default config locator; document the exact chosen location. An illustrative tracked example may use portable placeholders, never executable shell snippets. Missing configuration should show concise setup guidance, not guess private account locations or run an empty list successfully.

Check saved login status and one bounded live pong request for each configured account when the human invokes the task. Distinguish saved login from actual request availability and usage limits from authentication errors. Do not depend on exact model branding or exact one-word formatting for success. Report ambiguous results honestly. Continue through independent failures, label every account and return a nonzero aggregate status for failed/inconclusive checks. Bound each subprocess and clean up subprocesses on timeout/interruption. Never read or print credential files; use supported provider CLIs and preserve parent environment. Explicit account selection must not silently reuse another account's inherited provider home.

Tuner owns the justfile recipe, a small helper such as tools/provider_checks.py, necessary focused fake-CLI tests and usage documentation, plus this dossier. No existing implementation was created before interruption. Keep this a small operator convenience, not a provider framework or v12 adoption prerequisite. Validate argv/environment selection, paths containing spaces, mixed outcomes, missing CLI/config and timeout handling with fake CLIs. No live provider calls, login, token refresh command, daemon operation or Git mutation during author/reviewer verification. Human invocation of the finished task selects its live checks. Independent review through baton.bug, then owner.

## 2026-09-25 — owner excludes v12 credential checks

Owner confirms host CLI account checks only (the accounts used with current v11 tooling). V12 credential registries, profiles, injection, worker authentication and deployment-aware checking are explicitly out of scope. Host pong success must not be presented as v12 readiness. This clarifies and limits all earlier all-provider wording: all locally configured Codex/Claude host accounts, not every release credential mechanism. No v12 mode or preparation for it in this Work.

## 2026-09-25 — tuner implementation contract, claim265127

Use JSON at `${XDG_CONFIG_HOME:-$HOME/.config}/baton/provider-checks.json`,
optional `just provider-checks /path/to/config.json`. Schema: nonempty accounts
array, each with provider (`codex`/`claude`), unique printable label and optional
home (absolute or `~/...`); omitted home means HOME/.codex or HOME/.claude,
never an inherited alternate provider home. Validate the entire config before
any subprocess. Child environments remove known ambient provider credential/
endpoint/backend overrides, then set the selected provider home; parent unchanged.
Report fixed diagnostic categories, not raw CLI output or credentials. Login
and live results are separate; run both for every account even after a failed
login check. Successful live checks require structured successful terminal output
and a nonempty response, without matching model branding or literal pong.
Bound wall time and captured bytes; terminate the process group on timeout,
interruption or output overflow. Local CLI help consulted only (no login status
or provider request); tests use fake executables. Exact ownership: justfile,
tools/provider_checks.py, tools/test_provider_checks.py,
docs/PROVIDER-CHECKS.md and this dossier. No application/protocol edits.

## 2026-09-25 — future v12 diagnostic boundary agreed, not selected for implementation

Owner agrees the definitive v12 credential ping must run inside the selected worker Docker image using normal deployment credential selection/delivery and network configuration, with a bounded provider request and verified container/credential cleanup. A host pong cannot establish that path. Distinguish configuration validation from live provider availability; do not expose credentials in results.

This records a future requirement only. W265097 remains host-account checks only; no v12 implementation, live probe, additional adoption gate or runtime change is selected. Schedule a separate bounded Work if/when implementation is selected; do not expand Tuner's present assignment.

## 2026-09-25 — owner reports live Claude discrepancy; bounded correction selected

Observed by owner: just provider-checks returned login/live OK for both Codex homes, login OK for both Claude homes, but both Claude live checks failed (unclassified), aggregate exit1. After correcting a pasted LAUDE_CONFIG_DIR typo, owner confirmed the direct ACP command with CLAUDE_CONFIG_DIR and claude --print --permission-mode plan returned pong. This proves that direct ACP invocation worked then; it does not establish default-Claude availability or equivalence to the helper environment.

Hypothesis, not confirmed cause: helper commands places PROMPT directly after variadic --mcp-config and its JSON operand; the prompt may be parsed as another config. Revalidate CLI parsing and other argv/environment differences before asserting cause. Owner requests return to Tuner with this evidence. Earlier independent fake-CLI acceptance remains historical, but does not resolve this real discrepancy.

Selected correction: diagnose/fix the Claude invocation and add focused coverage that detects the actual failure instead of a fake that blindly accepts argv. Improve actionable failure diagnostics without printing raw provider output, credentials or account identity; classify local invocation failures separately where demonstrable and document remaining unknowns. Preserve Codex behavior, timeouts, account isolation, one aggregate command and host-only scope. No live provider calls or login/auth mutation by author/reviewer; give owner exact bounded live confirmation command after review.

## 2026-09-25 — bounded parser correction, tuner claim266039

Installed Claude2.1.263 help declares `--mcp-config <configs...>` and optional
positional prompt. Current helper leaves PROMPT inside that trailing variadic
option's operands. Correct it with an explicit `--` before the prompt. Test the
published grammar with an actual argument parser in the fake CLI, including the
old-vector negative control that consumes the prompt as a second config and
refuses. This demonstrates a mismatch with the documented command grammar;
it does not recover the owner's withheld stderr or prove that this was the sole
cause of both live failures. Real CLI execution remains help-only here.

Add safe fixed diagnostics for recognized MCP/settings/unsupported-option parser
errors and exit-code/context guidance for unknown failures. Never echo offending
values, paths or raw responses. No changes to account selection, Codex argv,
provider overrides, process limits or host-only scope. Existing review remains
historical; corrected candidate needs independent review and owner live confirmation.
