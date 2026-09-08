#!/usr/bin/env python3
"""Read Baton attention and notify an existing Codex prompt via its bridge.

No readiness consumption, claims, SQL, app-server connection, or shell commands.
See CODEX-COPILOT-NOTIFIER.md for the advisory delivery/restart contract.
"""

import argparse
from datetime import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import tempfile
import time


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def read_config(path):
    config = json.loads(Path(path).read_text())
    required = {"baton", "baton_config", "observer", "prompt_participant", "target", "socket", "state_file"}
    if set(config) - required - {"poll_seconds", "timeout_seconds"} or required - set(config):
        raise ValueError("config requires exactly the documented connection fields and optional timing fields")
    if any(not isinstance(config[k], str) or not config[k].strip() for k in required):
        raise ValueError("connection fields must be nonempty strings")
    for key in ("baton", "baton_config", "socket", "state_file"):
        if not Path(config[key]).is_absolute():
            raise ValueError(f"{key} must be an explicit absolute path")
    if config["observer"] == config["prompt_participant"]:
        raise ValueError("the operator observer and prompt participant must be distinct")
    for key in ("observer", "prompt_participant"):
        if not re.fullmatch(r"[^.\s]+\.[^.\s]+", config[key]):
            raise ValueError(f"{key} must be team.member")
    for key, default in (("poll_seconds", 30), ("timeout_seconds", 15)):
        config.setdefault(key, default)
        if type(config[key]) not in (int, float) or not 1 <= config[key] <= 300:
            raise ValueError(f"{key} must be between 1 and 300")
    return config


def baton_read(config, verb, *operands):
    if verb not in {"actionable-work", "obligations", "incidents", "runtime"}:
        raise ValueError("not a notifier read")
    result = subprocess.run([config["baton"], "--config", config["baton_config"], "--participant", config["observer"], verb, *operands], capture_output=True, text=True, timeout=config["timeout_seconds"], check=False)
    if result.returncode:
        raise RuntimeError(f"Baton {verb} failed (exit {result.returncode}); no notification acknowledged")
    envelope = json.loads(result.stdout)
    if envelope.get("protocol_version") != 11 or envelope.get("participant") != config["observer"] or not envelope.get("authority_uuid"):
        raise ValueError("unexpected Baton authority/protocol/participant envelope")
    return envelope


def attention(config, read=baton_read, *, stale_runtime_keys=None):
    items, after, cursors, authority = {}, None, set(), None
    while True:
        page = read(config, "actionable-work", "limit=100", *([f"after={after}"] if after else []))
        authority = authority or page["authority_uuid"]
        if page["authority_uuid"] != authority:
            raise ValueError("authority changed during scan")
        for row in page["result"]["rows"]:
            # Exclude volatile runtime/new/age fields. A changed handoff,
            # discussion count, or child completion merits another summary.
            item = {key: row.get(key) for key in ("id", "title", "last_change_seq", "message_count", "progress", "route")}
            items["work:" + row["id"]] = item
        after = page["result"]["next_after"]
        if after is None:
            break
        if not isinstance(after, str) or not after or after in cursors or len(cursors) >= 1000:
            raise ValueError("invalid or excessive pagination")
        cursors.add(after)
    obligations = read(config, "obligations")
    if obligations["authority_uuid"] != authority:
        raise ValueError("authority changed during scan")
    team, member = config["observer"].split(".", 1)
    for row in obligations["result"]:
        owed = row["owed_by"]
        handlers = owed["handlers"]
        if owed["endpoint"].split(".", 1)[0] != team or member not in handlers:
            continue
        if row.get("flavor") == "due_trial":
            key = "trial:" + digest([row["work"], row["trial"], row["deadline_generation"]])
        else:
            key = "obligation:" + str(row["seq"])
        items[key] = row
    incidents = read(config, "incidents")
    runtime = read(config, "runtime")
    if incidents["authority_uuid"] != authority or runtime["authority_uuid"] != authority:
        raise ValueError("authority changed during scan")
    for row in incidents["result"]["rows"]:
        if row["action_owner"] != config["observer"] or not row["open"]:
            continue
        items["incident:" + str(row["incident"])] = {key: row.get(key) for key in (*FAILURE_IDENTITY, "first_ts", "category")}
    for row in runtime["result"]["participants"]:
        run = row["runtime"]
        if run["action_owner"] != config["observer"]:
            continue
        key = "runtime:" + row["participant"]
        if stale_runtime_keys is not None and run["state"] == "unknown" and run.get("provenance") == "derived" and run.get("stale") is True:
            # Expiry hides the reported cause/transition; retain accepted hashes,
            # but never treat stale contact itself as new failure attention.
            stale_runtime_keys.add(key)
        if run["state"] != "failed":
            continue
        item = {key: run.get(key) for key in (*FAILURE_IDENTITY, "since")}
        item["participant"] = row["participant"]
        items[key] = item
    return authority, items


FAILURE_IDENTITY = ("participant", "incarnation", "session", "work", "episode", "cause")


def same_failure(incident, runtime):
    # Missing lease/transition identity must not hide independent attention.
    if not runtime.get("incarnation") or any(incident.get(k) != runtime.get(k) for k in FAILURE_IDENTITY):
        return False
    try:
        return datetime.fromisoformat(incident["first_ts"].replace("Z", "+00:00")) >= datetime.fromisoformat(runtime["since"].replace("Z", "+00:00"))
    except (KeyError, AttributeError, TypeError, ValueError):
        return False


def failure_changes(items, current, seen, paired):
    changed = {key for key in items if seen.get(key) != current[key]}
    covered = set()
    pairs = []
    for runtime_key, runtime in items.items():
        if not runtime_key.startswith("runtime:"):
            continue
        for incident_key, incident in items.items():
            if not incident_key.startswith("incident:") or not same_failure(incident, runtime):
                continue
            pairs.append((runtime_key, incident_key))
            if seen.get(runtime_key) == current[runtime_key] and paired.get(runtime_key) != current[runtime_key]:
                # The runtime already notified this exact failure; a late incident
                # adds a read locator, not a second model turn.
                covered.add(incident_key)
            elif seen.get(incident_key) == current[incident_key]:
                covered.add(runtime_key)
            else:
                # Both are new: prefer the durable incident, but acknowledge the
                # runtime only when that advisory is accepted.
                changed.discard(runtime_key)
    return sorted(changed - covered), covered, pairs


def remember_failure_pairs(state, current, pairs):
    for runtime_key, incident_key in pairs:
        if all(state["seen"].get(k) == current[k] for k in (runtime_key, incident_key)):
            state["paired"][runtime_key] = current[runtime_key]


def bridge_request(config, payload):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.settimeout(config["timeout_seconds"])
        connection.connect(config["socket"])
        connection.sendall(json.dumps(payload).encode() + b"\n")
        data = bytearray()
        while b"\n" not in data:
            chunk = connection.recv(65536)
            if not chunk:
                raise RuntimeError("bridge closed without acknowledgement")
            data.extend(chunk)
            if len(data) > 4 * 1024 * 1024:
                raise ValueError("bridge response exceeds limit")
        return json.loads(data.split(b"\n", 1)[0])


def poll(config, state, read=baton_read, request=bridge_request):
    status = request(config, {"control": "copilot-status"})
    target = status["targets"][config["target"]]
    if target.get("participant") != config["prompt_participant"] or target.get("role") != "prompt":
        raise ValueError("target must be the explicitly configured prompt participant")
    if not status.get("instanceId") or not target.get("threadId"):
        raise ValueError("bridge lacks copilot support; deploy the paired bridge first")
    stale_runtime_keys = set()
    authority, items = attention(config, read, stale_runtime_keys=stale_runtime_keys)
    scope = digest([authority, config["observer"], config["target"], config["prompt_participant"], status["instanceId"], target["threadId"]])
    seen = state.get("seen", {}) if state.get("scope") == scope else {}
    current = {key: digest(value) for key, value in items.items()}
    paired = state.get("paired", {}) if state.get("scope") == scope else {}
    changed, covered, pairs = failure_changes(items, current, seen, paired)
    # Prune resolved items, retaining accepted failures during derived expiry.
    # Nothing new is seen merely because it went stale or the prompt is busy.
    retained = {k: v for k, v in seen.items() if k in current or k in stale_runtime_keys}
    next_state = {"scope": scope, "seen": retained, "paired": {k: v for k, v in paired.items() if current.get(k) == v or (k in stale_runtime_keys and retained.get(k) == v)}}
    next_state["seen"].update({k: current[k] for k in covered})
    remember_failure_pairs(next_state, current, pairs)
    if not changed:
        return next_state, {"status": "unchanged", "attention": len(items)}
    if not target.get("connected") or not target.get("deliverable") or target.get("status") != "idle" or target.get("queueDepth") != 0:
        return next_state, {"status": "waiting-for-prompt", "changed": len(changed)}
    # A bounded locator-only event: model re-reads current canonical state.
    # Never copy arbitrary message bodies, credential-bearing logs, or titles.
    event = {
        "id": "copilot:" + digest([scope, [(key, current[key]) for key in changed]]),
        "target": config["target"], "source": "baton-copilot", "type": "operator-attention",
        "copilotThreadId": target["threadId"], "copilotInstanceId": status["instanceId"],
        "summary": f"Operator {config['observer']} has {len(changed)} new or changed attention items.",
        "details": json.dumps({"observer": config["observer"], "changed": changed[:50], "total_changed": len(changed), "baton": config["baton"], "config": config["baton_config"]}),
    }
    response = request(config, event)
    if response.get("accepted") is True:
        next_state["seen"].update(current)
        remember_failure_pairs(next_state, current, pairs)
        return next_state, {"status": "accepted", "changed": len(changed), "event": event["id"]}
    return next_state, {"status": "not-accepted", "reason": response.get("reason", "unknown")}


def save_state(path, state):
    # Separate from Baton's authoritative DB: only an advisory delivery cursor.
    descriptor, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w") as output:
            json.dump(state, output)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="notifier JSON configuration, not baton.json")
    parser.add_argument("--once", action="store_true", help="one delivery poll")
    parser.add_argument("--dry-run", action="store_true", help="read attention once; no socket, state writes, or model turn")
    args = parser.parse_args(argv)
    config = read_config(args.config)
    if args.dry_run:
        authority, items = attention(config)
        print(json.dumps({"authority": authority, "observer": config["observer"], "items": sorted(items)}))
        return 0
    path = Path(config["state_file"])
    # Parent must be operator-created. One watcher per target and state path.
    with open(str(path) + ".lock", "a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state = json.loads(path.read_text()) if path.exists() else {}
        if not isinstance(state, dict) or not isinstance(state.get("seen", {}), dict) or not isinstance(state.get("paired", {}), dict):
            raise ValueError("invalid notifier cursor; inspect it before retrying")
        while True:
            try:
                updated, result = poll(config, state)
                if updated != state:
                    save_state(path, updated)
                    state = updated
                print(json.dumps(result), flush=True)
            except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.TimeoutExpired) as error:
                # Don't put tool output, titles or arbitrary socket text in logs.
                print(json.dumps({"status": "error", "category": type(error).__name__, "message": "poll failed; cursor not advanced"}), flush=True)
                if args.once:
                    return 1
            if args.once:
                return 0
            time.sleep(config["poll_seconds"])


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
