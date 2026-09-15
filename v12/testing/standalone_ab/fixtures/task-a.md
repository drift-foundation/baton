# A: normalize greeting names

Implement this complete request on A's private line from the frozen original
base. Change only `demo/greeting.py` and `tests/test_greeting.py`.

`greet(name)` must strip surrounding whitespace, return `Hello, Ada!` for
both `Ada` and ` Ada `, and raise `ValueError("name is empty")` for empty or
whitespace-only names. Preserve the existing punctuation and ordinary-name
case. Replace the existing surrounding-spaces expectation with the trimmed
result. Add assertions for empty and whitespace-only rejection, including the
exception message. This explicitly schedules that existing-test behavior
change; retain the ordinary-name assertion.

Required verification argv: `["python3", "check_greeting.py"]`.
Submission `test_scope`: `["tests/test_greeting.py"]`.

No deliberate omission or injected correction is requested. If the independent
review requests a real correction, use the normal same-line correction path.
