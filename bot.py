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

# Profile of achievements
    elif message.content.lower() == '!achievements':
        achievements_data = players[person_key]
        embed = discord.Embed(title='Achievements', color=0x079DFA)
        if achievements_data['achievements']['500_messages']:
            embed.add_field(name='500 messages', value='✅', inline=False)
        else:
            embed.add_field(name='500 messages', value='❌', inline=False)
        if achievements_data['achievements']['level_5']:
            embed.add_field(name='level 5', value='✅', inline=False)
        else:
            embed.add_field(name='level 5', value='❌', inline=False)
        if achievements_data['achievements']['500_money']:
            embed.add_field(name='500 money', value='✅', inline=False)
        else:
            embed.add_field(name='500 money', value='❌', inline=False)
        await message.channel.send(embed=embed)

# List of top players from server
    elif message.content.lower() == '!top':
        server_players = {k: v for k, v in players.items() if k.endswith("_" + str(message.guild.id))}
        ranking = sorted(server_players.items(), key=lambda x: (x[1]['level'], x[1]['xp'], x[1]['money']), reverse=True)
        embed = discord.Embed(title='Top players 🏆', color=0xE0D90D)
        for i, (player_id, data) in enumerate(ranking[:10]):
            embed.add_field(
                name=f'{i + 1}. place',
                value=f'<@{player_id.split("_")[0]}> | Level {data["level"]} | XP: {data["xp"]}/{data["level"] * 100} | Money {data["money"]}',
                inline=False
            )
        await message.channel.send(embed=embed)

# daily money, once per day
    elif message.content.lower() == '!daily':
        player_data = players[person_key]
        if time.time() - player_data['last_daily'] >= 86400:
            players[person_key]['money'] += 100
            players[person_key]['last_daily'] = time.time()
            await message.channel.send(f"{message.author.mention} You claimed 100 Money! 💸")
            save_data(players)
        else:
            await message.channel.send('You already claimed your daily bonus today!')

# Simple chat commands
    elif message.content.lower() == '!hello':
        await message.channel.send('Hello 👋')
# Check the actual latency between discord and Bot
    elif message.content.lower() == '!ping':
        await message.channel.send(f"Latency is {round(client.latency * 1000)} ms")

# transfer money to another player
    elif message.content.lower().startswith('!give'):
        parts = message.content.lower().split()
        if len(parts) < 3:
            await message.channel.send("You typed the wrong command! For example, !give @Jason 100")
            return
        if not parts[2].isdigit():
            await message.channel.send("Give me a number of money that you want to give the person! For example, !give @Jason 100")
            return
        amount = int(parts[2])
        if amount <= 0:
            await message.channel.send("The amount must be greater than 0!")
            return
        target_id = parts[1].replace("<@", "").replace(">", "")
        if str(message.author.id) == target_id:
            await message.channel.send("You can't give money to yourself!")
            return
        target_key = f"{target_id}_{message.guild.id}"
        if target_key not in players:
            await message.channel.send("This person is not in the database!")
            return
        if players[person_key]['money'] < amount:
            await message.channel.send("You don't have enough money!")
            return
        players[person_key]['money'] -= amount
        players[target_key]['money'] += amount
        save_data(players)
        await message.channel.send(f"Nice! You have transferred {amount} money to <@{target_id}>")

# Check the statistics for the actual server
    elif message.content.lower() == '!stats':
        server_players = {k: v for k, v in players.items() if k.endswith("_" + str(message.guild.id))}
        if not server_players:
            await message.channel.send("No players on this server yet!")
            return
        player_count = len(server_players)
        total_money = sum(profile['money'] for profile in server_players.values())
        total_messages = sum(profile['total_messages'] for profile in server_players.values())
        richest_person = max(server_players.items(), key=lambda x: x[1]['money'])
        embed = discord.Embed(title='Server Stats 📈', color=0x9B59B6)
        embed.add_field(name='Number of players 👤', value=player_count, inline=False)
        embed.add_field(name='Amount of Money 💸', value=total_money, inline=False)
        embed.add_field(name='The Richest Person 👤💸', value=f"<@{richest_person[0].split('_')[0]}> has {richest_person[1]['money']}", inline=False)
        embed.add_field(name='Number of messages 📨', value=total_messages, inline=False)
        await message.channel.send(embed=embed)

# Challenge another person for coinflip
    elif message.content.lower().startswith('!challenge'):
        parts = message.content.lower().split()
        if len(parts) < 3:
            await message.channel.send("You typed the wrong command! For example, !challenge @Jason 100")
            return
        if not parts[2].isdigit():
            await message.channel.send("You didn't give me an amount! For example, !challenge @Jason 100")
            return
        amount = int(parts[2])
        if amount <= 0:
            await message.channel.send("The amount must be greater than 0!")
            return
        target_id = parts[1].replace("<@", "").replace(">", "")
        target_key = f"{target_id}_{message.guild.id}"
        if str(message.author.id) == target_id:
            await message.channel.send("You can't challenge yourself!")
            return
        if target_key not in players:
            await message.channel.send("This person is not in the database!")
            return
        if target_key in pending_bets:
            await message.channel.send("This person already has a pending challenge!")
            return
        if players[person_key]['money'] < amount:
            await message.channel.send("You don't have enough money to challenge this person")
            return
        if players[target_key]['money'] < amount:
            await message.channel.send("The person you want to challenge with doesn't have enough money!")
            return
        pending_bets[target_key] = {'challenger': person_key, 'amount': amount}
        await message.channel.send(f"<@{target_id}> you've been challenged by {message.author.mention} for {amount} Money! Type !accept to take this bet")

# Accept the challenge
    elif message.content.lower() == '!accept':
        if person_key not in pending_bets:
            await message.channel.send("You don't have any pending challenge")
            return
        challenger_key = pending_bets[person_key]['challenger']
        bet_amount = pending_bets[person_key]['amount']
        if players[challenger_key]['money'] < bet_amount:
            await message.channel.send("The person who challenged you doesn't have enough money to start the challenge")
            del pending_bets[person_key]
            return
        if players[person_key]['money'] < bet_amount:
            await message.channel.send("You don't have enough money for this challenge")
            del pending_bets[person_key]
            return
        del pending_bets[person_key]
        draw = random.choice([person_key, challenger_key])
        if draw == person_key:
            players[person_key]['money'] += bet_amount
            players[challenger_key]['money'] -= bet_amount
            await message.channel.send(f"Congratulations <@{person_key.split('_')[0]}>, you won {bet_amount} Money!")
        else:
            players[challenger_key]['money'] += bet_amount
            players[person_key]['money'] -= bet_amount
            await message.channel.send(f"Congratulations <@{challenger_key.split('_')[0]}>, you won {bet_amount} Money!")
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

# Roulette system
    elif message.content.lower().startswith('!roulette'):
        parts = message.content.lower().split()
        if len(parts) < 3:
            await message.channel.send("Wrong format! For example: !roulette red 20")
            return
        color = parts[1]
        amount = parts[2]
        try:
            if int(amount) <= 0:
                await message.channel.send("The amount must be greater than 0!")
                return
            if color not in ['red', 'black', 'green']:
                await message.channel.send("Wrong color! Choose: red, black or green")
                return
            if players[person_key]['money'] >= int(amount):
                result = random.choices(['red', 'black', 'green'], weights=[47.5, 47.5, 5])[0]
                if result == color:
                    players[person_key]['money'] += int(amount) * 2
                    await message.channel.send(f"{message.author.mention} The color is {result}. You won! 💰")
                    save_data(players)
                else:
                    await message.channel.send(f"The color is {result}. Not this time 😥")
                    players[person_key]['money'] -= int(amount)
                    save_data(players)
            else:
                await message.channel.send("You don't have enough money!")
        except ValueError:
            await message.channel.send("The amount must be a number! For example: !roulette red 20")

# steal money from another player - 50% chance
    elif message.content.lower().startswith("!steal"):
        parts = message.content.lower().split()
        if len(parts) < 2:
            await message.channel.send("Wrong format! For example: !steal @Jason")
            return
        target_id = parts[1].replace("<@", "").replace(">", "")
        target_key = f"{target_id}_{message.guild.id}"
        if str(message.author.id) == target_id:
            await message.channel.send("You can't steal from yourself!")
            return
        if target_key in players:
            if players[person_key]['money'] > 0 and players[target_key]['money'] > 0:
                stolen_money = random.randint(1, players[target_key]['money'])
                if random.randint(1, 2) == 1:
                    players[person_key]['money'] += stolen_money
                    players[target_key]['money'] -= stolen_money
                    await message.channel.send(f"You stole {stolen_money} Money! 😈")
                    save_data(players)
                else:
                    lost = min(players[person_key]['money'], stolen_money)
                    players[person_key]['money'] -= lost
                    await message.channel.send(f"Not this time, you lost {lost} money 😪")
                    save_data(players)
            else:
                await message.channel.send("You or the other person doesn't have enough money!")
        else:
            await message.channel.send("This person is not in the database!")

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
        await ctx.send("Give me a number, for example !dice 10")
    else:
        print(error)
        await ctx.send("Something went wrong!")

client.run(DISCORD_TOKEN)