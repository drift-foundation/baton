#!/usr/bin/env python3
"""Explicit multi-stack lifecycle orchestration; infra.py still owns each stack."""

from __future__ import annotations

import argparse
from contextlib import contextmanager, redirect_stdout
import fcntl
import io
import json
import os
import sys

import infra


REGISTRY = "infra-stacks.json"


def members(root):
    path = os.path.join(root, REGISTRY)
    try:
        with open(path, encoding="utf-8") as handle:
            document = json.load(handle, object_pairs_hook=infra._strict_object)
    except (OSError, ValueError) as error:
        raise infra.InfraError(f"cannot read {path}: {error}; register all stacks explicitly, or use tools/infra.py for single-stack maintenance") from error
    if not isinstance(document, dict) or set(document) != {"version", "stacks"} or type(document["version"]) is not int or document["version"] != 1:
        raise infra.InfraError("stack registry requires exactly version: 1 and stacks")
    if not isinstance(document["stacks"], list) or not document["stacks"]:
        raise infra.InfraError("stack registry requires a non-empty stacks array")
    result, names, paths = [], set(), set()
    for entry in document["stacks"]:
        if not isinstance(entry, dict) or set(entry) != {"name", "directory"}:
            raise infra.InfraError("each stack requires exactly name and directory")
        name, directory = entry["name"], entry["directory"]
        if not isinstance(name, str) or not infra.NAME_RE.fullmatch(name) or name in names:
            raise infra.InfraError("stack names must be valid and unique")
        if not isinstance(directory, str) or not directory or "\0" in directory or os.path.isabs(directory) or ".." in directory.split(os.sep):
            raise infra.InfraError(f"stack {name}: directory must be relative and cannot contain '..'")
        target = os.path.realpath(os.path.join(root, directory))
        if os.path.commonpath([root, target]) != root or target in paths:
            raise infra.InfraError(f"stack {name}: directory escapes deployment or duplicates a canonical stack path")
        names.add(name)
        paths.add(target)
        result.append({"name": name, "directory": target})
    if root not in paths:
        raise infra.InfraError("stack registry must include the main stack at directory '.'")
    return result


@contextmanager
def deployment_lock(root):
    # A different lock from infra.lock: never hold the member lock while
    # invoking infra.run, which acquires that same member lock itself.
    run = os.path.join(root, "run")
    infra._private_directory(run)
    fd = infra._open_owned(os.path.join(run, "deployment.lock"), os.O_RDWR | os.O_CREAT, "deployment lock")
    with os.fdopen(fd, "r+") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def invoke(command, member):
    output = io.StringIO()
    try:
        with redirect_stdout(output):
            code = infra.run([command, member["directory"]])
        report = json.loads(output.getvalue())
        if not isinstance(report, dict):
            raise ValueError("single-stack controller did not return an object")
        return {**member, "exit_code": code, "report": report}
    except (infra.InfraError, OSError, ValueError) as error:
        return {**member, "exit_code": 2, "report": {"healthy": False, "error": str(error)}}


def emit(command, root, rows):
    succeeded = all(row["exit_code"] == 0 and row["report"].get("healthy") is True for row in rows)
    print(json.dumps({"command": command, "deployment": root, "succeeded": succeeded, "stacks": rows}, indent=2))
    return 0 if succeeded else 1


def run(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("start", "stop", "status"))
    parser.add_argument("deployment")
    options = parser.parse_args(argv)
    root = os.path.realpath(os.path.abspath(options.deployment))
    if not os.path.isdir(root):
        raise infra.InfraError(f"deployment is not a directory: {root}")
    # Invalid registration cannot cause a partial lifecycle operation.
    members(root)
    with deployment_lock(root):
        stacks = members(root)
        if options.command == "start":
            errors = {}
            for member in stacks:
                try:
                    infra.load_manifest(member["directory"])
                except (infra.InfraError, OSError, ValueError) as error:
                    errors[member["name"]] = str(error)
            if errors:
                return emit(options.command, root, [{**member, "exit_code": 2, "report": {"healthy": False, "state": "not-attempted", "error": errors.get(member["name"], "another stack failed manifest preflight")}} for member in stacks])
        ordered = list(reversed(stacks)) if options.command == "stop" else stacks
        rows = []
        failed_start = False
        for member in ordered:
            if failed_start:
                rows.append({**member, "exit_code": 2, "report": {"healthy": False, "state": "not-attempted", "error": "an earlier stack failed to start; earlier stacks were not stopped"}})
                continue
            row = invoke(options.command, member)
            rows.append(row)
            if options.command == "start" and (row["exit_code"] != 0 or row["report"].get("healthy") is not True):
                failed_start = True
        return emit(options.command, root, rows)


def main():
    try:
        return run()
    except (infra.InfraError, OSError) as error:
        print(json.dumps({"succeeded": False, "error": str(error)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
