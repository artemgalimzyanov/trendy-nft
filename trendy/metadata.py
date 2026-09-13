"""Step 3a: build ERC-721 compatible NFT metadata (pure function)."""

COLLECTION_NAME = "Trendy"


def build_metadata(trends: list[str], image_uri: str, run_date: str, prompt: str = "") -> dict:
    """Return a metadata dict following the ERC-721 / OpenSea JSON schema."""
    if not trends:
        raise ValueError("trends must not be empty")
    if not image_uri:
        raise ValueError("image_uri must not be empty")

    attributes = [
        {"trait_type": f"Trend {i}", "value": trend} for i, trend in enumerate(trends, start=1)
    ]
    attributes.append({"trait_type": "Date", "value": run_date})

    return {
        "name": f"{COLLECTION_NAME} - {run_date}",
        "description": (
            f"AI artwork generated from the top trends of {run_date}: "
            + ", ".join(trends)
            + "."
        ),
        "image": image_uri,
        "attributes": attributes,
        "properties": {"prompt": prompt, "generator": "trendy-nft"},
    }
