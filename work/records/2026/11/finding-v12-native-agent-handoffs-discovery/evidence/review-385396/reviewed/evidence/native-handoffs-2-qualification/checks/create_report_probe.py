"""What the supported `manager create` command itself REPORTS on its own
stream about the native routing and the reviewer's answering grant.

W385331 qualification round 4 (review 2026-11-21T01-49-15Z): the create
helper must not open the Authority store; this probe demonstrates the one
supported surface that carries the routing and the per-Work `answer-handoff`
grant -- the create command's own installer report (`bootstrap.prepare`
through `creation_ports.NewJobBinding`, on the command's stderr). It reuses
the accepted connected-creation fixture (real installer, real command, a
stand-in runtime; no engine, no live provider) and captures that stream.

    cd v12/python && env PYTHONPATH=src:tools TMPDIR=… BATON_V12_STACK_TEST_ROOT=… \
        <prepared python> -m unittest -v create_report_probe -k test_the_report
"""
import contextlib
import io
import json
import os
import pathlib

from tests.tools import test_connected_creation as accepted

OUT = pathlib.Path(os.environ.get("CREATE_REPORT_PROBE_OUT", "/var/tmp/baton-v12-handoffs-2/tmp"))


class TheCreateCommandReportsRoutingAndTheAnsweringGrant(accepted.TheNativeRoutingThroughTheRealInstaller):

    def test_the_report_on_the_command_stream_names_routing_and_the_grant(self):
        from baton_v12.job_manager import role_contract

        self.installed(jobs=[], line_declared_base="a" * 40,
                       canonical_target_id="target-1",
                       native_handoff_routing=dict(self.ROUTING))
        report = io.StringIO()
        with contextlib.redirect_stderr(report):
            code, said = self.created(template=role_contract.HANDOFF_TEMPLATE,
                                      control_profile="native-handoff/1")
        self.assertEqual(code, 0, said)
        answer = json.loads(said)
        lines = report.getvalue().splitlines()
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "create-report-probe.stdout.json").write_text(said)
        (OUT / "create-report-probe.stderr.log").write_text(report.getvalue())
        # THE SUPPORTED REPORT: the routing selection, the Work created on the
        # implementation route, and the answering grant in that Work's own
        # scope -- with the product's own statement that no review grant was
        # made for the reviewer.
        # (formats are `bootstrap._compose`'s own: "routing%-14s reviewer …" with
        # an empty pad, so fifteen spaces; the Work line says "already exists;
        # left alone" because the command reserved the Work BEFORE its installer
        # preparation ran, which is what the report then finds)
        self.assertIn("routing%-14s reviewer %s, decisions to %s"
                      % ("", self.ROUTING["reviewer"], self.ROUTING["decision_recipient"]), lines)
        self.assertIn("work  %-14s already exists; left alone" % answer["work_id"], lines)
        self.assertIn("grant %-14s approve/review/verify/integrate in its own scope" % answer["work_id"], lines)
        self.assertIn("answer%-14s answer-handoff to %s in its own scope; no review grant"
                      % ("", self.ROUTING["reviewer"]), lines)
        self.assertEqual(answer["template"]["version"], role_contract.HANDOFF_TEMPLATE)
        self.assertEqual(answer["control"]["profile"], "native-handoff/1")
        # AND THE REPORT IS TRUE, by the accepted test's own assertion -- here
        # only to tie the printed line to the fact once; the helper reads the
        # report, never the store.
        from baton_v12.authority import messages
        authority = self.authority()
        scope = authority.project_work(answer["work_id"])["scope"]
        self.assertTrue(authority.holds_capability(self.ROUTING["reviewer"], messages.ANSWER_CAPABILITY, scope=scope))
        self.assertFalse(authority.holds_capability(self.ROUTING["reviewer"], "review", scope=scope))
