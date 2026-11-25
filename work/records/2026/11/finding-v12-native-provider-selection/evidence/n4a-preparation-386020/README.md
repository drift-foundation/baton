# N4a implementation preparation — E386020

Prepared by baton.codxpc, role impl, 2026-11-24, under E386019. This is a bounded implementation packet, not an implemented or qualified adapter. It makes the independent preparation concrete without editing K's pending shared implementation. No product file, test expectation, registry, image, credential or provider was changed or executed.

Current base: `317351e73c92749e201f536ba115c9fdf213077d`. Product input bytes match that checkpoint; current DESIGN includes later owner rulings and is captured separately. `START.json` binds initial source identities and positions; `INPUTS.json` binds exact N3 evidence and contracts. The earlier M386015 routing blocker is resolved by E386019/E386020. **K confirmed the ownership seam in M386022**, record `OWNERSHIP-N4A-DELIVERY-2026-11-24.md`, SHA256 `f0f41390b152f40b45090606e8954a683b651002440523e0d61ba363a512d16c`; acknowledged M386024. See the retained ownership record and HANDOFF.json for final positions. This confirms allocation and sequencing, not approval of D's pending whole contract.

## One deliverable and its boundaries

Implement the Codex **fresh implementation** realization, adapter subclass, validated/reaping entrypoint and production recipe source using the observed 0.169.0 arguments and version output. Reuse the existing workspace, verification, publication, result and retained-home owners. Return an exact candidate and focused deterministic evidence for independent review; no host import or Git mutation is included.

This preparatory packet does not select a build, engine run, credential read, real provider turn, native use, resume implementation or W385853's pending whole contract. N4b parsing and contributor sources require retained exact-build real-turn output or separately selected Q1. Until that evidence exists, keep the Codex participation list empty and attribution missing; unknown output cannot become a successful provider result. No fabricated success fixture or event-name table belongs in N4a.

## Evidence-backed invocation

`ARGV-PROPOSAL.json` is a data proposal, not installed configuration. The proposed argv is:

```text
codex exec --dangerously-bypass-approvals-and-sandbox --ignore-user-config --ignore-rules --json --model <explicit selection> <one prompt operand>
```

Every named option is present in the retained exact-image exec help. `--model` gets the explicit composition selection; no real selector or mapped identity is guessed here. The existing subprocess owner supplies candidate cwd and stdin DEVNULL, so no new `--cd`, `--skip-git-repo-check` or stdin channel is needed. Use the existing provider log rather than adding `--output-last-message` and a second mutable output path. Do not use ephemeral, resume, fork, alternate-provider, trust or worktree operands.

These flags are advertised by the exact build, not exercised together in a turn. `--ignore-user-config` says auth still uses CODEX_HOME; the selected environment remains composed and must not inherit host CODEX_HOME or API-key variables. Help for `--ignore-rules` concerns execpolicy files, not a promise to exclude AGENTS.md. K's execution-context label governs instruction applicability.

The observed version is exactly `codex-cli 0.169.0\n`. Pin this as a version fixture, with the source path and digest from INPUTS. Do not treat it as turn-output evidence.

## Concrete implementation seams

Locations below were read at the pinned product bytes; they identify responsibilities, not permission to edit shared files before allocation.

| Owner | Confirmed current behavior | Bounded N4a direction |
| --- | --- | --- |
| `worker/claude_agent.py:1966`, provider hooks | Class already separates program, argv, version, terminal and home seams | Add a Codex subclass; inherit ordinary task/workspace/verification/publication behavior. Refuse unsupported provider, role, build, legacy and context-bound Codex selections before provider effects. |
| `claude_agent.py:2255` version probe, parsing near 2298 | Bounded reader accepts a bare semantic version or the Claude Code suffix; rejects the observed Codex prefix | Extract only a provider-specific version-decoding hook; keep bounded I/O, timeout, stdin and output limits unchanged. Claude default preserves its exact current behavior; Codex accepts only the evidenced format and selected pin. Coordinate this small shared edit with K. |
| `claude_agent.py:5361` `_prepared_home` | New selection uses adapter credential path/mode but still takes the delivered slot from module constant `CREDENTIAL_SLOT = "claude"` | Make the delivered-slot selection provider-specific through one bounded hook or the agreed closed adapter field. Preserve legacy Claude slot behavior. Do not silently seed Codex from Claude credentials. |
| `provider_policy/__init__.py` | Only Claude realization; fixed dogfood entrypoint; managed entries empty | Add the Codex realization and provider-specific entrypoint only in the allocated shared slice. Preserve shared policy equality, adapter reconstruction, exact digests and missing participation. Reuse K's label/entry implementation after its selected interface exists. |
| `worker/dogfood_entry.py` | `supervised(run=...)` owns PID1 forwarding/reaping; `_production(build=...)` validates launch before constructing the agent | New `codex_entry.py` composes these existing seams with CodexAgent. No copied worker loop or new supervisor. Bind the new image entrypoint in the adapter. Reject a role/provider mismatch before construction where the existing validation seam permits, and always before invocation. |
| `claude_agent.py:2005` `provider_terminal` | Exit 0 currently returns success regardless of record shape | Codex must override this: absent qualified terminal evidence returns a bounded `unclassified` failure, never success from exit 0. Host attribution separately remains missing. Preserve actual process status; a zero process exit and failed semantic interpretation are distinct. |
| `claude_agent.py:5074`, `provider_policy/attribution.py` | One bounded raw record and Claude-shaped contributor parser | Keep capture and raw digest retention; do not implement JSONL terminal selection or Codex participation in N4a. Unknown/synthetic records may prove refusal only. N4b must revisit stream bounds and raw-evidence binding. |
| `claude_agent.py:4915` activity | Retained selected homes get unknown baseline, not a scan | Preserve unknown activity; no invented Codex session path or native transcript collector. No retained-home conversation-resume claim. |
| `tools/pool.py:685`, `tools/single_worker.py` | Existing role/deployment admission accepts shared provider selections | Enforce Codex implementation/fresh-only at composition and revalidation, including hand-authored documents. A subclass guard alone does not establish host admission refusal. Allocate these edits before implementation. |

## Home and instruction facts still needed

N3 proves that the selected help/version commands start with HOME at `/run/baton/provider-home`, and that writable HOME gets `.codex/tmp/arg0-linux` aliases. Help with read-only HOME succeeds with a warning. It proves neither turn-mode writable-home necessity nor auth, instruction or session filenames.

Keep these separate:

- **Selected policy:** one retained home per canonical authority/Job/worker; subscription seed copied once, refreshed copy retained; no host credential changes; exact managed entries only. N2 already implements the generic ownership, seeding and replacement behavior.
- **Missing provider facts:** credential filename, instruction entry target supported by the pending delivery contract, session layout and turn output. The JSON proposal leaves these paths null. Null is a preparation marker and must never be admitted as production configuration.
- **N4a integration requirement:** before enabling a complete Codex realization, retain an accepted exact-build source or selected bounded investigation establishing the necessary credential/managed-entry targets. No credentials, offline container or model call is selected here to fill that gap. Credential registry reference and actual model selection remain later owner execution inputs.

I1/I2 auto-loading observations remain informational per M386011. Do not recreate them as native-use gates: the label can name the managed document. But the current W385853 contract still calls for a pinned-evidence home target; resolve that exact target through the agreed interface rather than writing an invented path. Lack of turn output blocks N4b, not evidence-backed argv and entry/recipe preparation.

## File ownership and join

| Confirmed allocation | Paths | State |
| --- | --- | --- |
| Codxpc independent new files | `v12/worker/codex_agent.py`, `codex_entry.py`, `Dockerfile.codex`; dedicated Codex test modules; optional factory seam in `dogfood_entry.py` | Confirmed M386022; none written in this preparation. |
| D's eventual implementer owns instruction implementation; K coordinates | `provider_policy` label and packaged instruction bytes; `v12/python/pyproject.toml`; Claude prompt/home integration; manager label ending/status; delivery docs/shared tests | No overlap written. Whole-contract approval and implementer assignment remain pending; K explicitly holds no implementation claim. |
| N4a shared part follows D's imported checkpoint | `provider_policy/__init__.py` realization/entrypoint; named Claude version/credential hooks; own registry entries; own section of `v12/PROVIDER-SELECTION.md` | D first, N4a second, confirmed M386022. Hooks named in M386024 before any edit. No competing private shared-file candidates. |
| Additional allocation still required | Composition/revalidation role guards in `tools/pool.py` / `tools/single_worker.py` | Neither slice owns these by default. Need named in M386024; do not write before allocation. |

Independent implementation can prepare new Codex files against the pinned base, but joined acceptance must consume D's exact reviewed interface/base and recheck the shared diff. Do not merge competing private changes by accident, duplicate D's label implementation or authorize protected-main import. Consume the accepted shared result. A directory or containment relationship is not a dependency edge. M386022 permits direct preparatory tests before the registry join; this packet instead adds no product test module, preserving the repository rule that each new product module has exactly one execution registry and group when introduced. Any future staging of unregistered test drafts must not claim an accounted product run.

No new Work or graph edge was created in this preparation. W385830 remains the owning Work. If later slices are separately scheduled, the authorized handler installs and reads back the actual dependency relationships before dependent execution; the prose table is not a scheduling mechanism.

## Recipe direction

Use `v12/worker/Dockerfile.claude` as the source-layout reference, not the minimal N3 instrumentation recipe as a production image. Retain the Node 22 trixie family, trust store, Git/Python/verifier dependencies, UID65532, verifier root scaffold and exact layout marker. Carry the same worker/schema, refusal, capture, source-profile, provider-policy, verification-context and supervisor dependencies, plus CodexAgent and Codex entry. Install exact `@openai/codex@0.169.0`; keep Claude's pin 2.1.247 unchanged. No host home, credential, fixture provider or source checkout is copied into either image.

Retain a source-only file list and pin checks for review. Image construction, image-content proof and CLI execution are N5/selected engine work. A syntactically valid Dockerfile does not prove buildability. Coordinate one joined production packaging/qualification after the accepted instruction delivery, rather than building during preparation.

## Focused deterministic acceptance for implementation

Planned groups: `manager-pure` and `tools-pure`; no engine, packaged or full-suite selection. Proposed new modules `tests.manager.test_codex_agent`, `tests.manager.test_codex_entry`, and a source-only recipe module each belong to one PARALLEL_MODULES entry and manager-pure; add a focused composed-selection class in tools-pure after allocating that shared test file. Never reuse another module's TestCase classes. New names and registry writes are proposals, not present tests.

1. Trace every option and the exact version fixture to INPUTS; provenance absence/mismatch fails. Fake model identifiers prove argv transport only.
2. Exact argv is one prompt operand with explicit model, no shell interpolation, stdin DEVNULL and candidate cwd. No fallback/resume/provider substitution or ambient secret environment.
3. Codex version-prefix parsing accepts the retained output; wrong build, malformed, oversized, partial or unavailable version fails safely. Legacy Claude version behavior remains unchanged.
4. Composition and worker revalidation refuse Codex review, legacy/context selection and provider mismatch without a provider call. A hand-authored deployment cannot bypass the role guard.
5. Entry refuses invalid launches before adapter construction; valid launch uses CodexAgent and the existing supervisor; signal/exit behavior is inherited and verified at its seam.
6. Reuse real home owners with **synthetic seed bytes only**, labelled simulated. Show correct delivered slot, one-time seed, preserved refreshed value, separate Job/worker homes, existing-owner exclusion and no outward credential copy. Do not claim vendor acceptance of a synthetic filename.
7. Once K's accepted delivery is joined: every selected Codex invocation carries the same role label, same packaged worker bytes and digest binding; tampered/missing/oversized delivery refuses; legacy prompts remain unchanged.
8. Exit 0 with empty, malformed, oversized, partial or synthetic unknown output never yields Codex semantic success or matched attribution. Preserve actual exit status and bounded raw-evidence capture. No positive Codex terminal fixture exists in N4a.
9. Source-only recipe checks cover pin, entry, dependency COPY set, nonroot user and verifier marker. Actual image contents/version are separately selected N5 checks.
10. Run focused legacy Claude/policy/entry regression coverage for changed shared hooks. Retain log, collected/executed accounting, source identity, command/interpreter and measured timing per TESTING.md. Existing `test_dogfood_image` is manager-engine; do not invoke it as part of this deterministic selection.

Use supported `just test-one` for exact new/affected tests and `just test-group manager-pure` or `tools-pure` only when the selected change warrants the whole group. This packet runs no product tests and changes no registry. Its provenance check is a preparation check, not coverage of these ten behaviors.

## Handoff condition

Preparation is complete when this bounded packet, exact input identities, ownership request/status and explicit missing provider facts are retained and checked. Implementation acceptance is separate: finite candidate manifest/base/path modes, completed focused evidence, independent review, and explicit remaining N4b/qualification limitations. No broad supervisor refactor, new credential mechanism or weaker attribution is proposed.

Next bounded milestone: implement the disjoint N4a candidate under the confirmed ownership, retaining the named missing-input boundaries; join shared changes only after D's accepted/imported checkpoint and the named role-guard allocation. Do not replay N3, select N4b or demand another approval merely for ordinary in-scope deterministic work. When a required missing fact genuinely prevents a specific implementation operation, report that operation and source requirement precisely.
