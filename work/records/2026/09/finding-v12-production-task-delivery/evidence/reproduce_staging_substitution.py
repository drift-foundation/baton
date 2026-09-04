#!/usr/bin/env python3
"""Show whether task publication remains bound to its proved descriptor."""

import os
import stat
import tempfile
from unittest import mock

from tools import single_worker


def main():
    held = b'{"schema":"held-task"}'
    foreign = b'{"schema":"foreign-task"}'
    worker = object.__new__(single_worker._SingleWorker)
    worker.given = {"task_bytes": held}

    with tempfile.TemporaryDirectory(prefix="w81115-staging-") as inputs:
        place = os.path.join(inputs, single_worker.TASK_DOCUMENT)
        foreign_place = os.path.join(inputs, "foreign.json")
        with open(foreign_place, "wb") as writing:
            writing.write(foreign)
        link = os.link

        def substitute(staged, final, **options):
            os.unlink(staged)
            os.symlink(foreign_place, staged)
            return link(staged, final, **options)

        refused = None
        with mock.patch.object(single_worker.os, "link", substitute):
            try:
                worker._published_task(inputs)
            except BaseException as failure:
                refused = f"{type(failure).__name__}: {failure}"

        found = os.lstat(place)
        with open(place, "rb") as reading:
            final = reading.read()
        print({"refused": refused,
               "final_is_symlink": stat.S_ISLNK(found.st_mode),
               "foreign_bytes_published": final == foreign,
               "held_bytes_published": final == held})


if __name__ == "__main__":
    main()
