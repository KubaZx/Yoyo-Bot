import discord
from discord import app_commands
from discord.ext import commands
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

async def setup(bot):
    await bot.add_cog(Shop(bot))
