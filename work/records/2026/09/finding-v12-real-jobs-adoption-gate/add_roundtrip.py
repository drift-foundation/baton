"""Add the shipped-template CLI roundtrip cases to test_two_jobs.py. Run once."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
CASES = '''class TheSHIPPEDTemplateComposesThroughTheACTUALCLI(ArrangedCase):
    """The roundtrip review 2026-09-23T17:17:50Z asked for, end to end.

    THE SHIPPED FILE, not a synthetic one. `SELECTIONS-247941.json` is read as
    it ships, every `<OWNER: ...>` is resolved with a DISPOSABLE value taken
    from the accepted fixture, and `two_jobs.py` runs as a subprocess exactly
    as ADOPTION-247941.md step 3 prints it. Then the two documents it wrote go
    to the product's own readers.

    W239533 learned this at an owner's expense: every case in that suite wrote
    its own selections, so a template defect reached a live operator. A
    composer is only as good as the document an operator actually holds.
    """

    SHIPPED = os.path.join(HERE, "SELECTIONS-247941.json")

    def packet_root(self):
        held = os.path.join(self.root, "packet")
        os.makedirs(held, exist_ok=True)
        return held

    def resolved(self):
        """The shipped template with disposable operands, and nothing else."""
        import copy
        with open(self.SHIPPED, encoding="utf-8") as handle:
            document = json.load(handle)
        given = document["arrangement"]
        inherited = self.two_jobs()
        workers = {one["worker_id"]: one for one in inherited["workers"]}
        producer = workers["implementation-worker"]["deployment"]
        reviewer = workers["review-worker"]["deployment"]
        instance = given["instance"]
        shape = self.composed_document()
        instance.update({
            "run_root": os.path.join(self.packet_root(), "declared"),
            "authority_store": producer["authority_store"],
            "authority_uuid": producer["authority_uuid"],
            "job_store": os.path.join(self.packet_root(), "jobs.sqlite3"),
            "integration_store": self.integration_store,
            "state_root": self.state_root,
            "workspace_storage": producer["workspace_storage"],
            "launch_home": producer["launch_home"],
            "credential_home": producer["credential_home"],
            "credential_sources": producer["credential_sources"],
            "credential_slots": producer["credential_slots"],
            "credential_profile": producer["credential_profile"],
            "provider_network": producer["network"],
            "retention_policy_digest": producer["retention_policy_digest"],
            "retention_disposition": producer["retention_disposition"],
            "policy_digest": producer["policy_digest"],
            "adapter_name": producer["adapter_name"],
            "adapter_digest": producer["adapter_digest"],
            "engine": producer["engine"],
            "image_digest": producer["image_digest"],
            "workspace_group": producer["workspace_group"],
            "workspace_capacity": producer["workspace_capacity"],
            "launch_contract": producer["launch_contract"],
            "review_route": producer["review_route"],
            "reviewed_route": reviewer["review_route"],
            "checkpoint_profile": shape["checkpoint_profile"],
            "policy_generation": self.fixture_policy,
            "integration_profile": copy.deepcopy(shape["integration_profile"]),
            "receipt_participants": copy.deepcopy(
                shape["receipt_participants"]),
            "job_work_id": self.work, "review_work_id": self.work,
            "line_declared_base": self.base,
            "canonical_target_id": inherited["job_bindings"][0][
                "canonical_target_id"],
            "submission_id": "two-job-packet",
        })
        for one, binding in zip(given["jobs"], inherited["job_bindings"]):
            source = workers[binding["source_worker_id"]]["deployment"]
            judge = self.reviewer_for(binding, workers)
            held = judge["deployment"]
            one.update({
                "job_id": binding["job_id"],
                "work_id": binding["job_work_id"],
                "producer_worker_id": binding["source_worker_id"],
                "reviewer_worker_id": judge["worker_id"],
                "producer_participant": source["participant"],
                "reviewer_participant": held["participant"],
                "implementation_principal": source["principal"],
                "review_principal": held["principal"],
                "nominated_source": source["nominated_source"],
                "declared_base": binding["line_declared_base"],
                "task_document": source["task_document"],
                "canonical_target_id": binding["canonical_target_id"],
                "input_digest": source["input_manifest"]["manifest_digest"],
                "test_scope": ["v12/python/tests/job_manager"],
                "profile_name": source["profile_name"],
                "profile_digest": source["profile_digest"],
                "review_profile_name": held["profile_name"],
                "review_profile_digest": held["profile_digest"],
                "implementation_input_manifest": source["input_manifest"],
                "review_input_manifest": held["input_manifest"],
            })
        place = os.path.join(self.packet_root(), "resolved-selections.json")
        with open(place, "w", encoding="utf-8") as handle:
            json.dump(document, handle, indent=2, sort_keys=True)
        return place, document

    def bound_environment(self):
        return dict(os.environ, PYTHONDONTWRITEBYTECODE="1",
                    PYTHONPATH=os.pathsep.join(
                        [os.path.join(CHECKOUT, "v12/python/src"),
                         os.path.join(CHECKOUT, "v12/python"), HERE]))

    def composing(self, selections, into):
        import subprocess
        return subprocess.run(
            [sys.executable, "-B", os.path.join(HERE, "two_jobs.py"),
             "--selections", selections, "--into", into],
            capture_output=True, text=True, timeout=300, cwd=os.sep,
            env=self.bound_environment())

    def composed_packet(self):
        place, _ = self.resolved()
        into = os.path.join(self.packet_root(), "run")
        return self.composing(place, into), into

    def test_the_shipped_template_still_asks_every_operand_by_name(self):
        """Otherwise this class would resolve fields nobody ships."""
        with open(self.SHIPPED, encoding="utf-8") as handle:
            given = json.load(handle)["arrangement"]
        for name in two_jobs.INSTANCE_OPERANDS:
            with self.subTest(operand=name):
                self.assertIn(name, given["instance"])
        for index, one in enumerate(given["jobs"]):
            for name in two_jobs.JOB_OPERANDS:
                with self.subTest(job=index, operand=name):
                    self.assertIn(name, one)

    def test_the_documented_command_writes_both_documents(self):
        answer, into = self.composed_packet()
        self.assertEqual(answer.returncode, 0,
                         f"stdout={answer.stdout}\\nstderr={answer.stderr}")
        printed = json.loads(answer.stdout)
        self.assertEqual(sorted(printed),
                         ["deployment.json", "submission.json"])
        for name in printed:
            with self.subTest(document=name):
                self.assertTrue(os.path.exists(os.path.join(into, name)))

    def test_the_written_deployment_is_the_one_the_product_accepts(self):
        answer, into = self.composed_packet()
        self.assertEqual(answer.returncode, 0, answer.stderr)
        with open(os.path.join(into, "deployment.json"),
                  encoding="utf-8") as handle:
            deployment = json.load(handle)
        from tools import stage_execution
        self.assertEqual(deployment["schema"],
                         stage_execution.MULTI_CONFIG_SCHEMA)
        self.assertEqual(deployment["correction_policy"],
                         stage_execution.DECLINE_CORRECTION)
        self.assertEqual(len(deployment["workers"]), 4)
        stage_execution.held_configuration(deployment, checkout=self.checkout)

    def test_the_written_submission_is_one_the_public_reader_accepts(self):
        """R1's second half: the reader refused it for two missing members."""
        from baton_v12.job_manager import submit
        answer, into = self.composed_packet()
        self.assertEqual(answer.returncode, 0, answer.stderr)
        with open(os.path.join(into, "submission.json"),
                  encoding="utf-8") as handle:
            document = json.load(handle)
        job, _control = self.stores("packet-submission")
        submit(job, document)
        for one in document["jobs"]:
            with self.subTest(job=one["job_id"]):
                self.assertEqual([stage["kind"] for stage in one["stages"]],
                                 ["implementation", "review"])
                self.assertIn("test_scope", one)
                self.assertIn("terminal_policy", one)

    def test_an_unresolved_template_is_refused_by_name(self):
        into = os.path.join(self.packet_root(), "refused")
        answer = self.composing(self.SHIPPED, into)
        self.assertNotEqual(answer.returncode, 0)
        self.assertIn("not resolved", answer.stderr + answer.stdout)
        self.assertFalse(os.path.exists(into))


def load_tests(loader, standard, pattern):'''


def main():
    place = HERE / "test_two_jobs.py"
    body = place.read_text(encoding="utf-8")
    if "TheSHIPPEDTemplateComposesThroughTheACTUALCLI" in body:
        print("already added")
        return 0
    body = body.replace(
        "HERE = os.path.dirname(os.path.abspath(__file__))\n"
        "if HERE not in sys.path:",
        "HERE = os.path.dirname(os.path.abspath(__file__))\n"
        "CHECKOUT = os.path.dirname(os.path.dirname(os.path.dirname(\n"
        "    os.path.dirname(os.path.dirname(HERE)))))\n"
        "if HERE not in sys.path:")
    body = body.replace("def load_tests(loader, standard, pattern):", CASES, 1)
    place.write_text(body, encoding="utf-8")
    print("added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
