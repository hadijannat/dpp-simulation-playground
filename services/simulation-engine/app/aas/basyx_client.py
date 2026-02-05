from __future__ import annotations

from typing import Dict, Any, Optional
import requests


class BasyxClient:
    def __init__(self, base_url: str, api_prefix: str = "/api/v3.0"):
        self.base_url = base_url.rstrip("/")
        self.api_prefix = f"/{api_prefix.strip('/')}" if api_prefix else ""

    def _request(self, method: str, path: str, json: Optional[Dict[str, Any]] = None) -> requests.Response:
        primary = f"{self.base_url}{self.api_prefix}/{path.lstrip('/')}"
        resp = requests.request(method, primary, json=json, timeout=5)
        if resp.status_code == 404 and self.api_prefix:
            fallback = f"{self.base_url}/{path.lstrip('/')}"
            resp = requests.request(method, fallback, json=json, timeout=5)
        resp.raise_for_status()
        return resp

    def create_shell(self, shell: Dict[str, Any]) -> Dict[str, Any]:
        resp = self._request("POST", "shells", json=shell)
        return resp.json() if resp.content else shell

    def list_shells(self) -> Dict[str, Any]:
        resp = self._request("GET", "shells")
        return resp.json()

    def create_submodel(self, submodel: Dict[str, Any]) -> Dict[str, Any]:
        resp = self._request("POST", "submodels", json=submodel)
        return resp.json() if resp.content else submodel

    def get_submodel_elements(self, submodel_id: str) -> Dict[str, Any]:
        resp = self._request("GET", f"submodels/{submodel_id}/submodel-elements")
        return resp.json()

    def patch_submodel_elements(self, submodel_id: str, elements: Dict[str, Any] | list) -> Dict[str, Any]:
        path = f"submodels/{submodel_id}/submodel-elements"
        try:
            resp = self._request("PATCH", path, json=elements)
        except requests.RequestException:
            resp = self._request("PUT", path, json=elements)
        return resp.json() if resp.content else {"updated": True}

    def register_shell_descriptor(self, registry_url: str, shell: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not registry_url:
            return None
        descriptor = {
            "id": shell.get("id"),
            "idShort": shell.get("idShort"),
            "endpoints": [
                {
                    "protocolInformation": {
                        "href": f"{self.base_url}{self.api_prefix}/shells/{shell.get('id')}"
                    }
                }
            ],
        }
        resp = requests.post(
            f"{registry_url.rstrip('/')}/api/v3.0/registry/shell-descriptors",
            json=descriptor,
            timeout=5,
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
                        "href": f"{self.base_url}{self.api_prefix}/submodels/{submodel.get('id')}"
                    }
                }
            ],
        }
        resp = requests.post(
            f"{registry_url.rstrip('/')}/api/v3.0/registry/submodel-descriptors",
            json=descriptor,
            timeout=5,
        )
        resp.raise_for_status()
        return resp.json() if resp.content else descriptor
