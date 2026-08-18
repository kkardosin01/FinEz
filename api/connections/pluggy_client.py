"""
Cliente HTTP para o agregador Pluggy (seção 6).

Desenvolvimento inteiro no sandbox (gratuito). Credenciais só no servidor;
nunca expostas ao front (que só vê o connect token de curta duração).
"""
import httpx
from django.conf import settings


class PluggyClient:
    def __init__(self):
        self.base_url = settings.PLUGGY_BASE_URL
        self.client_id = settings.PLUGGY_CLIENT_ID
        self.client_secret = settings.PLUGGY_CLIENT_SECRET
        self._api_key: str | None = None

    def _authenticate(self) -> str:
        if self._api_key:
            return self._api_key
        response = httpx.post(
            f"{self.base_url}/auth",
            json={"clientId": self.client_id, "clientSecret": self.client_secret},
            timeout=10,
        )
        response.raise_for_status()
        self._api_key = response.json()["apiKey"]
        return self._api_key

    def _headers(self) -> dict:
        return {"X-API-KEY": self._authenticate()}

    def create_connect_token(self, item_id: str | None = None) -> str:
        """Token de curta duração pro widget do front. Nunca as credenciais reais."""
        payload = {"itemId": item_id} if item_id else {}
        response = httpx.post(
            f"{self.base_url}/connect_token", json=payload, headers=self._headers(), timeout=10
        )
        response.raise_for_status()
        return response.json()["accessToken"]

    def get_item(self, item_id: str) -> dict:
        response = httpx.get(f"{self.base_url}/items/{item_id}", headers=self._headers(), timeout=10)
        response.raise_for_status()
        return response.json()

    def list_transactions(self, account_id: str, page: int = 1, page_size: int = 500) -> dict:
        response = httpx.get(
            f"{self.base_url}/transactions",
            params={"accountId": account_id, "page": page, "pageSize": page_size},
            headers=self._headers(),
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def list_accounts(self, item_id: str) -> list[dict]:
        response = httpx.get(
            f"{self.base_url}/accounts", params={"itemId": item_id}, headers=self._headers(), timeout=15
        )
        response.raise_for_status()
        return response.json()["results"]

    def delete_item(self, item_id: str) -> None:
        """Revoga o consentimento no agregador (usado na exclusão LGPD)."""
        response = httpx.delete(f"{self.base_url}/items/{item_id}", headers=self._headers(), timeout=10)
        response.raise_for_status()
