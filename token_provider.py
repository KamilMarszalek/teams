from typing import Any

from azure.core.credentials import AccessToken
from azure.identity import ChainedTokenCredential
from msal import PublicClientApplication


class MSALTokenProvider(ChainedTokenCredential):
    def __init__(self, client_id: str, authority: str, scopes: list[str]):
        self.msal_app = PublicClientApplication(client_id=client_id, authority=authority)
        self.scopes = scopes

    def get_token(self, *scopes, **kwargs) -> AccessToken:
        accounts: list[dict[str, Any]] = self.msal_app.get_accounts()
        if accounts:
            result = self.msal_app.acquire_token_silent(self.scopes, account=accounts[0])
        else:
            result = None

        if not result or "access_token" not in result:
            result = self.msal_app.acquire_token_interactive(scopes=self.scopes)

        if "access_token" in result:
            return AccessToken(str(result["access_token"]), int(result["expires_in"]))
        else:
            raise Exception(f"Failed to acquire token: {result.get('error_description')}")
