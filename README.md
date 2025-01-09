# HomieBot
<img src="https://user-images.githubusercontent.com/103806406/223017612-6aec4e3a-64c5-4095-a3f2-74e2f60f25c6.png" width=10% height=10%>

My Discord bot for my own server. Use the `$help` command to see a list of commands. Additionally use `$help [command_name]` for detailed help on a certain command.  

## Features

### Admin Commands
- Moving users in voice channels.
  - Can move a list of users to a given voice channel.
  - Can move all users in the current voice channel to another voice channel.
  - Mispelling of channel argument corrects to most likely channel name.
- Mass deletion of messages.
  - Limit of 100 messages deletable at a time.
- Talking Stick
  - Allows only one person to talk at a time.
  - People in the voice channel can vote to skip the current person's turn.

### Weather
- Current weather
  - See the current weather around the world for a given city.
  - Provides information such as temperature, precipitation, relative humidity, and more.
- Weekly forecast
  - See the 7-day forecast around the world for a given city.
  - Provides similar information to the current weather feature.
  - Information contained in an paginated embed.
  
> [!NOTE]
> This requires an API key from Weatherbit.

## Examples

Using the `$weather` command:

<img src = "https://user-images.githubusercontent.com/103806406/223621188-e972f4fd-04e9-412b-8503-48f2cf0a49d3.png" width=40% height=40%>

## To-Do
- [ ] Finish fleshing out help command.
- [ ] Add logging for debugging.
- [x] Implement hybrid commands.
- [ ] Add proper comments for most command functions.
