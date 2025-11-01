import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Self


@dataclass
class Team:
    name: str
    team_id: str


@dataclass
class Channel:
    team_id: str
    name: str
    channel_id: str


class Database:
    def __init__(self, db_file: Path):
        self.db_file = db_file
        if self.db_file.parent:
            self.db_file.parent.mkdir(parents=True, exist_ok=True)

        self.conn: sqlite3.Connection = sqlite3.connect(str(self.db_file))
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self._ensure_schema()

    def _ensure_schema(self):
        with self.conn:
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS teams (
                    team_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL
                );
                """
            )
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS channels (
                    channel_id TEXT PRIMARY KEY,
                    team_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    FOREIGN KEY(team_id) REFERENCES teams(team_id) ON DELETE CASCADE
                );
                """
            )

    def load_initial_data(self, teams: list[Team], channels: list[Channel]):
        if not teams and not channels:
            return

        with self.conn:
            self.conn.executemany(
                "INSERT OR IGNORE INTO teams(team_id, name) VALUES (?, ?);",
                [(t.team_id, t.name) for t in teams],
            )
            self.conn.executemany(
                "INSERT OR IGNORE INTO channels(channel_id, team_id, name) VALUES (?, ?, ?);",
                [(c.channel_id, c.team_id, c.name) for c in channels],
            )

    def get_teams(self) -> list[Team]:
        cursor = self.conn.execute("SELECT name, team_id FROM teams ORDER BY name")
        return [Team(name=row[0], team_id=row[1]) for row in cursor.fetchall()]

    def get_channels_for_team(self, team_id: str) -> list[Channel]:
        cursor = self.conn.execute(
            "SELECT team_id, name, channel_id FROM channels WHERE team_id = ? ORDER BY name", (team_id,)
        )
        return [Channel(team_id=row[0], name=row[1], channel_id=row[2]) for row in cursor.fetchall()]

    def get_team_by_name(self, team_name: str) -> Team | None:
        cursor = self.conn.execute("SELECT name, team_id FROM teams WHERE name = ?", (team_name,))
        row = cursor.fetchone()
        return Team(name=row[0], team_id=row[1]) if row else None

    def get_channels_by_names(self, team_id: str, channel_names: list[str]) -> list[Channel]:
        if not channel_names:
            return []

        placeholders = ",".join("?" * len(channel_names))
        query = f"""
            SELECT team_id, name, channel_id
            FROM channels
            WHERE team_id = ? AND name IN ({placeholders})
            ORDER BY name
        """

        cursor = self.conn.execute(query, (team_id, *channel_names))
        return [Channel(team_id=row[0], name=row[1], channel_id=row[2]) for row in cursor.fetchall()]

    def close(self):
        if self.conn:
            try:
                self.conn.commit()
            finally:
                self.conn.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
