import discord
import re
from discord.ext import commands
import os, random

class Entertainment(commands.Cog):
    def __init__(self, bot)-> None:
        self.bot = bot

    @commands.command(help="This command is unfinished and only exists as a test for formatting.")
    async def movie(self, ctx:commands.Context) -> None:
        movie_dict = {
                      'title': 'The Last of Us', 
                      'year': '(2023)', 'rating': 9.1, 'runtime': '50 min', 
                      'genre': '\nAction, Adventure, Drama', 
                      'description': "\nAfter a global pandemic destroys civilization, a hardened survivor takes charge of a 14-year-old girl who may be humanity's last hope.", 
                      'directors': ['Neil Druckmann', 'Craig Mazin'], 'stars': ['Pedro Pascal', 'Bella Ramsey', 'Anna Torv', 'Gabriel Luna'], 
                      'image': 'https://m.media-amazon.com/images/M/MV5BZGUzYTI3M2EtZmM0Yy00NGUyLWI4ODEtN2Q3ZGJlYzhhZjU3XkEyXkFqcGdeQXVyNTM0OTY1OQ@@._V1_UX67_CR0,0,67,98_AL_.jpg'
                      }
        
        embed = discord.Embed(
                    title = movie_dict['title'] + " " + movie_dict['year'],
                    description = movie_dict['description'],
                    color = discord.Color.blue(),
                    url= "https://www.imdb.com/title/tt3581920/?ref_=adv_li_tt"
                )
        
        embed.set_thumbnail(url=movie_dict['image'])
        embed.set_author(name = "HomieBot")
        embed.add_field(name = "Genre", value = f"{movie_dict['genre']}", inline = True)
        embed.add_field(name = "Runtime", value = f"{movie_dict['runtime']}", inline = True)
        embed.add_field(name = "Rating", value = f":star: {movie_dict['rating']}", inline = False)
        if(movie_dict['directors']):
            embed.add_field(name = "Directors", value = ", ".join(movie_dict['directors']), inline = False)

        embed.add_field(name = "Stars", value = ", ".join(movie_dict['stars']), inline = False)

        await ctx.send(embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(Entertainment(bot))