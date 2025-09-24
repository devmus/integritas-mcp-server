# # services/stamp_data_helpers/mapping.py
# from typing import Any, Dict, Optional
# from ...models import StampDataResponse
# from .timeparse import parse_iso_utc
# from .status import map_status

# def map_payload_to_response(payload: Dict[str, Any], fallback_request_id: Optional[str]) -> StampDataResponse:
#     # Expected upstream shape:
#     # {
#     #   apiVersion, requestId, status, statusCode, message, timestamp,
#     #   data: {
#     #     sourceFile: { fileHash },
#     #     forwarded: { status, data, uid },
#     #     proofData: { ... },
#     #     proofFile: { filename, downloadUrl, ... }
#     #   }
#     # }
#     data = payload.get("data", {}) if isinstance(payload, dict) else {}
#     proof_file = data.get("proofFile") or {}
#     forwarded = data.get("forwarded") or {}

#     mapped_status = map_status(payload.get("status"))
#     uid = forwarded.get("uid")
#     stamped_at = parse_iso_utc(payload.get("timestamp"))
#     proof_url_raw = proof_file.get("download_url")

#     parts = []
#     if mapped_status: parts.append(f"Status: {mapped_status}")
#     if uid: parts.append(f"UID: {uid}")
#     if proof_url_raw: parts.append("Proof file ready")
#     summary = " · ".join(parts) or "Stamp request processed."

#     return StampDataResponse(
#         requestId=fallback_request_id or payload.get("requestId") or "unknown",
#         status=mapped_status or "unknown",
#         uid=uid,
#         stamped_at=stamped_at,
#         proof_url=proof_url_raw,
#         summary=summary,
#     )
