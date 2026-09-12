import discord
from discord.ext import commands
from utils.data import players, get_person_key
from discord import app_commands

class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # TODO: Showing player card with pillow:
    @app_commands.command(name='card', description='Show your profile card (work in progress)')
    async def card(self, interaction: discord.Interaction):
        await interaction.response.send_message("Work in progress 🫡")

    # Player profile, showing level; xp ; money
    @app_commands.command(name='profile', description='Show your level, XP and money')
    async def profile(self, interaction: discord.Interaction):
        person_key = get_person_key(interaction.user.id, interaction.guild.id)
        player_data = players[person_key]
        embed = discord.Embed(title='Player Profile', color=0x00ff00)
        embed.add_field(name='Level', value=player_data['level'], inline=True)
        embed.add_field(name='XP', value=f"{player_data['xp']}/{player_data['level'] * 100}", inline=True)
        embed.add_field(name='Money', value=player_data['money'], inline=True)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    # Profile of achievements
    @app_commands.command(name='achievements', description='Show your unlocked achievements')
    async def achievements(self, interaction: discord.Interaction):
        person_key = get_person_key(interaction.user.id, interaction.guild.id)
        achievements_data = players[person_key]
        embed = discord.Embed(title='Achievements', color=0x079DFA)
        if achievements_data['achievements']['500_messages']:
            embed.add_field(name='500 messages', value='✅', inline=False)
        else:
            embed.add_field(name='500 messages', value='❌', inline=False)
        if achievements_data['achievements']['level_5']:
            embed.add_field(name='Level 5', value='✅', inline=False)
        else:
            embed.add_field(name='Level 5', value='❌', inline=False)
        if achievements_data['achievements']['500_money']:
            embed.add_field(name='500 money', value='✅', inline=False)
        else:
            embed.add_field(name='500 money', value='❌', inline=False)
        await interaction.response.send_message(embed=embed)

    # List of top players from server
    @app_commands.command(name='top', description='Show the server ranking')
    async def top(self, interaction: discord.Interaction):
        server_players = {k: v for k, v in players.items() if k.endswith("_" + str(interaction.guild.id))}
        ranking = sorted(server_players.items(), key=lambda x: (x[1]['level'], x[1]['xp'], x[1]['money']), reverse=True)
        embed = discord.Embed(title='Top players 🏆', color=0xE0D90D)
        for i, (player_id, data) in enumerate(ranking[:10]):
            embed.add_field(
                name=f'{i + 1}. place',
                value=f'<@{player_id.split("_")[0]}> | Level {data["level"]} | XP: {data["xp"]}/{data["level"] * 100} | Money {data["money"]}',
                inline=False
            )
        await interaction.response.send_message(embed=embed)

    # Check the statistics for the actual server
    @app_commands.command(name='stats', description='Show server statistics')
    async def stats(self, interaction: discord.Interaction):
        server_players = {k: v for k, v in players.items() if k.endswith("_" + str(interaction.guild.id))}
        if not server_players:
            await interaction.response.send_message("No players on this server yet!")
            return
        player_count = len(server_players)
        total_money = sum(profile['money'] for profile in server_players.values())
        total_messages = sum(profile['total_messages'] for profile in server_players.values())
        richest_person = max(server_players.items(), key=lambda x: x[1]['money'])
        embed = discord.Embed(title='Server Stats 📈', color=0x9B59B6)
        embed.add_field(name='Number of Players 👤', value=player_count, inline=False)
        embed.add_field(name='Amount of Money 💸', value=total_money, inline=False)
        embed.add_field(name='The Richest Person 👤💸', value=f"<@{richest_person[0].split('_')[0]}> has {richest_person[1]['money']}", inline=False)
        embed.add_field(name='Number of Messages 📨', value=total_messages, inline=False)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Profile(bot))
