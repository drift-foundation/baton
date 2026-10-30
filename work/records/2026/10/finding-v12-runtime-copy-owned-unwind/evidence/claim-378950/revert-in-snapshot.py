"""Reverse THIS CLAIM's edits inside the attribution snapshot only.

The forward edits were applied by six deterministic scripts. Their literals are
read with `ast`, so raw and escaped forms both come out as the bytes that were
actually written. Landing on the claim-input digests is the only proof that the
snapshot is the right base:
  bootstrap.py       8a710afc4a6ad809a72602ad4e5e7cbb76cf3ba224e2fe92d6bfb2d83a38b8f4
  test_instance.py   0e7f4710b253bcfa75365ee9c3c0a4b876da50b9f2094f3d08a0b98e5f3954bb
"""
import ast
import hashlib
import pathlib
import sys

snapshot = pathlib.Path("/var/tmp/w376956-attribution/baton/v12/python")
scripts = ["/tmp/report-wording.py", "/tmp/create-step-cases.py",
           "/tmp/fix-foreign-case.py", "/tmp/align-descriptions.py",
           "/tmp/align-bootstrap.py", "/tmp/align-bootstrap2.py"]
WANT = {
    "tools/bootstrap.py":
        "8a710afc4a6ad809a72602ad4e5e7cbb76cf3ba224e2fe92d6bfb2d83a38b8f4",
    "tests/tools/test_instance.py":
        "0e7f4710b253bcfa75365ee9c3c0a4b876da50b9f2094f3d08a0b98e5f3954bb",
}


def read(script):
    """(target file, [(old, new), ...], inserted block or None)."""
    tree = ast.parse(pathlib.Path(script).read_text())
    held = {}
    pairs, order, block = [], [], None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name) \
                and isinstance(node.value, ast.Constant) \
                and isinstance(node.value.value, str):
            name = node.targets[0].id
            held[name] = node.value.value
            if name == "CASES":
                block = node.value.value
            if name == "new" and "old" in held:
                order.append((node.lineno, held["old"], held["new"]))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id == "swap" and len(node.args) >= 2 \
                and all(isinstance(one, ast.Constant) for one in node.args[:2]):
            order.append((node.lineno, node.args[0].value, node.args[1].value))
    pairs = [(old, new) for _line, old, new in sorted(order)]
    target = ("tests/tools/test_instance.py"
              if "test_instance.py" in pathlib.Path(script).read_text()
              else "tools/bootstrap.py")
    return target, pairs, block


applied = 0
for script in reversed(scripts):
    target, pairs, block = read(script)
    place = snapshot / target
    held = place.read_text()
    if block is not None:
        assert held.count(block) == 1, script
        held = held.replace(block, "")
        applied += 1
    for old, new in reversed(pairs):
        if held.count(new) != 1:
            print("MISS", script, repr(new[:60]), held.count(new))
            sys.exit(1)
        held = held.replace(new, old)
        applied += 1
    place.write_text(held)

print("reverted", applied, "edits")
for which, want in WANT.items():
    got = hashlib.sha256((snapshot / which).read_bytes()).hexdigest()
    print(("OK   " if got == want else "WRONG"), which, got)
