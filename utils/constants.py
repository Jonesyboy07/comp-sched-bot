import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
INVITE_LINK = f"https://discord.com/api/oauth2/authorize?client_id={DISCORD_CLIENT_ID}&permissions=2147544129&integration_type=0&scope=bot+applications.commands"


DONATION_LINK = os.getenv("DONATION_LINK", "N/A")