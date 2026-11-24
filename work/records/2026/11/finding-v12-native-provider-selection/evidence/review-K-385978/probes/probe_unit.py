"""Independent K review probes of W385965 candidate 2abcd544: pure functions, no harness of the candidate's.
Run with cwd=<tree>/v12/python, PYTHONPATH=src. Nothing here starts a provider, engine or container."""
import copy, hashlib, json, os, stat, sys, tempfile, unittest
from pathlib import Path
from baton_v12 import provider_policy as policy
from baton_v12.provider_policy import attribution, home as worker_home
from baton_v12.worker_manager import provider_home
from tools import next_run_bindings

SEL = dict(provider="claude", requested_model="sel-x", reported_identity="id-x", cli_build="2.1.247")


def delivery(attempt="a1", job="j1", worker="w1", **changes):
    selected = dict(SEL, **changes)
    v = next_run_bindings.deployment_identities(image_reference="i:r", image_digest="sha256:" + "a" * 64, cli_build=selected["cli_build"],
        provider_network="bridge", runtime_uid=None, turn_seconds=30, verification_seconds=30, implementer_invocations=1, contextual=False, provider_selection=selected)
    return policy.delivery({"selection": selected, "adapter": v["adapter"], "runtime_profile": v["runtime_profile"]}, adapter_digest=v["adapter_digest"],
        profile_digest=v["profile_digest"], tool_policy_digest=policy.digest(policy.POLICY), authority_uuid="auth", job_id=job, worker_id=worker, attempt_id=attempt)


def out(usage, **more):
    return json.dumps(dict(type="result", subtype="success", is_error=False, modelUsage=usage, **more)).encode()


class Attribution(unittest.TestCase):
    def rec(self, raw, **kw):
        return attribution.record(delivery(), phase="review", evidenced_build=kw.pop("build", "2.1.247"), raw=raw, **kw)

    def test_shapes_that_are_not_one_successful_terminal_object_are_missing(self):
        good = out({"id-x": {}})
        self.assertEqual(self.rec(good)["outcome"], "matched")
        for raw in (b"[" + good + b"]", good + b"\n" + good, b'{"type":"system","model":"id-x"}\n' + good, out({}), out([]), out("id-x"), out(None),
                    out({"": {}}), out({"id-x": {}}).replace(b'"success"', b'"error_max_turns"'),
                    good[:-1], good.replace(b'"modelUsage"', b'"modelUsage":{"id-x":{}},"modelUsage"', 1)):
            with self.subTest(raw=raw[:60]):
                self.assertEqual(self.rec(raw)["outcome"], "missing")
        self.assertEqual(self.rec(good + b"\n")["outcome"], "matched")           # one trailing newline is still one document
        self.assertEqual(self.rec(b'\xef\xbb\xbf' + good)["outcome"], "matched")   # (first run: I expected missing; a BOM-prefixed document is still one document. My expectation, corrected.)

    def test_zero_usage_entry_counts_as_a_contributor(self):
        # RECORDED, not judged: the contract leaves this open (section 7, last bullet).
        self.assertEqual(self.rec(out({"id-x": {"inputTokens": 0, "outputTokens": 0}}))["outcome"], "matched")

    def test_requested_selector_is_never_evidence(self):
        v = self.rec(out({"other": {}}, model="id-x", result="id-x sel-x"))
        self.assertEqual((v["outcome"], v["contributors"]), ("conflicting", ["other"]))
        self.assertEqual(self.rec(out({"sel-x": {}}))["outcome"], "conflicting")     # the SELECTOR appearing is not the mapped identity

    def test_host_validation_refuses_every_forgery_of_the_claim_but_cannot_check_the_build(self):
        d = delivery(); raw = out({"other": {}})
        honest = attribution.record(d, phase="review", evidenced_build="2.1.247", raw=raw)
        self.assertEqual(attribution.validate(honest, d, phase="review", raw=raw)["outcome"], "conflicting")
        forged = dict(honest, contributors=["id-x", "other"], contributor_sources={"id-x": ["modelUsage"], "other": ["modelUsage"]}, outcome="matched")
        for bad in (forged, dict(honest, outcome="matched"), dict(honest, extra=1), dict(honest, evidence=dict(honest["evidence"], digest="sha256:" + "0" * 64)),
                    {k: v for k, v in honest.items() if k != "evidence"}):
            with self.subTest(bad=sorted(bad)), self.assertRaises(policy.PolicyRefusal):
                attribution.validate(bad, d, phase="review", raw=raw)
        with self.assertRaises(policy.PolicyRefusal):
            attribution.validate(honest, d, phase="implementation", raw=raw)
        with self.assertRaises(policy.PolicyRefusal):
            attribution.validate(honest, delivery(attempt="a2"), phase="review", raw=raw)
        # THE BUILD IS THE WORKER'S WORD: the host re-derives everything else from retained bytes, and takes this member as claimed.
        good_raw = out({"id-x": {}})
        lying = attribution.record(d, phase="review", evidenced_build="2.1.247", raw=good_raw)
        self.assertEqual(attribution.validate(lying, d, phase="review", raw=good_raw)["outcome"], "matched")
        print("NOTE host accepts evidenced_cli_build as claimed by the worker (no host-side source for it)")

    def test_no_quantity_role_or_content_in_the_record(self):
        v = self.rec(out({"id-x": {"outputTokens": 987654321, "costUSD": 1.25}}, result="SECRET-TEXT"))
        self.assertNotIn("987654321", json.dumps(v)); self.assertNotIn("SECRET-TEXT", json.dumps(v))
        self.assertEqual(set(v), {"schema", "attempt_id", "job_id", "phase", "provider", "selected_cli_build", "evidenced_cli_build", "requested_model", "mapped_identity",
                                  "contributors", "contributor_sources", "outcome", "evidence"})


class Policy(unittest.TestCase):
    def test_every_member_of_the_adapter_and_delivery_is_bound(self):
        d = delivery(); binding = d["contract"]; a = binding["adapter"]
        for key in a:
            if key == "network": continue      # (first run: I expected refusal; the network is the deployment's own member, bound by the digest only. My expectation, corrected.)
            changed = copy.deepcopy(a); changed[key] = "tampered" if not isinstance(changed[key], str) or changed[key] != "tampered" else "t2"
            with self.subTest(key=key), self.assertRaises(policy.PolicyRefusal):
                policy.validate_adapter(changed, binding["selection"], adapter_digest=policy.digest(changed), tool_policy_digest=policy.digest(policy.POLICY))
        job = {"attempt_id": "a1", "job_id": "j1"}
        self.assertEqual(policy.validate_delivery(d, job), d)
        for bad_job in ({"attempt_id": "a2", "job_id": "j1"}, {"attempt_id": "a1", "job_id": "j2"}, None):
            with self.assertRaises(policy.PolicyRefusal):
                policy.validate_delivery(d, bad_job)
        for path, value in ((("home_identity", "worker_id"), "w2"), (("contract", "selection", "requested_model"), "other"), (("contract", "selection", "reported_identity"), "other"),
                            (("tool_policy_digest",), "sha256:" + "1" * 64), (("contract", "adapter", "argv_policy", "fallback"), "--fallback-model")):
            changed = copy.deepcopy(d); at = changed
            for part in path[:-1]: at = at[part]
            at[path[-1]] = value
            ok = True
            try: policy.validate_delivery(changed, job)
            except policy.PolicyRefusal: ok = False
            # worker_id is free text bound only by the manager's derivation; every other change must refuse
            print("DELIVERY change", ".".join(path), "->", "ACCEPTED" if ok else "refused")
            if path != ("home_identity", "worker_id"): self.assertFalse(ok, path)

    def test_argv_is_exactly_the_policy_with_no_fallback(self):
        d = delivery(); b = d["contract"]
        argv = policy.argv(b["adapter"], b["selection"], "PROMPT")
        self.assertEqual(argv, ["claude", "--print", "--dangerously-skip-permissions", "--output-format", "json", "--model", "sel-x", "PROMPT"])
        self.assertFalse(any("fallback" in one for one in argv))

    def test_unknown_provider_and_incomplete_selection_cannot_be_composed(self):
        for bad in (dict(SEL, provider="codex"), {k: v for k, v in SEL.items() if k != "requested_model"}, dict(SEL, requested_model=""), dict(SEL, reported_identity=None), dict(SEL, extra="x")):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                policy.adapter(bad, network="bridge")
        self.assertEqual(policy.adapter(dict(SEL, cli_build="9.9.9"), network="bridge")["participation_sources"], [])   # another build has NO sources: fail-closed


class HomePath(unittest.TestCase):
    ROOT = "/x/job-work"

    def test_components_are_fixed_digests_and_never_id_text(self):
        hostile = ["../../etc", "a/b", ".", "..", "-rf", " lead", "tab\tctl\x01", "ünï", "A" * 5000, "job", "JOB"]
        seen = {}
        for j in hostile:
            for w in hostile:
                place = provider_home.location(self.ROOT, {"authority_uuid": "auth", "job_id": j, "worker_id": w})
                rel = place.relative_to(self.ROOT).parts
                self.assertEqual(len(rel), 2); self.assertTrue(all(len(p) == 64 and set(p) <= set("0123456789abcdef") for p in rel))
                self.assertNotIn(place, seen, (j, w, seen.get(place))); seen[place] = (j, w)
        pairs = [("a", "bc"), ("ab", "c"), ("a/b", "c"), ("a", "b/c"), ("a\x00b", "c")]
        self.assertEqual(len({provider_home.location(self.ROOT, {"authority_uuid": "auth", "job_id": j, "worker_id": w}) for j, w in pairs}), len(pairs))
        one = provider_home.location(self.ROOT, {"authority_uuid": "auth", "job_id": "j", "worker_id": "w1"})
        two = provider_home.location(self.ROOT, {"authority_uuid": "auth", "job_id": "j", "worker_id": "w2"})
        other = provider_home.location(self.ROOT, {"authority_uuid": "auth2", "job_id": "j", "worker_id": "w1"})
        self.assertEqual(one.parent, two.parent); self.assertNotEqual(one, two); self.assertNotEqual(one.parent, other.parent)

    def test_cessation_needs_this_holder_destroyed_cleaned_and_not_older_than_activity(self):
        good = {"attempt_id": "a1", "runtime": "destroyed", "cleanup": "complete", "observed_at": "2026-11-24T00:00:01+00:00", "last_activity_at": "2026-11-24T00:00:00+00:00"}
        self.assertTrue(provider_home.ceased(good, "a1"))
        self.assertTrue(provider_home.ceased(dict(good, observed_at=good["last_activity_at"]), "a1"))      # equal instants count as not older
        for bad in (None, {}, dict(good, attempt_id="a2"), dict(good, runtime="quiescent"), dict(good, runtime="uncertain"), dict(good, runtime="not-started"),
                    dict(good, cleanup="pending"), dict(good, cleanup=None), dict(good, observed_at=None), dict(good, observed_at="2026-11-23T23:59:59+00:00"),
                    dict(good, observed_at="2026-11-24T00:00:01"), dict(good, last_activity_at="garbage")):
            with self.subTest(bad=bad):
                self.assertFalse(provider_home.ceased(bad, "a1"))


class HomeOwner(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=os.environ["PROBE_TMP"]); self.addCleanup(self.tmp.cleanup)
        self.root = os.path.join(self.tmp.name, "state", "job-work"); os.makedirs(os.path.dirname(self.root), mode=0o700)
        self.id = dict(authority_uuid="auth", job_id="j1", worker_id="w1")

    def acquire(self, attempt="a1", **kw):
        return provider_home.acquire(self.root, **dict(self.id, **kw.pop("ident", {})), attempt_id=attempt, **kw)

    def test_wrong_or_missing_record_is_refused_and_nothing_is_changed(self):
        one = self.acquire(); home = Path(one["home"]); record = home.parent / "record.json"
        (home / "kept").write_bytes(b"provider state")
        before = record.read_bytes()
        doc = json.loads(before)
        for change in (dict(doc, identity=dict(doc["identity"], job_id="other")), dict(doc, identity=dict(doc["identity"], worker_id="other")), dict(doc, schema="x"), dict(doc, extra=1), dict(doc, state="gone")):
            record.write_text(json.dumps(change)); os.chmod(record, 0o600)
            with self.subTest(change=change), self.assertRaises(provider_home.HomeRefusal) as caught:
                self.acquire()
            self.assertNotIsInstance(caught.exception, provider_home.HomePending)
            self.assertEqual(json.loads(record.read_text()), change); self.assertEqual((home / "kept").read_bytes(), b"provider state")
        record.unlink()
        with self.assertRaises(provider_home.HomeRefusal):
            self.acquire()
        self.assertFalse(record.exists()); self.assertEqual((home / "kept").read_bytes(), b"provider state")
        record.write_bytes(before); os.chmod(record, 0o600)
        os.chmod(record, 0o644)
        with self.assertRaises(provider_home.HomeRefusal):
            self.acquire()

    def test_symlinked_home_or_ancestor_is_refused(self):
        one = self.acquire(); home = Path(one["home"])
        os.rename(home, home.parent / "moved"); os.symlink(home.parent / "moved", home)
        with self.assertRaises((provider_home.HomeRefusal, OSError)):
            self.acquire()
        with self.assertRaises((provider_home.HomeRefusal, OSError)):
            provider_home.HomeMount(self.root, **self.id, attempt_id="a1")

    def test_a_second_holder_waits_without_evidence_and_takes_over_only_with_it(self):
        one = self.acquire()
        for evidence in (None, lambda holder: None, lambda holder: {"attempt_id": holder, "runtime": "not-started", "cleanup": "pending", "observed_at": None, "last_activity_at": "2026-11-24T00:00:00+00:00"}):
            with self.assertRaises(provider_home.HomePending):
                self.acquire("a2", previous_runtime=evidence)
        self.assertEqual(json.loads((Path(one["home"]).parent / "record.json").read_text())["holder"], "a1")
        with self.assertRaises(provider_home.HomeRefusal):
            provider_home.HomeMount(self.root, **self.id, attempt_id="a2")            # a non-holder can never obtain the mount
        good = lambda holder: {"attempt_id": holder, "runtime": "destroyed", "cleanup": "complete", "observed_at": "2026-11-24T00:00:01+00:00", "last_activity_at": "2026-11-24T00:00:00+00:00"}
        self.assertEqual(self.acquire("a2", previous_runtime=good)["home"], one["home"])
        with self.assertRaises(provider_home.HomeRefusal):
            provider_home.HomeMount(self.root, **self.id, attempt_id="a1")            # ... and the earlier holder loses it
        print("NOTE once a2 holds, any adapter built for a1 with a home mount is refused (HomeMount requires holder == attempt)")

    def test_placement_refuses_overlap_both_ways(self):
        for other in (self.root, os.path.dirname(self.root), os.path.join(self.root, "x"), "/"):
            with self.subTest(other=other), self.assertRaises(provider_home.HomeRefusal):
                provider_home.check_placement(self.root, [other])
        provider_home.check_placement(self.root, [self.root + "-sibling", os.path.join(os.path.dirname(self.root), "workspaces")])


class WorkerHome(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=os.environ["PROBE_TMP"]); self.addCleanup(self.tmp.cleanup)
        self.home = os.path.join(os.path.realpath(self.tmp.name), "h"); os.mkdir(self.home, 0o700)
        self.slot = os.path.join(os.path.realpath(self.tmp.name), "slot"); Path(self.slot).write_bytes(b"SEED-1"); os.chmod(self.slot, 0o400)

    def test_delivered_mode_leaves_only_a_reference(self):
        worker_home.prepare(self.home, credential_path=".claude/.credentials.json", delivered=self.slot, mode="delivered")
        link = Path(self.home, ".claude/.credentials.json")
        self.assertTrue(link.is_symlink()); self.assertEqual(os.readlink(link), self.slot)
        for path in Path(self.home).rglob("*"):
            self.assertFalse(path.is_file() and not path.is_symlink(), path)
        worker_home.prepare(self.home, credential_path=".claude/.credentials.json", delivered=self.slot, mode="delivered")      # idempotent
        link.unlink(); link.write_bytes(b"provider wrote a real file")
        with self.assertRaises(policy.PolicyRefusal):
            worker_home.prepare(self.home, credential_path=".claude/.credentials.json", delivered=self.slot, mode="delivered")
        self.assertEqual(link.read_bytes(), b"provider wrote a real file")

    def test_seeded_mode_writes_once_and_never_again(self):
        cred = Path(self.home, "auth/cred.json")
        worker_home.prepare(self.home, credential_path="auth/cred.json", delivered=self.slot, mode="seeded-retained")
        self.assertEqual(cred.read_bytes(), b"SEED-1"); self.assertEqual(stat.S_IMODE(cred.stat().st_mode), 0o600)
        cred.write_bytes(b"REFRESHED-BY-PROVIDER")
        os.chmod(self.slot, 0o600); Path(self.slot).write_bytes(b"SEED-2-DIFFERENT")
        worker_home.prepare(self.home, credential_path="auth/cred.json", delivered=self.slot, mode="seeded-retained")
        self.assertEqual(cred.read_bytes(), b"REFRESHED-BY-PROVIDER")
        os.unlink(self.slot)                                                                                                     # delivery gone entirely: retained copy still stands
        worker_home.prepare(self.home, credential_path="auth/cred.json", delivered=self.slot, mode="seeded-retained")
        self.assertEqual(cred.read_bytes(), b"REFRESHED-BY-PROVIDER")
        self.assertEqual(sorted(p.name for p in cred.parent.iterdir()), ["cred.json"])                                           # no seed temporary left behind

    def test_paths_cannot_escape_and_managed_entries_cannot_touch_provider_state(self):
        for bad in ("/abs", "../x", "a/../b", "a//b", ".", ""):
            with self.subTest(bad=bad), self.assertRaises(policy.PolicyRefusal):
                worker_home.prepare(self.home, credential_path=bad, delivered=self.slot, mode="delivered")
        payload = b"instructions"; d = "sha256:" + hashlib.sha256(payload).hexdigest()
        for name, provider_paths in ((".claude/.credentials.json", ()), (".claude", ()), (".claude/.credentials.json/x", ()), ("sessions/x", ("sessions",)), ("sessions", ("sessions/x",))):
            with self.subTest(name=name), self.assertRaises(policy.PolicyRefusal):
                worker_home.prepare(self.home, credential_path=".claude/.credentials.json", delivered=self.slot, mode="delivered", managed=[(name, payload, d)], provider_paths=provider_paths)
        self.assertEqual(list(Path(self.home).iterdir()), [])                                                                    # refused BEFORE any write
        os.chmod(self.home, 0o755)
        with self.assertRaises(policy.PolicyRefusal):
            worker_home.prepare(self.home, credential_path=".claude/.credentials.json", delivered=self.slot, mode="delivered")


if __name__ == "__main__":
    unittest.main(verbosity=2)
