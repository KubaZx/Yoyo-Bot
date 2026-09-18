import discord
import io
from PIL import Image, ImageDraw, ImageFont
from discord.ext import commands
from utils.data import players, get_person_key
from discord import app_commands

class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Player card with avatar, XP bar and stats:
    @app_commands.command(name='card', description='Show your profile card')
    async def card(self, interaction: discord.Interaction):
        image = Image.new('RGB', (520, 260), (30, 31, 34))
        font_bold = ImageFont.truetype('assets/arialbd.ttf', 28)
        font_regular = ImageFont.truetype('assets/arial.ttf', 16)
        draw = ImageDraw.Draw(image)
        person_key = get_person_key(interaction.user.id, interaction.guild.id)
        player_data = players[person_key]
        avatar_bytes = await interaction.user.display_avatar.read()
        avatar = Image.open(io.BytesIO(avatar_bytes)).convert('RGB').resize((72, 72))
        mask = Image.new('L', (72, 72), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse([(0, 0), (72, 72)], fill=255)
        image.paste(avatar, (30, 30), mask)
        draw.text((120, 30), interaction.user.display_name, fill=(255, 255, 255), font=font_bold)
        if player_data['active_title'] is not None:
            draw.text((120, 67), f"{player_data['active_title']}", fill=(255, 200, 50), font=font_regular)
        draw.text((120, 85), f"Level {player_data['level']}", fill=(150, 150, 150), font=font_regular)
        draw.text((30, 120), "XP", fill=(150, 150, 150), font=font_regular)
        draw.text((400, 120), f"{player_data['xp']} / {player_data['level'] * 100}", fill=(150, 150, 150), font=font_regular)
        progress = player_data['xp'] / (player_data['level'] * 100)
        draw.rectangle([(30, 145), (490, 155)], fill=(50, 51, 55))
        draw.rectangle([(30, 145),(int(30 + progress * 460), 155)], fill=(88, 101, 242))
        draw.text((30, 190), "Money", fill=(150, 150, 150), font=font_regular)
        draw.text((30, 210), str(player_data['money']), fill=(255, 255, 255), font=font_bold)
        draw.text((200, 190), "Messages", fill=(150, 150, 150), font=font_regular)
        draw.text((200, 210), f"{player_data['total_messages']}", fill=(255, 255, 255), font=font_bold)
        draw.text((370, 190), "Achievements", fill=(150, 150, 150), font=font_regular)
        draw.text((370, 210), f"{sum(player_data['achievements'].values())} / 3", fill=(255, 255, 255), font=font_bold)
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        file = discord.File(buffer, filename='card.png')
        await interaction.response.send_message(file=file)

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
