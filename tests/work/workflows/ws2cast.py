"""The shared WS-2 verification cast: a Lang provider whose reviewer route
is explicit, and three consumer teams each holding a `verify` endpoint."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wfdriver import team                                     # noqa: E402


def verification_teams() -> dict:
	spec = {}
	for name, member in (("push", "sl"), ("web", "wren"), ("mdb", "mo")):
		spec[name] = team(
			name.title(),
			{member: {"display": member.title(), "roles": ["dev"]}},
			{"dev": {"display": "Developer"}},
			{"main": {"role": "dev", "handlers": [member]}},
			{"bug": {"display": "Bug", "route": "main"},
			 "verify": {"display": "Verify", "route": "main"}})
	# W73: a handoff derives its phase from the destination ROUTE, so a
	# provider that receives passes needs real per-stage roles rather
	# than one generic `dev`. The cast's shape is otherwise unchanged.
	spec["lang"] = team(
		"Lang",
		{"ada": {"display": "Ada", "roles": ["rsrch", "impl"],
		         "capabilities": ["config"]},
		 "grace": {"display": "Grace", "roles": ["rsrch", "impl"]}},
		{"rsrch": {"display": "Research"},
		 "impl": {"display": "Implementation"}},
		{"intake": {"role": "rsrch", "handlers": ["ada"]},
		 "build": {"role": "impl", "handlers": ["ada"]}},
		{"rsrch": {"display": "Research", "route": "intake"},
		 "impl": {"display": "Implement", "route": "build"}})
	return spec
