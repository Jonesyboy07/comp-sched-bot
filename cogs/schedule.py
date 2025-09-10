from discord.ext import commands, tasks
from utils.funcs import WriteJSON, ReadJSON
from datetime import datetime
import pytz
import asyncio

class ScheduleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.schedule_lock = asyncio.Lock()

    @tasks.loop(minutes=1)
    async def schedule_core(self):
        async with self.schedule_lock:
            filename = "data/servers.json"
            try:
                data = ReadJSON(filename)
            except FileNotFoundError:
                data = {}

            updated = False

            for guild_id, guild_data in data.items():
                if not guild_data.get("SetupComplete", False):
                    continue

                for team in guild_data.get("teams", []):
                    tz_name = team.get("timezone", "UTC")
                    try:
                        tz = pytz.timezone(tz_name)
                    except pytz.UnknownTimeZoneError:
                        tz = pytz.UTC

                    now = datetime.now(tz)
                    today_str = now.strftime("%Y-%m-%d")

                    # Check last_synced
                    last_synced = team.get("last_synced")
                    if last_synced == today_str:
                        continue

                    if now.weekday() == 0 and now.hour == 12 and now.minute == 0:
                        channel_id = team.get("team_schedule_channel")
                        channel = self.bot.get_channel(channel_id)
                        if channel:
                            team_role_id = team.get("team_role")
                            team_role_mention = f"<@&{team_role_id}>" if team_role_id else ""
                            date_str = now.strftime("%A: The %d of %B")
                            clock_emojis = [
                                "🕛", # 12 PM
                                "🕐", # 1 PM
                                "🕑", # 2 PM
                                "🕒", # 3 PM
                                "🕓", # 4 PM
                                "🕔", # 5 PM
                                "🕕", # 6 PM
                                "🕖", # 7 PM
                                "🕗", # 8 PM
                                "🕘", # 9 PM
                                "🕙", # 10 PM
                                "🕚"  # 11 PM
                            ]

                            time_labels = [
                                "12 PM - 12:59 PM",
                                "1 PM - 1:59 PM",
                                "2 PM - 2:59 PM",
                                "3 PM - 3:59 PM",
                                "4 PM - 4:59 PM",
                                "5 PM - 5:59 PM",
                                "6 PM - 6:59 PM",
                                "7 PM - 7:59 PM",
                                "8 PM - 8:59 PM",
                                "9 PM - 9:59 PM",
                                "10 PM - 10:59 PM",
                                "11 PM - 11:59 PM"
                            ]

                            msg_content = (
                                f"{team_role_mention}\n"
                                f"**{date_str}**\n\n"
                                "Scheduling for today! React to the time slots below to indicate your availability:\n"
                            )

                            for emoji, label in zip(clock_emojis, time_labels):
                                msg_content += f"{emoji} **{label}**\n"

                            message = await channel.send(msg_content)
                            for emoji in clock_emojis:
                                await message.add_reaction(emoji)
                            # Update last_synced
                            team["last_synced"] = today_str
                            updated = True

            if updated:
                WriteJSON(data, filename)

    @commands.command(name="test_schedule")
    async def test_schedule(self, ctx):
        """Temporary backdoor to manually trigger schedule_core."""
        async with self.schedule_lock:
            filename = "data/servers.json"
            try:
                data = ReadJSON(filename)
            except FileNotFoundError:
                data = {}

            updated = False

            for guild_id, guild_data in data.items():
                if not guild_data.get("SetupComplete", False):
                    continue

                for team in guild_data.get("teams", []):
                    tz_name = team.get("timezone", "UTC")
                    try:
                        tz = pytz.timezone(tz_name)
                    except pytz.UnknownTimeZoneError:
                        tz = pytz.UTC

                    now = datetime.now(tz)
                    today_str = now.strftime("%Y-%m-%d")

                    # Check last_synced
                    last_synced = team.get("last_synced")
                    if last_synced == today_str:
                        continue

                    channel_id = team.get("team_schedule_channel")
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        team_role_id = team.get("team_role")
                        team_role_mention = f"<@&{team_role_id}>" if team_role_id else ""
                        date_str = now.strftime("%A: The %d of %B")
                        msg_content = (
                            f"{team_role_mention}\n"
                            f"**{date_str}**\n\n"
                            "Scheduling for today! React to the time slots below to indicate your availability:\n"
                        )
                        for hour in range(12, 24):
                            time_str = f"{hour % 12 or 12} {'PM' if hour < 12 else 'AM'} - {hour % 12 or 12}:59 {'PM' if hour < 12 else 'AM'}"
                            msg_content += f"\n:clock{hour if hour <= 12 else hour-12}: {time_str}\n"
                        message = await channel.send(msg_content)
                        for emoji in ["🕛","🕐","🕑","🕒","🕓","🕔","🕕","🕖","🕗","🕘","🕙","🕚"]:
                            await message.add_reaction(emoji)
                        team["last_synced"] = today_str
                        updated = True

            if updated:
                WriteJSON(filename, data)
            await ctx.send("Manual schedule run complete.")