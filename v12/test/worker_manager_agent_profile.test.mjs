// W2929 item 4, first slice: certifying one agent-session profile.
//
// THE FIXTURES BELOW ARE THE DESIGN MODEL'S OWN PROFILES, copied verbatim
// from `work/records/2026/08/finding-v12-isolated-agent-workers/findings/
// finding-v12-worker-contract/findings/finding-acp-agent-boundary/evidence/
// traces.json`, including their `document_digest`.
//
// That matters more than it looks. Those digests were computed by the ACP
// boundary's own model, and MEASURED HERE: both recompute exactly under this
// manager's RFC 8785 canonicalization. So the seal these cases check is not a
// number this suite produced and then agreed with — it is the design's, and
// the two boundaries independently arrive at it.
//
// They are embedded rather than read, because `v12/` is self-contained and a
// test that reached into another Work's dossier at run time would be the same
// mistake the module's own comment refuses.

import test, { after } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { ownedTemp, removeOwnedRoots } from "./owned_roots.mjs";
import { ContractError, GOLDEN_BEARER, digest }
	from "../src/worker_manager/contracts.mjs";
import { ControlStore } from "../src/worker_manager/store.mjs";
import { certifyRuntimeProfile, issueOffer }
	from "../src/worker_manager/offers.mjs";
import { AGENT_SESSION_SCHEMA_PATH, certifyAgentSessionProfile,
	isAgentSessionProfileCertified }
	from "../src/worker_manager/agent_profile.mjs";

after(removeOwnedRoots);

const NOW = "2026-08-22T12:00:00.000Z";
const HERE = dirname(fileURLToPath(import.meta.url));
const RECORD = join(HERE, "..", "..", "work", "records", "2026", "08",
	"finding-v12-isolated-agent-workers", "findings",
	"finding-v12-worker-contract", "findings",
	"finding-acp-agent-boundary");

function open() {
	return new ControlStore(join(ownedTemp("v12-manager-"), "control.sqlite3"),
		{ incarnation: "manager-1", clock: () => NOW });
}

test("W2929 review: the product schema is byte-identical to the frozen asset", () => {
	assert.deepEqual(readFileSync(AGENT_SESSION_SCHEMA_PATH), readFileSync(
		join(RECORD, "schema", "agent-session-1.0.schema.json")),
	"the product agent-session schema drifted from the frozen design asset");
});

const ACP_PROFILE = {
	 "session_family": "baton.agent-session",
	 "version": {
	  "major": 1,
	  "minor": 0
	 },
	 "document": "profile",
	 "profile_id": "profile-acp-worker-1",
	 "created_at": "2026-08-21T22:00:00.000Z",
	 "wire_protocol": "acp",
	 "pinned_wire_version": 1,
	 "provider_binding": null,
	 "adapter": {
	  "name": "native-acp-relay",
	  "version": "1.0-design",
	  "build_digest": "sha256:b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1"
	 },
	 "client_capabilities": {
	  "fs": {},
	  "terminal": false
	 },
	 "session_capabilities": [
	  "session.cancel",
	  "session.fresh",
	  "session.mode-pin",
	  "session.permission-refusal",
	  "session.prompt",
	  "session.update-normalization"
	 ],
	 "postures": {
	  "consent": {
	   "policy": {
	    "kind": "acp",
	    "session_mode_id": "plan"
	   },
	   "workspace": false,
	   "declared_output": false
	  },
	  "execution": {
	   "policy": {
	    "kind": "acp",
	    "session_mode_id": "acceptEdits"
	   },
	   "workspace": true,
	   "declared_output": true
	  }
	 },
	 "mcp_servers": [],
	 "limits": {
	  "setup_deadline_ms": 120000,
	  "turn_deadline_ms": 900000,
	  "cancel_drain_deadline_ms": 30000,
	  "max_event_bytes": 16000,
	  "max_queue_events": 1024,
	  "max_queue_bytes": 4194304
	 },
	 "agent_policy_digest": "sha256:c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3",
	 "document_digest": "sha256:3c7b7a50953dd4075533c7c3d90d034920f34bb458b07d799d0f61419bccbe4a"
	};

const CODEX_PROFILE = {
	 "session_family": "baton.agent-session",
	 "version": {
	  "major": 1,
	  "minor": 0
	 },
	 "document": "profile",
	 "profile_id": "profile-codex-app-server-1",
	 "created_at": "2026-08-21T22:00:00.000Z",
	 "wire_protocol": "codex-app-server",
	 "pinned_wire_version": null,
	 "provider_binding": {
	  "provider": "codex-app-server",
	  "server_build_id": "codex-cli-0.149.0",
	  "interface_digest": "sha256:70ff479c2fe907c9146af7d4653bc9cd86f89a470cace6a78a76e5e1fb82b7e0",
	  "certified_at": "2026-08-21T23:20:00.000Z",
	  "experimental_api": false
	 },
	 "adapter": {
	  "name": "codex-app-server-adapter",
	  "version": "1.0-design",
	  "build_digest": "sha256:d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4"
	 },
	 "client_capabilities": null,
	 "session_capabilities": [
	  "session.cancel",
	  "session.fresh",
	  "session.mode-pin",
	  "session.permission-refusal",
	  "session.prompt",
	  "session.update-normalization"
	 ],
	 "postures": {
	  "consent": {
	   "policy": {
	    "kind": "codex-app-server",
	    "thread_start": {
	     "approval_policy": "never",
	     "sandbox": "readOnly",
	     "cwd_role": "scratch",
	     "model": "gpt-5-codex"
	    },
	    "turn_start": {
	     "approval_policy": "never",
	     "sandbox_policy": {
	      "type": "readOnly"
	     },
	     "cwd_role": "scratch",
	     "model": "gpt-5-codex"
	    }
	   },
	   "workspace": false,
	   "declared_output": false
	  },
	  "execution": {
	   "policy": {
	    "kind": "codex-app-server",
	    "thread_start": {
	     "approval_policy": "never",
	     "sandbox": "workspaceWrite",
	     "cwd_role": "workspace",
	     "model": "gpt-5-codex"
	    },
	    "turn_start": {
	     "approval_policy": "never",
	     "sandbox_policy": {
	      "type": "workspaceWrite",
	      "network_access": false
	     },
	     "cwd_role": "workspace",
	     "model": "gpt-5-codex"
	    }
	   },
	   "workspace": true,
	   "declared_output": true
	  }
	 },
	 "mcp_servers": [],
	 "limits": {
	  "setup_deadline_ms": 120000,
	  "turn_deadline_ms": 900000,
	  "cancel_drain_deadline_ms": 30000,
	  "max_event_bytes": 16000,
	  "max_queue_events": 1024,
	  "max_queue_bytes": 4194304
	 },
	 "agent_policy_digest": "sha256:c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7",
	 "document_digest": "sha256:6696d638003763c781532cc8010d1109958d13952c79a34db71a4ae3d195a71d"
	};

/** Reseal a modified profile, so a case tests the rule it names rather than
 *  the seal that every edit also breaks. */
function resealed(profile, change) {
	const { document_digest: _was, ...rest } = structuredClone(profile);
	const edited = change(rest) ?? rest;
	return { ...edited, document_digest: digest(edited) };
}

test("W2929: the design model's own profiles certify unchanged", () => {
	const store = open();
	try {
		for (const profile of [ACP_PROFILE, CODEX_PROFILE]) {
			const answer = certifyAgentSessionProfile(store, profile);
			assert.equal(answer.digest, profile.document_digest,
				`${profile.profile_id}: the seal this manager recomputes is `
				+ `not the one the design sealed it with`);
			assert.equal(isAgentSessionProfileCertified(store, answer.digest),
				true, profile.profile_id);
		}
	} finally {
		store.close();
	}
});

test("W2929 review: no generic writer can forge agent-session certification", () => {
	const store = open();
	try {
		const forged = digest({ not: "an agent-session profile" });
		// THE OPERAND IS REFUSED RATHER THAN IGNORED, and the review's own
		// assertion is kept underneath it. Silently dropping a supplied
		// `agent-session` would satisfy this case while turning an attempted
		// agent-session forgery into a SUCCESSFUL RUNTIME one — certifying a
		// digest for an axis the caller never named. So the writer takes no
		// kind at all, and supplying one says so.
		assert.throws(() => certifyRuntimeProfile(store,
			{ kind: "agent-session", name: "forged", digest: forged }),
			(error) => error instanceof ContractError
				&& error.category === "integrity" && error.code === "schema");
		assert.equal(isAgentSessionProfileCertified(store, forged), false,
			"the generic profile writer bypassed shape, seal and policy");
		// And nothing was written to the OTHER axis either.
		assert.equal(store.db.prepare(
			"SELECT COUNT(*) AS n FROM profiles").get().n, 0,
			"a refused kind still certified something");
	} finally {
		store.close();
	}
});

test("W2929 review: runtime certification cannot satisfy agent-session", () => {
	const store = open();
	try {
		certifyRuntimeProfile(store, { name: "runtime-profile",
			digest: ACP_PROFILE.document_digest });
		assert.equal(isAgentSessionProfileCertified(store,
			ACP_PROFILE.document_digest), false,
			"profile lookup crossed the runtime/agent-session version axes");
	} finally {
		store.close();
	}
});

test("W2929 review: agent-session certification cannot satisfy runtime offer", () => {
	const store = open();
	try {
		const { digest: profileDigest } =
			certifyAgentSessionProfile(store, ACP_PROFILE);
		const api = {
			participant: "poc.claude",
			projectWork: () => ({
				authorityUuid: "43c55d4b00ee85c84ae4ed134de36df5",
				workId: "43c55d4b-W1439", status: "open", phase: "queued",
				handler: null, gate: null, ready: true,
			}),
			slotHolder: () => null,
		};
		assert.throws(() => issueOffer(store, api, {
			workId: "43c55d4b-W1439", participant: "poc.claude",
			runtimeAttemptId: "attempt-cross-axis",
			offerId: "offer-cross-axis", inputDigest: digest("input"),
			policyDigest: digest("policy"), profileDigest,
			mintBearer: () => "b".repeat(48),
		}), (error) => error instanceof ContractError
			&& error.category === "policy"
			&& error.code === "profile-uncertified",
		"an agent-session profile certified an offer's runtime profile axis");
	} finally {
		store.close();
	}
});

test("W2929: SHAPE is refused before the seal", () => {
	const store = open();
	try {
		// Both are wrong: the capability list is narrowed AND the declared
		// digest no longer describes the bytes. The shape failure is the one
		// reported, because every later rule reads members the schema has to
		// establish first.
		const broken = { ...structuredClone(ACP_PROFILE),
			session_capabilities: ["session.prompt"] };
		assert.throws(() => certifyAgentSessionProfile(store, broken),
			(error) => error instanceof ContractError
				&& error.category === "integrity" && error.code === "schema");
		assert.equal(store.db.prepare(
			"SELECT COUNT(*) AS n FROM profiles").get().n, 0);
	} finally {
		store.close();
	}
});

test("W2929: the SEAL is refused before policy", () => {
	const store = open();
	try {
		// Shape-valid, seal broken, and the policy rule broken too. A policy
		// decision about a document whose bytes do not match its own digest is
		// a decision about something nobody agreed to, so the seal answers.
		const broken = structuredClone(ACP_PROFILE);
		broken.postures.consent.policy.session_mode_id =
			broken.postures.execution.policy.session_mode_id;
		assert.throws(() => certifyAgentSessionProfile(store, broken),
			(error) => error instanceof ContractError
				&& error.category === "integrity" && error.code === "digest");
	} finally {
		store.close();
	}
});

test("W2929: TWO POSTURES WITH ONE POLICY are refused at certification", () => {
	// MEASURED, not assumed: the two families are refused by DIFFERENT
	// guards, and only one of them is the policy layer.
	//
	// The codex branch of the schema pins consent and execution to two
	// different policy DEFINITIONS, so equal policies are already
	// unrepresentable and the shape check answers first. The ACP branch pins
	// both to one definition with a free-form `session_mode_id`, which the
	// schema cannot compare — and that is exactly the gap the policy rule
	// exists to close. A rule is needed where the schema cannot state it.
	for (const [what, profile, category, code] of [
			["acp", ACP_PROFILE, "policy", "profile-uncertified"],
			["codex", CODEX_PROFILE, "integrity", "schema"]]) {
		const store = open();
		try {
			// Properly resealed, so this is the rule under test and not the
			// seal that every edit also breaks.
			const equal = resealed(profile, (p) => {
				p.postures.consent.policy =
					structuredClone(p.postures.execution.policy);
			});
			assert.throws(() => certifyAgentSessionProfile(store, equal),
				(error) => error instanceof ContractError
					&& error.category === category && error.code === code,
				what);
			assert.equal(store.db.prepare(
				"SELECT COUNT(*) AS n FROM profiles").get().n, 0, what);
		} finally {
			store.close();
		}
	}
});

test("W2929: a profile carrying a live bearer is never certified", () => {
	const store = open();
	try {
		const leaking = resealed(ACP_PROFILE, (p) => {
			p.adapter.version = `1.0-${GOLDEN_BEARER}`;
		});
		assert.throws(() => certifyAgentSessionProfile(store, leaking),
			(error) => error instanceof ContractError
				&& error.code === "secret-leak");
		assert.equal(store.db.prepare(
			"SELECT COUNT(*) AS n FROM profiles").get().n, 0);
	} finally {
		store.close();
	}
});

test("W2929: certification is BY DIGEST, so a re-edit is a new profile", () => {
	const store = open();
	try {
		const first = certifyAgentSessionProfile(store, ACP_PROFILE);
		// The same profile_id, one changed byte, properly resealed. A manager
		// that certified by NAME would have recertified itself.
		const edited = resealed(ACP_PROFILE, (p) => {
			p.postures.execution.policy.session_mode_id = "yolo";
		});
		const second = certifyAgentSessionProfile(store, edited);
		assert.notEqual(second.digest, first.digest);
		assert.equal(isAgentSessionProfileCertified(store, first.digest), false,
			"the superseded bytes are still certified");
		assert.equal(isAgentSessionProfileCertified(store, second.digest), true);
	} finally {
		store.close();
	}
});

test("W2929: a withdrawn profile is not certified", () => {
	const store = open();
	try {
		const { digest: key } = certifyAgentSessionProfile(store, ACP_PROFILE);
		store.db.prepare("UPDATE profiles SET withdrawn_at = ? WHERE digest = ?")
			.run(NOW, key);
		assert.equal(isAgentSessionProfileCertified(store, key), false);
	} finally {
		store.close();
	}
});

test("W2929: the certified bytes are the CANONICAL ones", () => {
	const store = open();
	try {
		// Member order is not identity. A profile whose members arrive in a
		// different order is the same document, and its seal says so.
		const reordered = Object.fromEntries(
			Object.entries(structuredClone(ACP_PROFILE)).reverse());
		const answer = certifyAgentSessionProfile(store, reordered);
		assert.equal(answer.digest, ACP_PROFILE.document_digest);
		assert.equal(answer.bytes,
			certifyAgentSessionProfile(store, ACP_PROFILE).bytes);
	} finally {
		store.close();
	}
});

test("W2929: a runtime profile still certifies its own axis", () => {
	const store = open();
	try {
		// The other side of the kind scoping: closing the cross-axis hole
		// must not close the axis itself.
		const runtimeDigest = digest("a runtime profile");
		certifyRuntimeProfile(store, { name: "runtime-profile",
			digest: runtimeDigest });
		const api = {
			participant: "poc.claude",
			projectWork: () => ({
				authorityUuid: "43c55d4b00ee85c84ae4ed134de36df5",
				workId: "43c55d4b-W1439", status: "open", phase: "queued",
				handler: null, gate: null, ready: true,
			}),
			slotHolder: () => null,
		};
		const offer = issueOffer(store, api, {
			workId: "43c55d4b-W1439", participant: "poc.claude",
			runtimeAttemptId: "attempt-same-axis", offerId: "offer-same-axis",
			inputDigest: digest("input"), policyDigest: digest("policy"),
			profileDigest: runtimeDigest, mintBearer: () => "b".repeat(48),
		});
		assert.equal(offer.offerId, "offer-same-axis");
	} finally {
		store.close();
	}
});

test("W2929: a WITHDRAWN runtime profile certifies nothing", () => {
	const store = open();
	try {
		const runtimeDigest = digest("a runtime profile");
		certifyRuntimeProfile(store, { name: "runtime-profile",
			digest: runtimeDigest });
		store.db.prepare("UPDATE profiles SET withdrawn_at = ? WHERE digest = ?")
			.run(NOW, runtimeDigest);
		const api = {
			participant: "poc.claude",
			projectWork: () => ({
				authorityUuid: "43c55d4b00ee85c84ae4ed134de36df5",
				workId: "43c55d4b-W1439", status: "open", phase: "queued",
				handler: null, gate: null, ready: true,
			}),
			slotHolder: () => null,
		};
		assert.throws(() => issueOffer(store, api, {
			workId: "43c55d4b-W1439", participant: "poc.claude",
			runtimeAttemptId: "attempt-withdrawn", offerId: "offer-withdrawn",
			inputDigest: digest("input"), policyDigest: digest("policy"),
			profileDigest: runtimeDigest, mintBearer: () => "b".repeat(48),
		}), (error) => error instanceof ContractError
			&& error.code === "profile-uncertified");
	} finally {
		store.close();
	}
});
