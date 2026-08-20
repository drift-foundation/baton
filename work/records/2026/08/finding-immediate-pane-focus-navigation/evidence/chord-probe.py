"""W1151 plan step 1 (the mandatory gate): can an IMMEDIATE Ctrl-W
chord be shown to fail through a real pty?

Run from the repository root with the development venv:

    .venv/bin/python work/records/2026/08/\
finding-immediate-pane-focus-navigation/evidence/chord-probe.py

It builds a throwaway authority, opens Work detail on a real pty, and
reads the focused pane from the `»` marker the detail view paints — a
TEXT cue, so the answer survives a replay that keeps no attributes.
Every case writes the whole chord in ONE write, with no pause between
the bytes.
"""
import os, sys, tempfile
sys.path.insert(0, "tests/work"); sys.path.insert(0, "src")
import baton_work as bw, fixtures as fx, ptyharness
from baton_work import transitions as tr
d = tempfile.mkdtemp()
cfg, db = fx.build_instance(d, {"lang": {"members": {"ada": ["dev"]}, "kinds": ["bug"]}})
s = bw.Authority(db)
born = tr.create_work(s, team="lang", kind="bug", title="focus subject",
                      origin="external-report", classification="suspected-defect",
                      author="ada", body="the opener")
for n in range(4):
    tr.post_thread(s, born["thread"], author_team="lang", author="ada", body=f"message number {n}")
s.close()

def focus_of(screen):
    for line in screen:
        if "»" in line:
            return line.strip().lstrip("»").split("(")[0].strip()
    return None

def run(script):
    text, status, steps = ptyharness.drive(cfg, "lang.ada", script, columns=120, lines=32)
    assert os.WEXITSTATUS(status) == 0, text[-300:]
    return [focus_of(ptyharness.replay(step, columns=120, lines=32)) for step in steps]

cases = {
  "ctrl-w j (one write)":            [(b"\r", 0.9), (b"\x17j", 0.6), (b"qy", 0.4)],
  "ctrl-w j then ctrl-w k, one write":[(b"\r", 0.9), (b"\x17j\x17k", 0.6), (b"qy", 0.4)],
  "ctrl-w DOWN csi (one write)":     [(b"\r", 0.9), (b"\x17\x1b[B", 0.6), (b"qy", 0.4)],
  "ctrl-w DOWN ss3 (one write)":     [(b"\r", 0.9), (b"\x17\x1bOB", 0.6), (b"qy", 0.4)],
  "ctrl-w j x3 rapid":               [(b"\r", 0.9), (b"\x17j\x17l\x17h", 0.6), (b"qy", 0.4)],
  "everything in ONE write with open":[(b"\r\x17j", 0.9), (b"qy", 0.4)],
}
for label, script in cases.items():
    print(f"{label:36s}", run(script))
