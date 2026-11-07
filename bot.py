import time
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from utils.data import get_player_db, get_achievements, unlock_achievement, save_player
from discord import app_commands
from pathlib import Path

BASE_DIR = Path(__file__).parent
load_dotenv(dotenv_path=BASE_DIR / '.env')
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)-8s] %(name)s: %(message)s')
intents = discord.Intents.default()
intents.message_content = True

client = commands.Bot(command_prefix='!', intents=intents, help_command=None)

@client.event
async def on_ready():
    await client.load_extension('cogs.games')
    await client.load_extension('cogs.profile')
    await client.load_extension('cogs.economy')
    await client.load_extension('cogs.misc')
    await client.load_extension('cogs.ai')
    await client.load_extension('cogs.shop')
    await client.load_extension('cogs.settings')
    synced = await client.tree.sync()
    logger.info(f'Synced {len(synced)} slash commands')
    logger.info(f'Bot is running as {client.user}')

@client.event
async def on_message(message):

# guard for messages from bots
    if message.author.bot:
        return

# guard for DMs
    if message.guild is None:
        await message.channel.send("Hey, I only work on servers 😁")
        return

# create the player from the database (creates a new one if needed)
    player_data = get_player_db(message.author.id, message.guild.id)

# unlocked achievements of player
    unlocked = get_achievements(message.author.id, message.guild.id)

# handle XP and level up
    xp_gain = 1
    if time.time() < player_data['boost_until']:
        xp_gain = 2
    player_data['xp'] += xp_gain
    if player_data['xp'] >= player_data['level'] * 100:
        player_data['xp'] = 0
        player_data['level'] += 1
        if player_data['level'] == 5 and 'level_5' not in unlocked:
            unlock_achievement(message.author.id, message.guild.id, 'level_5')
            await message.channel.send("Achievement unlocked! You reached level 5!")
        player_data['money'] += 100
        await message.channel.send(f"{message.author.mention} Nice! You reached level {player_data['level']}!")

# Achievement for reaching 500 money:
    if player_data['money'] >= 500 and '500_money' not in unlocked:
        unlock_achievement(message.author.id, message.guild.id, '500_money')
        await message.channel.send("Achievement unlocked! You have reached 500 money!")

# Giving money for messages
    player_data['messages'] += 1
    player_data['total_messages'] += 1
    if player_data['messages'] == 100:
        player_data['money'] += 100
        await message.channel.send("Congratulations, you got 100 money for 100 messages!")
        player_data['messages'] = 0
    if player_data['total_messages'] == 500 and '500_messages' not in unlocked:
        unlock_achievement(message.author.id, message.guild.id, '500_messages')
        await message.channel.send("Achievement unlocked! You reached 500 messages!")
    save_player(message.author.id, message.guild.id, player_data)


@client.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    logger.error(error, exc_info=True)
    if interaction.response.is_done():
        await interaction.followup.send("Something went wrong!")
    else:
        await interaction.response.send_message("Something went wrong!")


client.run(DISCORD_TOKEN, log_handler=None)
