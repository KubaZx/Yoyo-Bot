import discord
import random
from discord.ext import commands
from discord import app_commands

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
    @commands.command(name='coinflip')
    async def coinflip(self, ctx):
        coin = ['heads', 'tails']
        await ctx.send(random.choice(coin))

    # Choose between yes/maybe/no
    @commands.command(name='choose')
    async def choose(self, ctx):
        answers = ['yes', 'maybe', 'no']
        await ctx.send(random.choice(answers))

    # Game of rock, paper and scissors
    @commands.command(name='rps', usage='paper')
    async def rps(self, ctx, player_choice: str = ""):
        choices = ['rock', 'paper', 'scissors']
        if player_choice not in choices:
            await ctx.send("Wrong choice! Pick rock, paper or scissors")
            return
        bot_choice = random.choice(choices)
        if player_choice == bot_choice:
            await ctx.send(f"You picked {player_choice} and bot picked {bot_choice}, Draw!")
        elif (player_choice == 'rock' and bot_choice == 'scissors') or (player_choice == 'paper' and bot_choice == 'rock') or (player_choice == 'scissors' and bot_choice == 'paper'):
            await ctx.send(f"You won! Bot picked {bot_choice}")
        else:
            await ctx.send(f"Bot picked {bot_choice}, You lost!")

async def setup(bot):
    await bot.add_cog(Games(bot))
