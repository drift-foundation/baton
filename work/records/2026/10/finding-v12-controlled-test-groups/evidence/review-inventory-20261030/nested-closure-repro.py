"""Run from repository root with PYTHONPATH=v12/python/src:v12/python."""
import ast
from pathlib import Path
from unittest.mock import patch
from tests.manager import test_boundary_inventory as m
source = """
def outer(store, agent):
    def act(connection):
        def inner(agent):
            boundaries.capability(getattr(agent, "probe", None), "inner only")
        return inner(connection)
    return store.transact("op", "kind", "sig", act)
"""
m._clear_boundary_projections()
try:
    with patch.object(m, "_sources", lambda: ((Path("sample.py"), ast.parse(source)),)):
        labels = m._owned_here("sample.py:outer", "caller:agent")
        print("outer caller agent labels:", labels)
        print("owners:", dict(m.owning_validators()))
        assert labels == [], "inner parameter validator falsely credited to outer caller agent"
finally:
    m._clear_boundary_projections()
