#!/usr/bin/env python3
"""Show whether task publication stays bound to its final pathname."""

import os
import stat
from unittest import mock

from baton_v12.job_manager import submit
from baton_v12.worker_manager import attempt_preparation_failure_of
from tests.tools import test_single_worker as cases
from tools import single_worker


case = cases.TheWorkloadDocumentIsDeliveredWithTheProtocolPair(
    methodName="runTest")
case.setUp()
try:
    engine = cases.Engine()
    job, control = case.stores("w81115-final-name-substitution")
    submit(job, case.submission)
    operations = case.operations(job, control, engine)
    foreign = b'{"schema":"foreign-task"}'
    opened = os.open
    substituted = []

    def substitute_after_create(place, flags, *rest, **options):
        handle = opened(place, flags, *rest, **options)
        if isinstance(place, str) \
                and place.endswith(single_worker.TASK_DOCUMENT) \
                and flags & os.O_CREAT and not substituted:
            substituted.append(place)
            os.unlink(place)
            with open(place, "xb") as writing:
                writing.write(foreign)
        return handle

    with mock.patch.object(single_worker.os, "open", substitute_after_create):
        projected = case.running(job, operations)
    stage = projected["jobs"][0]["stages"][0]
    place = substituted[0]
    found = os.lstat(place)
    with open(place, "rb") as reading:
        final = reading.read()
    print({"stage_state": stage["state"],
           "engine_starts": len(engine.starts),
           "preparation_failure": attempt_preparation_failure_of(
               control, stage["attempt_id"]) is not None,
           "final_is_regular": stat.S_ISREG(found.st_mode),
           "final_mode": oct(stat.S_IMODE(found.st_mode)),
           "foreign_bytes_published": final == foreign,
           "held_bytes_published": final == case.task_bytes})
    operations.close()
finally:
    case.doCleanups()
