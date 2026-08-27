"""W14251: cut the acquisition/result vocabulary out of worker-control 1.0."""
import json, pathlib, sys

NEUTRAL_SOURCE = {
    "type": "object",
    "properties": {
        "name": {"$ref": "#/$defs/opaqueId"},
        "destination": {"$ref": "#/$defs/relativePath"},
        "required": {"type": "boolean"},
        "content_manifest": {"$ref": "#/$defs/contentManifest"},
        "consumption": {"$ref": "#/$defs/extensions"},
    },
    "required": ["name", "destination", "required", "content_manifest",
                 "consumption"],
    "additionalProperties": False,
}


def revise(path):
    text = path.read_text(encoding="utf-8")
    doc = json.loads(text)
    defs = doc["$defs"]

    # 1. ONE generic staged-input descriptor. No acquisition kind, and no
    #    `uri`: how the directory was populated is outside the manager.
    defs["sourceDescriptor"] = NEUTRAL_SOURCE
    for gone in ("gitSource", "directorySource"):
        del defs[gone]

    # 2. The declared output's kind becomes an OPAQUE label. The manager
    #    compares the declaration against the answer and never reads either.
    defs["outputDescriptor"]["properties"]["type"] = {"$ref": "#/$defs/opaqueId"}

    # 3. The answered output carries the same opaque label plus the
    #    format-specific metadata the ruling names.
    answered = defs["artifactOutput"]
    answered["properties"]["type"] = {"$ref": "#/$defs/opaqueId"}
    answered["properties"]["result_metadata"] = {"$ref": "#/$defs/extensions"}
    answered["required"] = ["name", "type", "status", "content_manifest",
                            "artifact", "result_metadata"]

    written = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
    path.write_text(written, encoding="utf-8")
    return len(defs)


for name in sys.argv[1:]:
    where = pathlib.Path(name)
    print(f"{where}: {revise(where)} defs")
