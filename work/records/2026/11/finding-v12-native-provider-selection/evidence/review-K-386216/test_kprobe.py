"""K review probes for candidate 4033a352 (synthetic provider/engine only)."""
import json, os, traceback
from tests.tools import test_stage_execution as T
from tests.tools.test_stage_execution import ComposedOneJobCase, TheComposedJobTraversesReviewAndAcceptance, stage_execution
OUT = os.environ["K_OUT"]
def note(name, value):
    with open(os.path.join(OUT, name + ".json"), "w") as f: json.dump(value, f, indent=1, sort_keys=True, default=repr)

class K(ComposedOneJobCase):
    tick = TheComposedJobTraversesReviewAndAcceptance.tick
    def route(self, **doc):
        from baton_v12.authority import Authority
        from baton_v12.authority.messages import ROUTING_SCHEMA
        a = Authority.open(self.authority_path, expected_authority_uuid=self.config["authority_uuid"])
        try: a.set_policy("native_handoff_routing", dict({"schema": ROUTING_SCHEMA}, **doc))
        finally: a.dispose()
    def uncertain(self, report, routing=dict(reviewer="baton.reviewer", decision_recipient="baton.slaw")):
        held = self.implemented()
        if routing: self.route(**routing)
        self.drive(held.job, held.composed, "review", "waiting")
        held.review = self.only_attempt(held.composed, "review")
        self.code = self.turn(held.control, "review", held.review, self.mounted(held.composed, "review", held.review), edits={"review-report.json": json.dumps(report) if not isinstance(report, str) else report})
        return held
    def facts(self, held):
        from baton_v12.job_manager import review_uncertainty, status
        from baton_v12.worker_manager import review_cycles
        from tests.job_manager import fixtures
        line = held.composed.deployment.line()["line_id"]
        return dict(items=review_uncertainty.items_of(held.job), states=self.states(held.job, held.composed),
            integration=review_cycles.integration_checkpoint(held.control, line), starts=len(self.engine.starts),
            status=status(held.job, held.composed, observed_at=fixtures.NOW)["jobs"][0])
    def run_ticks(self, held, n=6):
        seen = []
        for _ in range(n):
            try: seen.append(self.tick(held))
            except Exception as e: seen.append(dict(exception=type(e).__name__, text=str(e)[:600]))
        return seen
    GOOD = {"schema": "baton.review-uncertainty/1", "findings": "Unresolved; ask the owner."}

    def test_a_hold_no_relaunch(self):
        held = self.uncertain(self.GOOD)
        before = len(self.engine.starts)
        ticks = self.run_ticks(held)
        f = self.facts(held)
        note("a", dict(before=before, ticks=ticks, facts=f, engine=[k for k in dir(self.engine) if not k.startswith("__")], turn=self.code))
        self.assertEqual(f["starts"], before); self.assertEqual(len(f["items"]), 1)
        self.assertIsNone(f["integration"]); self.assertNotEqual(f["states"]["review"], "completed")
        self.assertNotIn("Unresolved", json.dumps(f["items"]))

    def test_b_recipient_changes_after_delivery(self):
        held = self.uncertain(self.GOOD)
        self.run_ticks(held, 3); first = self.facts(held)
        self.route(reviewer="baton.reviewer", decision_recipient="baton.other")
        ticks = self.run_ticks(held, 3); f = self.facts(held)
        note("b", dict(first=first["items"], ticks=ticks, facts=f))
        self.assertEqual(f["items"], first["items"]); self.assertIsNone(f["integration"])
        self.assertEqual(f["starts"], first["starts"])

    def test_c_reviewer_mismatch(self):
        held = self.uncertain(self.GOOD, routing=dict(reviewer="baton.elsewhere", decision_recipient="baton.slaw"))
        ticks = self.run_ticks(held, 3); f = self.facts(held); note("c", dict(ticks=ticks, facts=f))
        self.assertEqual(f["items"], []); self.assertNotEqual(f["states"]["review"], "completed"); self.assertIsNone(f["integration"])

    def variant(self, name, report):
        held = self.uncertain(report)
        before = len(self.engine.starts)
        ticks = self.run_ticks(held, 4); f = self.facts(held); note(name, dict(turn=self.code, ticks=ticks, facts=f, before=before))
        self.assertEqual(f["items"], []); self.assertNotEqual(f["states"]["review"], "completed"); self.assertIsNone(f["integration"])
        return f, before
    def test_e1_empty_findings(self): self.variant("e1", dict(self.GOOD, findings="  "))
    def test_e2_null_verdict_member(self): self.variant("e2", dict(self.GOOD, verdict=None))
    def test_e3_extra_member(self): self.variant("e3", dict(self.GOOD, retry=True))
    def test_e4_duplicate_keys(self): self.variant("e4", '{"schema":"baton.review-uncertainty/1","findings":"x","schema":"baton.review-report/1","verdict":"accepted"}')
    def test_e5_list(self): self.variant("e5", [self.GOOD])
    def test_e6_wrong_schema_no_verdict(self): self.variant("e6", {"schema": "baton.review-report/1", "findings": "x"})
