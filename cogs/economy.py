import time
from discord.ext import commands
from utils.data import players, save_data


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    #daily money, once per day
    @commands.command(name='daily')
    async def daily(self, ctx):
        person_key = f"{ctx.author.id}_{ctx.guild.id}"
        player_data = players[person_key]
        if time.time() - player_data['last_daily'] >= 86400:
            players[person_key]['money'] += 100
            players[person_key]['last_daily'] = time.time()
            await ctx.send(f"{ctx.author.mention} You claimed 100 Money! 💸")
            save_data(players)
        else:
            await ctx.send('You already claimed your daily bonus today!')

async def setup(bot):
    await bot.add_cog(Economy(bot))