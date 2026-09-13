import pytest

from trendy.metadata import build_metadata


def test_metadata_has_required_erc721_fields():
    data = build_metadata(["A", "B", "C"], "ipfs://abc", "2026-09-07", prompt="p")
    assert data["name"] == "Trendy - 2026-09-07"
    assert data["image"].startswith("ipfs://")
    assert "A" in data["description"]
    assert data["properties"]["prompt"] == "p"


def test_metadata_attributes_one_per_trend_plus_date():
    data = build_metadata(["A", "B"], "ipfs://abc", "2026-09-07")
    traits = {a["trait_type"]: a["value"] for a in data["attributes"]}
    assert traits == {"Trend 1": "A", "Trend 2": "B", "Date": "2026-09-07"}


def test_metadata_rejects_empty_inputs():
    with pytest.raises(ValueError):
        build_metadata([], "ipfs://abc", "2026-09-07")
    with pytest.raises(ValueError):
        build_metadata(["A"], "", "2026-09-07")
