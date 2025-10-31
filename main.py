import asyncio
from re import L
from typing import Any

from azure.core.credentials import AccessToken
from azure.identity import ChainedTokenCredential
from msal import PublicClientApplication
from msgraph.generated.models.channel import Channel
from msgraph.generated.models.chat_message import ChatMessage
from msgraph.generated.models.item_body import ItemBody
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


def get_channel_ids(channels: list[Channel], channel_names: list[str]) -> list[str]:
    channel_ids: list[str] = []

    for channel in channels:
        if channel.display_name in channel_names:
            channel_ids.append(str(channel.id))

    return channel_ids


async def send_message(client: GraphServiceClient, request: ChatMessage, team_id: str, channel_id: str):
    await client.teams.by_team_id(team_id).channels.by_channel_id(channel_id).messages.post(request)


async def send_messages(client: GraphServiceClient, message: str, team_name: str, channel_names: list[str]):
    channel_ids: list[str] = []
    team_id: str = ""

    for team in await get_teams(client):
        if team.display_name == team_name:
            channels = await get_channels(client, str(team.id))
            team_id = str(team.id)
            channel_ids = get_channel_ids(channels, channel_names)

    if not team_id:
        print("Incorrect team name")
        return

    if not channel_ids:
        print("No channel name matched")
        return

    tasks = [
        asyncio.create_task(send_message(client, ChatMessage(body=ItemBody(content=message)), team_id, channel_id))
        for channel_id in channel_ids
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    for channel_id, result in zip(channel_ids, results):
        if isinstance(result, Exception):
            print(f"Channel {channel_id}: error: {result}")
        else:
            print(f"Channel {channel_id}: message sent")


async def main():
    scopes: list[str] = ["User.Read", "Team.ReadBasic.All", "ChannelSettings.Read.All", "ChannelMessage.Send"]
    token_provider: MSALTokenProvider = MSALTokenProvider(
        client_id="87ba2a96-9fd0-4f8d-baff-89be50ff47ec",
        authority="https://login.microsoftonline.com/de3281e0-76b3-4f2e-a1e7-412b1b6cbfe6",
        scopes=scopes,
    )

    client = GraphServiceClient(credentials=token_provider, scopes=scopes)

    # await print_info(client)
    await send_messages(client, "Iter test", "PZSP2", ["General", "kanał 2"])


if __name__ == "__main__":
    asyncio.run(main())
