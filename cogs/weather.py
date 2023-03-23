import discord
import aiohttp
import json
import csv
import os
from MyMenuPages import MyMenuPages
from datetime import datetime
from dotenv import load_dotenv 
from discord.ext import commands
from discord.ext import menus


load_dotenv()

DEFAULT_CITY = 'Tokyo'

weather_parameters = {
    "city" : DEFAULT_CITY,
    "country":"",
    "key" : os.getenv('WEATHER_API_KEY'),
    "include" : "minutely"
}

weeklyforecast_parameters = {
    "city" : DEFAULT_CITY,
    "country":"",
    "key" : os.getenv('WEATHER_API_KEY'),
    "days" : "8"
}

#Only for testing purposes
def jprint(obj):
    text = json.dumps(obj, sort_keys = True, indent = 4)
    print(text)

def country_from_code(iso_code:str) -> str:
    """
    Finds a country based on its ISO 3166-1 alpha-2 code
  
    Uses a csv table to lookup the country based on its ISO 3166-1 alpha-2 code
  
    Parameters
    ----------
    iso_code (str): A ISO 3166-1 alpha-2 code.

    Returns
    ----------
    (str): The corresponding country.
    """
    #Country code uses ISO 3166-1 alpha-2
    #Code + File from: 
    # https://stackoverflow.com/questions/16253060/how-to-convert-country-names-to-iso-3166-1-alpha-2-values-using-python
    iso_country_codes = {}
    with open("wikipedia-iso-country-codes.csv") as f:
        country_code_csv = csv.DictReader(f, delimiter=',')
        for line in country_code_csv:
            iso_country_codes[line['Alpha-2 code']] = line['English short name lower case']
    return iso_country_codes[iso_code]

def find_2nd(string:str, substring:str) -> int:
    """
    Finds the second occurence of a substring in a string
  
    Parameters
    ----------
    string (str): String to find a substring in.
    substring (str): Substring to search for.

    Returns
    ----------
    (int): Index of second occurence.
    """
    return string.find(substring, string.find(substring) + 1)

def new_date_format(date:str) -> str:
    d = datetime.strptime(date, "%Y-%m-%d")
    date = d.strftime("%A, %B %d, %Y")
    date_slice = date[0:find_2nd(date, ",")-1]
    date_slice_two = date[find_2nd(date, ",")-1:]
    date_slice = date_slice.replace("0","")

    return date_slice + date_slice_two

class ForecastSource(menus.ListPageSource):
        async def format_page(self, menu, entries) -> discord.Embed:
            date = new_date_format(entries['valid_date'])

            city = entries['city']
            country = entries['country']

            #Both calculated midnight to midnight
            max_temp = entries['max_temp']
            min_temp = entries['min_temp']

            #Day-time high is calculated from 7am to 7pm
            #Night-time low is calculated from 7pm to 7am
            high_temp = entries['high_temp']
            low_temp = entries['low_temp']

            humidity = entries['rh']

            wind_dir = entries['wind_cdir']
            wind_spd = entries['wind_spd']

            precip = entries['precip']
            precip_prob = entries['pop']
            snow = entries['snow']
            uv_index = round(entries['uv'])
            uv_classification = ""
            
            #Classify UV-Index in each category
            match uv_index:         
                case uv_index if 0 <= uv_index <= 2:
                    uv_classification = "Low"
                case uv_index if 3 <= uv_index <= 5:
                    uv_classification = "Medium"
                case uv_index if 6 <= uv_index <= 7:
                    uv_classification = "High"
                case uv_index if 8 <= uv_index <= 10:
                    uv_classification = "Very High"
                case uv_index if uv_index >= 11:
                    uv_classification = "Extreme"      
                    
            
            weather_descrip = entries['weather']['description']
            weather_icon =  entries['weather']['icon']
            icon_url = 'https://www.weatherbit.io/static/img/icons/' + weather_icon + ".png"

            embed = discord.Embed(
                title = "Weather Forecast",
                description=f"The forecast for {date}, in {city}, {country}", 
                color=discord.Colour.random()
            )

            embed.set_author(name = "HomieBot")
            embed.set_thumbnail(url = icon_url)
            embed.add_field(name = "Max/Min Temperature", value = f"{min_temp}-{max_temp}°C", inline = True)
            embed.add_field(name = "High/Low Temperature", value = f"{low_temp}-{high_temp}°C", inline = True)
            embed.add_field(name = "Description", value = weather_descrip, inline = False)
            embed.add_field(name = "Precipitation Chance", value = f"{precip_prob}%", inline = True)
            embed.add_field(name = "Precipitation", value = f"{round(precip,2)}mm/hr", inline = True)
            embed.add_field(name = "Snowfall", value = f"{round(snow,2)}mm/hr", inline = False)
            embed.add_field(name = "UV-Index", value = f"{entries['uv']} ({uv_classification})", inline = False)
            embed.add_field(name = "Relative Humidity", value = f"{round(humidity,2)}%", inline = False)
            embed.add_field(name = "Wind Speed", value = f"{round(wind_spd,2)}m/s", inline = True)
            embed.add_field(name = "Wind Direction", value = f"{wind_dir}", inline = True)
        
            #Trying to make this multiline messes up the spacing for some reason.
            embed.set_footer(text = "Max and Min are measured from 12-12. High and Low are measured from 7am-7pm and 7pm-7am respectively. Also note that weather forecasts are never fully accurate.")
            return embed 

class Weather(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
    
    #Current Weather Command
    @commands.hybrid_command(
            description="Gives the current weather in a city. Format for city is [city_name, country]",
            help="Gives the current weather in a city. Format for city is [city_name, country]"
    )
    async def weather(self, ctx:commands.Context, *, city:str = DEFAULT_CITY) -> None:
        await ctx.defer()

        #Argument can be in form of City,Country Code (last is optional but will
        # default to some random option)
        if "," in city:
            weather_parameters["city"] = city.partition(",")[0]
            weather_parameters["country"] = city.partition(",")[2].strip()
        else:
            weather_parameters["city"] = city
            weather_parameters["country"] = ""

        #Can be slow at times but I guess at least it's non-blocking
        async with aiohttp.ClientSession() as cs:
            async with cs.get("https://api.weatherbit.io/v2.0/current", params = weather_parameters) as r:
                response_data = await r.json()
                 
                weather_data = response_data["data"][0]
        
                #Convert country code from result back to country name
                #Also get city name result in case user misspelled it
                country_code = weather_data['country_code']
                country = country_from_code(country_code)
                city = weather_data['city_name']

                feel_temp = weather_data['app_temp']
                temp = weather_data['temp']

                humidity = weather_data['rh']

                wind_dir = weather_data['wind_cdir']
                wind_spd = weather_data['wind_spd']

                precip = weather_data['precip']
                snow = weather_data['snow']

                weather_descrip = weather_data['weather']['description']
                weather_icon = weather_data['weather']['icon']
                icon_url = 'https://www.weatherbit.io/static/img/icons/' + weather_icon + ".png"

                embed = discord.Embed(
                    title = "Current Weather",
                    description = f"The current weather in {city}, {country}",
                    color = discord.Color.blue()
                )

                embed.set_author(name = "HomieBot")
                embed.set_thumbnail(url = icon_url)
                embed.add_field(name = "Temperature", value = f"{temp}°C", inline = True)
                embed.add_field(name = "Feels Like", value = f"{feel_temp}°C", inline = True)
                embed.add_field(name = "Description", value = weather_descrip, inline = False)
                embed.add_field(name = "Precipitation", value = f"{precip}mm/hr", inline = False)
                embed.add_field(name = "Snowfall", value = f"{snow}mm/hr", inline = False)
                embed.add_field(name = "Relative Humidity", value = f"{round(humidity,2)}%", inline = False)
                embed.add_field(name = "Wind Speed", value = f"{round(wind_spd,2)}m/s", inline = True)
                embed.add_field(name = "Wind Direction", value = f"{wind_dir}", inline = True)
        
                embed.set_footer(text = "Note results may be inaccurate")
                await ctx.send(embed=embed)

    #7-Day Forecast Command
    @commands.hybrid_command(
            description="Gives the weekly forecast for a city. Format for city is [city_name, country]",
            help="Gives the weekly forecast for city. Format for city is [city_name, country]"
    )
    async def weeklyforecast(self, ctx:commands.Context, *, city:str = DEFAULT_CITY) -> None:
        await ctx.defer()
        
        #Argument can be in form of City,Country Code (last is optional but will
        # default to some random option)
        if "," in city:
            weeklyforecast_parameters["city"] = city.partition(",")[0]
            weeklyforecast_parameters["country"] = city.partition(",")[2].strip()
        else:
            weeklyforecast_parameters["city"] = city
            weeklyforecast_parameters["country"] = ""
            
        #Can be slow at times but I guess at least it's non-blocking
        async with aiohttp.ClientSession() as cs:
            async with cs.get("https://api.weatherbit.io/v2.0/forecast/daily", params = weeklyforecast_parameters) as r:
                response_data = await r.json()
  
                forecast_data = response_data["data"]

                #Convert country code from result back to country name
                #Also get city name result in case user misspelled it
                country_code = response_data['country_code']
                country = country_from_code(country_code)
                city = response_data['city_name']
        
                #Unless there's an easier way, the city and country must be placed in each forecast dict to be used
                # in the embed.
                for data in forecast_data:
                    data.update({"city":city})
                    data.update({"country":country})

                formatter = ForecastSource(forecast_data, per_page=1)
                menu = MyMenuPages(formatter)

                #Unless pagination code is rewritten we must directly reply like this to avoid the "The application did not respond".
                await ctx.send(f"Here is the weekly forecast for {city}, {country}") 
                await menu.start(ctx)
           
async def setup(bot) -> None:
    await bot.add_cog(Weather(bot))
