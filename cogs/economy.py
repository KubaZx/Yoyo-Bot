import discord
import time
import random
from discord.ext import commands
from utils.data import players, save_data, get_person_key


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pending_bets = {}

    # daily money, once per day
    @commands.command(name='daily')
    async def daily(self, ctx):
        person_key = get_person_key(ctx.author.id, ctx.guild.id)
        player_data = players[person_key]
        if time.time() - player_data['last_daily'] >= 86400:
            players[person_key]['money'] += 100
            players[person_key]['last_daily'] = time.time()
            await ctx.send(f"{ctx.author.mention} You claimed 100 Money! 💸")
            save_data(players)
        else:
            await ctx.send("You already claimed your daily bonus today!")

    # transfer money to another player
    @commands.command(name='give', usage='@Jason 100')
    async def give(self, ctx, target: discord.Member, amount: int):
        person_key = get_person_key(ctx.author.id, ctx.guild.id)
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
    @commands.command(name='steal', usage='@Jason')
    async def steal(self, ctx, target: discord.Member):
        person_key = get_person_key(ctx.author.id, ctx.guild.id)
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

    # roulette system
    @commands.command(name='roulette', usage='red 20')
    async def roulette(self, ctx, color: str = "", amount: int = 0):
        person_key = get_person_key(ctx.author.id, ctx.guild.id)
        if amount <= 0:
            await ctx.send("The amount must be greater than 0!")
            return
        if color not in ['red', 'black', 'green']:
            await ctx.send("Wrong color! Choose: red, black or green!")
            return
        if players[person_key]['money'] < amount:
            await ctx.send("You don't have enough money!")
            return
        result = random.choices(['red', 'black', 'green'], weights=[47.5, 47.5, 5])[0]
        if result == color:
            players[person_key]['money'] += amount * 2
            await ctx.send(f"{ctx.author.mention} The color is {result}. You won! 💰")
            save_data(players)
        else:
            await ctx.send(f"The color is {result}. Not this time 😪")
            players[person_key]['money'] -= amount
            save_data(players)

    # challenge another person for coinflip
    @commands.command(name='challenge', usage='@Jason 100')
    async def challenge(self, ctx, target: discord.Member, amount: int):
        person_key = get_person_key(ctx.author.id, ctx.guild.id)
        target_key = f"{target.id}_{ctx.guild.id}"
        if amount <= 0:
            await ctx.send("The amount must be greater than 0!")
            return
        if ctx.author.id == target.id:
            await ctx.send("You can't challenge yourself!")
            return
        if target_key not in players:
            await ctx.send("This person is not in the database!")
            return
        if target_key in self.pending_bets:
            await ctx.send("This person already has a pending challenge!")
            return
        if players[person_key]['money'] < amount:
            await ctx.send("You don't have enough money to challenge this person!")
            return
        if players[target_key]['money'] < amount:
            await ctx.send("The person you want to challenge with doesn't have enough money!")
            return
        self.pending_bets[target_key] = {'challenger': person_key, 'amount': amount}
        await ctx.send(f"{target.mention} You've been challenged by {ctx.author.mention} for {amount} Money! Type !accept to take this bet.")

    # accept the challenge
    @commands.command(name='accept')
    async def accept(self, ctx):
        person_key = get_person_key(ctx.author.id, ctx.guild.id)
        if person_key not in self.pending_bets:
            await ctx.send("You don't have any pending challenge!")
            return
        challenger_key = self.pending_bets[person_key]['challenger']
        bet_amount = self.pending_bets[person_key]['amount']
        if players[challenger_key]['money'] < bet_amount:
            await ctx.send("The person who challenged you, doesn't have enough money to start the challenge!")
            del self.pending_bets[person_key]
            return
        if players[person_key]['money'] < bet_amount:
            await ctx.send("You don't have enough money for this challenge!")
            del self.pending_bets[person_key]
            return
        del self.pending_bets[person_key]
        draw = random.choice([person_key, challenger_key])
        if draw == person_key:
            players[person_key]['money'] += bet_amount
            players[challenger_key]['money'] -= bet_amount
            await ctx.send(f"Congratulations {ctx.author.mention}, you won {bet_amount} Money! 💰")
        else:
            players[challenger_key]['money'] += bet_amount
            players[person_key]['money'] -= bet_amount
            await ctx.send(f"Congratulations <@{challenger_key.split('_')[0]}>, you won {bet_amount} Money! 💰")
        save_data(players)

    # decline the challenge
    @commands.command(name='decline')
    async def decline(self, ctx):
        person_key = get_person_key(ctx.author.id, ctx.guild.id)
        if person_key not in self.pending_bets:
            await ctx.send("You don't have any pending challenge")
            return
        challenger_key = self.pending_bets[person_key]['challenger']
        del self.pending_bets[person_key]
        await ctx.send(f"<@{challenger_key.split('_')[0]}> {ctx.author.display_name} declined your challenge!")

async def setup(bot):
    await bot.add_cog(Economy(bot))
    