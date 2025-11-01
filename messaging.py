import asyncio

from msgraph.generated.models.chat_message import ChatMessage
from msgraph.generated.models.item_body import ItemBody
from msgraph.graph_service_client import GraphServiceClient

from db import Database


async def send_message(client: GraphServiceClient, message: str, team_id: str, channel_id: str):
    request = ChatMessage(body=ItemBody(content=message))
    await client.teams.by_team_id(team_id).channels.by_channel_id(channel_id).messages.post(request)


async def send_messages_to_channels(
    client: GraphServiceClient, db: Database, message: str, team_name: str, channel_names: list[str]
):
    team = db.get_team_by_name(team_name)
    if team is None:
        print(f"Error: Team '{team_name}' not found")
        return

    channels = db.get_channels_by_names(team.team_id, channel_names)
    if not channels:
        print(f"Error: No matching channels found in team '{team_name}'")
        print(f"Requested: {', '.join(channel_names)}")
        return

    print(f"Sending message to {len(channels)} channel(s) in '{team_name}'...")

    tasks = [send_message(client, message, team.team_id, channel.channel_id) for channel in channels]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    for channel, result in zip(channels, results):
        if isinstance(result, Exception):
            print(f"Channel {channel.name}: error: {result}")
        else:
            print(f"Channel {channel.name}: message sent")
