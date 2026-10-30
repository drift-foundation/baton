"""Landlock confinement from accepted managed entry7547b27f; fail closed."""
import ctypes
import os
import platform
import stat

# THE ONE FACILITY REAL SOURCE-LINE MATERIALIZATION NEEDS, and nothing else.
#
# W339626, run w339626-live-345599: the live start failed before any runtime
# with `ProfileRefusal: Git line materialization failed: fatal: could not open
# '/dev/null' for reading and writing: Permission denied`. Git's subprocess
# launcher opens the null device O_RDWR to suppress a child's streams, and the
# sole rule below allowed writes only beneath the run root -- so the open was
# denied and the clone never started. Reproduced with this module unchanged,
# the real kernel and a real `git clone`: errno 13, and the composed message is
# the recorded 125-character field exactly.
#
# WHAT THIS IS NOT. Not a /dev grant, not a writable-root expansion, not a
# caller-selected path: the device is FIXED here, identified by TYPE and DEVICE
# NUMBER rather than by its spelling, and it receives WRITE_FILE alone -- no
# truncate, no create, no remove, no directory right. A null device cannot
# carry data, so a write right over it leaks nothing; the point is only that
# the open succeeds.
#
# AND IT FAILS CLOSED. If the path is absent, is not a character device, or is
# not the null device's (1,3), confinement REFUSES rather than proceeding with
# a weaker boundary or an unexamined inode.
NULL_DEVICE = '/dev/null'
NULL_DEVICE_NUMBER = (1, 3)
WRITE_FILE = 2

def refuse(message):
    raise ValueError(message)

def _null_device():
    """The null device's own inode, type-proved and device-number-proved.

    O_PATH|O_NOFOLLOW: the descriptor is for naming an inode to Landlock and
    never for reading or writing, and a symlink in its place is refused rather
    than followed. The rule binds the INODE this returns, so a later path
    substitution cannot redirect it -- the same reason the root rule binds a
    descriptor and not a spelling.
    """
    try:
        held = os.open(NULL_DEVICE, os.O_PATH | os.O_NOFOLLOW)
    except OSError as failed:
        refuse(f'the null device {NULL_DEVICE} could not be opened for '
               f'confinement: {failed.strerror}')
    try:
        state = os.fstat(held)
        if not stat.S_ISCHR(state.st_mode):
            refuse(f'{NULL_DEVICE} is not a character device')
        if (os.major(state.st_rdev), os.minor(state.st_rdev)) \
                != NULL_DEVICE_NUMBER:
            refuse(f'{NULL_DEVICE} is not the null device')
    except BaseException:
        os.close(held)
        raise
    return held

def restrict_writes(root):
    """Linux Landlock ABI>=3; deny content writes/create/remove outside root.

    Rules bind inodes, not a checked path spelling. Descendants inherit the
    restriction. Docker daemon is not a descendant, hence operational custody
    above is separately mandatory. No namespace rewrites host mount paths.

    TWO rules and no more: every handled write right beneath `root`, and
    WRITE_FILE on the validated null device, which a real Git subprocess
    launcher opens O_RDWR before it can start. See NULL_DEVICE above.
    """
    if platform.system() != 'Linux' or platform.machine() not in ('x86_64','aarch64'):
        refuse('unsupported Landlock platform')
    libc = ctypes.CDLL(None, use_errno=True)
    def call(number, *args):
        result = libc.syscall(number, *args)
        if result < 0: raise OSError(ctypes.get_errno(), 'Landlock refusal')
        return result
    if call(444, 0, 0, 1) < 3:
        refuse('Landlock ABI3 required for truncate confinement')
    writes = 2 | sum(1 << n for n in range(4,15))
    class Ruleset(ctypes.Structure):
        _fields_ = [('fs', ctypes.c_uint64)]
    class Beneath(ctypes.Structure):
        _pack_ = 1
        _fields_ = [('access',ctypes.c_uint64),('fd',ctypes.c_int32)]
    rule = Ruleset(writes)
    ruleset = call(444, ctypes.byref(rule), ctypes.sizeof(rule), 0)
    parent = os.open(root, os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW)
    # VALIDATED BEFORE THE RULESET IS ENFORCED, so a bad or missing device
    # refuses with nothing applied rather than leaving a half-built boundary.
    null = _null_device()
    try:
        allowed = Beneath(writes,parent)
        call(445,ruleset,1,ctypes.byref(allowed),0)
        permitted = Beneath(WRITE_FILE,null)
        call(445,ruleset,1,ctypes.byref(permitted),0)
        if libc.prctl(38,1,0,0,0) != 0:
            raise OSError(ctypes.get_errno(),'no_new_privs refusal')
        call(446,ruleset,0)
    finally:
        os.close(null)
        os.close(parent)
        os.close(ruleset)

