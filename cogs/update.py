import discord
from discord.ext import commands
from discord import app_commands
from utils.funcs import ReadJSON

class UpdateCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="update", description="Send the latest update from data/update.txt to all update logs channels in every server.")
    async def update(self, interaction: discord.Interaction):
        servers = ReadJSON("data/servers.json")

        try:
            with open("data/update.txt", "r", encoding="utf-8") as f:
                update_text = f.read().strip()
        except FileNotFoundError:
            await interaction.response.send_message("No update.txt file found in the data folder.", ephemeral=True)
            return

        sent_count = 0
        for guild_id, server_data in servers.items():
            update_channel_id = server_data.get("update_logs_channel")
            if update_channel_id:
                guild = self.bot.get_guild(int(guild_id))
                if guild:
                    channel = guild.get_channel(int(update_channel_id))
                    if channel:
                        await channel.send(f"📢 **Update:**\n{update_text}")
                        sent_count += 1

        await interaction.response.send_message(
            f"Update sent to {sent_count} update logs channel(s).", ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(UpdateCog(bot))