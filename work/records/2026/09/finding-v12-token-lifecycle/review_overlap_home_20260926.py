"""Independent real-filesystem probe: a symlinked attempt home is not a sibling."""
import importlib.util
import os
from pathlib import Path
import unittest
from baton_v12.contracts import ContractRefusal

spec = importlib.util.spec_from_file_location('author_overlap', Path(__file__).with_name('test_governed_start.py'))
author = importlib.util.module_from_spec(spec)
spec.loader.exec_module(author)

class HomeAlias(unittest.TestCase):
    def test_nested_workspace_via_home_alias_is_refused(self):
        case = author.TheConflictDomainExcludesOVERLAP()
        case.setUp()
        self.addCleanup(case.doCleanups)
        original = case.allocated('attempt-a')
        root = os.path.join(case.storage, 'attempt-a', 'workspace')
        os.mkdir(os.path.join(root, 'workspace'))
        os.symlink(root, os.path.join(case.storage, 'attempt-b'))
        with self.assertRaises(ContractRefusal):
            nested = case.workspaces.governed_resource_identity(case.store, 'attempt-b')
            self.assertNotEqual(original, nested)

if __name__ == '__main__':
    unittest.main()
