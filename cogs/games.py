import random
from discord.ext import commands


class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='dice')
    async def dice(self, ctx, sides: int = 6):
        if sides < 2:
            await ctx.send("A dice needs at least 2 sides!")
            return
        await ctx.send(f"You rolled {random.randint(1, sides)}!")

async def setup(bot):
    await bot.add_cog(Games(bot))
