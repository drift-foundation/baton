"""W106673 pure preparation contract. No provider, filesystem or Docker execution.

Independent fixed-byte verifier and process/session comparison for ONE pair.
Inputs to verification must be collected only after exact revocation/shutdown.
This module does not mint or replace that controller receipt.
"""
import re
import unittest

INITIAL = b"def scale(value):\n    return value * 2\n"
CORRECTED = b"def scale(value):\n    return value * 3\n"
NONCE = re.compile(r"[0-9a-f]{32}\Z")
SESSION = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\Z")
CORRECTION = (
    "Review correction: scale must multiply by 3, not 2. Change only /output/solution.py "
    "to exactly these bytes: def scale(value):\\n    return value * 3\\n . "
    "Write /output/continuity.txt containing only the 32-character token I asked you "
    "to remember in the first turn, followed by a newline. No other files. "
    "Finish all tools, close workspace handles and keep your working directory "
    "outside /output. Do not start background tasks. Report completion."
)


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def first_prompt(token):
    require(isinstance(token, str) and NONCE.fullmatch(token), "invalid-fixture-token")
    return (
        "This is a tiny disposable experiment. Use tools only on /output/solution.py. "
        "Create it with exactly these bytes: def scale(value):\\n    return value * 2\\n . "
        "Remember this token in the conversation for a later correction: " + token + ". "
        "Do not write the token to any file or repeat it in your response. "
        "Do not read credentials or session state. Do not create other files, "
        "background jobs or helpers. Finish all tools, close workspace handles, "
        "keep your cwd outside /output, and report completion."
    )


def verify(files, token, corrected):
    """No execution of agent-authored code; exact tiny artifact acceptance."""
    require(isinstance(token, str) and NONCE.fullmatch(token), "invalid-fixture-token")
    wanted = {"solution.py": CORRECTED if corrected else INITIAL}
    if corrected:
        wanted["continuity.txt"] = (token + "\n").encode()
    return files == wanted


def comparable(retained, restored):
    """Reject missing continuity/equivalence evidence; report observable intervals."""
    for arm in (retained, restored):
        require(arm["first_artifact_verified"] is True and arm["correction_verified"] is True,
                "useful-correction-unproved")
        require(arm["consumption_receipts_verified"] is True, "consumption-unproved")
        require(arm["workspace_before"] == arm["workspace_after"], "workspace-replaced")
        require(SESSION.fullmatch(arm["session_before"]) is not None
                and arm["session_before"] == arm["session_after"], "session-continuity-unproved")
        times = [arm[key] for key in ("end_of_work_ns", "review_ready_ns",
                 "correction_dispatch_ns", "correction_done_ns", "verified_correction_ns")]
        require(all(type(value) is int and value >= 0 for value in times)
                and times == sorted(times), "invalid-monotonic-order")
    require(retained["process_before"] == retained["process_after"]
            and retained["pidfd_continuously_live"] is True, "retained-process-changed")
    require(restored["process_before"] != restored["process_after"]
            and restored["old_container_shutdown_confirmed"] is True
            and restored["resume_requested"] == restored["session_before"], "restore-unproved")
    for key in ("image", "model", "cli_version", "initial_prompt_sha256",
                "correction_prompt_sha256", "initial_bytes_sha256", "review_delay_ns"):
        require(retained[key] == restored[key], "comparison-inputs-differ")
    return {name: {"end_to_verified_correction_ns": arm["verified_correction_ns"] - arm["end_of_work_ns"],
                   "review_readiness_ns": arm["review_ready_ns"] - arm["end_of_work_ns"],
                   "correction_response_ns": arm["correction_done_ns"] - arm["correction_dispatch_ns"],
                   "final_revocation_and_verification_ns": arm["verified_correction_ns"] - arm["correction_done_ns"]}
            for name, arm in (("retained", retained), ("restored", restored))}


class ContractTests(unittest.TestCase):
    def test_verifier_requires_correction_and_remembered_token(self):
        token = "a" * 32
        self.assertTrue(verify({"solution.py": INITIAL}, token, False))
        self.assertTrue(verify({"solution.py": CORRECTED, "continuity.txt": (token + "\n").encode()}, token, True))
        self.assertFalse(verify({"solution.py": INITIAL}, token, True))
        self.assertFalse(verify({"solution.py": CORRECTED, "continuity.txt": b"wrong\n"}, token, True))
        self.assertFalse(verify({"solution.py": INITIAL, "extra": b""}, token, False))
        self.assertNotIn(token, CORRECTION)
        self.assertIn(token, first_prompt(token))

    def pair(self):
        session = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        common = dict(first_artifact_verified=True, correction_verified=True,
                      consumption_receipts_verified=True, workspace_before=[1, 2], workspace_after=[1, 2],
                      session_before=session, session_after=session, end_of_work_ns=10,
                      review_ready_ns=20, correction_dispatch_ns=30, correction_done_ns=40,
                      verified_correction_ns=50, process_before=["container", 100, 200],
                      image="pinned", model="pinned", cli_version="2.1.247",
                      initial_prompt_sha256="first", correction_prompt_sha256="second",
                      initial_bytes_sha256="empty", review_delay_ns=5)
        retained = dict(common, process_after=common["process_before"], pidfd_continuously_live=True)
        restored = dict(common, process_after=["replacement", 101, 201],
                        old_container_shutdown_confirmed=True, resume_requested=session)
        return retained, restored

    def test_comparison_rejects_replacement_disguised_as_retention(self):
        retained, restored = self.pair()
        self.assertEqual(comparable(retained, restored)["retained"]["end_to_verified_correction_ns"], 40)
        retained["process_after"] = restored["process_after"]
        with self.assertRaisesRegex(ValueError, "retained-process-changed"):
            comparable(retained, restored)

    def test_comparison_rejects_unrestored_new_conversation(self):
        retained, restored = self.pair()
        restored["session_after"] = "00000000-bbbb-cccc-dddd-eeeeeeeeeeee"
        with self.assertRaisesRegex(ValueError, "session-continuity-unproved"):
            comparable(retained, restored)

    def test_comparison_rejects_unsafe_consumption_and_unequal_inputs(self):
        for key, value in (("consumption_receipts_verified", False),
                           ("initial_prompt_sha256", "other"), ("review_ready_ns", 51)):
            retained, restored = self.pair()
            restored[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                comparable(retained, restored)


if __name__ == "__main__":
    unittest.main(verbosity=2)
