import discord
from discord.ext import commands
from utils.funcs import WriteJSON, ReadJSON

class JoinedCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        filename = "data/servers.json"
        try:
            data = ReadJSON(filename)
        except FileNotFoundError:
            data = {}

        guild_id = str(guild.id)
        data[guild_id] = {"SetupComplete": False}

        WriteJSON(data, filename, indent=4)