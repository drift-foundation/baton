"""Reverse this claim's stage_execution edits into /tmp, to test whether the
13 test_stage_execution errors predate them. The working file is copied first
and restored by the caller; nothing here touches Git."""
import re
import sys

src = "/home/sl/src/baton/v12/python/tools/stage_execution.py"
s = open(src, encoding="utf-8").read()
before = len(s)

# 1. drop the two added module functions
start = s.index("def _host_scratch(deployment):")
end = s.index("def _host_seconds(deployment, stage):")
s = s[:start] + s[end:]

# 2. the owner's registry
s = s.replace('''        # AND WHERE A TREE THAT COULD NOT BE REMOVED IS HANDED ON. Same
        # ownership as the retention and for the same reason: see
        # `_host_scratch`. A composition given none keeps its own, which is a
        # standalone owner whose caller holds it.
        self._surviving = {} if surviving is None else surviving
''', "")
s = s.replace('''    def __init__(self, participant, argv, runner, root, *, seconds=None,
                 retention=None, scope=None, surviving=None):''',
              '''    def __init__(self, participant, argv, runner, root, *, seconds=None,
                 retention=None, scope=None):''')
s = s.replace('''                 seconds=None, retention=None, scope=None, surviving=None):
        super().__init__(participant, argv, runner, root, seconds=seconds,
                         retention=retention, scope=scope,
                         surviving=surviving)''',
              '''                 seconds=None, retention=None, scope=None):
        super().__init__(participant, argv, runner, root, seconds=seconds,
                         retention=retention, scope=scope)''')
s = s.replace('''                 retention=None, scope=None, surviving=None):
        super().__init__(participant, argv, runner, root, seconds=seconds,
                         retention=retention, scope=scope,
                         surviving=surviving)''',
              '''                 retention=None, scope=None):
        super().__init__(participant, argv, runner, root, seconds=seconds,
                         retention=retention, scope=scope)''')
s = s.replace('''            # AND IT IS HANDED TO THE RUNTIME THAT OWNS IT. Naming a surviving
            # tree in a diagnostic tells an operator it is there and leaves
            # nobody responsible for it; the deployment releases it with its
            # other handles. The diagnosis is unchanged either way -- it is
            # what this answer reports, and a later cleanup does not edit it.
            self._surviving[where] = detail
''', "")
s = s.replace('''                surviving=_host_scratch(deployment),
''', "")
s = s.replace('''            surviving=_host_scratch(deployment),
''', "")

# 3. the closer
start = s.index("    def _closers(self):")
end = s.index("        for one in reversed(self.workers):", start)
s = s[:start] + "    def _closers(self):\n" + s[end:]

open("/tmp/stage_execution.reverted.py", "w", encoding="utf-8").write(s)
print("reverted", before, "->", len(s))
assert "surviving" not in s, [one for one in s.splitlines() if "surviving" in one][:3]
assert "_host_scratch" not in s
