import discord
import asyncio
import os
import logging
from discord.ext import commands
from discord import ui
from dotenv import load_dotenv 

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
activity = discord.Game(name="$help")
bot = commands.Bot(command_prefix = '$', activity=activity, intents = intents)
discord.utils.setup_logging()

@bot.event
async def on_ready() -> None:
    print('We have logged in as {0.user}'.format(bot))

#Command to sync slash commands
@bot.command(hidden=True)
@commands.is_owner()
async def sync(ctx: commands.Context) -> None:
    synced = await ctx.bot.tree.sync()

    await ctx.send(f"Synced {len(synced)} commands")


#Loads a cog.
@bot.command(hidden=True)
@commands.is_owner()
async def load(ctx:commands.Context, extension) -> None:
    try:
        await bot.load_extension(f"cogs.{extension}")
    except commands.ExtensionAlreadyLoaded:
        await ctx.reply(f"{extension} cog is already loaded")
    except commands.ExtensionNotFound:
        await ctx.reply(f"{extension} cog not found")
    else:
        await ctx.reply(f"{extension} cog is loaded")
        
#Unloads a cog.
@bot.command(hidden=True)
@commands.is_owner()
async def unload(ctx:commands.Context, extension) -> None:
    try:
        await bot.unload_extension(f"cogs.{extension}")
    except commands.ExtensionNotLoaded:
        await ctx.reply(f"{extension} cog is already unloaded or not found")
    else:
        await ctx.reply(f"{extension} cog is unloaded")

#Reloads a cog.
@bot.command(hidden=True)
@commands.is_owner()
async def reload(ctx:commands.Context, extension) -> None:
    try:
        await bot.unload_extension(f"cogs.{extension}")
    except commands.ExtensionNotLoaded: 
        await ctx.reply(f"{extension} cog could not be reloaded")
    else:
        await bot.load_extension(f"cogs.{extension}")
        await ctx.reply(f"{extension} cog has been reloaded")

#Loads extensions from file.
async def load_extensions() -> None:
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")

async def main() -> None:
    async with bot:
        await load_extensions()
        await bot.start(os.getenv('DISCORD_TOKEN'))

asyncio.run(main())