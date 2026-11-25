"""Fail before fixtures can discover a repository outside their own roots.

This is a test-entry preflight, not a sandbox for deliberately escaping code.
It performs filesystem reads only; no Git command is needed for refusal.
"""
import os
from pathlib import Path
import tempfile


class FixtureIsolationRefusal(RuntimeError):
    pass


REDIRECTS = ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE",
             "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES")
ROOTS = ("TMPDIR", "TEMP", "TMP", "BATON_V12_DISK_ROOT", "BATON_V12_STACK_TEST_ROOT")


def enclosing_repository(path):
    path = Path(path).resolve()
    for parent in (path, *path.parents):
        # lexists includes dangling gitfiles/symlinks: uncertainty refuses.
        if os.path.lexists(parent / ".git") or (
                (parent / "HEAD").is_file() and (parent / "objects").is_dir()
                and (parent / "refs").is_dir()):
            return parent
    return None


def require_fixture_root(path):
    found = enclosing_repository(path)
    if found is not None:
        raise FixtureIsolationRefusal(
            f"fixture root {str(path)!r} is inside Git repository {str(found)!r}; "
            "use a disk-backed directory outside every repository")
    return str(Path(path).resolve())


def preflight(*, environ=None, temporary=None, source=None):
    environ = os.environ if environ is None else environ
    for name in REDIRECTS:
        if name in environ:
            raise FixtureIsolationRefusal(f"fixture execution refuses inherited {name}")
    for name in ROOTS:
        if environ.get(name):
            require_fixture_root(environ[name])
    require_fixture_root(tempfile.gettempdir() if temporary is None else temporary)
    source = Path(__file__).resolve().parents[3] if source is None else Path(source).resolve()
    found = enclosing_repository(source)
    if found is not None and found != source:
        raise FixtureIsolationRefusal(
            "test source export discovers an enclosing Git repository; "
            "give the disposable export independent metadata or move it outside the checkout")
    if os.path.lexists(source / ".git") and (
            (source / ".git").is_symlink() or not (source / ".git").is_dir()
            or (source / ".git" / "commondir").exists()):
        raise FixtureIsolationRefusal("test source must not use linked/shared Git metadata")
