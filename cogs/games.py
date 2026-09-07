import random
from discord.ext import commands


class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Roll a random number
    @commands.command(name='dice')
    async def dice(self, ctx, sides: int = 6):
        if sides < 2:
            await ctx.send("A dice needs at least 2 sides!")
            return
        await ctx.send(f"You rolled {random.randint(1, sides)}!")

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

async def setup(bot):
    await bot.add_cog(Games(bot))
