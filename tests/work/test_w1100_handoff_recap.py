"""W1100: the operating guide teaches the human-handoff recap.

`work/records/2026/08/finding-visible-work-handoff-action/`. After W459
passed to `baton.ops`, the durable pass comment said exactly what the
operator had to do next — and the Messages view did not show it,
because `pass` is deliberately a threadless Work event. The operator
read Messages, saw no recap, and reasonably concluded the instruction
was absent.

The Work's own scope correction (promoted as revision 1) rules that the
fix is neither a projection nor a TUI feature: `pass` already requires
a non-empty comment, and Baton cannot judge whether prose is a
sufficient recap. What was missing is the CONVENTION, written where
agents read it — leave the recap as a discussion Message first, then
perform the authoritative pass, and for a human reviewer or approver
that message is required rather than optional.

So this suite checks the guide, mechanically where it can and by the
three ruled elements where it must. It also pins the scope correction
itself: the guide must not promise the TUI summary or the JSON
projection that this finding superseded.
"""

from __future__ import annotations

import pathlib
import re

from baton_work import cli as _cli

REPO = pathlib.Path(__file__).resolve().parents[2]
GUIDE = REPO / "docs" / "EFFECTIVE-BATON.md"
HEADING = "### Say it in the discussion before you hand it over"


def guide():
	return GUIDE.read_text(encoding="utf-8")


def section():
	"""The handoff section alone, so a phrase elsewhere in the guide
	cannot satisfy a check about this one."""
	body = guide()
	assert HEADING in body, "the handoff convention has no section"
	start = body.index(HEADING)
	rest = body[start + len(HEADING):]
	end = rest.find("\n## ")
	return rest if end < 0 else rest[:end]


def prose(text):
	return " ".join(text.split())


# -- the convention is stated -------------------------------------------------

def test_the_guide_says_a_pass_comment_is_not_a_message():
	"""The fact the operator was missing: it is durable and
	authoritative, and it lives where Messages are not."""
	text = prose(section())
	assert "not a message" in text.lower()
	assert "Events" in text and "Messages" in text
	assert "will not see it" in text, \
		"the guide does not say the consequence plainly"


def test_the_guide_teaches_message_first_then_pass():
	text = section()
	say_at = text.index("$BATON say")
	pass_at = text.index("$BATON pass")
	assert say_at < pass_at, \
		"the example passes before it explains, which is the habit " \
		"this Work exists to correct"
	assert "post the recap first" in prose(text)


def test_a_human_handoff_names_all_three_ruled_elements():
	"""Result or status, the decision or action expected, and the
	recommended next step — the promoted contract names exactly these."""
	text = prose(section())
	assert "not optional" in text
	for element in ("result or current status",
	                "decision or action now expected from the human",
	                "recommended next step"):
		assert element in text, element


def test_the_guide_says_the_human_must_not_reconstruct_it():
	text = prose(section())
	assert "must not have to reconstruct" in text
	assert "agent's job" in text or "agents job" in text


def test_the_guide_calls_it_a_convention_and_not_a_rule():
	"""Baton requires a non-empty comment and cannot judge prose. A
	guide that implied enforcement would be promising something the
	authority does not do."""
	text = prose(section())
	assert "cannot judge" in text
	assert "operating convention" in text
	assert "not a rule the authority enforces" in text


def test_the_authoritative_transfer_is_still_the_pass():
	text = prose(section())
	assert "still the authoritative transfer" in text
	assert "complete audit" in text or "audited" in text


# -- the scope correction is respected ----------------------------------------

def test_the_guide_promises_no_tui_summary_or_new_projection():
	"""The superseded half of the finding. A guide that described the
	current-action summary would document a feature that does not exist
	and that this Work deliberately did not build."""
	text = prose(section())
	for absent in ("current-action summary", "action summary",
	               "handoff projection", "current_action"):
		assert absent not in text, absent


def test_message_counts_are_not_claimed_to_change():
	text = prose(section())
	assert "inflate a discussion count" in text, \
		"the guide no longer explains why the pass stays threadless"
	assert "moves no conversational count" in prose(guide())


# -- the example is real ------------------------------------------------------

def test_every_verb_and_operand_in_the_section_exists():
	"""Mechanical, in W104's spirit: the guide may teach only what the
	CLI actually accepts."""
	text = section()
	for verb in re.findall(r"\$BATON ([a-z-]+)", text):
		assert verb in _cli.GRAMMAR, verb
	for verb, operands in (("say", ("thread", "body")),
	                       ("pass", ("work", "to", "comment"))):
		keys = {key["name"] for key in _cli.GRAMMAR[verb]["keys"]}
		for operand in operands:
			assert operand in keys, (verb, operand)
			assert f"{operand}=" in text, (verb, operand)


def test_the_section_sits_with_the_rest_of_the_handoff_path():
	"""Discoverable where an operator is already reading about `pass`,
	not in an appendix nobody reaches."""
	body = guide()
	assert body.index("## The straight-through path") < body.index(HEADING)
	assert body.index(HEADING) < body.index(
		"## Saying why something is not moving")
