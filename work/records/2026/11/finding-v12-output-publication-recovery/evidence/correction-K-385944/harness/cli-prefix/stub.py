"""Deterministic stand-in for the provider API: no model. Scripted tool calls.

argv: PORT SCRIPT.json LOG.  SCRIPT is a list of Bash tool inputs; each
conversation turn with N tool_results so far gets script[N], then a final text.
"""
import json, sys, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
PORT, SCRIPT, LOG = int(sys.argv[1]), json.load(open(sys.argv[2])), sys.argv[3]
lock = threading.Lock()
def log(doc):
    with lock, open(LOG, "a") as out:
        out.write(json.dumps(doc) + "\n")
def sse(events):
    return "".join(f"event: {e['type']}\ndata: {json.dumps(e)}\n\n" for e in events).encode()
def message(model, blocks, stop):
    events = [{"type": "message_start", "message": {"id": "msg_stub", "type": "message", "role": "assistant", "model": model, "content": [], "stop_reason": None, "stop_sequence": None, "usage": {"input_tokens": 1, "output_tokens": 1}}}]
    for i, b in enumerate(blocks):
        if b["type"] == "text":
            events += [{"type": "content_block_start", "index": i, "content_block": {"type": "text", "text": ""}},
                       {"type": "content_block_delta", "index": i, "delta": {"type": "text_delta", "text": b["text"]}}]
        else:
            events += [{"type": "content_block_start", "index": i, "content_block": {"type": "tool_use", "id": b["id"], "name": b["name"], "input": {}}},
                       {"type": "content_block_delta", "index": i, "delta": {"type": "input_json_delta", "partial_json": json.dumps(b["input"])}}]
        events.append({"type": "content_block_stop", "index": i})
    events += [{"type": "message_delta", "delta": {"stop_reason": stop, "stop_sequence": None}, "usage": {"output_tokens": 1}}, {"type": "message_stop"}]
    return events
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        log({"GET": self.path}); self.send_response(404); self.end_headers()
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("content-length", 0))) or b"{}")
        tools = [t.get("name") for t in body.get("tools", [])]
        results = []
        for m in body.get("messages", []):
            if isinstance(m.get("content"), list):
                results += [c for c in m["content"] if c.get("type") == "tool_result"]
        log({"TOOLS": sorted(tools)}) if tools else None
        log({"POST": self.path, "model": body.get("model"), "stream": body.get("stream"), "tools": len(tools), "has_bash": "Bash" in tools, "results": [json.dumps(r.get("content"))[:1500] for r in results]})
        if "count_tokens" in self.path:
            out = json.dumps({"input_tokens": 1}).encode(); ctype = "application/json"
        else:
            if "Bash" in tools and len(results) < len(SCRIPT):
                blocks = [{"type": "tool_use", "id": f"toolu_{len(results):02d}", "name": "Bash", "input": SCRIPT[len(results)]}]; stop = "tool_use"
            else:
                blocks = [{"type": "text", "text": "done"}]; stop = "end_turn"
            if body.get("stream"):
                out = sse(message(body.get("model"), blocks, stop)); ctype = "text/event-stream"
            else:
                out = json.dumps({"id": "msg_stub", "type": "message", "role": "assistant", "model": body.get("model"), "content": blocks, "stop_reason": stop, "stop_sequence": None, "usage": {"input_tokens": 1, "output_tokens": 1}}).encode(); ctype = "application/json"
        self.send_response(200); self.send_header("content-type", ctype); self.send_header("content-length", str(len(out))); self.end_headers(); self.wfile.write(out)
ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
