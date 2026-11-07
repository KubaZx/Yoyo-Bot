import discord
import time
import random
from discord.ext import commands
from utils.data import get_person_key, get_player_db, save_player
from discord import app_commands
from typing import Literal


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pending_bets = {}

    # daily money, once per day
    @app_commands.command(name='daily', description='Claim daily money')
    async def daily(self, interaction: discord.Interaction):
        player_data = get_player_db(interaction.user.id, interaction.guild.id)
        if time.time() - player_data['last_daily'] >= 86400:
            player_data['money'] += 100
            player_data['last_daily'] = time.time()
            await interaction.response.send_message(f"{interaction.user.mention} You claimed 100 Money! 💸")
            save_player(interaction.user.id, interaction.guild.id, player_data)
        else:
            await interaction.response.send_message("You already claimed your daily bonus today!")

    # transfer money to another player
    @app_commands.command(name='give', description='Give money to another person')
    async def give(self, interaction: discord.Interaction, target: discord.Member, amount: int):
        player_data = get_player_db(interaction.user.id, interaction.guild.id)
        if amount <= 0:
            await interaction.response.send_message("The amount must be greater than 0!")
            return
        if interaction.user.id == target.id:
            await interaction.response.send_message("You can't give money to yourself!")
            return
        if target.bot:
            await interaction.response.send_message("You can't give money to a bot!")
            return
        if player_data['money'] < amount:
            await interaction.response.send_message("You don't have enough money!")
            return
        target_data = get_player_db(target.id, interaction.guild.id)
        player_data['money'] -= amount
        target_data['money'] += amount
        save_player(interaction.user.id, interaction.guild.id, player_data)
        save_player(target.id, interaction.guild.id, target_data)
        await interaction.response.send_message(f"Nice! You have transferred {amount} money to {target.mention}")

    # steal money from another player - 50% chance
    @app_commands.command(name='steal', description='Steal money from other person')
    async def steal(self, interaction: discord.Interaction, target: discord.Member):
        player_data = get_player_db(interaction.user.id, interaction.guild.id)
        if interaction.user.id == target.id:
            await interaction.response.send_message("You can't steal from yourself")
            return
        if target.bot:
            await interaction.response.send_message("You can't steal money from a bot!")
            return
        target_data = get_player_db(target.id, interaction.guild.id)
        if time.time() < target_data['protected_until']:
            await interaction.response.send_message(f"{target.display_name} has activated protection!")
            return
        if player_data['money'] <= 0 or target_data['money'] <= 0:
            await interaction.response.send_message("You or the other person doesn't have enough money!")
            return
        stolen_money = random.randint(1, target_data['money'])
        if random.randint(1, 2) == 1:
            player_data['money'] += stolen_money
            target_data['money'] -= stolen_money
            await interaction.response.send_message(f"You stole {stolen_money} Money 😈")
            save_player(interaction.user.id, interaction.guild.id, player_data)
            save_player(target.id, interaction.guild.id, target_data)
        else:
            lost = min(player_data['money'], stolen_money)
            player_data['money'] -= lost
            await interaction.response.send_message(f"Not this time, you lost {lost} money 😪")
            save_player(interaction.user.id, interaction.guild.id, player_data)

    # roulette system
    @app_commands.command(name='roulette', description='Play roulette and try to win money')
    async def roulette(self, interaction: discord.Interaction, color: Literal['red', 'black', 'green'], amount: int):
        player_data = get_player_db(interaction.user.id, interaction.guild.id)
        if amount <= 0:
            await interaction.response.send_message("The amount must be greater than 0!")
            return
        if player_data['money'] < amount:
            await interaction.response.send_message("You don't have enough money!")
            return
        result = random.choices(['red', 'black', 'green'], weights=[47.5, 47.5, 5])[0]
        if result == color:
            if color == 'green':
                player_data['money'] += amount * 14
            else:
                player_data['money'] += amount
            await interaction.response.send_message(f"{interaction.user.mention} The color is {result}. You won! 💰")
            save_player(interaction.user.id, interaction.guild.id, player_data)
        else:
            await interaction.response.send_message(f"The color is {result}. Not this time 😪")
            player_data['money'] -= amount
            save_player(interaction.user.id, interaction.guild.id, player_data)

    # challenge another person for coinflip
    @app_commands.command(name='challenge', description='challenge someone for coinflip')
    async def challenge(self, interaction: discord.Interaction, target: discord.Member, amount: int):
        player_data = get_player_db(interaction.user.id, interaction.guild.id)
        person_key = get_person_key(interaction.user.id, interaction.guild.id)
        target_key = f"{target.id}_{interaction.guild.id}"
        if amount <= 0:
            await interaction.response.send_message("The amount must be greater than 0!")
            return
        if interaction.user.id == target.id:
            await interaction.response.send_message("You can't challenge yourself!")
            return
        if target.bot:
            await interaction.response.send_message("You can't challenge a bot!")
            return
        if target_key in self.pending_bets:
            await interaction.response.send_message("This person already has a pending challenge!")
            return
        if player_data['money'] < amount:
            await interaction.response.send_message("You don't have enough money to challenge this person!")
            return
        target_data = get_player_db(target.id, interaction.guild.id)
        if target_data['money'] < amount:
            await interaction.response.send_message("The person you want to challenge with doesn't have enough money!")
            return
        self.pending_bets[target_key] = {'challenger': person_key, 'amount': amount}
        await interaction.response.send_message(f"{target.mention} You've been challenged by {interaction.user.mention} for {amount} Money! Type /accept to take this bet or /decline to refuse.")

    # accept the challenge
    @app_commands.command(name='accept', description='accept the challenge')
    async def accept(self, interaction: discord.Interaction):
        person_key = get_person_key(interaction.user.id, interaction.guild.id)
        player_data = get_player_db(interaction.user.id, interaction.guild.id)
        if person_key not in self.pending_bets:
            await interaction.response.send_message("You don't have any pending challenge!")
            return
        challenger_key = self.pending_bets[person_key]['challenger']
        parts = challenger_key.split('_')
        challenger_id = int(parts[0])
        bet_amount = self.pending_bets[person_key]['amount']
        challenger_data = get_player_db(challenger_id, interaction.guild.id)
        if challenger_data['money'] < bet_amount:
            await interaction.response.send_message("The person who challenged you, doesn't have enough money to start the challenge!")
            del self.pending_bets[person_key]
            return
        if player_data['money'] < bet_amount:
            await interaction.response.send_message("You don't have enough money for this challenge!")
            del self.pending_bets[person_key]
            return
        del self.pending_bets[person_key]
        draw = random.choice([person_key, challenger_key])
        if draw == person_key:
            player_data['money'] += bet_amount
            challenger_data['money'] -= bet_amount
            await interaction.response.send_message(f"Congratulations {interaction.user.mention}, you won {bet_amount} Money! 💰")
        else:
            challenger_data['money'] += bet_amount
            player_data['money'] -= bet_amount
            await interaction.response.send_message(f"Congratulations <@{challenger_id}>, you won {bet_amount} Money! 💰")
        save_player(interaction.user.id, interaction.guild.id, player_data)
        save_player(challenger_id, interaction.guild.id, challenger_data)

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
    