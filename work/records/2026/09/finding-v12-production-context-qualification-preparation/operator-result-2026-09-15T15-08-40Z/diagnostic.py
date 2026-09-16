import json
import os
import stat
from pathlib import Path


work = Path("/tmp/baton-w177936-qualification-178579/work")
expected = b"def scale(value):\n    return value * 2\n"
report = {}

try:
    info = work.lstat()
    if not stat.S_ISDIR(info.st_mode):
        raise ValueError("workspace is not a regular directory")
    entries = list(work.iterdir())
    report["workspace"] = {
        "entries": len(entries),
        "unexpected_entries": sum(p.name != "solution.py" for p in entries),
        "mode": oct(stat.S_IMODE(info.st_mode)),
        "uid": info.st_uid,
        "gid": info.st_gid,
    }
    target = work / "solution.py"
    info = target.lstat()
    report["solution"] = {
        "regular_file": stat.S_ISREG(info.st_mode),
        "size": info.st_size,
        "mode": oct(stat.S_IMODE(info.st_mode)),
        "uid": info.st_uid,
        "gid": info.st_gid,
    }
    fd = os.open(target, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        if stat.S_ISREG(info.st_mode) and info.st_size <= 65536:
            actual = stream.read(65537)
            report["solution"].update(
                exact_match=actual == expected,
                matches_after_crlf_normalization=actual.replace(b"\r\n", b"\n") == expected,
                matches_ignoring_outer_whitespace=actual.strip() == expected.strip(),
            )
except (OSError, ValueError) as error:
    report["inspection_error"] = type(error).__name__

result = json.loads(Path("/tmp/baton-w177936-qualification-178579-export/qualification.json").read_text())
report["failure_code"] = result["failure_code"]
report["terminal"] = result["arms"][0]["terminal"]
print(json.dumps(report, indent=2))
