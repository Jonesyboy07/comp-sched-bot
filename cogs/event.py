import discord
from discord.ext import commands
from discord import app_commands
from utils.funcs import ReadJSON, log_to_discord
from utils.constants import TIMEZONE_MAP
from datetime import datetime
import pytz
import os
import json

ATTEND_EMOJI = "✅"
MAYBE_EMOJI = "🤔"
CANT_EMOJI = "❌"

def get_pytz_timezone(friendly_name):
    return pytz.timezone(TIMEZONE_MAP.get(friendly_name, "UTC"))

class EventRSVPView(discord.ui.View):
    def __init__(self, event_cog, message_id):
        super().__init__(timeout=None)
        self.event_cog = event_cog
        self.message_id = message_id

    @discord.ui.button(label="Can Attend", style=discord.ButtonStyle.success, emoji=ATTEND_EMOJI)
    async def can_attend(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.event_cog.handle_rsvp(interaction, self.message_id, ATTEND_EMOJI)

    @discord.ui.button(label="May be able to", style=discord.ButtonStyle.secondary, emoji=MAYBE_EMOJI)
    async def maybe_attend(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.event_cog.handle_rsvp(interaction, self.message_id, MAYBE_EMOJI)

    @discord.ui.button(label="Can't Attend", style=discord.ButtonStyle.danger, emoji=CANT_EMOJI)
    async def cant_attend(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.event_cog.handle_rsvp(interaction, self.message_id, CANT_EMOJI)

    @discord.ui.button(label="Remove Attendance", style=discord.ButtonStyle.danger, emoji="🚫")
    async def remove_attendance(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.event_cog.handle_remove_attendance(interaction, self.message_id)

class EventCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.events_folder = 'data/events'
        os.makedirs(self.events_folder, exist_ok=True)

    def get_events_file(self, guild_id):
        return os.path.join(self.events_folder, f"{guild_id}.json")

    def load_events(self, guild_id):
        file_path = self.get_events_file(guild_id)
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        return {}

    def save_events(self, guild_id, events):
        file_path = self.get_events_file(guild_id)
        with open(file_path, 'w') as f:
            json.dump(events, f, indent=4)

    async def handle_rsvp(self, interaction, message_id, emoji):
        guild_id = str(interaction.guild_id)
        events = self.load_events(guild_id)
        event_data = events.get(str(message_id), {})
        for key in ["attend", "maybe", "cant"]:
            if key not in event_data:
                event_data[key] = []

        # Remove user from all lists first
        for key in ["attend", "maybe", "cant"]:
            if interaction.user.id in event_data[key]:
                event_data[key].remove(interaction.user.id)

        # Add user to the selected list
        if emoji == ATTEND_EMOJI:
            event_data["attend"].append(interaction.user.id)
            await log_to_discord(self.bot, guild_id, f"{interaction.user} ({interaction.user.id}) RSVP'd as Can Attend for event {event_data.get('event_name', '')}")
            await interaction.response.send_message("You've RSVP'd as **Can Attend**.", ephemeral=True)
        elif emoji == MAYBE_EMOJI:
            event_data["maybe"].append(interaction.user.id)
            await log_to_discord(self.bot, guild_id, f"{interaction.user} ({interaction.user.id}) RSVP'd as Maybe for event {event_data.get('event_name', '')}")
            await interaction.response.send_message("You've RSVP'd as **May be able to**.", ephemeral=True)
        elif emoji == CANT_EMOJI:
            event_data["cant"].append(interaction.user.id)
            await log_to_discord(self.bot, guild_id, f"{interaction.user} ({interaction.user.id}) RSVP'd as Can't Attend for event {event_data.get('event_name', '')}")
            await interaction.response.send_message("You've RSVP'd as **Can't Attend**.", ephemeral=True)

        events[str(message_id)] = event_data
        self.save_events(guild_id, events)
        await self.update_embed(interaction.message, event_data)

    async def update_embed(self, message, event_data):
        embed = message.embeds[0]
        attend_list = [f"<@{uid}>" for uid in event_data.get("attend", [])]
        maybe_list = [f"<@{uid}>" for uid in event_data.get("maybe", [])]
        cant_list = [f"<@{uid}>" for uid in event_data.get("cant", [])]

        embed.set_field_at(0, name=f"Can Attend {ATTEND_EMOJI} ({len(attend_list)})", value="\n".join(attend_list) if attend_list else "No one yet", inline=False)
        embed.set_field_at(1, name=f"May be able to {MAYBE_EMOJI} ({len(maybe_list)})", value="\n".join(maybe_list) if maybe_list else "No one yet", inline=False)
        embed.set_field_at(2, name=f"Can't Attend {CANT_EMOJI} ({len(cant_list)})", value="\n".join(cant_list) if cant_list else "No one yet", inline=False)

        await message.edit(embed=embed)

    async def team_autocomplete(self, interaction: discord.Interaction, current: str):
        guild_id = str(interaction.guild_id)
        teams = ReadJSON("data/servers.json").get(guild_id, {}).get("teams", [])
        return [
            app_commands.Choice(name=team["team_name"], value=team["team_name"])
            for team in teams
            if current.lower() in team["team_name"].lower()
        ][:25]

    @app_commands.command(name="event", description="Create a team event with RSVP buttons.")
    @app_commands.describe(
        team_name="The team for the event.",
        date="The date for the event (YYYY-MM-DD).",
        time="The time for the event (hhmm, 24hr format).",
        event_name="The name of the event."
    )
    @app_commands.autocomplete(team_name=team_autocomplete)
    async def event(
        self,
        interaction: discord.Interaction,
        team_name: str,
        date: str,
        time: int,
        event_name: str
    ):
        guild_id = str(interaction.guild_id)
        teams = ReadJSON("data/servers.json").get(guild_id, {}).get("teams", [])
        team = next((t for t in teams if t["team_name"].lower() == team_name.lower()), None)
        if not team:
            await log_to_discord(self.bot, guild_id, f"Event creation failed: team '{team_name}' not found by {interaction.user} ({interaction.user.id})")
            await interaction.response.send_message("Team not found.", ephemeral=True)
            return

        tz_name = team.get("timezone", "UTC")
        try:
            tz = get_pytz_timezone(tz_name)
        except Exception:
            tz = pytz.UTC

        # Parse date and time
        try:
            event_date = datetime.strptime(date, "%Y-%m-%d")
            event_time = datetime.strptime(str(time), "%H%M")
            event_dt = event_date.replace(hour=event_time.hour, minute=event_time.minute)
            event_dt = tz.localize(event_dt)
        except Exception:
            await log_to_discord(self.bot, guild_id, f"Event creation failed: invalid date/time format by {interaction.user} ({interaction.user.id})")
            await interaction.response.send_message("Invalid date or time format. Date must be YYYY-MM-DD, time must be hhmm (24hr).", ephemeral=True)
            return

        unix_time = int(event_dt.timestamp())

        channel_id = team.get("team_schedule_channel")
        channel = interaction.guild.get_channel(channel_id)
        if not channel:
            await log_to_discord(self.bot, guild_id, f"Event creation failed: schedule channel not found for team '{team_name}' by {interaction.user} ({interaction.user.id})")
            return await interaction.response.send_message("Team schedule channel not found. Please notify a server admin to check.", ephemeral=True)

        team_role_id = team.get("team_role")
        team_role_mention = f"<@&{team_role_id}>" if team_role_id else ""

        embed = discord.Embed(
            title=f"{event_name}",
            description=(
                f"**Event Time:** <t:{unix_time}:F> ({tz_name})\n"
                f"**Date:** {event_dt.strftime('%A, %B %d, %Y')}\n"
                f"**Time:** {event_dt.strftime('%I:%M %p')} ({tz_name})\n"
                f"React below to RSVP!"
            ),
            color=discord.Color.purple()
        )
        embed.add_field(name=f"Can Attend {ATTEND_EMOJI}", value="No one yet", inline=False)
        embed.add_field(name=f"May be able to {MAYBE_EMOJI}", value="No one yet", inline=False)
        embed.add_field(name=f"Can't Attend {CANT_EMOJI}", value="No one yet", inline=False)

        message_obj = await channel.send(content=team_role_mention, embed=embed, view=EventRSVPView(self, None))
        await message_obj.edit(view=EventRSVPView(self, message_obj.id))
        await log_to_discord(self.bot, guild_id, f"Event '{event_name}' created for team '{team_name}' by {interaction.user} ({interaction.user.id}) in channel {channel.mention}")
        await interaction.response.send_message(f"Event created in {channel.mention}", ephemeral=True)

        # Save event info under guild_id and message.id
        events = self.load_events(guild_id)
        event_data = {
            "event_name": event_name,
            "team_name": team_name,
            "datetime": event_dt.isoformat(),
            "attend": [],
            "maybe": [],
            "cant": []
        }
        events[str(message_obj.id)] = event_data
        self.save_events(guild_id, events)

    async def handle_remove_attendance(self, interaction, message_id):
        guild_id = str(interaction.guild_id)
        events = self.load_events(guild_id)
        event_data = events.get(str(message_id), {})
        removed = False

        for key in ["attend", "maybe", "cant"]:
            if interaction.user.id in event_data.get(key, []):
                event_data[key].remove(interaction.user.id)
                removed = True

        events[str(message_id)] = event_data
        self.save_events(guild_id, events)
        await self.update_embed(interaction.message, event_data)

        if removed:
            await log_to_discord(self.bot, guild_id, f"{interaction.user} ({interaction.user.id}) removed their attendance for event {event_data.get('event_name', '')}")
            await interaction.response.send_message("Your attendance has been removed.", ephemeral=True)
        else:
            await log_to_discord(self.bot, guild_id, f"{interaction.user} ({interaction.user.id}) attempted to remove attendance but was not signed up for event {event_data.get('event_name', '')}")
            await interaction.response.send_message("You were not signed up for this event.", ephemeral=True)


