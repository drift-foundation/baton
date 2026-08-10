"""The durable documents must not contradict themselves.

`work/finding-human-console/` is the normative contract: an agent rebooted
with no mailbox history builds from it. That makes an internally inconsistent
document worse than a missing one -- a stale key map is a specification of the
superseded behaviour, sitting beside the rule that superseded it, with nothing
to say which wins.

Found by review rather than by a test: FINDING ruled "no automatic `Re:`" in
one section while its key map still described `r` as editing a `Re: ` line.
"""

from __future__ import annotations

import pathlib
import re

import pytest

FINDING_DIR = (pathlib.Path(__file__).resolve().parents[2]
               / "work" / "finding-human-console")

# The three DURABLE DOCUMENTS, named rather than globbed.
#
# `materialize` projects mailbox messages into this folder, so a glob swept
# them in too. Two consequences, both bad. The suite's test count became a
# function of how much mail had been projected -- it moved by two per
# projection, with no code change, which is exactly the kind of number people
# reconcile by hand and then stop trusting. And the checks themselves were
# wrong for those files: a projection is a byte-exact copy of an immutable
# message, so a rule it presents as current cannot be corrected, only
# superseded elsewhere. History is allowed to record what was true when it was
# written; that is why TRIAL's own historical entries say so in place rather
# than being rewritten.
#
# The store is the authority for projections. These three are the normative
# record, and they are what this file is about.
DOC_NAMES = ("FINDING.md", "PLAN.md", "TRIAL.md")
DOCS = [FINDING_DIR / name for name in DOC_NAMES]


def _lines(path):
	return [(number, text) for number, text
	        in enumerate(path.read_text().splitlines(), start=1)]


def test_the_finding_documents_exist():
	for path in DOCS:
		assert path.is_file(), f"{path.name} is missing"


def test_the_checked_set_does_not_move_with_projections():
	"""The count of these tests must be a property of the TREE, not of how
	much mail has been materialized into the folder. Globbing `*.md` made it
	move by two per projection, which is a suite that quietly disagrees with
	itself between runs."""
	assert len(DOCS) == 3
	projections = [path for path in FINDING_DIR.glob("*.md")
	               if path.name not in DOC_NAMES]
	for path in projections:
		assert path not in DOCS, f"{path.name} is a projection, not the record"


@pytest.mark.parametrize("path", DOCS, ids=lambda p: p.name)
def test_no_document_describes_an_automatic_re_prefix_as_current(path):
	"""The ruling is exact subject preservation. A `Re: ` may appear ONLY
	where the superseded rule is being recorded as superseded, or where a
	subject genuinely contains those characters."""
	# Structural rather than a phrase list. A phrase list has to be extended
	# every time the prose is reworded, which makes it a test of the wording
	# rather than of the property. Two things make a `Re:` legitimate:
	#
	#   1. it sits in a section that is explicitly about what was superseded
	#      or how the decision moved -- history is allowed to quote the rule
	#      it is recording;
	#   2. the line itself says the prefix is NOT what happens.
	history = ("supersed", "reversal", "history", "decided after", "trial round",
	           "decisions", "not implemented", "rejected")
	denial = ("superseded", "supersedes", "no automatic", "no `re:`", "never",
	          "not prefixed", "is noise", "unprefixed", "did not start",
	          "already prefixed", "one prefix per hop")
	section = ""
	for number, text in _lines(path):
		if text.startswith("#"):
			section = text.lstrip("#").strip().lower()
		if "Re: " not in text and "`Re:`" not in text:
			continue
		if any(marker in section for marker in history):
			continue
		assert any(marker in text.lower() for marker in denial), (
			f"{path.name}:{number} presents `Re:` as current behaviour, and is "
			f"not in a section about what was superseded "
			f"(section: {section!r}): {text.strip()}")


@pytest.mark.parametrize("path", DOCS, ids=lambda p: p.name)
def test_no_document_points_at_a_section_that_does_not_exist(path):
	"""A cross-reference to a removed section sends a reader looking for a
	decision that is no longer written down."""
	text = path.read_text()
	headings = {line.lstrip("#").strip().lower()
	            for line in text.splitlines() if line.startswith("#")}
	for number, line in _lines(path):
		match = re.search(r"\(?[Ss]ee ([A-Z][A-Z ]{4,})", line)
		if not match:
			continue
		target = match.group(1).strip().lower()
		assert any(target in heading for heading in headings), (
			f"{path.name}:{number} refers to a section that does not exist: "
			f"{target!r}")


def test_no_decision_is_recorded_as_both_open_and_closed():
	"""The heading and the body have to agree. FINDING §8 said "one settled,
	one open" while both entries read RULED, closed."""
	text = (FINDING_DIR / "FINDING.md").read_text()
	section = text.split("## 8.")[1].split("\n## ")[0]
	heading = section.splitlines()[0].lower()
	says_open = "open" in heading or "unsettled" in heading
	body_has_open = "UNSETTLED" in section or "STILL OPEN" in section
	assert says_open == body_has_open, (
		f"the §8 heading and its body disagree: heading {heading!r}, "
		f"body has an open item: {body_has_open}")
