"""SOURCE PROFILES: what a worker does with the directory it was mounted.

W71917's other half, and it is a SEPARATE PACKAGE for one reason that is worth
stating before anything else: the Worker Manager is Git-agnostic, and a
boundary that exists only as a paragraph in a docstring is a boundary the next
change walks through. `baton_v12.worker_manager` does not import this package,
this package imports nothing from it, and `tests/manager/test_dependencies`
holds the manager to a vocabulary in which none of the words below appear.

WHAT THE MANAGER DID, so a reader can see where this begins. It validated one
nominated source directory, bound it READ-ONLY at `/input/source` without
walking, copying, hashing or enumerating it, and gave the worker one writable
disk-backed workspace whose declared capacity it proved the storage could meet
before the runtime started. It carried a PROFILE word through the input
manifest as opaque text. It did not look inside either tree.

THAT CAPACITY IS ADMISSION EVIDENCE AND NOT A CEILING THE WORKER IS HELD TO,
which is worth knowing here because this is the package that decides how much
a checkout writes. The workspace bind is ordinary and writable; only the
runtime's small `/tmp` and `/dev/shm` are bounded by the kernel.

WHAT A PROFILE IS. The word the worker reads back, and the plan it implies for
turning a read-only mount into something the worker may work in. Two exist:

  `generic`  the mount is the source, read in place. Nothing is cloned,
             nothing is inferred, and the workspace is for what the worker
             PRODUCES rather than for a second copy of what it was given.
  `git`      the worker clones from the mount into its own workspace and then
             verifies the base revision the assignment DECLARED. The clone is
             copy-safe -- no hardlinks into the read-only mount -- and the
             verification is the worker proving it received what it was
             promised, which is exactly the proof the manager is not allowed
             to perform on its behalf.

BOTH USE THE SAME BOUNDARY. That is the point of having two rather than one:
the generic profile is not a degraded version of the Git one, it is the same
mount and the same workspace with no version-control inference at all, and a
tree that happens to carry version-control metadata gets no different
treatment unless the assignment DECLARED that it should.

THESE ARE PLANS, NOT EXECUTIONS. Every function here composes a closed argument
vector and returns it; nothing here starts a process, and no capability to do
so is imported. That is the manager's own `run_vector` shape and it is the
right one for the same reasons: a vector is provable without the tool it names,
the party that runs it is the party that owns the failure, and a composer that
also executed would be two boundaries wearing one name.
"""

from .checkout import (BASE_KINDS, CHECKOUT_NAME, GENERIC_PROFILE,
                       GIT_PROFILE, PROFILES, ProfileRefusal, checkout_plan,
                       check_declared_base, clone_vector, detach_vector,
                       verify_vector)

__all__ = ["BASE_KINDS", "CHECKOUT_NAME", "GENERIC_PROFILE", "GIT_PROFILE",
           "PROFILES", "ProfileRefusal", "checkout_plan",
           "check_declared_base", "clone_vector", "detach_vector",
           "verify_vector"]
