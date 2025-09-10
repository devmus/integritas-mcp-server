# src\integritas_mcp_server\services\verify_data.py

# async def stamp_data_complete(
#     req: VerifyDataRequest,
#     request_id: Optional[str] = None,
#     api_key: Optional[str] = None,
# ) -> VerifyDataResponse:
#     """
#     Prefer URL upload if present; otherwise use local file path.
#     Returns a validated VerifyDataResponse.
#     """
#     # quick input guard (the model should already enforce one-of)
#     if not (req.file_url or req.file_path):
#         return VerifyDataResponse(
#             requestId=request_id or "unknown",
#             status="failed",
#             summary="Neither file_url nor file_path provided.",
#         )

#     headers = build_headers(req.api_key, api_key)
#     endpoint = f"{API_BASE_URL}/v1/verify/one-shot"