import discord
import time
import random
from discord.ext import commands
from utils.data import players, save_data, get_person_key
from discord import app_commands
from typing import Literal


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pending_bets = {}

    # daily money, once per day
    @app_commands.command(name='daily', description='Claim daily money')
    async def daily(self, interaction: discord.Interaction):
        person_key = get_person_key(interaction.user.id, interaction.guild.id)
        player_data = players[person_key]
        if time.time() - player_data['last_daily'] >= 86400:
            players[person_key]['money'] += 100
            players[person_key]['last_daily'] = time.time()
            await interaction.response.send_message(f"{interaction.user.mention} You claimed 100 Money! 💸")
            save_data(players)
        else:
            await interaction.response.send_message("You already claimed your daily bonus today!")

    # transfer money to another player
    @app_commands.command(name='give', description='Give money to another person')
    async def give(self, interaction: discord.Interaction, target: discord.Member, amount: int):
        person_key = get_person_key(interaction.user.id, interaction.guild.id)
        if amount <= 0:
            await interaction.response.send_message("The amount must be greater than 0!")
            return
        if interaction.user.id == target.id:
            await interaction.response.send_message("You can't give money to yourself!")
            return
        target_key = f"{target.id}_{interaction.guild.id}"
        if target_key not in players:
            await interaction.response.send_message("This person is not in the database!")
            return
        if players[person_key]['money'] < amount:
            await interaction.response.send_message("You don't have enough money!")
            return
        players[person_key]['money'] -= amount
        players[target_key]['money'] += amount
        save_data(players)
        await interaction.response.send_message(f"Nice! You have transferred {amount} money to {target.mention}")

    # steal money from another player - 50% chance
    @app_commands.command(name='steal', description='Steal money from other person')
    async def steal(self, interaction: discord.Interaction, target: discord.Member):
        person_key = get_person_key(interaction.user.id, interaction.guild.id)
        target_key = f"{target.id}_{interaction.guild.id}"
        if interaction.user.id == target.id:
            await interaction.response.send_message("You can't steal from yourself")
            return
        if target_key not in players:
            await interaction.response.send_message("This person is not in the database!")
            return
        if players[person_key]['money'] <= 0 or players[target_key]['money'] <= 0:
            await interaction.response.send_message("You or the other person doesn't have enough money!")
            return
        stolen_money = random.randint(1, players[target_key]['money'])
        if random.randint(1, 2) == 1:
            players[person_key]['money'] += stolen_money
            players[target_key]['money'] -= stolen_money
            await interaction.response.send_message(f"You stole {stolen_money} Money 😈")
            save_data(players)
        else:
            lost = min(players[person_key]['money'], stolen_money)
            players[person_key]['money'] -= lost
            await interaction.response.send_message(f"Not this time, you lost {lost} money 😪")
            save_data(players)

    # roulette system
    @app_commands.command(name='roulette', description='Play roulette and try to win money')
    async def roulette(self, interaction: discord.Interaction, color: Literal['red', 'black', 'green'], amount: int):
        person_key = get_person_key(interaction.user.id, interaction.guild.id)
        if amount <= 0:
            await interaction.response.send_message("The amount must be greater than 0!")
            return
        if players[person_key]['money'] < amount:
            await interaction.response.send_message("You don't have enough money!")
            return
        result = random.choices(['red', 'black', 'green'], weights=[47.5, 47.5, 5])[0]
        if result == color:
            players[person_key]['money'] += amount * 2
            await interaction.response.send_message(f"{interaction.user.mention} The color is {result}. You won! 💰")
            save_data(players)
        else:
            await interaction.response.send_message(f"The color is {result}. Not this time 😪")
            players[person_key]['money'] -= amount
            save_data(players)

    # challenge another person for coinflip
    @app_commands.command(name='challenge', description='challenge someone for coinflip')
    async def challenge(self, interaction: discord.Interaction, target: discord.Member, amount: int):
        person_key = get_person_key(interaction.user.id, interaction.guild.id)
        target_key = f"{target.id}_{interaction.guild.id}"
        if amount <= 0:
            await interaction.response.send_message("The amount must be greater than 0!")
            return
        if interaction.user.id == target.id:
            await interaction.response.send_message("You can't challenge yourself!")
            return
        if target_key not in players:
            await interaction.response.send_message("This person is not in the database!")
            return
        if target_key in self.pending_bets:
            await interaction.response.send_message("This person already has a pending challenge!")
            return
        if players[person_key]['money'] < amount:
            await interaction.response.send_message("You don't have enough money to challenge this person!")
            return
        if players[target_key]['money'] < amount:
            await interaction.response.send_message("The person you want to challenge with doesn't have enough money!")
            return
        self.pending_bets[target_key] = {'challenger': person_key, 'amount': amount}
        await interaction.response.send_message(f"{target.mention} You've been challenged by {interaction.user.mention} for {amount} Money! Type /accept to take this bet.")

    # accept the challenge
    @app_commands.command(name='accept', description='accept the challenge')
    async def accept(self, interaction: discord.Interaction):
        person_key = get_person_key(interaction.user.id, interaction.guild.id)
        if person_key not in self.pending_bets:
            await interaction.response.send_message("You don't have any pending challenge!")
            return
        challenger_key = self.pending_bets[person_key]['challenger']
        bet_amount = self.pending_bets[person_key]['amount']
        if players[challenger_key]['money'] < bet_amount:
            await interaction.response.send_message("The person who challenged you, doesn't have enough money to start the challenge!")
            del self.pending_bets[person_key]
            return
        if players[person_key]['money'] < bet_amount:
            await interaction.response.send_message("You don't have enough money for this challenge!")
            del self.pending_bets[person_key]
            return
        del self.pending_bets[person_key]
        draw = random.choice([person_key, challenger_key])
        if draw == person_key:
            players[person_key]['money'] += bet_amount
            players[challenger_key]['money'] -= bet_amount
            await interaction.response.send_message(f"Congratulations {interaction.user.mention}, you won {bet_amount} Money! 💰")
        else:
            players[challenger_key]['money'] += bet_amount
            players[person_key]['money'] -= bet_amount
            await interaction.response.send_message(f"Congratulations <@{challenger_key.split('_')[0]}>, you won {bet_amount} Money! 💰")
        save_data(players)

    # decline the challenge
    @app_commands.command(name='decline', description='decline the challenge')
    async def decline(self, interaction: discord.Interaction):
        person_key = get_person_key(interaction.user.id, interaction.guild.id)
        if person_key not in self.pending_bets:
            await interaction.response.send_message("You don't have any pending challenge")
            return
        challenger_key = self.pending_bets[person_key]['challenger']
        del self.pending_bets[person_key]
        await interaction.response.send_message(f"<@{challenger_key.split('_')[0]}> {interaction.user.display_name} declined your challenge!")

async def setup(bot):
    await bot.add_cog(Economy(bot))
    