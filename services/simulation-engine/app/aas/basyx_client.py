from __future__ import annotations

from typing import Dict, Any, Optional
import requests


class BasyxClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def create_shell(self, shell: Dict[str, Any]) -> Dict[str, Any]:
        resp = requests.post(f"{self.base_url}/api/v3.0/shells", json=shell, timeout=10)
        resp.raise_for_status()
        return resp.json() if resp.content else shell

    def list_shells(self) -> Dict[str, Any]:
        resp = requests.get(f"{self.base_url}/api/v3.0/shells", timeout=10)
        resp.raise_for_status()
        return resp.json()

    def create_submodel(self, submodel: Dict[str, Any]) -> Dict[str, Any]:
        resp = requests.post(f"{self.base_url}/api/v3.0/submodels", json=submodel, timeout=10)
        resp.raise_for_status()
        return resp.json() if resp.content else submodel

    def register_shell_descriptor(self, registry_url: str, shell: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not registry_url:
            return None
        descriptor = {
            "id": shell.get("id"),
            "idShort": shell.get("idShort"),
            "endpoints": [
                {
                    "protocolInformation": {
                        "href": f"{self.base_url}/api/v3.0/shells/{shell.get('id')}"
                    }
                }
            ],
        }
        resp = requests.post(
            f"{registry_url.rstrip('/')}/api/v3.0/registry/shell-descriptors",
            json=descriptor,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json() if resp.content else descriptor

    def register_submodel_descriptor(self, registry_url: str, submodel: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not registry_url:
            return None
        descriptor = {
            "id": submodel.get("id"),
            "idShort": submodel.get("idShort"),
            "endpoints": [
                {
                    "protocolInformation": {
                        "href": f"{self.base_url}/api/v3.0/submodels/{submodel.get('id')}"
                    }
                }
            ],
        }
        resp = requests.post(
            f"{registry_url.rstrip('/')}/api/v3.0/registry/submodel-descriptors",
            json=descriptor,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json() if resp.content else descriptor
