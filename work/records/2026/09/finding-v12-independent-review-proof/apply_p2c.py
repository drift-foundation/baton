import pathlib

p = pathlib.Path(__file__).resolve().parent / "test_attachment.py"
lines = p.read_text(encoding="utf-8").split("\n")
# 0-indexed: 526..538 is the docstring tail and the act.
assert lines[526].strip().startswith("claims. `create_line`"), lines[526]
assert lines[536].strip() == 'authority_uuid=AUTHORITY, work_id=WORK)', lines[536]
replacement = '''        claims. `create_line` is one of the product's own mutators, and the
        operands name a Work this store holds NO line for, so it has to INSERT
        one.

        THE FIRST DRAFT OF THIS CASE PASSED THE EXISTING WORK AND NOTHING WAS
        RAISED -- correctly: that call is a pure replay, and a replay writes
        nothing. Measuring a read-only boundary with an operand that needs no
        write measures nothing at all, and the draft is recorded here rather
        than quietly replaced.
        """
        fresh = AUTHORITY[:8] + "-W31337"
        reader = attachment.reading(self.control_path, clock=lambda: NOW)
        try:
            with self.assertRaises(Exception) as caught:
                create_line(reader, source=nominate_source(self.source),
                            declared_base=BASE, profile=self.profile,
                            authority_uuid=AUTHORITY, work_id=fresh)'''.split("\n")
lines[526:537] = replacement
p.write_text("\n".join(lines), encoding="utf-8")
print("applied")
