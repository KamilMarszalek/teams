import asyncio
from re import L
from typing import Any

from azure.core.credentials import AccessToken
from azure.identity import ChainedTokenCredential
from msal import PublicClientApplication
from msgraph.generated.models.channel import Channel
from msgraph.generated.models.team import Team
from msgraph.graph_service_client import GraphServiceClient


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


async def get_teams(client: GraphServiceClient) -> list[Team]:
    teams = await client.me.joined_teams.get()
    if teams is None:
        return []
    return teams.value or []


async def get_channels(client: GraphServiceClient, team_id: str) -> list[Channel]:
    channels = await client.teams.by_team_id(team_id).all_channels.get()
    if channels is None:
        return []
    return channels.value or []


async def print_info(client: GraphServiceClient):
    try:
        if (user := await client.me.get()) is None:
            return

        print(f"Name: {user.display_name}")
        print(f"Email: {user.mail or user.user_principal_name}")

        teams = await get_teams(client)

        print(f"\nJoined teams:")
        for team in teams:
            print(f"- {team.display_name}")
            for channel in await get_channels(client, str(team.id)):
                print(f"    - {channel.display_name}")

    except Exception as e:
        print(f"Error: {e}")


async def main():
    scopes: list[str] = ["User.Read", "Team.ReadBasic.All", "ChannelSettings.Read.All"]
    token_provider: MSALTokenProvider = MSALTokenProvider(
        client_id="87ba2a96-9fd0-4f8d-baff-89be50ff47ec",
        authority="https://login.microsoftonline.com/de3281e0-76b3-4f2e-a1e7-412b1b6cbfe6",
        scopes=scopes,
    )

    client = GraphServiceClient(credentials=token_provider, scopes=scopes)

    await print_info(client)


if __name__ == "__main__":
    asyncio.run(main())
