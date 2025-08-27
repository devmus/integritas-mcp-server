from integritas_mcp_server.models import normalize_hash

def test_normalize_hex():
    assert normalize_hash("0xAaBb") == "aabb"
    assert normalize_hash("AABB") == "aabb"

def test_normalize_base64():
    # 0xdeadbeef
    assert normalize_hash("3q2+7w==") == "deadbeef"
