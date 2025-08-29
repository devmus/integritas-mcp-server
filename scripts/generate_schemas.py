# scripts\generate_schemas.py

from __future__ import annotations
import json, pathlib
from integritas_mcp_server.models import StampRequest, StampResponse

OUT = pathlib.Path("schemas")
OUT.mkdir(parents=True, exist_ok=True)

(OUT / "stamp.request.schema.json").write_text(json.dumps(StampRequest.model_json_schema(), indent=2))
(OUT / "stamp.response.schema.json").write_text(json.dumps(StampResponse.model_json_schema(), indent=2))

manifest = {
  "tools": [
    {
      "name": "stamp_hash",
      "description": "Stamp a content hash on the Minima blockchain.",
      "input_schema": StampRequest.model_json_schema(),
      "output_schema": StampResponse.model_json_schema(),
    }
  ]
}
(OUT / "tools.manifest.json").write_text(json.dumps(manifest, indent=2))

print(f"Wrote schemas to {OUT}/")
