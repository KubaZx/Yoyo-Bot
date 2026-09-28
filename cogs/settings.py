from discord import app_commands
from discord.ext import commands
import discord
from utils.data import get_guild_settings, save_settings, settings


class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='settings', description='Turn on/off AI messages limit')
    @app_commands.choices(setting=[
        app_commands.Choice(name='AI rate limit', value='ai_rate_limit')
    ])
    async def settings_command(self, interaction: discord.Interaction, setting: app_commands.Choice[str], enabled: bool):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You don't have permission to change this setting!")
            return
        guild_settings = get_guild_settings(interaction.guild.id)
        guild_settings[setting.value] = enabled
        save_settings(settings)
        await interaction.response.send_message(f"The {setting.name} has been changed to {enabled}")


async def setup(bot):
    await bot.add_cog(Settings(bot))
