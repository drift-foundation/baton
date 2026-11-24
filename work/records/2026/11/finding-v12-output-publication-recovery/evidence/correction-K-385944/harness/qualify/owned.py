#!/usr/bin/env python3
"""owned.py list|kill NAME=VALUE -- the live processes whose own environment carries NAME=VALUE. The harness
gives every dry run a unique HARNESS_RUN value, so what it reports and ends afterwards is that run's and
nothing else's."""
import os, sys
want = sys.argv[2].encode(); found = []
for name in os.listdir("/proc"):
    if name.isdigit() and int(name) != os.getpid():
        try:
            if want in open("/proc/%s/environ" % name, "rb").read().split(b"\0") and open("/proc/%s/stat" % name, "rb").read().rsplit(b")", 1)[1].split()[0] != b"Z":
                found.append((int(name), open("/proc/%s/cmdline" % name, "rb").read().replace(b"\0", b" ").decode(errors="replace").strip()))
        except (OSError, IndexError):
            pass
for pid, argv in sorted(found):
    if sys.argv[1] == "list": print(pid, argv[:120])
    else:
        try: os.kill(pid, 9)
        except OSError: pass
