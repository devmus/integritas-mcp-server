# src\integritas_mcp_server\tool_descriptions.py
HEALTH_DESCRIPTION = """
Liveness: quick, in-process check (no network).
"""

READY_DESCRIPTION = """
"""

STAMP_DATA_DESCRIPTION = """
Stamp a file or a hash on the Minima blockchain via Integritas one-shot API.

Input:
  - file_url: Presigned URL (recommended)
  - file_path: Server-accessible local path
  - file_hash: sha3-256 hash of the file
Output:
  - status, uid, stamped_at, proof_url, summary
"""

VERIFY_DATA_DESCRIPTION = """
Verifies data on the Minima blockchain via Integritas one-shot API using a provided proof file .

Input:
  - file_url: Presigned URL (recommended)
  - file_path: Server-accessible local path
Output:
  - result, block_number, nfttxnid, txpow_id, transactionid, matched_hash, verification_url, summary
"""

# STAMP_HASH_DESCRIPTION = """
# Initiates a request to the Integritas API to process a content hash.
# This tool sends the hash to a backend service.
# The API response indicates the immediate status of this request.
# Final confirmation of recording requires checking the status via the 'stamp_status' tool.
# Input:
#   - hash: Sha3-256 hex (with/without 0x) or base64 string. Will be normalized to lowercase hex.
# Output:
#   - uid: A unique identifier for this request.
#   - stamped_at: Timestamp when the request was accepted by the API.
#   - summary: A brief message indicating the immediate result of the API call (e.g., "Hash forwarded successfully").
# """

# STAMP_STATUS_DESCRIPTION = """
# Checks the blockchain transaction status for a list of UIDs.
# Input:
#   - uids: A list of UIDs to check.
# Output:
#   - The full status response object.
# """