import json

import pytest
import responses

from trendy import storage


@pytest.fixture(autouse=True)
def pinata_jwt(monkeypatch):
    monkeypatch.setenv("PINATA_JWT", "test-jwt")


@responses.activate
def test_upload_file_returns_cid_and_sets_auth():
    responses.post(storage.PIN_FILE_URL, json={"IpfsHash": "QmFile"})
    cid = storage.upload_file(b"\x89PNG", "image.png")
    assert cid == "QmFile"
    req = responses.calls[0].request
    assert req.headers["Authorization"] == "Bearer test-jwt"
    assert b"image.png" in req.body


@responses.activate
def test_upload_json_returns_cid_and_wraps_content():
    responses.post(storage.PIN_JSON_URL, json={"IpfsHash": "QmJson"})
    cid = storage.upload_json({"name": "x"}, "meta.json")
    assert cid == "QmJson"
    body = json.loads(responses.calls[0].request.body)
    assert body["pinataContent"] == {"name": "x"}
    assert body["pinataMetadata"]["name"] == "meta.json"


@responses.activate
def test_upload_raises_on_http_error():
    responses.post(storage.PIN_FILE_URL, status=401, json={"error": "bad jwt"})
    with pytest.raises(Exception):
        storage.upload_file(b"x", "x.png")


def test_uri_helpers():
    assert storage.ipfs_uri("Qm1") == "ipfs://Qm1"
    assert storage.gateway_url("Qm1") == "https://gateway.pinata.cloud/ipfs/Qm1"


def test_missing_jwt_gives_clear_error(monkeypatch):
    monkeypatch.delenv("PINATA_JWT")
    with pytest.raises(RuntimeError, match="PINATA_JWT"):
        storage.upload_file(b"x", "x.png")
