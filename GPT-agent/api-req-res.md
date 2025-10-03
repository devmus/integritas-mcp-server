Action: `stamp_start`
Endpoint: `/core/v1/timestamp/post`
Post - Req: `{"hash": "3A985DA74FE225B2045C172D6BD390BD855F086E3E9D525B46BFE24511431532"}`

Example Res:

```
{
    "apiVersion": 1,
    "requestId": "my-test-reqest-id",
    "status": "success",
    "statusCode": 200,
    "message": "Hash forwarded successfully",
    "timestamp": "2025-10-03T09:58:08.581Z",
    "data": {
        "status": true,
        "data": "0x3A985DA74FE225B2045C172D6BD390BD855F086E3E9D525B46BFE24511431532",
        "uid": "0xDDECF964CCB254147A92"
    }
}
```

Action: `stamp_status`
Endpoint: `/core/v1/timestamp/get-proof-file-link`
Post - Req: `{"uids": ["0xC0F0290EA5F62ED57FB1"]}`

Example Res:

```
{
    "apiVersion": 1,
    "requestId": "my-test-reqest-id",
    "status": "success",
    "statusCode": 200,
    "message": "Proof file uploaded successfully",
    "timestamp": "2025-10-03T14:26:33.199Z",
    "data": {
        "proof_data": {
            "proof": "0x000100000100",
            "address": "0xFFEEDD",
            "root": "0x17C59BA16C9C32B3572241A04E07640AFDFD837FE19027C812D3B653E80A799B",
            "data": "0x3A985DA74FE225B2045C172D6BD390BD855F086E3E9D525B46BFE24511431532"
        },
        "proof_file": {
            "file_name": "proof-file-2025-10-03T14-26-33-187Z.json",
            "download_url": "https://integritas.minima.global/files/proofs/proof-file-2025-10-03T14-26-33-187Z.json?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=minioadmin%2F20251003%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20251003T142633Z&X-Amz-Expires=3600&X-Amz-Signature=be36bf7beac6f5a9f5893833e9cea611db221cbc0d09ff7d3511da06214d85cd&X-Amz-SignedHeaders=host&response-content-disposition=attachment%3B%20filename%3D%22proof-file-2025-10-03T14-26-33-187Z.json%22&x-amz-checksum-mode=ENABLED&x-id=GetObject",
            "file_size": 232,
            "expires_in": "1 hour",
            "bucket": "proofs"
        }
    }
}
```

Action: `verify_data`
Endpoint: `/core/v1/verify/post-lite-pdf`
Post - Req:

```json
{
  "body": [
    {
      "address": "0xFFEEDD",
      "data": "0xa7476dbfeee5c444493a6d1f4df504f76ec1078b47722c6f07dfa8fcc375f8cb",
      "proof": "0x000100000100",
      "root": "0x929C7C74E75AE367F1861D6C8311B961F61A6AF80998FC0771183E1615F634C2"
    }
  ]
}
```

Example Res:

```
{
    "apiVersion": 1,
    "requestId": "abc",
    "status": "success",
    "statusCode": 200,
    "message": "Verification complete - PDF uploaded",
    "timestamp": "2025-10-03T13:12:40.613Z",
    "data": {
        "verification": {
            "fileHash": "0xa7476dbfeee5c444493a6d1f4df504f76ec1078b47722c6f07dfa8fcc375f8cb",
            "nftcoinid": "0x61123152784B085929C42D18B3FB139295524E8BCAF2BF0C8044D88751E60814",
            "nfttxnid": "0x0000237EB0B5C9223CC7765D2E3B3C9E441581AEC6C1AF9F5A73D7CDD7A2D6A8",
            "data": {
                "result": "full match",
                "validationMethod": "timestamplite",
                "blockchain_data": [
                    {
                        "block_number": 1713614,
                        "block_date": "2025-10-01 11:56:53",
                        "txpow_id": "0x0000001B12B4BEAF973A43880BB48D043EF13745E4AE790B6D23ACAD13778D53",
                        "transactionid": "0x00001CD4BA276B1E45DDF65D62C8B3346D7343384E0F1EE503F689AE400E484B",
                        "coin_id": "0x7A6353DA2BD859F27051706BCB3C19ABB6C4BDF252C7E83D9B1FE348282BC4DC",
                        "matched_hash": "0xa7476dbfeee5c444493a6d1f4df504f76ec1078b47722c6f07dfa8fcc375f8cb"
                    }
                ]
            }
        },
        "file": {
            "file_name": "verification-report-2025-10-03T13-12-40-596Z.pdf",
            "download_url": "https://integritas.minima.global/files/reports/verification-report-2025-10-03T13-12-40-596Z.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=minioadmin%2F20251003%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20251003T131240Z&X-Amz-Expires=3600&X-Amz-Signature=12033c362b7680db417d6c26f76783bf1ce5b1b591c4775aec5fead319c8f10f&X-Amz-SignedHeaders=host&response-content-disposition=attachment%3B%20filename%3D%22verification-report-2025-10-03T13-12-40-596Z.pdf%22&x-amz-checksum-mode=ENABLED&x-id=GetObject",
            "file_size": 89210,
            "expires_in": "1 hour",
            "bucket": "reports"
        }
    }
}
```
