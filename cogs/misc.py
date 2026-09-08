from discord.ext import commands

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

async def setup(bot):
    await bot.add_cog(Misc(bot))