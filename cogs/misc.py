from discord.ext import commands
import discord

class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='hello')
    async def hello(self, ctx):
        await ctx.send(f"Hello {ctx.author.display_name} 👋")

    # check the actual latency between discord and Bot
    @commands.command(name='ping')
    async def ping(self, ctx):
        await ctx.send(f"Latency is {round(self.bot.latency * 1000)} ms")

    # creating a form
    @commands.command(name='form', usage='Should we order pizza?')
    async def form(self, ctx, *, question: str):
        sent_form = await ctx.send("Form: " + question)
        await sent_form.add_reaction('👍')
        await sent_form.add_reaction('👎')

    # Command help - showing all existing commands
    @commands.command(name='help')
    async def help(self, ctx):
        embed = discord.Embed(title='List of commands', color=0x9B59B6)
        embed.add_field(name='PROFILE', value="**!profile** - show your level, XP and money\n**!top** - ranking of players\n**!stats** - list of statistics for this server\n**!achievements** - list of your unlocked achievements\n**!card** - work in progress", inline=False)
        embed.add_field(name='ECONOMY', value="**!daily** - you can claim 100 Money once per day\n**!give** - you can transfer money to the other person, for example: !give @Jason 100\n**!roulette** - you can play roulette (red, green, black), for example !roulette red 20\n**!steal** - you can steal money from another player, your chance is 50%, for example !steal @Jason\n**!challenge** - bet money against another player, for example: !challenge @Jason 100\n**!accept** - accept a pending challenge\n**!decline** - decline a pending challenge", inline=False)
        embed.add_field(name='GAMES', value="**!dice** - you can roll a random number 1-6 or you can pick different numbers, for example: !dice 100\n**!coinflip** - you can flip a coin\n**!rps** - a game for rock, scissors and paper, for example: !rps paper\n**!choose** - bot is choosing instead of you, he has options (yes/maybe/no)", inline=False)
        embed.add_field(name='AI', value="**!ai** - You type !ai and write your question, bot will answer you (basic model)\n**!aichannel** - the same as !ai but this time bot reads your channel history and comments on it, for example: !aichannel #games what games should we play? (basic model)\n**!aipro** - the same command as !ai but with pro model\n**!aireset** - reset AI memory with one command and start a fresh conversation", inline=False)
        embed.add_field(name='OTHER', value="**!hello** - bot will welcome you :D\n**!ping** - check the actual latency between bot and discord\n**!form** - type this command and write your question, bot will start the form\n**!help** - type this command to see what you're looking for (help menu)", inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Misc(bot))
