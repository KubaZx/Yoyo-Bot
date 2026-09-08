import time
import discord
from discord.ext import commands
from utils.data import players, save_data
from utils.ai_client import openai_client


class AI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Clear AI conversation memory
    @commands.command(name='aireset')
    async def aireset(self, ctx):
        person_key = f"{ctx.author.id}_{ctx.guild.id}"
        ai_memory = players[person_key]['ai_memory']
        ai_memory.clear()
        save_data(players)
        await ctx.send("Your AI memory has been cleared!")

    # AI using the basic model
    @commands.command(name='ai')
    async def ai(self, ctx, *, question: str):
        person_key = f"{ctx.author.id}_{ctx.guild.id}"
        if not question:
            await ctx.send("Write your question!")
            return
        ai_memory = players[person_key]['ai_memory']
        messages_to_send = ai_memory[-4:]
        messages_to_send.insert(0, {"role": "system", "content": "Answer concisely and stay on topic. Discord has a 2000 character limit, so don't write more than that. You can be casual and use light humor to keep the conversation fun."})
        messages_to_send.append({"role": "user", "content": question})
        temp_message = await ctx.reply("Thinking...")
        try:
            async with ctx.typing():
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
                    await ctx.send(piece)
                    rest = rest[2000:]

            ai_memory.append({"role": "user", "content": question})
            ai_memory.append({"role": "assistant", "content": collected_text})
            save_data(players)
        except Exception as e:
            print(e)
            await temp_message.edit(content="Something went wrong with AI, try again in a moment 🥴"[:2000])

    # AI using the pro model
    @commands.command(name='aipro')
    async def aipro(self, ctx, *, question: str):
        person_key = f"{ctx.author.id}_{ctx.guild.id}"
        if not question:
            await ctx.send("Write your question!")
            return
        ai_memory = players[person_key]['ai_memory']
        messages_to_send = ai_memory[-4:]
        messages_to_send.insert(0, {"role": "system", "content": "Answer concisely and stay on topic. Discord has a 2000 character limit, so don't write more than that. You can be casual and use light humor to keep the conversation fun."})
        messages_to_send.append({"role": "user", "content": question})
        temp_message = await ctx.reply("Thinking...")
        try:
            async with ctx.typing():
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
                    await ctx.send(piece)
                    rest = rest[2000:]

            ai_memory.append({"role": "user", "content": question})
            ai_memory.append({"role": "assistant", "content": collected_text})
            save_data(players)
        except Exception as e:
            print(e)
            await temp_message.edit(content="Something went wrong with AI, try again in a moment 🥴"[:2000])

    # AI with channel context - read 50 messages from the given channel
    @commands.command(name='aichannel', usage='#games what games should we play?')
    async def aichannel(self, ctx, channel: discord.TextChannel, *, question: str):
        temp_message = await ctx.reply("Reading history and thinking...")
        try:
            async with ctx.typing():
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
                    await ctx.send(piece)
                    rest = rest[2000:]
        except Exception as e:
            print(e)
            await temp_message.edit(content="Something went wrong with AI, try again in a moment 🥴"[:2000])

async def setup(bot):
    await bot.add_cog(AI(bot))
