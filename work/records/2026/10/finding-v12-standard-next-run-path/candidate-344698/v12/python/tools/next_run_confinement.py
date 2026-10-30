"""Landlock confinement from accepted managed entry7547b27f; fail closed."""
import ctypes
import os
import platform

def refuse(message):
    raise ValueError(message)

def restrict_writes(root):
    """Linux Landlock ABI>=3; deny content writes/create/remove outside root.

    Rules bind inodes, not a checked path spelling. Descendants inherit the
    restriction. Docker daemon is not a descendant, hence operational custody
    above is separately mandatory. No namespace rewrites host mount paths.
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
    try:
        allowed = Beneath(writes,parent)
        call(445,ruleset,1,ctypes.byref(allowed),0)
        if libc.prctl(38,1,0,0,0) != 0:
            raise OSError(ctypes.get_errno(),'no_new_privs refusal')
        call(446,ruleset,0)
    finally:
        os.close(parent)
        os.close(ruleset)

