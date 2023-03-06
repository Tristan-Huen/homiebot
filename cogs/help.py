import discord
from discord.ext import commands
from typing import Optional, List, Mapping

EMBED_COLOR=16124415

class MyHelp(commands.MinimalHelpCommand):

    #Default $help command which lists all the cogs, their commands, and the syntax.
    async def send_bot_help(self, mapping:Mapping[Optional[commands.Cog], List[commands.Command]]) -> None:
        embed = discord.Embed(title="Help")
        for cog, commands in mapping.items():
           
           #Filter commands by removing any commands that the user cannot use.
           #Get the proper signature of each command.
           filtered = await self.filter_commands(commands, sort=True)
           command_signatures = [self.get_command_signature(c) for c in filtered]

           if command_signatures:
                cog_name = getattr(cog, "qualified_name", "No Category")
                embed.add_field(name=cog_name, value="\n".join(command_signatures), inline=False)

        channel = self.get_destination()
        await channel.send(embed=embed)

    #Help command for syntax $help [command]
    async def send_command_help(self, command:commands.Command)-> None:
        embed = discord.Embed(
            title=self.get_command_signature(command),
            color=discord.Color(EMBED_COLOR)
        )

        embed.add_field(name="Description", value=command.help)
        alias = command.aliases
        if alias:
            embed.add_field(name="Aliases", value=", ".join(alias), inline=False)

        channel = self.get_destination()
        await channel.send(embed=embed)

    #For the case where an error occurs
    async def send_error_message(self, error:str) -> None:
        embed = discord.Embed(
            title="Error", 
            description=error,
            color=discord.Color(EMBED_COLOR)
        )

        channel = self.get_destination()
        await channel.send(embed=embed)

class Help(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        help_command = MyHelp()
        help_command.cog = self
        bot.help_command = help_command

async def setup(bot)-> None:
    await bot.add_cog(Help(bot))
