import discord
import random
from discord.ext import commands
from discord import app_commands
from typing import Literal

class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Roll a random number
    @app_commands.command(name='dice', description='Roll a dice')
    async def dice(self, interaction: discord.Interaction, sides: int = 6):
        if sides < 2:
            await interaction.response.send_message("A dice needs at least 2 sides!")
            return
        await interaction.response.send_message(f"You rolled {random.randint(1, sides)}!")

    # Coinflip - 50/50
    @app_commands.command(name='coinflip', description='Flip a coin')
    async def coinflip(self, interaction: discord.Interaction):
        coin = ['heads', 'tails']
        await interaction.response.send_message(random.choice(coin))

    # Choose between yes/maybe/no
    @app_commands.command(name='choose', description='Let the bot decide for you')
    async def choose(self, interaction: discord.Interaction):
        answers = ['yes', 'maybe', 'no']
        await interaction.response.send_message(random.choice(answers))

    # Game of rock, paper and scissors
    @app_commands.command(name='rps', description='Play rock-paper-scissors')
    async def rps(self, interaction: discord.Interaction, player_choice: Literal['rock', 'paper', 'scissors']):
        choices = ['rock', 'paper', 'scissors']
        bot_choice = random.choice(choices)
        if player_choice == bot_choice:
            await interaction.response.send_message(f"You picked {player_choice} and bot picked {bot_choice}, Draw!")
        elif (player_choice == 'rock' and bot_choice == 'scissors') or (player_choice == 'paper' and bot_choice == 'rock') or (player_choice == 'scissors' and bot_choice == 'paper'):
            await interaction.response.send_message(f"You won! Bot picked {bot_choice}")
        else:
            await interaction.response.send_message(f"Bot picked {bot_choice}, You lost!")

async def setup(bot):
    await bot.add_cog(Games(bot))
