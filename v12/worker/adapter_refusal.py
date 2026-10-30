"""THE SHARED TYPED ADAPTER DECLARATION REFUSAL, and its four codes.

W376586, owner E376465, `AMENDMENT-376531.md` SHA-256
`ced2e81f031e7f56c060963d2724cca524e1a7e17e3e5f18d1c5fc777c38f68e`,
beside DESIGN OBS-3a.

ONE MODULE SO ONE TYPE. The amendment requires the catch to "exercise actual
package imports so a duplicate type definition cannot defeat it": if the
producer and the catcher each defined their own class, an `except` would be
testing identity against the wrong object and a typed refusal would escape as
a generic agent failure. Every party imports THIS module.

FOUR LITERAL CAUSES AND NO OTHERS. They are the four pre-provider shared-role
declaration faults, in the order the existing check already applies them:

    declaration-set-invalid        the declaration set is not a usable set --
                                   absent, empty, or naming one output twice
    declaration-name-unsupported   a declared name this workload does not write
    role-output-missing            no declaration for an output THIS role writes
    other-role-output-required     an output this role does not write, declared
                                   required, which no single turn can satisfy

A MALFORMED GENERAL DECLARATION, A BARE `TaskRefusal`, AN UNKNOWN EXCEPTION OR
A PROVIDER FAILURE IS NONE OF THESE. The amendment forbids reaching a code by
string matching, so a code is only ever passed as one of these literals by the
check that actually established it.

NOTHING BUT TRUSTED LITERALS CROSSES. The typed evidence carries the component,
the code and the role and nothing else -- no exception text, class, repr or
attribute, no output name, no provider content, no host path and no arbitrary
identifier. That is why `facts()` composes its answer from the constants below
rather than from anything it was handed.
"""

COMPONENT = "role-adapter"

SET_INVALID = "declaration-set-invalid"
NAME_UNSUPPORTED = "declaration-name-unsupported"
ROLE_OUTPUT_MISSING = "role-output-missing"
OTHER_ROLE_OUTPUT_REQUIRED = "other-role-output-required"

CODES = (SET_INVALID, NAME_UNSUPPORTED, ROLE_OUTPUT_MISSING,
         OTHER_ROLE_OUTPUT_REQUIRED)

ROLES = ("implementation", "review")


class AdapterDeclarationRefusal(Exception):
    """One pre-provider declaration fault, typed, from trusted literals.

    IT SUBCLASSES THE WORKLOAD'S OWN REFUSAL at the import site rather than
    here, so this module stays free of provider imports and every existing
    caller that already handles the generic refusal keeps working byte for
    byte. What is ADDED is the three facts a report may carry.

    THE CODE AND ROLE ARE CHECKED, not trusted. A caller that passed anything
    but one of the closed literals would be inventing a cause, which is the
    one thing the four-code vocabulary exists to prevent -- so this raises
    `ValueError` for that, which is a programming fault rather than a task
    refusal and must not be reportable as one.
    """

    def __init__(self, message, *, code, role):
        if code not in CODES:
            raise ValueError("an adapter declaration refusal carries one of "
                             + ", ".join(CODES))
        if role not in ROLES:
            raise ValueError("an adapter declaration refusal names one of "
                             + ", ".join(ROLES))
        super().__init__(message)
        self.component = COMPONENT
        self.code = code
        self.role = role

    def facts(self):
        """The typed evidence, and nothing else.

        Composed from this object's own three checked members, so no message,
        output name or provider content can ride along.
        """
        return {"component": COMPONENT, "code": self.code, "role": self.role}
