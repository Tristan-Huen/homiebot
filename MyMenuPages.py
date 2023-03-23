import discord
from discord.ext import commands
from discord.ext import menus
from typing import Any

class MyMenuPages(discord.ui.View, menus.MenuPages):
    def __init__(self, source)-> None:
        super().__init__(timeout=180)
        self._source = source
        self.current_page = 0
        self.ctx = None
        self.message = None

    async def start(self, ctx:commands.Context, *, channel = None, wait:bool = False)-> None:
        await self._source._prepare_once()
        self.ctx = ctx
        self.message = await self.send_initial_message(ctx, ctx.channel)

    async def _get_kwargs_from_page(self, page) -> (dict | dict[str, Any] | None):
        value = await super()._get_kwargs_from_page(page)
        if 'view' not in value:
            value.update({'view': self})
        return value

    async def interaction_check(self, interaction:discord.Interaction)-> bool:
        return interaction.user == self.ctx.author

    #Note: Some old code uses a different order for these parameters which will cause
    # errors now. Correct order is the interaction param before the button param.
    @discord.ui.button(emoji='\U000023EA', style=discord.ButtonStyle.blurple)
    async def first_page(self, interaction:discord.Interaction, button)-> None:
        await self.show_page(0)
        await interaction.response.defer()

    @discord.ui.button(emoji='\U00002B05', style=discord.ButtonStyle.blurple)
    async def before_page(self, interaction:discord.Interaction, button)-> None:
        await self.show_checked_page(self.current_page - 1)
        await interaction.response.defer()

    @discord.ui.button(emoji='\U000027A1', style=discord.ButtonStyle.blurple)
    async def next_page(self, interaction:discord.Interaction, button)-> None:
        await self.show_checked_page(self.current_page + 1)
        await interaction.response.defer()

    @discord.ui.button(emoji='\U000023ED', style=discord.ButtonStyle.blurple)
    async def last_page(self, interaction:discord.Interaction, button)-> None:
        await self.show_page(self._source.get_max_pages() - 1)
        await interaction.response.defer()