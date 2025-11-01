import asyncio
from pathlib import Path
from typing import TypeVar

from msgraph.graph_service_client import GraphServiceClient

from db import Channel, Database, Team

T = TypeVar("T")


def unwrap_or(value: T | None, default: T) -> T:
    if value is None:
        return default
    return value


async def get_teams(client: GraphServiceClient) -> list[Team]:
    teams = await client.me.joined_teams.get()
    team_values = unwrap_or(teams.value if teams else None, [])

    return [Team(name=unwrap_or(team.display_name, ""), team_id=unwrap_or(team.id, "")) for team in team_values]


async def get_channels(client: GraphServiceClient, team_id: str) -> list[Channel]:
    channels = await client.teams.by_team_id(team_id).all_channels.get()
    channel_values = unwrap_or(channels.value if channels else None, [])

    return [
        Channel(team_id=team_id, name=unwrap_or(channel.display_name, ""), channel_id=unwrap_or(channel.id, ""))
        for channel in channel_values
    ]


async def fetch_all_channels(client: GraphServiceClient, teams: list[Team]) -> list[Channel]:
    tasks = [get_channels(client, team.team_id) for team in teams]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    channels = []
    for result in results:
        if isinstance(result, Exception):
            print(f"Warning: Failed to fetch channels: {result}")
        elif isinstance(result, list):
            channels.extend(result)

    return channels


async def initialize_database_from_graph(db_file: Path, client: GraphServiceClient) -> Database:
    print("Fetching teams and channels from Microsoft Graph...")
    teams = await get_teams(client)
    channels = await fetch_all_channels(client, teams)
    print(f"Fetched {len(teams)} teams and {len(channels)} channels")

    db: Database = Database(db_file)
    db.load_initial_data(teams, channels)
    return db
