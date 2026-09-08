import discord
from discord.ext import commands
import random
import os
import time
from dotenv import load_dotenv
import openai
import copy
from utils.data import players, DEFAULT_PROFILE, save_data

load_dotenv(dotenv_path='.env')
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
openai_client = openai.AsyncOpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

pending_bets = {}

intents = discord.Intents.default()
intents.message_content = True

client = commands.Bot(command_prefix='!', intents=intents)

@client.event
async def on_ready():
    await client.load_extension('cogs.games')
    await client.load_extension('cogs.profile')
    await client.load_extension('cogs.economy')
    await client.load_extension('cogs.misc')
    print(f'Bot is running as {client.user}')

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
    person_key = f"{message.author.id}_{message.guild.id}"

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

# AI with channel context - read 50 messages from the given channel
    elif message.content.lower().startswith('!ai <#'):
        parts = message.content.lower().split()
        question = ' '.join(parts[2:]).strip()
        if not question:
            await message.channel.send("Write your question!")
            return
        channel_text = parts[1].replace('<#', '').replace('>', "")
        if not channel_text.isdigit():
            await message.channel.send("Give me a valid channel!")
            return
        channel_id = int(channel_text)
        channel = message.guild.get_channel(channel_id)
        if channel is None:
            await message.channel.send("Channel not found!")
            return
        temp_message = await message.reply("Reading history and thinking...")

        try:
            async with message.channel.typing():
                history = []
                async for msg in channel.history(limit=50):
                    history.append(f"{msg.author.name}: {msg.content}")
                context = '\n'.join(history)
                context += "\n\nAnswer concisely and stay on topic. Discord has a 2000 character limit, so don't write more than that. You can be casual and use light humor to keep the conversation fun."

                collected_text = ""
                last_edit = time.time()

                response = await openai_client.chat.completions.create(
                    model="deepseek-v4-flash",
                    messages=[
                        {"role": "system", "content": context},
                        {"role": "user", "content": question}
                    ],
                    max_tokens=2500,
                    stream=True
                )
                async for chunk in response:
                    chunk_text = chunk.choices[0].delta.content
                    if chunk_text is not None:
                        collected_text += chunk_text
                    if collected_text and time.time() - last_edit >= 1:
                        await temp_message.edit(content=collected_text[:2000])
                        last_edit = time.time()
                first_chunk = collected_text[:2000]
                rest = collected_text[2000:]
                await temp_message.edit(content=first_chunk)

                while len(rest) > 0:
                    piece = rest[:2000]
                    await message.channel.send(piece)
                    rest = rest[2000:]
        except Exception as e:
            print(e)
            await temp_message.edit(content="Something went wrong with AI, try again in a moment 😒"[:2000])

# AI command using the pro model:
    elif message.content.lower().startswith('!aipro'):
        question = (message.content[6:].strip())
        if not question:
            await message.channel.send("Write your question!")
            return
        ai_memory = players[person_key]['ai_memory']
        messages_to_send = ai_memory[-4:]
        messages_to_send.insert(0, {"role": "system", "content": "Answer concisely and stay on topic. Discord has a 2000 character limit, so don't write more than that. You can be casual and use light humor to keep the conversation fun."})
        messages_to_send.append({"role": "user", "content": question})
        temp_message = await message.reply("Thinking...")
        try:
            async with message.channel.typing():
                collected_text = ""
                last_edit = time.time()
                response = await openai_client.chat.completions.create(
                    model="deepseek-v4-pro",
                    messages=messages_to_send,
                    max_tokens=3000,
                    stream=True
                )
                async for chunk in response:
                    chunk_text = chunk.choices[0].delta.content
                    if chunk_text is not None:
                        collected_text += chunk_text
                    if collected_text and time.time() - last_edit >= 1:
                        await temp_message.edit(content=collected_text[:2000])
                        last_edit = time.time()
                first_chunk = collected_text[:2000]
                rest = collected_text[2000:]
                await temp_message.edit(content=first_chunk)

                while len(rest) > 0:
                    piece = rest[:2000]
                    await message.channel.send(piece)
                    rest = rest[2000:]

            ai_memory.append({"role": "user", "content": question})
            ai_memory.append({"role": "assistant", "content": collected_text})
            save_data(players)
        except Exception as e:
            print(e)
            await temp_message.edit(content="Something went wrong with AI, try again in a moment 🥴"[:2000])

# Clear AI conversation memory
    elif message.content.lower() == '!aireset':
        ai_memory = players[person_key]['ai_memory']
        ai_memory.clear()
        save_data(players)
        await message.channel.send("Your AI memory has been cleared!")

# AI using the basic model:
    elif message.content.lower().startswith('!ai'):
        question = (message.content[3:].strip())
        if not question:
            await message.channel.send("Write your question!")
            return
        ai_memory = players[person_key]['ai_memory']
        messages_to_send = ai_memory[-4:]
        messages_to_send.insert(0, {"role": "system", "content": "Answer concisely and stay on topic. Discord has a 2000 character limit, so don't write more than that. You can be casual and use light humor to keep the conversation fun."})
        messages_to_send.append({"role": "user", "content": question})
        temp_message = await message.reply("Thinking...")
        try:
            async with message.channel.typing():
                collected_text = ""
                last_edit = time.time()
                response = await openai_client.chat.completions.create(
                    model="deepseek-v4-flash",
                    messages=messages_to_send,
                    max_tokens=2000,
                    stream=True
                )
                async for chunk in response:
                    chunk_text = chunk.choices[0].delta.content
                    if chunk_text is not None:
                        collected_text += chunk_text
                    if collected_text and time.time() - last_edit >= 1:
                        await temp_message.edit(content=collected_text[:2000])
                        last_edit = time.time()
                first_chunk = collected_text[:2000]
                rest = collected_text[2000:]
                await temp_message.edit(content=first_chunk)

                while len(rest) > 0:
                    piece = rest[:2000]
                    await message.channel.send(piece)
                    rest = rest[2000:]

            ai_memory.append({"role": "user", "content": question})
            ai_memory.append({"role": "assistant", "content": collected_text})
            save_data(players)
        except Exception as e:
            print(e)
            await temp_message.edit(content="Something went wrong with AI, try again in a moment 🥴"[:2000])

# Creating a form
    elif message.content.lower().startswith('!form'):
        sent_form = await message.channel.send('Form: ' + message.content[5:])
        await sent_form.add_reaction('👍')
        await sent_form.add_reaction('👎')

# Command help - showing all existing commands
    elif message.content.lower() == '!help':
        embed = discord.Embed(title='List of commands', color=0x9B59B6)
        embed.add_field(name='PROFILE', value="**!profile** - show your level, XP and money\n**!top** - ranking of players\n**!stats** - list of statistics for this server\n**!achievements** - list of your unlocked achievements\n**!card** - work in progress", inline=False)
        embed.add_field(name='ECONOMY', value="**!daily** - you can claim 100 Money once per day\n**!give** - you can transfer money to the other person, for example: !give @Jason 100\n**!roulette** - you can play roulette (red, green, black), for example !roulette red 20\n**!steal** - you can steal money from another player, your chance is 50%, for example !steal @Jason\n**!challenge** - bet money against another player, for example: !challenge @Jason 100\n**!accept** - accept a pending challenge", inline=False)
        embed.add_field(name='GAMES', value="**!dice** - you can roll a random number 1-6 or you can pick different numbers, for example: !dice 100\n**!coinflip** - you can flip a coin\n**!rps** - a game for rock, scissors and paper, for example: !rps paper\n**!choose** - bot is choosing instead of you, he has options (yes/maybe/no)", inline=False)
        embed.add_field(name='AI', value="**!ai** - You type !ai and write your question, bot will answer you (basic model)\n**!ai <#channel>** - the same as !ai but this time bot reads your channel history and comments on it, for example: !ai #games what games should we play? (basic model)\n**!aipro** - the same command as !ai but with pro model\n**!aireset** - reset AI memory with one command and start a fresh conversation", inline=False)
        embed.add_field(name='OTHER', value="**!hello** - bot will welcome you :D\n**!ping** - check the actual latency between bot and discord\n**!form** - type this command and write your question, bot will start the form\n**!help** - type this command to see what you're looking for (help menu)", inline=False)
        await message.channel.send(embed=embed)
    await client.process_commands(message)

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"Wrong argument for command {ctx.command.name}, use: !{ctx.command.name} {ctx.command.usage}")
    else:
        print(error)
        await ctx.send("Something went wrong!")

client.run(DISCORD_TOKEN)