"""Extract every ```sh block from COMMANDS.md and run `bash -n` over it.

Proves the claim COMMANDS.md makes about itself rather than asserting it.
"""
import pathlib
import re
import subprocess
import sys

place = pathlib.Path(sys.argv[1])
blocks = re.findall(r"```sh\n(.*?)```", place.read_text(), re.S)
print("blocks found:", len(blocks))
bad = 0
for n, block in enumerate(blocks, 1):
    done = subprocess.run(["bash", "-n"], input=block, text=True,
                          capture_output=True)
    state = "OK" if done.returncode == 0 else "SYNTAX ERROR"
    print("block %d: %s (%d lines)" % (n, state, len(block.splitlines())))
    if done.returncode != 0:
        bad += 1
        print(done.stderr)
print("blocks:", len(blocks), "syntax errors:", bad)
sys.exit(1 if bad or not blocks else 0)
