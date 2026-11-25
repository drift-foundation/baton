"""Render reviewable argv only. Never run a command or read a credential."""
import argparse
import json
from pathlib import Path
import re

IMAGE = "sha256:17d250b7f620cf69fce0fd96dc1ccbb5b76151a2a6f6bae4fedb2027076f6b0c"
CANDIDATE = "sha256:9c365d72625de16e193198d2f1938d82cc51cedad59d3dd54f1cd259db66c458"


def render(s, phase, *, proposal=False):
    if s.get("service_tier") not in (None, "fast"):
        raise ValueError("unrealized service tier")
    if proposal and phase == "live":
        raise ValueError("proposal mode renders only Stage A")
    if s.get("source_checkpoint") != "1ed26970e74ea48013e3e533e057e6ace08d0058":
        raise ValueError("wrong source checkpoint")
    required = ["run_id", "execution_root", "uid", "gid", "authorization_offline"]
    if phase == "login-status":
        required += ["login_status_help_evidence"]
    if phase == "live":
        if s.get("j1_closure_standard") != "B1-option-1-approved":
            raise ValueError("wrong J1 closure standard")
        required += ["credential_source_reference", "credential_source_custodian",
                     "subscription_login_attestation", "credential_relative_path",
                     "credential_path_evidence", "credential_storage_mode_evidence",
                     "codex_home_relative_to_home", "instruction_relative_to_home",
                     "instruction_path_nonoverlap_evidence", "explicit_model", "live_network",
                     "authorization_live", "private_retention_and_cleanup_owner", "refresh_copy_disposition", "login_status_help_evidence", "tool_inventory_evidence", "image_tool_decision"]
    if proposal:
        required = [k for k in required if k not in ("authorization_offline", "login_status_help_evidence")]
    missing = [k for k in required if s.get(k) is None or s.get(k) == ""]
    if missing:
        raise ValueError("unselected: " + ", ".join(missing))
    if s.get("image") != IMAGE or s.get("accepted_candidate") != CANDIDATE:
        raise ValueError("image/candidate differs from this packet")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,31}", s["run_id"]):
        raise ValueError("invalid run id")
    root = Path(s["execution_root"])
    if not root.is_absolute() or any(c in str(root) for c in (",", "\n", "\0")):
        raise ValueError("execution root must be absolute and mount-safe")
    if any(type(s[k]) is not int or s[k] < 1 for k in ("uid", "gid")):
        raise ValueError("explicit non-root uid/gid required")
    if phase == "live" and (s["live_network"] in ("host", "none") or not re.fullmatch(r"[a-zA-Z0-9_.-]+", s["live_network"])):
        raise ValueError("select an isolated egress network, not host/none")
    name = "n4q-" + s["run_id"] + "-" + phase
    # Live home is automatically seeded by prepare_launch.py, using the
    # selected one-time source configuration; this renderer never reads it.
    mounts = []
    for src, dst, ro in [(root / "packet", "/packet", True),
                         (root / phase / "home", "/run/baton/provider-home", False),
                         (root / phase / "workspace", "/workspace", False),
                         (root / phase / "private-output", "/private-output", False)]:
        mounts += ["--mount", f"type=bind,src={src},dst={dst}" + (",readonly" if ro else "")]
    create = ["docker", "create", "--name", name, "--label", "baton.qualification=" + s["run_id"],
              "--network", s["live_network"] if phase == "live" else "none",
              "--read-only", "--cap-drop=ALL", "--security-opt=no-new-privileges",
              "--user", f"{s['uid']}:{s['gid']}", "--pids-limit", "128",
              "--memory", "1g" if phase == "live" else "512m", "--cpus", "1",
              "--tmpfs", "/tmp:rw,nosuid,nodev,size=128m", "--workdir", "/workspace",
              *mounts, "--entrypoint", "python3", IMAGE, "/packet/capture.py", phase]
    return {"render_only": True, "execution_authorized": False, "proposed_for_selection": proposal, "phase": phase, "name": name,
            "prerequisites": "README phase gates and approved frozen selection; no implicit execution authority",
            "preflight": [["docker", "image", "inspect", IMAGE]],
            "workspace_preparation_after_external_root_ownership_check": [["git", "init", "--quiet", str(root / phase / "workspace")]] if phase == "live" else [],
            "create": create, "start": ["docker", "start", name],
            "wait": ["docker", "wait", name],
            "inspect_before_removal": ["docker", "inspect", name],
            "deadline_seconds": 255 if phase == "live" else 60,
            "on_deadline": [["docker", "stop", "--time", "15", name], ["docker", "inspect", name]],
            "only_if_still_running": ["docker", "kill", name],
            "after_confirmed_exit": ["docker", "rm", name],
            "verify_absence": [["docker", "inspect", name], ["docker", "ps", "-aq", "--filter", "label=baton.qualification=" + s["run_id"]]],
            "no_automatic_retry": True}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("selection"); p.add_argument("phase", choices=["login-help", "login-status", "live"])
    p.add_argument("--proposal", action="store_true", help="render unselected Stage A settings only")
    a = p.parse_args()
    try:
        print(json.dumps(render(json.loads(Path(a.selection).read_text()), a.phase, proposal=a.proposal), indent=2))
    except (ValueError, KeyError, TypeError) as e:
        p.exit(2, "refused: " + str(e) + "\n")
