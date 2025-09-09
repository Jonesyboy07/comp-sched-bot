import discord
from discord.ext import commands
from discord import app_commands
from utils.funcs import CheckIfAdminRole, ReadJSON, WriteJSON


class SetupCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @app_commands.command(name="setup", description="Setup the bot in this server")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_command(
        self, 
        interaction: discord.Interaction, 
        command_channel: discord.TextChannel, 
        admin_role: discord.Role
        ):
        
        GuildID = str(interaction.guild.id)
        BotChannel = str(command_channel.id)
        AdminRole = str(admin_role.id)
        
        # Load existing server data
        filename = "data/servers.json"
        try:
            with open(filename, 'r') as f:
                data = ReadJSON(f)
        except FileNotFoundError:
            data = {}

        # Only allow setup if SetupComplete is not True
        if GuildID in data and data[GuildID].get("SetupComplete", False):
            return await interaction.response.send_message(
                "Setup has already been completed for this server. Use other commands to modify settings.",
                ephemeral=True
            )

        # Perform setup
        data[GuildID] = {
            "bot_channels": [BotChannel],
            "admin_roles": [AdminRole],
            "leagues": [],
            "SetupComplete": True
        }

        # Save updated data
        with open(filename, 'w') as f:
            WriteJSON(data, f, indent=4)

        await interaction.response.send_message(
            f"Setup complete! Channel(s): <#{BotChannel}> ({BotChannel}), Admin role(s): <@&{AdminRole}>.",
            ephemeral=True
        )
        
    @app_commands.command(name="addbotchannel", description="Add a bot channel")
    async def add_bot_channel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):
        GuildID = str(interaction.guild.id)
        ChannelID = str(channel.id)

        # Check if user has admin role
        if not CheckIfAdminRole([role.id for role in interaction.user.roles], interaction.guild.id):
            return await interaction.response.send_message(
                "You do not have permission to use this command.",
                ephemeral=True
            )

        # Load existing server data
        filename = "data/servers.json"
        try:
            with open(filename, 'r') as f:
                data = ReadJSON(f)
        except FileNotFoundError:
            return await interaction.response.send_message(
                "Server is not set up yet. Please run /setup first.",
                ephemeral=True
            )

        if GuildID not in data or not data[GuildID].get("SetupComplete", False):
            return await interaction.response.send_message(
                "Server is not set up yet. Please run /setup first.",
                ephemeral=True
            )

        if ChannelID in data[GuildID]["bot_channels"]:
            return await interaction.response.send_message(
                f"Channel <#{ChannelID}> is already a bot channel.",
                ephemeral=True
            )

        data[GuildID]["bot_channels"].append(ChannelID)

        # Save updated data
        with open(filename, 'w') as f:
            WriteJSON(data, f, indent=4)

        await interaction.response.send_message(
            f"Channel <#{ChannelID}> has been added as a bot channel.",
            ephemeral=True
        )

    @app_commands.command(name="removebotchannel", description="Remove a bot channel")
    async def remove_bot_channel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):
        GuildID = str(interaction.guild.id)
        ChannelID = str(channel.id)

        # Check if user has admin role
        if not CheckIfAdminRole([role.id for role in interaction.user.roles], interaction.guild.id):
            return await interaction.response.send_message(
                "You do not have permission to use this command.",
                ephemeral=True
            )

        # Load existing server data
        filename = "data/servers.json"
        try:
            with open(filename, 'r') as f:
                data = ReadJSON(f)
        except FileNotFoundError:
            return await interaction.response.send_message(
                "Server is not set up yet. Please run /setup first.",
                ephemeral=True
            )

        if GuildID not in data or not data[GuildID].get("SetupComplete", False):
            return await interaction.response.send_message(
                "Server is not set up yet. Please run /setup first.",
                ephemeral=True
            )

        if ChannelID not in data[GuildID]["bot_channels"]:
            return await interaction.response.send_message(
                f"Channel <#{ChannelID}> is not a bot channel.",
                ephemeral=True
            )

        data[GuildID]["bot_channels"].remove(ChannelID)

        # Save updated data
        with open(filename, 'w') as f:
            WriteJSON(data, f, indent=4)

        await interaction.response.send_message(
            f"Channel <#{ChannelID}> has been removed from bot channels.",
            ephemeral=True
        )
        
    @app_commands.command(name="listbotchannels", description="List all bot channels")
    async def list_bot_channels(self, interaction: discord.Interaction):
        GuildID = str(interaction.guild.id)
        # Check if user has admin role
        if not CheckIfAdminRole([role.id for role in interaction.user.roles], interaction.guild.id):
            return await interaction.response.send_message(
                "You do not have permission to use this command.",
                ephemeral=True
            )
        
        # Load existing server data
        filename = "data/servers.json"
        try:
            with open(filename, 'r') as f:
                data = ReadJSON(f)
        except FileNotFoundError:
            return await interaction.response.send_message(
                "Server is not set up yet. Please run /setup first.",
                ephemeral=True
            )

        if GuildID not in data or not data[GuildID].get("SetupComplete", False):
            return await interaction.response.send_message(
                "Server is not set up yet. Please run /setup first.",
                ephemeral=True
            )

        bot_channels = data[GuildID].get("bot_channels", [])
        if not bot_channels:
            return await interaction.response.send_message(
                "No bot channels have been set.",
                ephemeral=True
            )

        channel_mentions = [f"<#{ch}>" for ch in bot_channels]
        await interaction.response.send_message(
            "Bot Channels:\n" + "\n".join(channel_mentions),
            ephemeral=True
        )
        
    @app_commands.command(name="listadminroles", description="List all admin roles")
    async def list_admin_roles(self, interaction: discord.Interaction):
        GuildID = str(interaction.guild.id)
        # Check if user has admin role
        if not CheckIfAdminRole([role.id for role in interaction.user.roles], interaction.guild.id):
            return await interaction.response.send_message(
                "You do not have permission to use this command.",
                ephemeral=True
            )
        
        # Load existing server data
        filename = "data/servers.json"
        try:
            with open(filename, 'r') as f:
                data = ReadJSON(f)
        except FileNotFoundError:
            return await interaction.response.send_message(
                "Server is not set up yet. Please run /setup first.",
                ephemeral=True
            )

        if GuildID not in data or not data[GuildID].get("SetupComplete", False):
            return await interaction.response.send_message(
                "Server is not set up yet. Please run /setup first.",
                ephemeral=True
            )

        admin_roles = data[GuildID].get("admin_roles", [])
        if not admin_roles:
            return await interaction.response.send_message(
                "No admin roles have been set.",
                ephemeral=True
            )

        role_mentions = [f"<@&{role}>" for role in admin_roles]
        await interaction.response.send_message(
            "Admin Roles:\n" + "\n".join(role_mentions),
            ephemeral=True
        )
        
    @app_commands.command(name="addadminrole", description="Add an admin role")
    async def add_admin_role(
        self,
        interaction: discord.Interaction,
        role: discord.Role
    ):
        GuildID = str(interaction.guild.id)
        RoleID = str(role.id)

        # Check if user has admin role
        if not CheckIfAdminRole([role.id for role in interaction.user.roles], interaction.guild.id):
            return await interaction.response.send_message(
                "You do not have permission to use this command.",
                ephemeral=True
            )

        # Load existing server data
        filename = "data/servers.json"
        try:
            with open(filename, 'r') as f:
                data = ReadJSON(f)
        except FileNotFoundError:
            return await interaction.response.send_message(
                "Server is not set up yet. Please run /setup first.",
                ephemeral=True
            )

        if GuildID not in data or not data[GuildID].get("SetupComplete", False):
            return await interaction.response.send_message(
                "Server is not set up yet. Please run /setup first.",
                ephemeral=True
            )

        if RoleID in data[GuildID]["admin_roles"]:
            return await interaction.response.send_message(
                f"Role <@&{RoleID}> is already an admin role.",
                ephemeral=True
            )

        data[GuildID]["admin_roles"].append(RoleID)

        # Save updated data
        with open(filename, 'w') as f:
            WriteJSON(data, f, indent=4)

        await interaction.response.send_message(
            f"Role <@&{RoleID}> has been added as an admin role.",
            ephemeral=True
        )
        
    @app_commands.command(name="removeadminrole", description="Remove an admin role")
    async def remove_admin_role(
        self,
        interaction: discord.Interaction,
        role: discord.Role
    ):
        GuildID = str(interaction.guild.id)
        RoleID = str(role.id)

        # Check if user has admin role
        if not CheckIfAdminRole([role.id for role in interaction.user.roles], interaction.guild.id):
            return await interaction.response.send_message(
                "You do not have permission to use this command.",
                ephemeral=True
            )

        # Load existing server data
        filename = "data/servers.json"
        try:
            with open(filename, 'r') as f:
                data = ReadJSON(f)
        except FileNotFoundError:
            return await interaction.response.send_message(
                "Server is not set up yet. Please run /setup first.",
                ephemeral=True
            )

        if GuildID not in data or not data[GuildID].get("SetupComplete", False):
            return await interaction.response.send_message(
                "Server is not set up yet. Please run /setup first.",
                ephemeral=True
            )

        if RoleID not in data[GuildID]["admin_roles"]:
            return await interaction.response.send_message(
                f"Role <@&{RoleID}> is not an admin role.",
                ephemeral=True
            )

        data[GuildID]["admin_roles"].remove(RoleID)

        # Save updated data
        with open(filename, 'w') as f:
            WriteJSON(data, f, indent=4)

        await interaction.response.send_message(
            f"Role <@&{RoleID}> has been removed from admin roles.",
            ephemeral=True
        )