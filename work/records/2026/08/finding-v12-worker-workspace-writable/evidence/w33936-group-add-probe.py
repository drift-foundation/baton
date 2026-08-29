"""W33936 — is the reviewer's direction available, and does it work?

Three questions, measured against the real daemon rather than reasoned about,
so the ruling that has to be requested is a choice between measured options.

1. Does the engine APPLY a supplementary group, and does the process inside
   receive it?  The reviewer confirmed the CLI accepts `--group-add`; accepting
   a flag and applying it are two facts.
2. With the workspace narrowed to 0770 and the primary identity left at the
   pinned 65532:65532, does a supplementary group grant the write?
3. What is the group this manager would otherwise have inherited, and what else
   does it reach?  That is the reviewer's objection, stated as a measurement.
"""
import grp
import json
import os
import pwd
import subprocess
import tempfile
import uuid

root = tempfile.mkdtemp(prefix="w33936-groupadd-")
workspace = os.path.join(root, "workspace")
os.makedirs(workspace)
os.chmod(workspace, 0o770)
service_gid = os.stat(workspace).st_gid

answers = {"manager_uid_gid": [os.getuid(), os.getgid()],
           "workspace_mode": oct(os.stat(workspace).st_mode & 0o777),
           "workspace_gid": service_gid}
try:
    answers["service_group_name"] = grp.getgrgid(service_gid).gr_name
    answers["service_group_members"] = grp.getgrgid(service_gid).gr_mem
    answers["is_login_group_of"] = [
        one.pw_name for one in pwd.getpwall() if one.pw_gid == service_gid]
except KeyError:
    answers["service_group_name"] = None

PROBE = ("import json, os\n"
         "print(json.dumps({'uid_gid': [os.getuid(), os.getgid()],"
         " 'groups': sorted(os.getgroups()),"
         " 'workspace_writable': os.access('/workspace', os.W_OK)}))\n")


def run(extra):
    name = "w33936-" + uuid.uuid4().hex[:8]
    argv = (["docker", "run", "--rm", "--name", name, "--network", "none",
             "--read-only", "--user", "65532:65532",
             "--mount", f"type=bind,source={workspace},target=/workspace,"
                        f"readonly=false"]
            + extra
            + ["--entrypoint", "python3", "python:3.13-slim", "-c", PROBE])
    finished = subprocess.run(argv, capture_output=True, timeout=300)
    raw = finished.stdout.decode().strip()
    if not raw:
        return {"error": finished.stderr.decode()[-300:]}
    return json.loads(raw.splitlines()[-1])


answers["without_group_add"] = run([])
answers["with_group_add"] = run(["--group-add", str(service_gid)])
print(json.dumps(answers, indent=1))
