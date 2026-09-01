"""Reproduce W62535 against the real dogfood arc and manager store.

The fixture supplies only the authority session, engine adapter and worker
conversation. Offer, workspace and attempt operations are the real v12
implementations. The one deliberate variation is a fresh control store whose
runtime profile has not been certified.
"""

import json
import os
from contextlib import ExitStack
from unittest import mock

import baton_v12.worker_manager as manager
from baton_v12.contracts import ContractRefusal
from tests.tools import test_dogfood_operator as fixture


def main():
    case = fixture.TheArcIsEffectivelyOnceAndAFreshAttemptIsFresh(
        "test_an_exact_replay_starts_no_second_runtime_or_provider_turn")
    case.setUp()
    try:
        with mock.patch.object(manager, "certify_profile",
                               lambda *_arguments, **_operands: None):
            store = case.store()
        session, port = case.authority()
        adapter = case.Adapter()
        refusal = None
        with ExitStack() as patches:
            try:
                case.attempt(store, port, session, adapter,
                             attempt_id="attempt-uncertified",
                             patches=patches)
            except ContractRefusal as caught:
                refusal = caught

        attempt_root = os.path.join(case.home, "storage",
                                    "attempt-uncertified")
        source_root = os.path.join(attempt_root, "inputs", "source")
        first = {
            "category": refusal.category if refusal else None,
            "code": refusal.code if refusal else None,
            "attempt_root_exists": os.path.isdir(attempt_root),
            "source_root_exists": os.path.isdir(source_root),
            "runtime_starts": len(adapter.started),
            "provider_turns": len(session.turns()),
            "authority_calls": [one[0] for one in session.calls],
        }
        if first != {
                "category": "policy",
                "code": "profile-uncertified",
                "attempt_root_exists": True,
                "source_root_exists": True,
                "runtime_starts": 0,
                "provider_turns": 0,
                "authority_calls": ["project_work"]}:
            raise AssertionError(f"the W62535 footprint changed: {first!r}")

        manager.certify_profile(store, "runtime", "dogfood",
                                fixture.PROFILE)
        retry = None
        with ExitStack() as patches:
            try:
                case.attempt(store, port, session, adapter,
                             attempt_id="attempt-uncertified",
                             patches=patches)
            except fixture.OperatorRefusal as caught:
                retry = str(caught)
        if retry is None or "stages its source once" not in retry:
            raise AssertionError(
                f"the same-attempt stage-once refusal changed: {retry!r}")

        print(json.dumps({"first_run": first,
                          "same_attempt_after_certification": retry},
                         indent=2, sort_keys=True))
    finally:
        case.doCleanups()


if __name__ == "__main__":
    main()
