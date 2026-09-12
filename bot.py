import discord
from discord.ext import commands
import os
import copy
import logging
from dotenv import load_dotenv
from utils.data import players, DEFAULT_PROFILE, save_data, get_person_key

load_dotenv(dotenv_path='.env')
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

# unique key per user per server
    person_key = get_person_key(message.author.id, message.guild.id)

# create profile and fill in missing fields, then handle XP and level up
    if person_key not in players:
        players[person_key] = {}
    for key, value in DEFAULT_PROFILE.items():
        if key not in players[person_key]:
            players[person_key][key] = copy.deepcopy(value)
    players[person_key]['xp'] += 1
    if players[person_key]['xp'] >= players[person_key]['level'] * 100:
        players[person_key]['xp'] = 0
        players[person_key]['level'] += 1
        if players[person_key]['level'] == 5 and not players[person_key]['achievements']['level_5']:
            players[person_key]['achievements']['level_5'] = True
            await message.channel.send("Achievement unlocked! You reached level 5!")
            save_data(players)
        players[person_key]['money'] += 100
        await message.channel.send(f"{message.author.mention} Nice! You reached level {players[person_key]['level']}!")
    save_data(players)

# Achievement for reaching 500 money:
    if players[person_key]['money'] >= 500 and not players[person_key]['achievements']['500_money']:
        players[person_key]['achievements']['500_money'] = True
        await message.channel.send("Achievement unlocked! You have reached 500 money!")
        save_data(players)

# Giving money for messages
    players[person_key]['messages'] += 1
    players[person_key]['total_messages'] += 1
    if players[person_key]['messages'] == 100:
        players[person_key]['money'] += 100
        await message.channel.send("Congratulations, you got 100 money for 100 messages!")
        players[person_key]['messages'] = 0
        save_data(players)
    if players[person_key]['total_messages'] == 500 and not players[person_key]['achievements']['500_messages']:
        players[person_key]['achievements']['500_messages'] = True
        await message.channel.send("Achievement unlocked! You reached 500 messages!")
        save_data(players)

    await client.process_commands(message)

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Wrong command! To get help check the !help command")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"You forgot an argument for {ctx.command.name}, use: !{ctx.command.name} {ctx.command.usage}")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"Wrong argument for command {ctx.command.name}, use: !{ctx.command.name} {ctx.command.usage}")
    else:
        logger.error(error, exc_info=True)
        await ctx.send("Something went wrong!")

client.run(DISCORD_TOKEN, log_handler=None)
