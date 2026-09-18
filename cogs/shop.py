import time
import discord
from discord import app_commands, Interaction
from discord.ext import commands
from utils.data import get_person_key, players, save_data, SHOP_ITEMS

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
    @app_commands.choices(item=[
        app_commands.Choice(name='Pro title', value='title_pro'),
        app_commands.Choice(name='XP boost (1h)', value='xp_boost'),
        app_commands.Choice(name='Protection from steal (6h)', value='protection'),
        app_commands.Choice(name='Special role', value='role')
    ])
    async def buy(self, interaction: discord.Interaction, item: str):
        person_key = get_person_key(interaction.user.id, interaction.guild.id)
        player_data = players[person_key]
        item_type = SHOP_ITEMS[item]['type']
        if player_data['money'] < SHOP_ITEMS[item]['price']:
            await interaction.response.send_message(f"You don't have enough money for {SHOP_ITEMS[item]['name']}!")
            return
        if item in player_data['inventory']:
            await interaction.response.send_message(f"You already bought {SHOP_ITEMS[item]['name']}!")
            return
        if item_type == 'boost' and time.time() - player_data['boost_last_bought'] < SHOP_ITEMS[item]['cooldown']:
            await interaction.response.send_message("You can buy XP boost once per day!")
            return
        if item_type == 'protection' and time.time() - player_data['protection_last_bought'] < SHOP_ITEMS[item]['cooldown']:
            await interaction.response.send_message("You can buy protection once every 3 days!")
            return
        player_data['money'] -= SHOP_ITEMS[item]['price']
        if item_type == 'boost':
            player_data['boost_until'] = time.time() + SHOP_ITEMS[item]['value']
            player_data['boost_last_bought'] = time.time()
        elif item_type == 'protection':
            player_data['protected_until'] = time.time() + SHOP_ITEMS[item]['value']
            player_data['protection_last_bought'] = time.time()
        elif item_type == 'role':
            role = discord.utils.get(interaction.guild.roles, name=SHOP_ITEMS[item]['value'])
            if role is None:
                role = await interaction.guild.create_role(name=SHOP_ITEMS[item]['value'], color=discord.Color.gold())
            await interaction.user.add_roles(role)
            player_data['inventory'].append(item)
        else:
            player_data['inventory'].append(item)
        await interaction.response.send_message(f"Nice! You bought {SHOP_ITEMS[item]['name']}!")
        save_data(players)

    # Equip a title
    @app_commands.command(name='equip', description='Equip a title you own')
    @app_commands.choices(title=[
        app_commands.Choice(name='Pro title', value='title_pro')

    ])
    async def equip(self, interaction: discord.Interaction, title: str):
        person_key = get_person_key(interaction.user.id, interaction.guild.id)
        player_data = players[person_key]
        if title not in player_data['inventory']:
            await interaction.response.send_message("You don't own this")
            return
        player_data['active_title'] = SHOP_ITEMS[title]['value']
        save_data(players)
        await interaction.response.send_message(f"You equipped {SHOP_ITEMS[title]['name']}!")

async def setup(bot):
    await bot.add_cog(Shop(bot))
