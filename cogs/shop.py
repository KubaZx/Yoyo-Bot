import time
import discord
from discord import app_commands
from discord.ext import commands
from utils.data import get_person_key, players, save_data, SHOP_ITEMS
from typing import Literal

from utils.data import SHOP_ITEMS

class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # shop
    @app_commands.command(name='shop', description='Browse items you can buy')
    async def shop(self, interaction: discord.Interaction):
        embed = discord.Embed(title='Shop', color=0x9B59B6)
        for item_id, item in SHOP_ITEMS.items():
            embed.add_field(name=f"{item['name']} - {item['price']} money", value=item['description'], inline=False)
        await interaction.response.send_message(embed=embed)

    # buy items from shop
    @app_commands.command(name='buy', description='Buy items from the shop')
    async def buy(self, interaction: discord.Interaction, item: Literal['title_pro', 'xp_boost', 'protection', 'role']):
        person_key = get_person_key(interaction.user.id, interaction.guild.id)
        player_data = players[person_key]
        if player_data['money'] < SHOP_ITEMS[item]['price']:
            await interaction.response.send_message(f"You have no money for {SHOP_ITEMS[item]['name']}!")
            return
        if item in player_data['inventory']:
            await interaction.response.send_message("You already bought it!")
            return
        player_data['money'] -= SHOP_ITEMS[item]['price']
        item_type = SHOP_ITEMS[item]['type']
        if item_type == 'boost':
            player_data['boost_until'] = time.time() + SHOP_ITEMS[item]['value']
        elif item_type == 'protection':
            player_data['protected_until'] = time.time() + SHOP_ITEMS[item]['value']
        else:
            player_data['inventory'].append(item)
        await interaction.response.send_message(f"Nice! You bought {SHOP_ITEMS[item]['name']}")
        save_data(players)


async def setup(bot):
    await bot.add_cog(Shop(bot))
