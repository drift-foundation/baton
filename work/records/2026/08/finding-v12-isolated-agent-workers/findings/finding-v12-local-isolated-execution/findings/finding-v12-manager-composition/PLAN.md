# Plan: complete the Python manager contracts inventory and public composition

The Job has two deliverables and they are not one cut. Each is claimed,
evidenced and reviewed on its own, which is what umbrella item 20 asked for.

1. [cut A; this round] **The real composition path, with the ACP
   client-capability consumer at its centre.** Ported from the frozen
   `agent_profile.mjs` and `agent_handshake.mjs` by obligation:
   - a `profiles` table in the manager's own control store, and the schema
     version bump that goes with it — a table arrives with the cut that gives
     it meaning;
   - `certify_agent_session_profile`, composing SHAPE, then the DOCUMENT SEAL,
     then POLICY, in that order and for the reasons the frozen module states:
     every later rule reads members, and a policy decision about a document
     whose bytes do not match its own digest is a decision about something
     nobody agreed to;
   - `certified_agent_session_profile`, reading one back with ALL THREE
     witnesses agreeing — what the document declares, what its canonical bytes
     recompute to, and the key it is filed under. Two of three is not
     agreement;
   - `check_client_capabilities`, §2.2's EXACT rule, reached from the
     certification path rather than exported beside it;
   - `negotiate_acp`, the exact wire-version match with no downgrade.
   W641's one canonical representation is preserved: `{"fs": {}, "terminal":
   false}`, absence is withholding, no synthesized explicit `false`.
2. [cut B; next round of this Job] **The contracts-package receiving
   inventory.** The analogue of `tests/manager/test_boundary_inventory.py` for
   `baton_v12.contracts`: the universe discovered from a structure that exists
   WHETHER OR NOT ANYBODY OWNED IT — the package's real public export set and
   every parameter of every exported operation — with one owner and one probe
   per entry, and the private-body path pinned structurally so a composite
   cannot quietly stop calling the rule it claims to compose.
3. [after cut B] Hand W1593 the boundary it is waiting for: it exercises its
   already-signed-off bounded exact-record diagnostic through
   `check_client_capabilities`' caller-local closed refusal pair, as
   black-box acceptance. W1593 does that in its own claim; this Job does not
   write W1593's acceptance for it.
4. [not this Job] §13's durable-secret rule and manifest retention. Named here
   only so their absence is deliberate.

---

1-done. [cut A delivered 2026-08-24] `handshake.py`, the `profiles` table at
   schema version 6, two new outbound contracts, and
   `validate_agent_session_fragment` over a SECOND definition table rather than
   one merged namespace. §2.2 is enforced AT EMISSION rather than on the
   certification path, because measurement showed the frozen schema already
   states it exactly for a profile-carried document and a rule repeated after
   the schema has spoken is the second live source of truth the schema's own
   prose warns about. Mutation 16/16 after three survivors each taught
   something. Gate 618 at source and 618 in the locked build.
   Evidence: `evidence/w6592-cut-a-composition-2026-08-24.txt`.

1-changes-requested. [independent review 2026-08-24] Preserve the delivered
   composition, but close two exact-type gaps before cut A can be signed off:
   refuse a Boolean wire answer rather than allowing `True == 1` to widen the
   frozen type-strict pin, and make `_offered` establish one exact built-in
   list whose members are text rather than accepting a record or silently
   dropping JSON non-text members. The additive review regressions are in
   `tests/manager/test_handshake.py`; focused evidence is
   `evidence/review-cut-a-exact-input-types-2026-08-24.txt`.
1-corrected. [re-review 2026-08-25] Both exact-type gaps pass their focused
   cases. One stateful certification gap remains: after A is replaced by B
   under the same profile ID, certifying A again must make A current rather
   than replay an old success whose effect is no longer present. Preserve the
   operation journal's historical truth without treating it as proof of
   current state. Also update `handshake.py`'s stale module narrative to say
   §2.2 is enforced at emission, matching the recorded decision and code.
   Regression and evidence:
   `tests/manager/test_handshake.py::OneProfileIsCertifiedInOneOrder::test_recertifying_prior_bytes_makes_them_current_again`
   and `evidence/review-cut-a-recertification-2026-08-25.txt`.
2-waiting. Cut B does not begin until cut A returns and is signed off.

2-superseded. [M6776, 2026-08-24] A second review round inside W6592 does not
   provide the independent claim, evidence, review and outcome required by
   umbrella item 20. W6592 now owns Cut A only. The contracts-package receiving
   inventory moves to its own W3-contained Job and canonical dossier; it does
   not wait here and must not be implemented under this claim.

## Final re-review — 2026-08-25

1. [done] Exact wire-version and exact capability-list input types.
2. [done] Current-state recertification after A → B → A, without historical
   journal replay substituting for the replaced effect.
3. [done] One current §2.2 placement at emission in code and module narrative.
4. [signed off] W6592 Cut A is complete. Contracts inventory remains W6782;
   downstream manager/session/security Works keep their independent scope.
