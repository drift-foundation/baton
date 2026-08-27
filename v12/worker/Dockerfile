# The v12 OCI reference worker image.
#
# W6633. Every line here is a decision the acceptance names, so each carries
# the reason rather than the setting alone.
#
# THE BASE IS PINNED BY DIGEST, not by tag. `python:3.13-slim` is a name
# somebody moves; a worker built from a moved tag is a worker nobody can say
# the contents of afterwards, which makes the image digest the manager records
# a description of something else. The digest below is the one this recipe was
# built and reviewed against, and changing it is a reviewed change.
# Resolved 2026-08-24 from `docker manifest inspect -v python:3.13-slim`
# on this host: docker.io/library/python:3.13-slim at the index digest
# below. Recorded rather than described, so a reviewer can re-resolve it.
FROM python@sha256:8fef26df932191825664e4957ff488c96dfe64918327634a357a55facbc994d3

# NO BUILD TOOLCHAIN, NO PACKAGE MANAGER STATE, NO NETWORK CLIENT. The worker
# runs one Python program; anything else in the image is something a
# compromised worker can use.
#
# The two files ARE the program. Nothing from `baton_v12` is copied in: a
# worker that could import the manager is a worker one bug away from holding
# the manager's capabilities, and the absence is enforced by a case rather than
# by this comment.
COPY baton_worker.py /opt/baton/baton_worker.py
COPY scripted_agent.py /opt/baton/scripted_agent.py

# AND THE FROZEN CONTRACT, AS DATA. W19784 review [P0]: the worker read the
# manager's two `/input/` documents by picking out the members it wanted, so a
# false self-digest or an extra top-level member -- a second identity alias,
# which the ruling rejected -- reached the agent.
#
# This is a DATA file, not code, and it is not `baton_v12`. The rule above is
# that the worker must not be able to import the manager; a schema document is
# the contract both sides are held to, and shipping it is what lets the worker
# derive the closed member sets instead of carrying a hand-typed second copy
# of them. `test_frozen` proves this copy is byte-identical to the other four,
# so there is one contract with five identical copies rather than five
# contracts. The image gains no library and no import path it did not have.
COPY worker-control-1.0.schema.json /opt/baton/worker-control-1.0.schema.json

# A FIXED NON-ROOT USER, by numeric id so it does not depend on a passwd entry
# the base image might change. 65532 is the conventional "nonroot" id and is
# the same one the adapter's `--user` restriction names -- two places agreeing
# because they were written from one decision, and a case asserts they agree.
USER 65532:65532

# No shell form, so there is no shell in the process tree and nothing to
# interpret a signal or a metacharacter on the worker's behalf. The manager
# stops this container by signalling PID 1, and PID 1 is Python.
ENTRYPOINT ["python3", "/opt/baton/baton_worker.py"]

# Deterministic bytes: no `.pyc` written at run time, unbuffered streams so a
# frame is never left in a buffer when the process is stopped, and the module
# path is explicit rather than inherited from a working directory.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/opt/baton \
    PYTHONHASHSEED=0

# The posture and the SESSION IDENTITY both arrive from the manager, never
# from the image. An image that defaulted to a posture would run as
# `execution` when the manager forgot to say -- and forgetting is exactly when
# a default matters. An image that carried a session identity would be an
# image every container built from it shares one identity with, which is the
# opposite of what `baton.worker-entry/1` binds a frame to.
#
# There is deliberately no `ENV BATON_WORKER_POSTURE` and no
# `ENV BATON_WORKER_SESSION`. A container started without the session cannot
# correlate anything it says, so it exits non-zero WITHOUT a frame and the
# Worker Manager settles its already identified operation from the engine.
#
# There is also no `VOLUME`, no `EXPOSE` and no `HEALTHCHECK`: the worker has
# no network, its writable workspace is a mount the manager names per
# assignment, and its health is observed by the adapter through the engine
# rather than announced by the container.
