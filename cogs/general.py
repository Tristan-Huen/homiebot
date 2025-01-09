import discord
import matplotlib.pyplot as plt
from discord.ext import commands

class General(commands.Cog):
    def __init__(self,bot) -> None:
        self.bot = bot

    # Ping Command.
    @commands.hybrid_command(
            description="Get bot latency",
            help="Returns bot latency in milliseconds."
    )
    async def ping(self, ctx:commands.Context)-> None:
        #Fixed by https://stackoverflow.com/questions/65263497/latency-in-a-cog-in-discord-py-isnt-recognized-as-a-valid-attribute
        await ctx.reply(f'Pong! {round(self.bot.latency * 1000)} ms')

async def setup(bot)-> None:
    await bot.add_cog(General(bot))
