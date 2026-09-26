# W265097 implementation checkpoint

2026-09-25 UTC, baton.tuner claim265127; owner handoff265124. Complete current
events read through265127 and T265097 through265097, no pending obligations.

Implemented one aggregate `just provider-checks [CONFIG]`, stdlib helper
`tools/provider_checks.py`, focused fake-CLI suite `tools/test_provider_checks.py`
and usage/setup document `docs/PROVIDER-CHECKS.md`. Exact path ownership recorded
in FINDING before implementation. No protocol/application edits. Helper validates
user-local JSON before execution; uses explicit per-account homes; removes known
ambient auth/backend overrides from child copies; independently labels saved
login/live structured results; continues failures and aggregates exit status;
bounds output/time and terminates process groups. No raw provider output printed.

Verification command:
`python3 -B -W error::ResourceWarning -m unittest discover -s tools -p test_provider_checks.py -v`.
Initial 8-case run: 7 passed, real just-entrypoint test failed because inherited
XDG runtime directory /run/user/1000/just was read-only in this managed context.
No provider ran. Corrected test runner to use its own writable temporary XDG
runtime directory, retaining the actual just recipe and argv. This is a runner
prerequisite correction, not a Baton workaround or permission escalation.
Initial measured unittest duration2.335s. Second run: all8 pass; final measured
duration recorded below. Covers fake Codex/Claude both homes, paths with spaces
and literal shell metacharacters, mixed quota/auth/malformed responses, missing
CLI/home/config, process-group timeout/SIGTERM cleanup and output cap. Real
provider commands used only --help; no login status/live request/auth mutation.

Limitations: fake-CLI coverage does not assert live account availability; human
invocation selects that. CLI-owned auth/keychain mapping and normal live refresh
are outside helper control. Unsupported flags/schema are reported unsuccessful;
no silent fallback. Local group termination does not attest remote cancellation.
No Git mutation. Ready for independent review via baton.bug, then owner; routine
corrections remain within recorded implementation scope.

Final second run: 8 tests passed in2.390s; total measured unittest time4.725s
including the initial runner failure. No live verification.

Candidate SHA256 (independent reviewer should recheck before running):

- `justfile`: `7e3d00dce043dba0a4da1d04e02f884009e71de354a55e71ff9fa6cc29140830`
- `tools/provider_checks.py`: `63bfa7fc75a5e885cefc4ef8cd6c3297119f30ac7e5367b34d349bd5260d1844`
- `tools/test_provider_checks.py`: `c66dbd6845c06330c353f26e781835cb858931862c4d86605be7ecb99951b022`
- `docs/PROVIDER-CHECKS.md`: `2227a128d3de6dd86e46b52927a569c5b3d8dae5945f90c137c72dc2a55c2b17`

## 2026-09-25 — correction awaiting review, claim266039

Owner266036 selects the host Claude discrepancy correction. Read events through
266039 and existing T265097 through265140 (detail confirms no newer discussion).
Read current scope/PLAN and full prior review-2026-09-25T10-55-23Z.md.

Corrected Claude argv to terminate options explicitly before PROMPT. Installed
Claude2.1.263 help confirms --mcp-config <configs...>; read-only binary string
inspection confirms that spelling and the Invalid MCP configuration diagnostic.
No actual Claude invocation beyond help and no account/auth read was performed.
The fake now uses argparse with the documented greedy variadic option/optional
positional grammar. Negative control removes -- from actual helper argv: fake
refuses Invalid MCP configuration before any response; corrected argv succeeds.
This demonstrates the documented grammar mismatch; the owner's actual stderr
was not retained here, so sole-cause attribution and live correction remain
for owner confirmation. Argparse models the relevant grammar; it is not the
installed native Claude parser.

The direct owner command and helper are deliberately not otherwise identical:
helper retains tools/skills/hooks/MCP suppression, settings isolation, ephemeral
output, temporary cwd and known ambient credential filtering; direct command
used permission-mode plan. Home selection was already explicit and unchanged.
No evidence justifies reverting isolation controls or assuming default-Claude
availability from the direct ACP result.

Added fixed MCP/settings/options invocation-error categories and exit-code/
documentation guidance for unknown failures; no raw offending values are printed.
New tests exercise safe local errors and successful text containing error words;
existing quota/auth/aggregation/Codex/timeouts/account isolation remain covered.
No test assertions removed. New behavior is tested inside the existing aggregate
just fake as well as the old-vector negative control.

Exact focused command unchanged:
python3 -B -W error::ResourceWarning -m unittest discover -s tools -p test_provider_checks.py -v
Result:10 passed in2.452s, no skipped tests. Author measured total now7.177s;
prior reviewer2.605s remains separate. No live provider/auth mutation, v12 edit,
broad suite or Git mutation. Only helper, author test, docs and owning dossier
updated; justfile unchanged. Return baton.bug then owner; owner live-confirmation
command: just provider-checks, using the existing private default inventory.

Corrected candidate SHA256:

- `justfile`: `7e3d00dce043dba0a4da1d04e02f884009e71de354a55e71ff9fa6cc29140830`
- `tools/provider_checks.py`: `d3ab09f5179e086e8708aaa952b97922fe235ef59a24b4036082a809c7c85138`
- `tools/test_provider_checks.py`: `c014931c6e5f1330cc9f37a670b8644bd71ca8f3b6239319d6f99a03bc6f8a0d`
- `docs/PROVIDER-CHECKS.md`: `169e1f7be42e368d5632ed07cbc256e9b8437ffd531ebfaf9bebd211b924eabd`
