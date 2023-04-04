import discord
import inspect
import re
import asyncio
import os, random
from discord.ext import commands
from discord.utils import get
from collections import deque
from typing import List, Any, Set, Iterable, Callable, TypeVar

T = TypeVar('T')

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

async def concurrent_execute(objs:Iterable[T],objs_skip:Set[T] | T, method:Callable[..., Any], *args:Any, **kwargs:Any) -> List[Any]:
        """
        Concurrently executes an object method on each object in a list and allows ability to skip objects
        in the list.
    
        Uses asyncio to execute an object method on each object in a list by using `asyncio.gather`. 
        There is an additional parameter containing set of objects whose execution will be skipped. 
        Use `None` for this parameter if no skips are required. 
    
        Parameters
        ----------
        objs (Iterable[T]): A iterable of objects all of the same type/class.
        objs_skip (Set[T] | T): A set of objects or object in objs which will be skipped. Use `None` if nothing to skip. 
        method (Callable): A method to execute on each object.
        args (Any): Optional positional arguments to be passed to the method.
        kwargs (Any): Optional keyword arguments to be passed to the method.
    
        Returns
        ----------
        (List[Any]): A list of results returned by the method.
        """

        if objs_skip is None:

            tasks = []
            for obj in objs:
                task = asyncio.ensure_future(method(obj, *args, **kwargs))
                tasks.append(task)
        
        else:
            if(type(objs_skip) == set):   
                tasks = []
                for obj in objs:
                    if obj not in objs_skip:
                        task = asyncio.ensure_future(method(obj, *args, **kwargs))
                        tasks.append(task)
            else:
                tasks = []
                for obj in objs:
                    if obj != objs_skip:
                        task = asyncio.ensure_future(method(obj, *args, **kwargs))
                        tasks.append(task)
        
        return await asyncio.gather(*tasks)

class Voter(discord.ui.View):

    def __init__(self,max_votes:int) -> None:
        super().__init__(timeout=15)
        self.users = set()
        self.max_votes = max_votes
        self.votes = 0
    
    @discord.ui.button(label='0', style=discord.ButtonStyle.red)
    async def count(self, interaction:discord.Interaction, button:discord.ui.Button) -> None:
        if(interaction.user not in self.users):
            self.users.add(interaction.user)

            self.votes = int(button.label) if button.label else 0
            if self.votes + 1 >= self.max_votes:
                button.style = discord.ButtonStyle.green
                button.disabled = True
                self.stop()
            button.label = str(self.votes+1)

        await interaction.response.edit_message(view=self)

class AdminCommands(commands.Cog):
    def __init__(self, bot)-> None:
        self.bot = bot
        self.ALPHANUMERIC_MATCH = r"[^a-zA-Z0-9\s]+"
        self.talkingstick_active = False
        self.muteall_active = False
        self.talkingstick_chan = None
        self.muteall_chan = None

        #NOTE: Currently do not like this as I would prefer a non-shared variable if multiple timers exist.
        #      For now such an implementation works but for the future I would prefer some kind of way to have
        #      each instance of a countdown timer have their own way to cancel without relying on a single class
        #      variable shared by all.       
        self.cancel_timer = False
        
        with open("mark_adlibs.txt") as f:
            self.mark_quotes = f.readlines()

        with open("ivaylo_quotes.txt") as f:
            self.ivaylo_quotes = f.readlines()

    async def countdown(self, t: int, message:discord.Message, content:str) -> None:

        while t > 0 and not self.cancel_timer:
            await message.edit(content = content + str(t) + "s.")
            t -= 1
            await asyncio.sleep(1)
        
        self.cancel_timer = False

    @commands.Cog.listener()
    async def on_voice_state_update(self, member:discord.Member, before:discord.VoiceState, after:discord.VoiceState) -> None:

        if (self.talkingstick_active or self.muteall_active):

            if before.channel is not self.muteall_chan and after.channel == self.muteall_chan:
                try:
                    await member.edit(mute = True)
                except discord.errors.HTTPException:
                    pass


    # Ping Command.
    @commands.hybrid_command(
            description="Get bot latency",
            help="Returns bot latency in milliseconds."
    )
    async def ping(self, ctx:commands.Context)-> None:
        #Fixed by https://stackoverflow.com/questions/65263497/latency-in-a-cog-in-discord-py-isnt-recognized-as-a-valid-attribute
        await ctx.reply(f'Pong! {round(self.bot.latency * 1000)} ms')

    # Purge Command
    @commands.hybrid_command(
            aliases = ['clear','delete'], 
            description='Purges a given amount of messages.',
            help="Deletes a given amount of messages. Max limit is 100."
    )
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx:commands.Context, amount:int)-> None:
        await ctx.defer(ephemeral=True)

        #Since the slash command purges an extra message we can take advantage of the fact that
        #ctx.interaction only exists when invoked as a slash command.
        if(ctx.interaction):
            amount = amount -1

        if amount < 0:
            if ctx.interaction:
                await ctx.channel.purge(limit = 0)
                amount = -1
            else:
                await ctx.channel.purge(limit = 1)
                amount = 0
        elif amount > 99:
            await ctx.channel.purge(limit = 100)
        else:
            await ctx.channel.purge(limit = amount + 1)
        
        #Hybrid commands already handle followups so, just use ctx.send instead of ctx.channel.send.
        if(ctx.interaction):
            await ctx.send(f"Deleted {amount+1 if amount <= 99 else 100} messages", delete_after=2)
        else:
            await ctx.send(f"Deleted {amount if amount <= 99 else 100} messages", delete_after=2)

    # Random Image of Person Command.
    @commands.hybrid_command(
            description="Gets the photo of a random person. Use their first name with the first letter capitalized.",
            help="Gets the photo of a random person in the server. Use their first name with the first letter capitalized."
    )
    @commands.is_owner() #Temporary since command needs overhauling
    async def image(self, ctx:commands.Context, name:str) -> None:
        PHOTO_DIRECTORY =os.getenv('PHOTO_DIRECTORY')

        try:
            photo = random.choice(os.listdir(PHOTO_DIRECTORY + name))

            #Discord can't display HEIC files so just pass them.
            #Unless I can figure out a way to convert these files. 
            while(photo.endswith("HEIC")):
                photo = random.choice(os.listdir(PHOTO_DIRECTORY + name))
        except FileNotFoundError:
            await ctx.reply("Person does not exist")
        except discord.errors.HTTPException:
            #Deals with file being bigger than 8MB. Future option is to compress and then send
            while(int(os.path.getsize(PHOTO_DIRECTORY + name + "\\" +photo)) >= 8388608):
                photo = random.choice(os.listdir(PHOTO_DIRECTORY + name))
        else:
            with open(PHOTO_DIRECTORY + name + "\\" + photo, mode='rb') as p:
                photo_file = discord.File(p)

            await ctx.reply(file=photo_file)

    # Send random Mark Adlib.
    @commands.hybrid_command(
            description="Say a Mark adlib",
            help="Says a random Mark adlib."
    )
    async def markadlib(self, ctx:commands.Context)-> None:
        adlib = random.choice(self.mark_quotes)
        await ctx.reply(f"Mark says: {adlib}")

    # Send random Ivaylo League quote.
    @commands.hybrid_command(
            description="Say a Ivaylo quote from LOL",
            help="Says a random Ivaylo quote when he plays LOL"
    )
    async def ivayloquote(self, ctx:commands.Context)-> None:
        quote = random.choice(self.ivaylo_quotes)
        await ctx.reply(f"Ivaylo in League of Legends says: {quote}")
    
    # Moves members to a specified channel.
    @commands.hybrid_command(
            description="Move members in to a voice channel. Use @ symbol for users",
            help="Moves the given user(s) to a specified voice channel"
    )
    @commands.has_guild_permissions(move_members=True) #Other permissions property assumes only text-channels
    async def move(self, ctx:commands.Context, users:commands.Greedy[discord.Member], *,channel:str)-> None:
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

        users = list(dict.fromkeys(users))

        #Test this with asyncio tasks to see if an exception occurs or not.
        for user in users:
            try:
                await user.move_to(channel=channel)
            except discord.errors.HTTPException:
                users.remove(user)
            except discord.ext.commands.errors.MemberNotFound:
                users.remove(user)

        names = ", ".join(user.display_name for user in users)
        if names:
            await ctx.reply(f"Moved {names} to {channel}")
        else:
            await ctx.reply("No members to move.")
    
    # Moves all members in the user's voice channnel to a specified channel.
    @commands.hybrid_command(
            description="Move all members in current channel to another",
            help="Moves all the members in your current voice channel to a specified voice channel"
    )
    @commands.has_guild_permissions(move_members=True) #Other permissions property assumes only text-channels
    async def moveall(self, ctx:commands.Context, channel:str)-> None:
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

        await concurrent_execute(users, None, discord.Member.move_to, channel=channel)

        await ctx.reply(f"Moved {names} to {channel}")

    @commands.hybrid_command(
            description="Mutes all users except command sender for a certain amount of seconds.",
            help="Mutes all users except command sender for a certain amount of seconds."
    )
    @commands.has_guild_permissions(mute_members=True)
    async def muteall(self,ctx:commands.Context,time:int) -> None:
        self.muteall_active = True

        if(time > 60):
            time = 60

        author = ctx.message.author
        chan_author = author.voice.channel
        self.muteall_chan = chan_author
        users = chan_author.members

        #Mute all users except for author.
        await concurrent_execute(users, author, discord.Member.edit, mute=True)

        #Countdown mute time.
        message = await ctx.reply("Muted all users.")
        content = "Muted all users for " 
        await self.countdown(time,message,content)

        await concurrent_execute(users, None, discord.Member.edit, mute=False)
        await message.edit(content="Unmuted all users.")

        self.muteall_active = False
        self.muteall_chan = None

    @commands.hybrid_command(
            description="Only one person can talk at a time. Default talktime is 60s.",
            help="Mutes all users and only allows one to talk at a time for a certain duration."
    )
    async def talkingstick(self, ctx:commands.Context, talktime:int=60) -> None:
        if(self.talkingstick_active):
            await ctx.reply("There can only be one talking stick!")
            return

        self.talkingstick_active = True

        if(talktime > 60):
            talktime = 60
        elif(talktime <= 0):
            talktime = 1    

        author = ctx.message.author
        chan_author = author.voice.channel
        self.talkingstick_chan = chan_author
        users = chan_author.members
        user_stick = author

        await concurrent_execute(users, user_stick, discord.Member.edit, mute=True)

        #Start with author first.
        message = await ctx.reply(f"{author.display_name} has the talking stick.")
        content=f"{author.display_name} has the talking stick for "
        await self.countdown(talktime, message, content)
        await user_stick.edit(mute=True)

        user_queue = deque(users)

        while (len(user_queue) != 0):

            #Takes care of when a new user joins the channel. Note: needs more work.
            new_user_list = set(ctx.message.author.voice.channel.members).difference(set(users))
            if(new_user_list):
                users = ctx.message.author.voice.channel.members
                user_queue.extend(new_user_list)

            user_stick = user_queue.popleft()

            if(user_stick != author):
                await user_stick.edit(mute=False)
                content=f"{user_stick.display_name} has the talking stick for "
                await self.countdown(talktime, message, content)

                await user_stick.edit(mute=True)

        await concurrent_execute(users, None, discord.Member.edit, mute=False)
        await message.edit(content="Talking stick has been destroyed.")

        self.talkingstick_active = False
        self.talkingstick_chan = None
    
    @commands.hybrid_command(
            description="Votes to skip the current user with the talking stick.",
            help="Votes to skip the current user with the talking stick."
    )
    async def skipturn(self,ctx:commands.Context):
        if self.talkingstick_active:
            max_votes = round(len(ctx.message.author.voice.channel.members) * 0.5)

            voter = Voter(max_votes=max_votes)

            message = await ctx.send(f"Vote to skip current user. Need {max_votes} votes to skip.", view = voter)
            await voter.wait()
            
            if voter.votes + 1 == max_votes:
                await message.edit(content="Skipping user.", delete_after=5)
                self.cancel_timer = True
            else:
                await message.edit(content="Not enough votes to skip user.", delete_after=5)

async def setup(bot)-> None:
    await bot.add_cog(AdminCommands(bot))