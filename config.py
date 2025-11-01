from pathlib import Path

CLIENT_ID = "87ba2a96-9fd0-4f8d-baff-89be50ff47ec"
AUTHORITY = "https://login.microsoftonline.com/de3281e0-76b3-4f2e-a1e7-412b1b6cbfe6"
SCOPES = ["User.Read", "Team.ReadBasic.All", "ChannelSettings.Read.All", "ChannelMessage.Send"]

DB_FILE = Path("teams.db")
