import discord
from discord.ext import commands
import json

class JoinedCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        filename = "data/servers.json"
        try:
            with open(filename, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}

        guild_id = str(guild.id)
        data[guild_id] = {"SetupComplete": False}

        with open(filename, "w") as f:
            json.dump(data, f, indent=4)