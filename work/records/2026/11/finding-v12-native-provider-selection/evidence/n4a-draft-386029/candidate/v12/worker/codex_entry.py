"""Codex construction through the existing validated, reaping worker entry.

This draft adds no serve loop, launch reader or signal handler. The adapter
continues to refuse home preparation until its selected shared join exists.
"""
import sys

import dogfood_entry
from codex_agent import CodexAgent


def production(place=None, read=None, build=None, command_root=None, event_root=None):
    return dogfood_entry._production(place=place, read=read,
        build=CodexAgent if build is None else build,
        command_root=command_root, event_root=event_root)


def main():
    return dogfood_entry.supervised(run=production)


if __name__ == "__main__":
    sys.exit(main())
