"""Ordinary-tests fixture support for the shared resource token.

W275774 child A, review 2026-09-26T14:28:00Z: the boundary-inventory witnesses first
reached child A's selector by importing it from the dossier record by path. Reusable
fixture support belongs in the ordinary test tree, so it lives here and the dossier
selector stays what it is -- evidence for one Work rather than a library.

Real disposable `ControlStore` instances in a temporary directory, no engine, no provider
and no process created or signalled.
"""
import os
import tempfile

from baton_v12.worker_manager import tokens
from baton_v12.worker_manager.store import ControlStore

INSTANT = "2026-09-26T14:00:00.000Z"


class TokenFixture:
    """One disposable store and one governed domain, with the ordinary vectors."""

    def __init__(self, case, instant=INSTANT):
        root = tempfile.TemporaryDirectory(prefix="v12-token-support-")
        case.addCleanup(root.cleanup)
        self.root = root.name
        self.instant = instant
        self.store = ControlStore.open(
            os.path.join(self.root, "control.sqlite3"),
            incarnation="token-support", clock=lambda: self.instant)
        case.addCleanup(self.store.close)
        self.domain = tokens.domain_of("workspace", "line-7/workspace")

    def held(self, *, operation="runtime.start:support",
             execution="attempt-support", attempt="attempt-support", seconds=900):
        return tokens.acquire(self.store, self.domain, operation=operation,
                              execution=execution, attempt=attempt, seconds=seconds)

    def launched(self, token, container="container-support", launch="launch:support"):
        """A token whose container is BOUND, so owner guards are the thing under test."""
        tokens.journal_launch(self.store, token, launch)
        tokens.bind_container(self.store, token, container, launch=launch)
        return {"domain": token["domain"], "generation": token["generation"],
                "launch": launch, "container": container,
                "stopped": True, "helpers": []}
