from pathlib import Path
import json,re
root=Path(__file__).resolve().parent
lines=(root/'base/AGENTS.md').read_text().splitlines()
# Every source line is assigned. Historical clauses are explicitly classified,
# never inferred as active merely because the baseline retained them.
ranges=[
(1,10,'shared','Git, files and recovery','Preserve required inputs/evidence; disk scratch and no blanket cleanup.'),
(11,39,'shared','Git, files and recovery','Protected main versus real disposable Git permission; no indirect mutation or live scope expansion.'),
(40,53,'host','Git, files and recovery','Protected Git inspection only; human index/history ownership; readiness does not grant mutations.'),
(54,55,'shared','Git, files and recovery','Avoid readability-only wrapping and indentation churn.'),
(56,63,'superseded','Verification and test authority','Per-test confirmation is replaced by standing test-change authority.'),
(64,88,'shared','Verification and test authority','All roles may change necessary tests; record reasons/ownership; independent expectations review; exact import and acceptance intact.'),
(89,114,'historical duplicate','Verification and test authority','Campaign-specific test authority folds into the unrevoked general standing rule; no revival of old approval limits.'),
(115,140,'shared/host','Product scope and development workflow','Normative DESIGN, owner-pinned specification, v12 versus later work, graph classification and one authority.'),
(141,162,'superseded with retained recovery','Product scope and development workflow','Optional-reuse release classification superseded; fresh isolated recovery and historical evidence retained, no silent rerouting.'),
(163,186,'shared','Product scope and development workflow','Reuse required for delivery but not initial adoption; no broad refactor/automatic integration selection.'),
(187,211,'shared','Verification and test authority','Focused cumulative seconds not a gate; sensible per-run limits, truthful durations, investigate resource uncertainty; scope unchanged.'),
(212,233,'shared','Verification and test authority','Deterministic providers at normal boundary; genuine live question and truthful evidence, no fake owner receipts.'),
(234,245,'host, later route corrections','Coordination and identity','Read protocol, explicit deployment, role identities; later route rulings determine current reviewer/implementer selection.'),
(246,254,'host, later route corrections','Coordination and identity','No hidden duplicate contexts; prompt non-routable; mapped runtime publisher. Sole codex reviewer superseded by rvpc routing.'),
(255,261,'host','Coordination and identity','Actionable operator commands, prerequisites, outcomes and boundaries without impersonation.'),
(262,284,'host','Review, decomposition, integration and checkpoints + docs/HOST-INTEGRATION.md','Distinct optional integrator; whole-set authority and exact reviewed test paths; refuse stale/mismatched/ambiguous review; no redesign/staging.'),
(285,294,'host','docs/HOST-INTEGRATION.md','Custody modes not checkout modes; non-symlink regular/base/owner-writable preflight; entire refusal before mutation; ops repair; final modes.'),
(295,304,'host','Claim, execution and handoff','One readiness path, act immediately, wait read-only, obligations/acknowledgments, rearm and no unattended completion.'),
(305,305,'host','Coordination and identity','Supported authority surfaces only; no raw SQLite reads or writes.'),
(306,317,'host','Coordination and identity','Prompt routine coordination within scope, owner spec decisions, graph relationships, no handler impersonation.'),
(318,325,'host','Permanent records and decisions','Shared methodology examples, no concrete recipes or transient identities; policy and exceptions in proper locations.'),
(326,334,'host','Permanent records and decisions','Pin confirmed decisions before edits; chronological finding/current plan; revalidate, explicit supersession; restart from records.'),
(335,338,'historical rationale','Permanent records and decisions','Historical motivation retained in baseline; no separate current instruction.'),
(339,354,'host, legacy superseded','Permanent records and decisions','Canonical permanent dossier layout replaces ephemeral lifecycle; no new legacy folders.'),
(355,379,'host','Permanent records and decisions','Permanent locators, repository-relative bindings, optional open indexes/lightweight Work, exactly one Work per dossier, terminal followups.'),
(380,399,'host','Permanent records and decisions + Review, decomposition, integration and checkpoints','Serial work and priority; record responsibilities; implementation-ready review evidence and claim revalidation.'),
(400,403,'host, reading narrowed later','Claim, execution and handoff','Read current record fresh and revalidate claims; targeted checkpoint policy supersedes indiscriminate historical reread.'),
(404,417,'host','Permanent records and decisions','Role-neutral discovery; child records, depth/promotion/forwarding, parent cannot close with open child.'),
(418,436,'host','Permanent records and decisions','Actual implementer owns append-only PROGRESS; reviewer journals immutable, handoff paths, ownership and standalone artifacts.'),
(437,470,'host','Review, decomposition, integration and checkpoints','Proactive bounded decomposition; pin outcomes and ownership, real graph gates, joined acceptance; no takeover/scope expansion or transplanting v11 to v12.'),
(471,486,'host','Claim, execution and handoff','Atomic exclusive claim, Route/Handler/Next distinction, scheduler phases and atomic pass release.'),
(487,500,'host','Coordination and identity + Claim, execution and handoff','Direct routine corrections, explicit destination, accepted owner delivery, no routine partial/continuation approval gate.'),
(501,523,'host','Claim, execution and handoff','Ordered concise handoffs, outcome-based verification, illustrative code paths not exclusive edit list, bounded milestone and exact interrupted checkpoint.'),
(524,542,'host','Claim, execution and handoff + Review, decomposition, integration and checkpoints','Current checkpoint/new discussion and obligations; expand if stale; durable supported context maintenance, no duplicate consumer or invented exhaustion.'),
(543,563,'host','Review, decomposition, integration and checkpoints','Required human major-milestone checkpoint; truthful proposed message and observed identity; recovery not acceptance; native continuity outcomes.'),
(564,571,'host, reading narrowed above','Claim, execution and handoff','Canonical detail and standalone claim before execution, complete current handoff and relevant new discussion, scope revalidation.'),
(572,581,'host','Claim, execution and handoff','Continue turn, never end claimed, incomplete route and checkpoint, canonical release verification, exceptional recovery.'),
(582,606,'host','Claim, execution and handoff + Git, files and recovery','Standalone exact operations; no escalation/stronger denial retries; optional cleanup restraint; preserve and relinquish blocked work.'),
(607,613,'host/shared','Permanent records and decisions','Log defects before workaround, distinguish misuse, stopgap not supported fix; no privileged bypass masking defects.'),
(614,621,'host, historical route revised','Coordination and identity','Separate rvpc reviewer identity/context; current review solely rvpc, codex registered outside route; no interruption/overwrite.'),
(622,625,'host','Review, decomposition, integration and checkpoints','Human plus agent default integration; managed integrator only selected, exact bytes and human Git preserved.'),
(626,629,'host','Coordination and identity','codxpc additional impl, baton.codx/implpc routing; exclusive own identity, no claim release or concurrent edits implied.'),
(630,657,'superseded execution mandate','Product scope and development workflow','v12-only development/no fallback mandate suspended; preserve scope, provenance, independent review and Git rules.'),
(658,670,'host','Execution context + Permanent records and decisions','Temporary specific exceptions in owning FINDING/PLAN, revalidate scope/lifetime; relocation does not revoke or revive.'),
(671,684,'shared/host','Product scope and development workflow','Useful parallel delivery without mandatory orchestration, disjoint ownership/dependencies and serial overlapping integration.'),
(685,694,'host','Product scope and development workflow','Native coordination target; bridge temporary, no permanent reporter investment, preserve one authority until explicit cutover.'),
(695,717,'host','Product scope and development workflow','Direct development selected, no orchestration packet gate; no extra live/install/claim/Git authority, safe transitions.'),
(718,745,'shared','Verification and test authority','Mandatory TESTING guide, groups/prepared interpreter, selected full run, exact required accounting and registries; transient evidence stays dossier.')]
covered=[n for a,b,*_ in ranges for n in range(a,b+1)]
assert covered==list(range(1,len(lines)+1))
# Subdivide at paragraph boundaries and at individual list items so every rule
# is addressable, including multi-clause source bullets.
rows=[]
for a,b,scope,destination,rule in ranges:
 start=a
 for n in range(a,b+2):
  boundary=n==b+1 or (n>start and (not lines[n-1].strip() or lines[n-1].startswith('- ')))
  if boundary:
   text='\n'.join(lines[start-1:n-1]).strip()
   if text: rows.append(dict(start=start,end=n-1,scope=scope,destination=destination,current_rule=rule,source=text))
   start=n
(root/'rule-matrix.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
out=['# Complete baseline rule preservation/classification matrix','',
'Baseline: `base/AGENTS.md`, all 745 source lines assigned; each paragraph/list item below is separately addressable. Destination headings refer to candidate AGENTS.md unless a document is named. Full source wording is retained in rule-matrix.json and the byte-identical baseline. This coverage check does not establish semantic equivalence: independent review must judge every mapped rule and the explicit supersessions.','',
'Worker scope: shared Git/isolation/verification/honest-evidence rules additionally appear in `docs/V12-WORKER-INSTRUCTIONS.md`; host v11 claim/dossier procedures intentionally do not. Worker permission is selected by this Work FINDING and DESIGN RUN-4/REV-5, not a source directory.','',
'Historical decision links are preserved below verbatim as locators, not active instructions. Relative targets resolve from the repository root as in the baseline.','',
'| Old lines | Scope/classification | Current rule / disposition | New location |', '| --- | --- | --- | --- |']
for r in rows:
 out.append(f"| {r['start']}–{r['end']} | {r['scope']} | {r['current_rule']} | {r['destination']} |")
out+=['','## Retained historical evidence locators','']
for link in re.findall(r'\[[^\]]+\]\([^\)]+\)', '\n'.join(lines)):
 if 'work/records/' in link: out.append('- '+link)
out+=['','## Specific supersessions checked','',
'- Lines 56–63 and the bounded campaign wording at 89–114 do not revive test approval gates; general standing authority at 64–88 governs.',
'- Optional reuse (141–162) is historical. Required reuse and fresh-context initial adoption (163–186) both survive.',
'- The blanket Git sentence at 555–556 is interpreted under the explicit protected-main/disposable ruling at 14–39; it cannot revoke disposable authority.',
'- The old codex-only/two-reviewer routing language is superseded by rvpc-only routing, without taking over claims.',
'- Whole-history reading requirements are narrowed by lines 524–538, without dropping pending obligations/new decisions.',
'- The v12-only/no-direct-fallback mandate is superseded by direct development at 695–717; native coordination remains the target.',
'- Required human major-milestone checkpoints remain host policy even though DESIGN OBS-5 uses non-gating product wording. No new continuation gate was added.',
'- Host child-dossier rules remain explicit; native DESIGN flat-storage semantics do not silently relocate host records.']
(root/'RULE-MATRIX.md').write_text('\n'.join(out)+'\n')
print('matrix',len(rows),'source blocks; 745 lines assigned exactly once')
