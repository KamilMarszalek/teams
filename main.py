import asyncio
from pathlib import Path

from msgraph.graph_service_client import GraphServiceClient

from config import AUTHORITY, CLIENT_ID, DB_FILE, SCOPES
from db import Database
from graph_client import initialize_database_from_graph
from messaging import send_messages_to_channels
from token_provider import MSALTokenProvider


def create_graph_client() -> GraphServiceClient:
    token_provider = MSALTokenProvider(
        client_id=CLIENT_ID,
        authority=AUTHORITY,
        scopes=SCOPES,
    )
    return GraphServiceClient(credentials=token_provider, scopes=SCOPES)


async def load_database(db_file: Path, client: GraphServiceClient) -> Database:
    if not db_file.exists():
        return await initialize_database_from_graph(db_file, client)
    return Database(db_file)


def print_teams_and_channels(db: Database):
    try:
        teams = db.get_teams()

        if not teams:
            print("No teams found in database")
            return

        print(f"\nJoined teams ({len(teams)}):")
        for team in teams:
            print(f"- {team.name}")
            channels = db.get_channels_for_team(team.team_id)
            for channel in channels:
                print(f"    - {channel.name}")

    except Exception as e:
        print(f"Error printing info: {e}")


async def main():
    with await load_database(DB_FILE, create_graph_client()) as db:
        print_teams_and_channels(db)
        # await send_messages_to_channels(client, db, "Test message", "PZSP2", ["General", "kanał 2"])


if __name__ == "__main__":
    asyncio.run(main())
