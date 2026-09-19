"""The deterministic test tree, and the one thing it may never do.

W194457, operational finding: a wiring attempt in claim 195045 reached
`single_worker._engine_run` -- `subprocess.run` on a real `docker run` argv --
and HUNG until the test process was killed. Whether a container actually
started is not knowable after the fact. The design that reached the engine has
since been superseded by the owner's trusted-configuration decision, so nothing
in the product tries to start a container from a composition any more. THE
GUARD STAYS ANYWAY: it costs one environment lookup, it is not about that
design, and a tree that can hang on an unintended `docker run` is one that can
hang again for a reason nobody has thought of yet.

WHY IT FAILS FAST RATHER THAN RECORDING. A hang is the worst possible shape for
this mistake: it produces no traceback, no named resource and no bound on what
was created. Raising on the FIRST unintended call gives the exact stack that
reached the boundary, before any container exists, and the suite fails in
milliseconds instead of hanging.

WHY IT IS NOT `subprocess.run`. Plenty of deterministic cases legitimately run
local processes. The guarded boundary is the single place this package starts
CONTAINERS, so the guard says exactly what it means.

THE ENGINE SUITES ARE UNAFFECTED. `tests/manager/test_*_engine.py` drive a real
engine through their own `subprocess.run` and their own skip conditions; they
never went through this boundary. A deterministic case that genuinely wants the
real runner asks for it out loud with `allowed_live_engine()`.
"""
import contextlib
import os


ALLOW = "BATON_V12_ALLOW_LIVE_ENGINE"


class UnintendedLiveEngine(RuntimeError):
    """A deterministic test reached the real container runner."""


@contextlib.contextmanager
def allowed_live_engine():
    """Opt one block into the real runner, out loud and bounded."""
    before = os.environ.get(ALLOW)
    os.environ[ALLOW] = "1"
    try:
        yield
    finally:
        if before is None:
            os.environ.pop(ALLOW, None)
        else:
            os.environ[ALLOW] = before


def _install_live_engine_guard():
    from tools import single_worker

    real = single_worker._engine_run
    if getattr(real, "_baton_v12_guarded", False):
        return real

    def guarded(argv, *, seconds=None):
        if os.environ.get(ALLOW) == "1":
            return real(argv, seconds=seconds)
        raise UnintendedLiveEngine(
            "a deterministic test reached the REAL container engine runner "
            "with argv " + repr(list(argv)[:6]) + "; nothing in this tree may "
            "start a container. Inject an engine port into the composition "
            "under test, or wrap the call in tests.allowed_live_engine() if "
            "a real engine is genuinely the subject.")

    guarded._baton_v12_guarded = True
    single_worker._engine_run = guarded
    return guarded


_install_live_engine_guard()
