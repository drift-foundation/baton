#!/usr/bin/env python3
"""Keep the shell cleanup alive when the operator interrupts its wrapper."""
import os,signal,subprocess,sys
child=subprocess.Popen(sys.argv[1:],start_new_session=True)
try:
    result=child.wait()
except KeyboardInterrupt:
    print("Interrupted; waiting for owned cleanup. Do not close this terminal.",flush=True)
    signal.signal(signal.SIGINT,signal.SIG_IGN)
    if child.poll() is None:
        os.killpg(child.pid,signal.SIGTERM)
    result=child.wait()
    if result==0:result=130
raise SystemExit(result)
