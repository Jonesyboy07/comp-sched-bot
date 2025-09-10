import os
from dotenv import load_dotenv

import discord
from discord.ext import commands
from cogs.init import get_cogs
from utils.stats_cache import cache_stats

load_dotenv()
token = os.getenv("DISCORD_TOKEN")
clientid = os.getenv("DISCORD_CLIENT_ID")
prefix = os.getenv("PREFIX", "!")

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.guild_messages = True
intents.message_content = True
client = commands.Bot(command_prefix=prefix,
                    intents=intents,
                    help_command=None, 
                    application_id=clientid)

# Event: When the bot is ready
@client.event
async def on_ready():
    print("Bot is online")
    print(f"Logged in as: {client.user} - {client.user.id}")
    client.loop.create_task(cache_stats(client))
    # await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="The Number One Free Scheduling Bot"))
    try:
        synced_commands = await client.tree.sync()  # Ensure commands are synced
        print(f"Synced {len(synced_commands)} command(s)")
        for command in synced_commands:
            print(f"- {command.name}")
        print("----------------------------")
        print(f"We are in the following guild(s) - ({len(client.guilds)}):")
        for guild in client.guilds:
            print(f"- {guild.name} (id: {guild.id})")
    except Exception as e:
        print(e)


# Event: When the bot joins a guild
@client.event
async def on_guild_join(guild: discord.Guild):  
    await client.tree.sync(guild=guild)

# Load cogs
async def load_cogs():
    for cog in get_cogs(client):
        await client.add_cog(cog)
        print(f"Added commands from {cog.__class__.__name__}:")
        for command in cog.get_commands():
            print(f"- {command.name}")

# Sync commands on startup
async def setup_hook():
    await load_cogs()

client.setup_hook = setup_hook

# Run the bot
client.run(token)
