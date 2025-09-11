import discord
from discord.ext import commands
from discord import app_commands
from utils.funcs import CheckIfAdminRole, ReadJSON, WriteJSON, log_to_discord


class SetupCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup", description="Set up the bot in this server.")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_command(
        self, 
        interaction: discord.Interaction, 
        command_channel: discord.TextChannel, 
        admin_role: discord.Role,
        update_logs: discord.TextChannel,
        bot_logs: discord.TextChannel
    ):
        GuildID = str(interaction.guild.id)
        BotChannel = str(command_channel.id)
        AdminRole = str(admin_role.id)
        UpdateLogsChannel = str(update_logs.id)
        
        # Load existing server data
        filename = "data/servers.json"
        try:
            data = ReadJSON(filename)
        except FileNotFoundError:
            data = {}

        # Only allow setup if SetupComplete is not True
        if GuildID in data and data[GuildID].get("SetupComplete", False):
            await log_to_discord(self.bot, GuildID, f"Setup attempted but already completed by {interaction.user} ({interaction.user.id})")
            return await interaction.response.send_message(
                "Setup has already been completed for this server. Use other commands to modify settings.",
                ephemeral=True
            )

        # Perform setup
        data[GuildID] = {
            "bot_channels": [BotChannel],
            "admin_roles": [AdminRole],
            "update_logs_channel": UpdateLogsChannel,
            "bot_logs_channel": bot_logs.id,
            "leagues": [],
            "teams": [],
            "SetupComplete": True
        }

        # Save updated data
        WriteJSON(data, filename, indent=4)

        await log_to_discord(self.bot, GuildID, f"Setup completed by {interaction.user} ({interaction.user.id})")

        await interaction.response.send_message(
            f"""Setup complete! Channel(s): <#{BotChannel}> ({BotChannel}), Admin role(s): <@&{AdminRole}>.

I now recommend going to your server's 'Integrations' tab and disabling some commands for the '@everyone' role, so that only permitted users can see private commands.

You can add more bot channels with /addbotchannel and more admin roles with /addadminrole.

You can also remove them with /removebotchannel and /removeadminrole.

Run /help to see a list of commands and how to utilize them.""",
            ephemeral=True
        )
        
    @app_commands.command(name="addbotchannel", description="Add a bot channel.")
    async def add_bot_channel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):
        GuildID = str(interaction.guild.id)
        ChannelID = str(channel.id)

        # Check if user has admin role
        if not CheckIfAdminRole([role.id for role in interaction.user.roles], interaction.guild.id):
            await log_to_discord(self.bot, GuildID, f"Unauthorized addbotchannel attempt by {interaction.user} ({interaction.user.id})")
            return await interaction.response.send_message(
                "You do not have permission to use this command.",
                ephemeral=True
            )

        # Load existing server data
        filename = "data/servers.json"
        try:
            data = ReadJSON(filename)
        except FileNotFoundError:
            await log_to_discord(self.bot, GuildID, f"addbotchannel failed: server not set up ({interaction.user.id})")
            return await interaction.response.send_message(
                "Server is not set up yet. Please run /setup first.",
                ephemeral=True
            )

        if GuildID not in data or not data[GuildID].get("SetupComplete", False):
            await log_to_discord(self.bot, GuildID, f"addbotchannel failed: setup incomplete ({interaction.user.id})")
            return await interaction.response.send_message(
                "Server is not set up yet. Please run /setup first.",
                ephemeral=True
            )

        if ChannelID in data[GuildID]["bot_channels"]:
            await log_to_discord(self.bot, GuildID, f"addbotchannel: channel already exists ({ChannelID}) by {interaction.user.id}")
            return await interaction.response.send_message(
                f"Channel <#{ChannelID}> is already a bot channel.",
                ephemeral=True
            )

        data[GuildID]["bot_channels"].append(ChannelID)

        # Save updated data
        WriteJSON(data, filename, indent=4)

        await log_to_discord(self.bot, GuildID, f"Bot channel <#{ChannelID}> added by {interaction.user} ({interaction.user.id})")

        await interaction.response.send_message(
            f"Channel <#{ChannelID}> has been added as a bot channel.",
            ephemeral=True
        )

    @app_commands.command(name="removebotchannel", description="Remove a bot channel.")
    async def remove_bot_channel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):
        GuildID = str(interaction.guild.id)
        ChannelID = str(channel.id)

        # Check if user has admin role
        if not CheckIfAdminRole([role.id for role in interaction.user.roles], interaction.guild.id):
            await log_to_discord(self.bot, GuildID, f"Unauthorized removebotchannel attempt by {interaction.user} ({interaction.user.id})")
            return await interaction.response.send_message(
                "You do not have permission to use this command.",
                ephemeral=True
            )

        # Load existing server data
        filename = "data/servers.json"
        try:
            data = ReadJSON(filename)
        except FileNotFoundError:
            await log_to_discord(self.bot, GuildID, f"removebotchannel failed: server not set up ({interaction.user.id})")
            return await interaction.response.send_message(
                "Server is not set up yet. Please run /setup first.",
                ephemeral=True
            )

        if GuildID not in data or not data[GuildID].get("SetupComplete", False):
            await log_to_discord(self.bot, GuildID, f"removebotchannel failed: setup incomplete ({interaction.user.id})")
            return await interaction.response.send_message(
                "Server is not set up yet. Please run /setup first.",
                ephemeral=True
            )

        if ChannelID not in data[GuildID]["bot_channels"]:
            await log_to_discord(self.bot, GuildID, f"removebotchannel: channel not found ({ChannelID}) by {interaction.user.id}")
            return await interaction.response.send_message(
                f"Channel <#{ChannelID}> is not a bot channel.",
                ephemeral=True
            )

        data[GuildID]["bot_channels"].remove(ChannelID)

        # Save updated data
        WriteJSON(data, filename, indent=4)

        await log_to_discord(self.bot, GuildID, f"Bot channel <#{ChannelID}> removed by {interaction.user} ({interaction.user.id})")

        await interaction.response.send_message(
            f"Channel <#{ChannelID}> has been removed from bot channels.",
            ephemeral=True
        )
        
    @app_commands.command(name="listbotchannels", description="List all bot channels.")
    async def list_bot_channels(self, interaction: discord.Interaction):
        GuildID = str(interaction.guild.id)
        # Check if user has admin role
        if not CheckIfAdminRole([role.id for role in interaction.user.roles], interaction.guild.id):
            await log_to_discord(self.bot, GuildID, f"Unauthorized listbotchannels attempt by {interaction.user} ({interaction.user.id})")
            return await interaction.response.send_message(
                "You do not have permission to use this command.",
                ephemeral=True
            )
        
        # Load existing server data
        filename = "data/servers.json"
        try:
            data = ReadJSON(filename)
        except FileNotFoundError:
            await log_to_discord(self.bot, GuildID, f"listbotchannels failed: server not set up ({interaction.user.id})")
            return await interaction.response.send_message(
                "Server is not set up yet. Please run /setup first.",
                ephemeral=True
            )

        if GuildID not in data or not data[GuildID].get("SetupComplete", False):
            await log_to_discord(self.bot, GuildID, f"listbotchannels failed: setup incomplete ({interaction.user.id})")
            return await interaction.response.send_message(
                "Server is not set up yet. Please run /setup first.",
                ephemeral=True
            )

        bot_channels = data[GuildID].get("bot_channels", [])
        if not bot_channels:
            await log_to_discord(self.bot, GuildID, f"listbotchannels: no bot channels set by {interaction.user.id}")
            return await interaction.response.send_message(
                "No bot channels have been set.",
                ephemeral=True
            )

        channel_mentions = [f"<#{ch}>" for ch in bot_channels]
        await log_to_discord(self.bot, GuildID, f"Bot channels listed by {interaction.user} ({interaction.user.id})")
        await interaction.response.send_message(
            "Bot Channels:\n" + "\n".join(channel_mentions),
            ephemeral=True
        )
        
    @app_commands.command(name="listadminroles", description="List all admin roles.")
    async def list_admin_roles(self, interaction: discord.Interaction):
        GuildID = str(interaction.guild.id)
        # Check if user has admin role
        if not CheckIfAdminRole([role.id for role in interaction.user.roles], interaction.guild.id):
            await log_to_discord(self.bot, GuildID, f"Unauthorized listadminroles attempt by {interaction.user} ({interaction.user.id})")
            return await interaction.response.send_message(
                "You do not have permission to use this command.",
                ephemeral=True
            )
        
        # Load existing server data
        filename = "data/servers.json"
        try:
            data = ReadJSON(filename)
        except FileNotFoundError:
            await log_to_discord(self.bot, GuildID, f"listadminroles failed: server not set up ({interaction.user.id})")
            return await interaction.response.send_message(
                "Server is not set up yet. Please run /setup first.",
                ephemeral=True
            )

        if GuildID not in data or not data[GuildID].get("SetupComplete", False):
            await log_to_discord(self.bot, GuildID, f"listadminroles failed: setup incomplete ({interaction.user.id})")
            return await interaction.response.send_message(
                "Server is not set up yet. Please run /setup first.",
                ephemeral=True
            )

        admin_roles = data[GuildID].get("admin_roles", [])
        if not admin_roles:
            await log_to_discord(self.bot, GuildID, f"listadminroles: no admin roles set by {interaction.user.id}")
            return await interaction.response.send_message(
                "No admin roles have been set.",
                ephemeral=True
            )

        role_mentions = [f"<@&{role}>" for role in admin_roles]
        await log_to_discord(self.bot, GuildID, f"Admin roles listed by {interaction.user} ({interaction.user.id})")
        await interaction.response.send_message(
            "Admin Roles:\n" + "\n".join(role_mentions),
            ephemeral=True
        )
        
    @app_commands.command(name="addadminrole", description="Add an admin role.")
    async def add_admin_role(
        self,
        interaction: discord.Interaction,
        role: discord.Role
    ):
        GuildID = str(interaction.guild.id)
        RoleID = str(role.id)

        # Check if user has admin role
        if not CheckIfAdminRole([role.id for role in interaction.user.roles], interaction.guild.id):
            await log_to_discord(self.bot, GuildID, f"Unauthorized addadminrole attempt by {interaction.user} ({interaction.user.id})")
            return await interaction.response.send_message(
                "You do not have permission to use this command.",
                ephemeral=True
            )

        # Load existing server data
        filename = "data/servers.json"
        try:
            data = ReadJSON(filename)
        except FileNotFoundError:
            await log_to_discord(self.bot, GuildID, f"addadminrole failed: server not set up ({interaction.user.id})")
            return await interaction.response.send_message(
                "Server is not set up yet. Please run /setup first.",
                ephemeral=True
            )

        if GuildID not in data or not data[GuildID].get("SetupComplete", False):
            await log_to_discord(self.bot, GuildID, f"addadminrole failed: setup incomplete ({interaction.user.id})")
            return await interaction.response.send_message(
                "Server is not set up yet. Please run /setup first.",
                ephemeral=True
            )

        if RoleID in data[GuildID]["admin_roles"]:
            await log_to_discord(self.bot, GuildID, f"addadminrole: role already exists ({RoleID}) by {interaction.user.id}")
            return await interaction.response.send_message(
                f"Role <@&{RoleID}> is already an admin role.",
                ephemeral=True
            )

        data[GuildID]["admin_roles"].append(RoleID)

        WriteJSON(data, filename, indent=4)

        await log_to_discord(self.bot, GuildID, f"Admin role <@&{RoleID}> added by {interaction.user} ({interaction.user.id})")

        await interaction.response.send_message(
            f"Role <@&{RoleID}> has been added as an admin role.",
            ephemeral=True
        )
        
    @app_commands.command(name="removeadminrole", description="Remove an admin role.")
    async def remove_admin_role(
        self,
        interaction: discord.Interaction,
        role: discord.Role
    ):
        GuildID = str(interaction.guild.id)
        RoleID = str(role.id)

        # Check if user has admin role
        if not CheckIfAdminRole([role.id for role in interaction.user.roles], interaction.guild.id):
            await log_to_discord(self.bot, GuildID, f"Unauthorized removeadminrole attempt by {interaction.user} ({interaction.user.id})")
            return await interaction.response.send_message(
                "You do not have permission to use this command.",
                ephemeral=True
            )

        # Load existing server data
        filename = "data/servers.json"
        try:
            data = ReadJSON(filename)
        except FileNotFoundError:
            await log_to_discord(self.bot, GuildID, f"removeadminrole failed: server not set up ({interaction.user.id})")
            return await interaction.response.send_message(
                "Server is not set up yet. Please run /setup first.",
                ephemeral=True
            )

        if GuildID not in data or not data[GuildID].get("SetupComplete", False):
            await log_to_discord(self.bot, GuildID, f"removeadminrole failed: setup incomplete ({interaction.user.id})")
            return await interaction.response.send_message(
                "Server is not set up yet. Please run /setup first.",
                ephemeral=True
            )

        if RoleID not in data[GuildID]["admin_roles"]:
            await log_to_discord(self.bot, GuildID, f"removeadminrole: role not found ({RoleID}) by {interaction.user.id}")
            return await interaction.response.send_message(
                f"Role <@&{RoleID}> is not an admin role.",
                ephemeral=True
            )

        data[GuildID]["admin_roles"].remove(RoleID)

        # Save updated data
        WriteJSON(data, filename, indent=4)

        await log_to_discord(self.bot, GuildID, f"Admin role <@&{RoleID}> removed by {interaction.user} ({interaction.user.id})")

        await interaction.response.send_message(
            f"Role <@&{RoleID}> has been removed from admin roles.",
            ephemeral=True
        )
        
    @app_commands.command(name="setbotlogchannel", description="Set or change the bot logging channel.")
    async def set_bot_log_channel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):
        GuildID = str(interaction.guild.id)
        # Check if user has admin role
        if not CheckIfAdminRole([role.id for role in interaction.user.roles], interaction.guild.id):
            await log_to_discord(self.bot, GuildID, f"Unauthorized setbotlogchannel attempt by {interaction.user} ({interaction.user.id})")
            return await interaction.response.send_message(
                "You do not have permission to use this command.",
                ephemeral=True
            )

        filename = "data/servers.json"
        try:
            data = ReadJSON(filename)
        except FileNotFoundError:
            data = {}

        # If server not setup, create minimal entry
        if GuildID not in data:
            data[GuildID] = {"SetupComplete": False}

        # If bot_logs_channel key doesn't exist, create it
        if "bot_logs_channel" not in data[GuildID]:
            data[GuildID]["bot_logs_channel"] = None

        if not data[GuildID].get("SetupComplete", False):
            await log_to_discord(self.bot, GuildID, f"setbotlogchannel failed: setup incomplete ({interaction.user.id})")
            return await interaction.response.send_message(
                "Server is not set up yet. Please run /setup first.",
                ephemeral=True
            )

        old_channel = data[GuildID].get("bot_logs_channel")
        data[GuildID]["bot_logs_channel"] = str(channel.id)
        WriteJSON(data, filename, indent=4)

        await log_to_discord(self.bot, GuildID, f"Bot log channel changed from {old_channel} to {channel.id} by {interaction.user} ({interaction.user.id})")
        await interaction.response.send_message(
            f"Bot log channel set to <#{channel.id}>.",
            ephemeral=True
        )

