#!/usr/bin/env bash
# Friendly-denial layer in front of the kernel boundary (W163 R10:
# self-contained — the guard resolves beside this wrapper).
exec python3 "$(cd "$(dirname "$0")" && pwd)/git_guard.py"
