#!/usr/bin/env python3
"""Show whether task publication refuses a final-name creation race."""

import os
import tempfile
from unittest import mock

from tools import single_worker


def main():
    held = b'{"schema":"held-task"}'
    foreign = b'{"schema":"foreign-task"}'
    worker = object.__new__(single_worker._SingleWorker)
    worker.given = {"task_bytes": held}

    with tempfile.TemporaryDirectory(prefix="w81115-publish-") as inputs:
        place = os.path.join(inputs, single_worker.TASK_DOCUMENT)
        replace = os.replace

        def collide(staged, final):
            with open(final, "xb") as writing:
                writing.write(foreign)
            replace(staged, final)

        refused = None
        with mock.patch.object(single_worker.os, "replace", collide):
            try:
                worker._published_task(inputs)
            except BaseException as failure:
                refused = f"{type(failure).__name__}: {failure}"

        with open(place, "rb") as reading:
            final = reading.read()
        print({"refused": refused,
               "foreign_target_survived": final == foreign,
               "held_target_replaced_it": final == held})


if __name__ == "__main__":
    main()
