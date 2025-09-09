import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from os import path
from dotenv import load_dotenv


def LoadJSON(filename):
    with open(filename, 'r') as f:
        return json.load(f)

class SectionDropdown(discord.ui.Select):
    def __init__(self, sections):
        options = [
            discord.SelectOption(label="All", value="all", description="Show all commands")
        ]
        for section in sections:
            options.append(
                discord.SelectOption(label=section["name"], value=section["name"], description=f"Show {section['name']} commands")
            )
        super().__init__(placeholder="Choose a section...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        view: HelpView = self.view
        view.selected_section = self.values[0]
        view.page = 0
        view.update_buttons()
        await interaction.response.edit_message(embed=view.get_embed(), view=view)

class HelpView(discord.ui.View):
    def __init__(self, sections, per_page=5):
        super().__init__(timeout=120)
        self.sections = sections
        self.per_page = per_page
        self.selected_section = "all"
        self.page = 0

        self.prev_button = discord.ui.Button(label="Previous", style=discord.ButtonStyle.secondary)
        self.next_button = discord.ui.Button(label="Next", style=discord.ButtonStyle.secondary)
        self.stop_button = discord.ui.Button(label="Stop", style=discord.ButtonStyle.danger)
        self.prev_button.callback = self.prev_page
        self.next_button.callback = self.next_page
        self.stop_button.callback = self.stop_view
        self.add_item(self.prev_button)
        self.add_item(self.next_button)
        self.add_item(SectionDropdown(sections))
        self.add_item(self.stop_button)
        self.update_buttons()

    def get_commands(self):
        if self.selected_section == "all":
            commands = []
            for section in self.sections:
                commands.extend(section["commands"])
            return commands
        else:
            for section in self.sections:
                if section["name"] == self.selected_section:
                    return section["commands"]
            return []

    def update_buttons(self):
        commands = self.get_commands()
        max_page = max(0, (len(commands) - 1) // self.per_page)
        self.prev_button.disabled = self.page == 0
        self.next_button.disabled = self.page >= max_page
        self.max_page = max_page

    async def prev_page(self, interaction: discord.Interaction):
        if self.page > 0:
            self.page -= 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.get_embed(), view=self)

    async def next_page(self, interaction: discord.Interaction):
        if self.page < self.max_page:
            self.page += 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.get_embed(), view=self)

    async def stop_view(self, interaction: discord.Interaction):
        await interaction.message.delete()
        await interaction.response.defer()  # Prevent "interaction failed" message

    def get_embed(self):
        commands = self.get_commands()
        embed = discord.Embed(
            title="Help",
            description=f"List of commands in section: {self.selected_section.capitalize()}",
            color=discord.Color.blue()
        )
        start = self.page * self.per_page
        end = start + self.per_page
        for command in commands[start:end]:
            admin_required = "✅ Requires Admin" if command.get("AdminRole", False) else "❌ No Admin Required"
            embed.add_field(
                name=f"{command['name']} ({command['usage']})",
                value=f"{command['description']}\n{admin_required}",
                inline=False
            )
        embed.set_footer(text=f"Page {self.page + 1} of {self.max_page + 1}")
        return embed

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Show help information")
    async def help_command(self, interaction: discord.Interaction):
        sections = LoadJSON("data/commands.json")["sections"]
        view = HelpView(sections)
        await interaction.response.send_message(embed=view.get_embed(), view=view)

    @app_commands.command(name="version", description="Show bot version")
    async def version_command(self, interaction: discord.Interaction):
        load_dotenv(dotenv_path=path.abspath(path.join(os.getcwd(), ".env")))
        version = os.getenv("VERSION", "Unknown")
        await interaction.response.send_message(f"Bot version: {version}")

    @app_commands.command(name="ping", description="Check bot latency")
    async def ping_command(self, interaction: discord.Interaction):
        latency = self.bot.latency * 1000  # Convert to milliseconds
        await interaction.response.send_message(f"Pong! Latency: {latency:.3f} ms")