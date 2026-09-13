"""Step 3b: upload files and JSON to IPFS via Pinata."""

import json

import requests

from trendy.config import require_env

PINATA_API = "https://api.pinata.cloud"
PIN_FILE_URL = f"{PINATA_API}/pinning/pinFileToIPFS"
PIN_JSON_URL = f"{PINATA_API}/pinning/pinJSONToIPFS"
GATEWAY = "https://gateway.pinata.cloud/ipfs"
TIMEOUT = 60


def _headers() -> dict:
    return {"Authorization": f"Bearer {require_env('PINATA_JWT')}"}


def upload_file(data: bytes, filename: str, name: str | None = None) -> str:
    """Pin raw bytes to IPFS and return the CID."""
    response = requests.post(
        PIN_FILE_URL,
        headers=_headers(),
        files={"file": (filename, data)},
        data={"pinataMetadata": json.dumps({"name": name or filename})},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()["IpfsHash"]


def upload_json(obj: dict, name: str) -> str:
    """Pin a JSON object to IPFS and return the CID."""
    response = requests.post(
        PIN_JSON_URL,
        headers=_headers(),
        json={"pinataContent": obj, "pinataMetadata": {"name": name}},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()["IpfsHash"]


def ipfs_uri(cid: str) -> str:
    return f"ipfs://{cid}"


def gateway_url(cid: str) -> str:
    return f"{GATEWAY}/{cid}"
