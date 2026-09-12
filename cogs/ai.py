import time
import discord
import logging
from discord.ext import commands
from utils.data import players, save_data, get_person_key
from utils.ai_client import openai_client
from discord import app_commands

logger = logging.getLogger(__name__)

class AI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def run_ai(self, interaction: discord.Interaction, question, model, max_tokens):
        person_key = get_person_key(interaction.user.id, interaction.guild.id)
        await interaction.response.defer()
        if not question:
            await interaction.followup.send("Write your question!")
            return
        ai_memory = players[person_key]['ai_memory']
        messages_to_send = ai_memory[-4:]
        messages_to_send.insert(0, {"role": "system", "content": "Answer concisely and stay on topic. Discord has a 2000 character limit, so don't write more than that. You can be casual and use light humor to keep the conversation fun."})
        messages_to_send.append({"role": "user", "content": question})
        try:
            collected_text = ""
            last_edit = time.time()
            response = await openai_client.chat.completions.create(
                model=model,
                messages=messages_to_send,
                max_tokens=max_tokens,
                stream=True
            )
            async for chunk in response:
                chunk_text = chunk.choices[0].delta.content
                if chunk_text is not None:
                    collected_text += chunk_text
                if collected_text and time.time() - last_edit >= 1:
                    await interaction.edit_original_response(content=collected_text[:2000])
                    last_edit = time.time()
            if not collected_text:
                await interaction.edit_original_response(content="AI returned an empty response, try again")
                return
            first_chunk = collected_text[:2000]
            rest = collected_text[2000:]
            await interaction.edit_original_response(content=first_chunk)

            while len(rest) > 0:
                piece = rest[:2000]
                await interaction.followup.send(piece)
                rest = rest[2000:]

            ai_memory.append({"role": "user", "content": question})
            ai_memory.append({"role": "assistant", "content": collected_text})
            save_data(players)
        except Exception as e:
            logger.error(e, exc_info=True)
            await interaction.edit_original_response(content="Something went wrong with AI, try again in a moment 🥴"[:2000])


    # Clear AI conversation memory
    @app_commands.command(name='aireset', description='reset your AI memory')
    async def aireset(self, interaction: discord.Interaction):
        person_key = get_person_key(interaction.user.id, interaction.guild.id)
        ai_memory = players[person_key]['ai_memory']
        ai_memory.clear()
        save_data(players)
        await interaction.response.send_message("Your AI memory has been cleared!")

    # AI using the basic model
    @app_commands.command(name='ai', description='chat with the basic AI model')
    async def ai(self, interaction: discord.Interaction, question: str):
        await self.run_ai(interaction, question, "deepseek-v4-flash", 2000)

    # AI using the pro model
    @app_commands.command(name='aipro', description='chat with the pro AI model')
    async def aipro(self, interaction: discord.Interaction, question: str):
        await self.run_ai(interaction, question, "deepseek-v4-pro", 3000)

    # AI with channel context - read 50 messages from the given channel
    @app_commands.command(name='aichannel', description='Chat with the basic AI model about messages on server channel')
    async def aichannel(self, interaction: discord.Interaction, channel: discord.TextChannel, question: str):
        await interaction.response.defer()
        try:
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
                    await interaction.edit_original_response(content=collected_text[:2000])
                    last_edit = time.time()
            if not collected_text:
                await interaction.edit_original_response(content="AI returned an empty response, try again")
                return
            first_chunk = collected_text[:2000]
            rest = collected_text[2000:]
            await interaction.edit_original_response(content=first_chunk)

            while len(rest) > 0:
                piece = rest[:2000]
                await interaction.followup.send(piece)
                rest = rest[2000:]
        except Exception as e:
            logger.error(e, exc_info=True)
            await interaction.edit_original_response(content="Something went wrong with AI, try again in a moment 🥴"[:2000])

async def setup(bot):
    await bot.add_cog(AI(bot))
