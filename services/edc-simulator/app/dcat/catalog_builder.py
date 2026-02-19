from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def _policy_summary(policy: dict[str, Any]) -> dict[str, int]:
    permissions = _as_list(policy.get("permission"))
    prohibitions = _as_list(policy.get("prohibition"))
    obligations = _as_list(policy.get("obligation"))
    return {
        "permissions": len(permissions),
        "prohibitions": len(prohibitions),
        "obligations": len(obligations),
    }


def _keywords_for_asset(asset: dict[str, Any]) -> list[str]:
    raw_keywords = asset.get("keywords") or asset.get("dataAddress", {}).get("keywords") or []
    keywords = [str(keyword).strip() for keyword in _as_list(raw_keywords) if str(keyword).strip()]
    if asset.get("name"):
        keywords.extend([part.lower() for part in str(asset["name"]).split() if part])
    seen: set[str] = set()
    unique: list[str] = []
    for keyword in keywords:
        if keyword in seen:
            continue
        unique.append(keyword)
        seen.add(keyword)
    return unique


def _distribution_for_asset(asset: dict[str, Any]) -> list[dict[str, Any]]:
    data_address = asset.get("dataAddress") or {}
    endpoint = (
        data_address.get("endpoint")
        or data_address.get("endpoint_url")
        or data_address.get("url")
    )
    distribution: dict[str, Any] = {
        "@id": f"urn:dpp:distribution:{asset.get('id', 'unknown')}",
        "@type": "dcat:Distribution",
        "type": "Distribution",
        "format": data_address.get("format") or "application/json",
    }
    if endpoint:
        distribution["accessService"] = {
            "@type": "dcat:DataService",
            "type": "DataService",
            "endpointURL": endpoint,
        }
    if data_address.get("method"):
        distribution["method"] = data_address.get("method")
    return [distribution]


def build_catalog(assets: list[dict[str, Any]]) -> dict[str, Any]:
    datasets: list[dict[str, Any]] = []
    for asset in assets:
        policy = asset.get("policy") or {}
        publisher = asset.get("publisher") or {}
        dataset = {
            "@id": f"urn:dpp:dataset:{asset['id']}",
            "@type": "dcat:Dataset",
            "type": "Dataset",
            "id": asset["id"],
            "name": asset.get("name"),
            "title": asset.get("title") or asset.get("name"),
            "description": asset.get("description") or f"EDC dataset for {asset.get('name') or asset['id']}",
            "keyword": _keywords_for_asset(asset),
            "keywords": _keywords_for_asset(asset),
            "publisher": {
                "@type": "foaf:Agent",
                "type": "Agent",
                "id": publisher.get("id"),
                "name": publisher.get("name"),
            },
            "distribution": _distribution_for_asset(asset),
            "policySummary": _policy_summary(policy),
            "policy": policy,
            "dataAddress": asset.get("dataAddress") or {},
        }
        datasets.append(dataset)
    return {
        "@context": [
            "https://www.w3.org/ns/dcat#",
            "https://www.w3.org/ns/odrl.jsonld",
        ],
        "@type": "dcat:Catalog",
        "type": "Catalog",
        "@id": "urn:dpp:catalog",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "dataset": datasets,
    }
