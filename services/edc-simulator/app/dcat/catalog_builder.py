from typing import Dict, List


def build_catalog(assets: List[Dict]) -> Dict:
    return {
        "@context": "https://www.w3.org/ns/dcat#",
        "type": "Catalog",
        "dataset": assets,
    }
