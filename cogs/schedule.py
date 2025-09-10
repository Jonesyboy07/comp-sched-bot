import discord
from discord.ext import commands, tasks
from discord import app_commands
from utils.funcs import WriteJSON, ReadJSON, CheckIfAdminRole
from datetime import datetime, timedelta
import pytz
import asyncio

def get_previous_monday(dt):
    # If today is Monday, return today; else, return previous Monday
    return dt - timedelta(days=dt.weekday())

def build_intro_embed(team_role_mention, start_date):
    clock_emojis = get_clock_emojis()
    time_labels = [
        "12 PM", "1 PM", "2 PM", "3 PM", "4 PM", "5 PM", "6 PM", "7 PM",
        "8 PM", "9 PM", "10 PM", "11 PM"
    ]
    times_str = "\n".join([f"{emoji} = {label}" for emoji, label in zip(clock_emojis, time_labels)])
    embed = discord.Embed(
        title="Weekly Scheduling",
        description=(
            f"{team_role_mention}\n"
            f"**{start_date.strftime('%A: The %d of %B')}**\n\n"
            "Scheduling for this week!\n"
            "Each day will have a message for you to react to, indicating your availability for that day.\n"
            "Time slots run from **12 PM to 11:59 PM**.\n"
            "React to each day's message using the clock emojis below:\n\n"
            f"{times_str}\n"
        ),
        color=discord.Color.blue()
    )
    embed.set_footer(text="React to each day's message to indicate your availability.")
    return embed

def build_day_message(date_str):
    return f"**{date_str}**"

async def send_weekly_schedule_messages(channel, team_role_mention, start_date):
    # Send intro embed (with ping)
    embed = build_intro_embed(team_role_mention, start_date)
    await channel.send(content=team_role_mention, embed=embed)

    clock_emojis = get_clock_emojis()
    # Send a message for each day (Monday to Sunday), no ping
    for i in range(7):
        day_date = start_date + timedelta(days=i)
        day_str = day_date.strftime("%A: The %d of %B")
        msg_content = build_day_message(day_str)
        message = await channel.send(msg_content)
        for emoji in clock_emojis:
            await message.add_reaction(emoji)

def update_last_synced(servers, guild_id, team_idx, today_str):
    current_server = servers.get(guild_id, {})
    teams = current_server.get("teams", [])
    teams[team_idx]["last_synced"] = today_str
    current_server["teams"] = teams
    servers[guild_id] = current_server
    return servers

class TeamScheduleDropdown(discord.ui.Select):
    def __init__(self, teams):
        options = [
            discord.SelectOption(label=team["team_name"], value=str(idx))
            for idx, team in enumerate(teams)
        ]
        super().__init__(placeholder="Select a team to send scheduling...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)  # Prevent timeout error

        idx = int(self.values[0])
        team = self.view.teams[idx]
        tz_name = team.get("timezone", "UTC")
        try:
            tz = pytz.timezone(tz_name)
        except pytz.UnknownTimeZoneError:
            tz = pytz.UTC

        now = datetime.now(tz)
        monday = get_previous_monday(now)
        channel_id = team.get("team_schedule_channel")
        channel = interaction.guild.get_channel(channel_id)
        if not channel:
            await interaction.followup.send("Schedule channel not found.", ephemeral=True)
            return

        team_role_id = team.get("team_role")
        team_role_mention = f"<@&{team_role_id}>" if team_role_id else ""

        await send_weekly_schedule_messages(channel, team_role_mention, monday)

        # Update last_synced for today (Monday)
        today_str = now.strftime("%Y-%m-%d")
        guild_id = str(interaction.guild_id)
        servers = ReadJSON("data/servers.json")
        servers = update_last_synced(servers, guild_id, idx, today_str)
        WriteJSON(servers, "data/servers.json")

        await interaction.followup.send(
            f"Weekly scheduling messages sent for **{team['team_name']}**.", ephemeral=True
        )

class TeamScheduleView(discord.ui.View):
    def __init__(self, teams):
        super().__init__(timeout=60)
        self.teams = teams
        self.add_item(TeamScheduleDropdown(teams))

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

                for idx, team in enumerate(guild_data.get("teams", [])):
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
                            await send_schedule_message(channel, team_role_mention, date_str)
                            # Update last_synced
                            data = update_last_synced(data, guild_id, idx, today_str)
                            updated = True

            if updated:
                WriteJSON(data, filename)

    @app_commands.command(name="send_schedule", description="Send a scheduling message for a team (admin or team captain only).")
    async def send_schedule(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        user_roles = [role.id for role in interaction.user.roles]
        servers = ReadJSON("data/servers.json")
        current_server = servers.get(guild_id, {})
        if not current_server.get("SetupComplete", False):
            await interaction.response.send_message("Bot not setup yet.", ephemeral=True)
            return
        teams = current_server.get("teams", [])
        if not teams:
            await interaction.response.send_message("No teams found.", ephemeral=True)
            return

        # Only allow admins or team captains to use
        allowed_team_idxs = []
        for idx, team in enumerate(teams):
            if CheckIfAdminRole(user_roles, guild_id) or team.get("team_cap_role") in user_roles:
                allowed_team_idxs.append(idx)
        if not allowed_team_idxs:
            await interaction.response.send_message("You do not have permission to send scheduling for any team.", ephemeral=True)
            return

        allowed_teams = [teams[idx] for idx in allowed_team_idxs]
        view = TeamScheduleView(allowed_teams)
        await interaction.response.send_message("Select a team to send scheduling for:", view=view, ephemeral=True)

async def send_schedule_message(channel, team_role_mention, date_str):
    msg_content = build_day_message(team_role_mention, date_str)
    clock_emojis = get_clock_emojis()
    message = await channel.send(msg_content)
    for emoji in clock_emojis:
        await message.add_reaction(emoji)

def get_clock_emojis():
    """Returns the list of clock emojis for 12 PM to 11 PM."""
    return [
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
        "🕚", # 11 PM
    ]

