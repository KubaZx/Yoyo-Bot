import discord
import time
import random
from discord.ext import commands
from utils.data import players, save_data


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # daily money, once per day
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
            await ctx.send("You already claimed your daily bonus today!")
    # transfer money to another player
    @commands.command(name='give')
    async def give(self, ctx, target: discord.Member, amount: int):
        person_key = f"{ctx.author.id}_{ctx.guild.id}"
        if amount <= 0:
            await ctx.send("The amount must be greater than 0!")
            return
        if ctx.author.id == target.id:
            await ctx.send("You can't give money to yourself!")
            return
        target_key = f"{target.id}_{ctx.guild.id}"
        if target_key not in players:
            await ctx.send("This person is not in the database!")
            return
        if players[person_key]['money'] < amount:
            await ctx.send("You don't have enough money!")
            return
        players[person_key]['money'] -= amount
        players[target_key]['money'] += amount
        save_data(players)
        await ctx.send(f"Nice! You have transferred {amount} money to {target.mention}")

    # steal money from another player - 50% chance
    @commands.command(name='steal')
    async def steal(self, ctx, target: discord.Member):
        person_key = f"{ctx.author.id}_{ctx.guild.id}"
        target_key = f"{target.id}_{ctx.guild.id}"
        if ctx.author.id == target.id:
            await ctx.send("You can't steal from yourself")
            return
        if target_key not in players:
            await ctx.send("This person is not in the database!")
            return
        if players[person_key]['money'] <= 0 or players[target_key]['money'] <= 0:
            await ctx.send("You or the other person doesn't have enough money!")
            return
        stolen_money = random.randint(1, players[target_key]['money'])
        if random.randint(1, 2) == 1:
            players[person_key]['money'] += stolen_money
            players[target_key]['money'] -= stolen_money
            await ctx.send(f"You stole {stolen_money} Money 😈")
            save_data(players)
        else:
            lost = min(players[person_key]['money'], stolen_money)
            players[person_key]['money'] -= lost
            await ctx.send(f"Not this time, you lost {lost} money 😪")
            save_data(players)


async def setup(bot):
    await bot.add_cog(Economy(bot))