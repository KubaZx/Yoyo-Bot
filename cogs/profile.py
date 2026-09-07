import discord
from discord.ext import commands
from utils.data import players

class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # TODO: Showing player card with pillow:
    @commands.command(name='card')
    async def card(self, ctx):
        await ctx.send("Work in progress 🫡")


async def setup(bot):
    await bot.add_cog(Profile(bot))