import discord
import re
from discord.ext import commands
import os, random

def levenshtein_distance(s:str,t:str) -> int:
    """
    Computes the Levenshtein distance between two strings
  
    Computes the Levenshtein distance between two strings using an iterative algorithm
    with two matrix rows. Based on pseudocode found here: https://en.wikipedia.org/wiki/Levenshtein_distance
  
    Parameters
    ----------
    s (str): A string.
    t (str): Another string.
  
    Returns
    ----------
    (int): Levenshtein distance.
    """

    #Create lists for the integer representations of each char.
    s=[ord(c) for c in s]
    t=[ord(c) for c in t]
    
    s_len = len(s)
    t_len = len(t)
    substitute_cost = 0
    
    v0 = [i for i in range(0,t_len+1)]
    v1 = [0] * (t_len+1)
    
    for i in range(0,s_len):
        v1[0] = i+1
        
        for j in range(0,t_len):
            deletion_cost = v0[j+1] + 1
            insertion_cost = v1[j]+1
            if s[i] == t[j]:
                substitute_cost = v0[j]
            else:
                substitute_cost = v0[j]+1
            v1[j+1] = min(deletion_cost,insertion_cost,substitute_cost)
        v0,v1 = v1,v0
    return v0[t_len]

class AdminCommands(commands.Cog):
    def __init__(self, bot)-> None:
        self.bot = bot
        self.ALPHANUMERIC_MATCH = r"[^a-zA-Z0-9\s]+"

        with open("mark_adlibs.txt") as f:
            self.mark_quotes = f.readlines()

        with open("ivaylo_quotes.txt") as f:
            self.ivaylo_quotes = f.readlines()

    # Ping Command.
    @commands.command()
    async def ping(self, ctx)-> None:
        #Fixed by https://stackoverflow.com/questions/65263497/latency-in-a-cog-in-discord-py-isnt-recognized-as-a-valid-attribute
        await ctx.reply(f'Pong! {round(self.bot.latency * 1000)} ms')

    # Purge Command
    @commands.command(aliases = ['purge','delete'], description='Purges a given amount of messages')
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, limit:int)-> None:
        if limit == None:
            await ctx.channel.purge(limit = 0)
        elif limit > 99:
            await ctx.channel.purge(limit = 100)
        else:
            await ctx.channel.purge(limit = limit + 1)

    # Random Image of Person Command.
    @commands.command()
    async def image(self, ctx, name:str) -> None:
        try:
            photo = random.choice(os.listdir(os.getenv('PHOTO_DIRECTORY') + name))

            #Discord can't display HEIC files so just pass them.
            #Unless I can figure out a way to convert these files. 
            while(photo.endswith("HEIC")):
                photo = random.choice(os.listdir(os.getenv('PHOTO_DIRECTORY') + name))
        except FileNotFoundError:
            await ctx.channel.send("Person does not exist")
        except discord.errors.HTTPException:
            #Deals with file being bigger than 8MB. Future option is to compress and then send
            while(int(os.path.getsize(os.getenv('PHOTO_DIRECTORY') + name + "\\" +photo)) >= 8388608):
                photo = random.choice(os.listdir(os.getenv('PHOTO_DIRECTORY') + name))
        else:
            await ctx.channel.send(photo=discord.File(os.getenv('PHOTO_DIRECTORY') + name + "\\" +photo))

    # Send random Mark Adlib.
    @commands.command()
    async def markadlib(self, ctx)-> None:
        adlib = random.choice(self.mark_quotes)
        await ctx.channel.send(f"Mark says: {adlib}")

    # Send random Ivaylo League quote.
    @commands.command()
    async def ivayloquote(self, ctx)-> None:
        quote = random.choice(self.ivaylo_quotes)
        await ctx.channel.send(f"Ivaylo in League of Legends says: {quote}")
    
    # Moves members to a specified channel.
    @commands.command()
    @commands.has_guild_permissions(move_members=True) #Other permissions property assumes only text-channels
    async def move(self, ctx, users:commands.Greedy[discord.Member], *,channel:str)-> None:
        names = ", ".join(user.display_name for user in users)
        voice_channels = ctx.guild.voice_channels
        voice_channels_names = [chan.name for chan in voice_channels]
        voice_channels_stripped = [re.sub(self.ALPHANUMERIC_MATCH, "",chan).lower() for chan in voice_channels_names]

        #If the channel is not a valid channel then compute the Levenshtein distance between it and actual channels
        if(channel not in voice_channels_names):
            distances = []

            #Strip the input channel name of any non-valid characters as well as convert to lowercase
            channel_stripped = re.sub(self.ALPHANUMERIC_MATCH, "",channel).lower()
            words = channel_stripped.split()

            #Compute Levenshtein distance between input channel name and actual channel names
            for voice_chan_name in voice_channels_stripped:
                voice_chan_words = voice_chan_name.split()
                distances.append(sum(list(map(levenshtein_distance,words,voice_chan_words))))
            
            #Find the element with minimum distance and set channel to corresponding one.
            minimum_distance = min(distances)
            channel = voice_channels[distances.index(minimum_distance)]
 
        else:
            #Find discord.VoiceChannel object that matches channel name
            channel = next((chan for chan in voice_channels if chan.name == channel),None)

        for user in users:
            await user.move_to(channel=channel)
        await ctx.reply(f"Moved {names} to {channel}")
    
    # Moves all members in the user's voice channnel to a specified channel.
    @commands.command()
    @commands.has_guild_permissions(move_members=True) #Other permissions property assumes only text-channels
    async def moveall(self, ctx, channel:str)-> None:
        voice_channels = ctx.guild.voice_channels
        voice_channels_names = [chan.name for chan in voice_channels]
        voice_channels_stripped = [re.sub(self.ALPHANUMERIC_MATCH, "",chan).lower() for chan in voice_channels_names]

        #If the channel is not a valid channel then compute the Levenshtein distance between it and actual channels
        if(channel not in voice_channels_names):
            distances = []

            #Strip the input channel name of any non-valid characters as well as convert to lowercase
            channel_stripped = re.sub(self.ALPHANUMERIC_MATCH, "",channel).lower()
            words = channel_stripped.split()

            #Compute Levenshtein distance between input channel name and actual channel names
            for voice_chan_name in voice_channels_stripped:
                voice_chan_words = voice_chan_name.split()
                distances.append(sum(list(map(levenshtein_distance,words,voice_chan_words))))
            
            #Find the element with minimum distance and set channel to corresponding one.
            minimum_distance = min(distances)
            channel = voice_channels[distances.index(minimum_distance)]
 
        else:
            #Find discord.VoiceChannel object that matches channel name
            channel = next((chan for chan in voice_channels if chan.name == channel),None)

        author = ctx.message.author
        chan_author = author.voice.channel
        users = chan_author.members

        names = ", ".join(user.display_name for user in users)

        for user in users:
            await user.move_to(channel=channel)
        await ctx.reply(f"Moved {names} to {channel}")


async def setup(bot)-> None:
    await bot.add_cog(AdminCommands(bot))