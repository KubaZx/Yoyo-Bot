import json
import time
import discord
import logging
from discord.ext import commands
from utils.data import get_setting, clear_memory, get_memory, add_memory, get_player_db, get_achievements
from utils.ai_client import openai_client
from discord import app_commands

logger = logging.getLogger(__name__)
AI_CALL_LIMIT = 5
AI_RATE_WINDOW = 3600

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_my_stats",
            "description": "Returns the stats of the user who is asking: xp (it belongs to the current level, it's not total xp), xp_to_next_level, level, level_rule, money, last_daily, messages (count towards the next 100-message reward), total_messages, active_title, boost_until, protected_until, boost_last_bought, protection_last_bought, unlocked_achievements, all achievements with their requirements, and the current time. Use it only when the user asks about their own stats and progress.",
            "parameters": {"type": "object", "properties": {}}
        }
    }
]

def get_my_stats(user_id, guild_id):
    player_data = get_player_db(user_id, guild_id)
    player_data['unlocked_achievements'] = get_achievements(user_id, guild_id)
    player_data['achievement_requirements'] = {
        "500_messages": "Send 500 messages in total",
        "level_5": "Reach level 5",
        "500_money": "Have at least 500 money"
    }
    player_data['current_time'] = time.time()
    player_data['xp_to_next_level'] = player_data['level'] * 100 - player_data['xp']
    player_data['level_rule'] = "To reach the next level: your current level * 100, xp = 0 after reaching the next level"
    return player_data

class AI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ai_usage = {}

    #Check if user is limited
    def is_rate_limited(self, user_id):
        now = time.time()
        timestamps = self.ai_usage.get(user_id, [])
        timestamps = [t for t in timestamps if now - t < AI_RATE_WINDOW]
        self.ai_usage[user_id] = timestamps
        return len(timestamps) >= AI_CALL_LIMIT

    #Record a successful AI call for the rate limit
    def record_ai_usage(self, user_id):
        now = time.time()
        timestamps = self.ai_usage.get(user_id, [])
        timestamps.append(now)
        self.ai_usage[user_id] = timestamps

    #The same logic to run both ai/aipro commands
    async def run_ai(self, interaction: discord.Interaction, question, model, max_tokens, use_tools=False):
        if get_setting(interaction.guild.id, 'ai_rate_limit') and self.is_rate_limited(interaction.user.id):
            await interaction.response.send_message(f"You've run out of {AI_CALL_LIMIT} AI messages! Try again in {AI_RATE_WINDOW // 60} minutes!")
            return
        await interaction.response.defer()
        if not question:
            await interaction.followup.send("Write your question!")
            return
        messages_to_send = get_memory(interaction.user.id, interaction.guild.id, 4)
        messages_to_send.insert(0, {"role": "system", "content": "Answer concisely and stay on topic. Discord has a 2000 character limit, so don't write more than that. You can be casual and use light humor to keep the conversation fun. Discord doesn't support markdown tables, use bullet lists instead."})
        messages_to_send.append({"role": "user", "content": question})
        extra_body = None
        should_stream = True
        collected_text = ""
        if use_tools:
            extra_body = {"thinking": {"type": "disabled"}}
        try:
            if use_tools:
                first_response = await openai_client.chat.completions.create(
                    model=model,
                    messages=messages_to_send,
                    max_tokens=max_tokens,
                    tools=TOOLS,
                    extra_body=extra_body
                )
                message = first_response.choices[0].message
                if message.tool_calls:
                    messages_to_send.append(message)
                    for tool_call in message.tool_calls:
                        if tool_call.function.name == "get_my_stats":
                            result = get_my_stats(interaction.user.id, interaction.guild.id)
                            messages_to_send.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": json.dumps(result)
                            })
                else:
                    collected_text = message.content
                    should_stream = False
            if should_stream:
                last_edit = time.time()
                response = await openai_client.chat.completions.create(
                    model=model,
                    messages=messages_to_send,
                    max_tokens=max_tokens,
                    stream=True,
                    extra_body=extra_body
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

            add_memory(interaction.user.id, interaction.guild.id, "user", question)
            add_memory(interaction.user.id, interaction.guild.id, "assistant", collected_text)
            self.record_ai_usage(interaction.user.id)
        except Exception as e:
            logger.error(e, exc_info=True)
            await interaction.edit_original_response(content="Something went wrong with AI, try again in a moment 🥴"[:2000])


    # Clear AI conversation memory
    @app_commands.command(name='aireset', description='reset your AI memory')
    async def aireset(self, interaction: discord.Interaction):
        clear_memory(interaction.user.id, interaction.guild.id)
        await interaction.response.send_message("Your AI memory has been cleared!")

    # AI using the basic model
    @app_commands.command(name='ai', description='chat with the basic AI model')
    async def ai(self, interaction: discord.Interaction, question: str):
        await self.run_ai(interaction, question, "deepseek-flash", 2000, use_tools=True)

    # AI using the pro model
    @app_commands.command(name='aipro', description='chat with the pro AI model')
    async def aipro(self, interaction: discord.Interaction, question: str):
        await self.run_ai(interaction, question, "deepseek-v4-pro", 3000)

    # AI with channel context - read 50 messages from the given channel
    @app_commands.command(name='aichannel', description='Chat with the basic AI model about messages on server channel')
    async def aichannel(self, interaction: discord.Interaction, channel: discord.TextChannel, question: str):
        if get_setting(interaction.guild.id, 'ai_rate_limit') and self.is_rate_limited(interaction.user.id):
            await interaction.response.send_message(f"You've run out of {AI_CALL_LIMIT} AI messages! Try again in {AI_RATE_WINDOW // 60} minutes!")
            return
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
                model="deepseek-flash",
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
            self.record_ai_usage(interaction.user.id)

        except Exception as e:
            logger.error(e, exc_info=True)
            await interaction.edit_original_response(content="Something went wrong with AI, try again in a moment 🥴"[:2000])

async def setup(bot):
    await bot.add_cog(AI(bot))
