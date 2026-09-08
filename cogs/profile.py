import discord
from discord.ext import commands
from utils.data import players

class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # TODO: Showing player card with pillow:
    @commands.command(name='card')
    async def card(self, ctx):
        await ctx.send("Work in progress 🫡")

    #Player profile, showing level; xp ; money
    @commands.command(name='profile')
    async def profile(self, ctx):
        person_key = f"{ctx.author.id}_{ctx.guild.id}"
        player_data = players[person_key]
        embed = discord.Embed(title='Player Profile', color=0x00ff00)
        embed.add_field(name='Level', value=player_data['level'], inline=True)
        embed.add_field(name='XP', value=f"{player_data['xp']}/{player_data['level'] * 100}", inline=True)
        embed.add_field(name='Money', value=player_data['money'], inline=True)
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    #Profile of achievements
    @commands.command(name='achievements')
    async def achievements(self, ctx):
        person_key = f"{ctx.author.id}_{ctx.guild.id}"
        achievements_data = players[person_key]
        embed = discord.Embed(title='Achievements', color=0x079DFA)
        if achievements_data['achievements']['500_messages']:
            embed.add_field(name='500 messages', value='✅', inline=False)
        else:
            embed.add_field(name='500 messages', value='❌', inline=False)
        if achievements_data['achievements']['level_5']:
            embed.add_field(name='Level 5', value='✅', inline=False)
        else:
            embed.add_field(name='Level 5', value='❌', inline=False)
        if achievements_data['achievements']['500_money']:
            embed.add_field(name='500 money', value='✅', inline=False)
        else:
            embed.add_field(name='500 money', value='❌', inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Profile(bot))
