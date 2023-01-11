import aiohttp
from typing import Union
import os
from discord.ext import commands
from discord.commands import SlashCommandGroup
import discord
from sqlalchemy import select
from models import Session, SteamApps, PriceInfo

ITAD_API = os.getenv('ITAD_API')

async def api_call(url, params: dict = None, headers: dict = None, ssl: bool = False):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            url, 
            params = params, 
            headers = headers, 
            ssl = False
        ) as resp:
            return await resp.json()

async def fetch_steam_app_details(app_ids: Union[int, list[int]]) -> dict:
    '''Fetches app info from steam. Used for showing game info to users.'''
    if type(app_ids) == list:
        ','.join(app_ids)
    url = 'https://store.steampowered.com/api/appdetails/'
    params = {'appids': app_ids}
    return await api_call(url, params)

async def fetch_itad_game_overview(app_ids: Union[int, list[int]]) -> dict:
    '''Fetches app info from steam. Used for showing game price info to users.'''
    if type(app_ids) == list:
        apps = ','.join([f'app/{app_id}' for app_id in app_ids])
    else:
        apps = f'app/{app_ids}'
    url = 'https://api.isthereanydeal.com/v01/game/overview/'
    params = {'key': ITAD_API, 'shop': 'steam', 'ids': apps}
    return await api_call(url, params)

async def get_game_name_options(
    ctx: discord.AutocompleteContext
) -> list[discord.OptionChoice]:
    '''Gets all of the matching game names from the steam app table. This is 
    used to autocomplete the options when users search for game prices.'''
    if not ctx.value:
        return ['Begin Typing']
    with Session() as session:
        stmt = f'''SELECT name FROM steam_apps
            WHERE name % '{ctx.value}'
            ORDER BY name <-> '{ctx.value}'
            LIMIT 20;'''
        results = session.execute(stmt).scalars().all()
    return results

async def get_game_appid(game_name: str) -> int:
    '''Gets an appid of a given game title. This is used to fetch the app
    data from steam.'''
    with Session() as session:
        stmt = select(SteamApps.appid).where(SteamApps.name == game_name)
        result = session.execute(stmt).scalars().first()
    return result

class Price(commands.Cog):

    def __init__(self, bot_: discord.Bot):
        self.bot = bot_

    price = SlashCommandGroup("price", "Commands for game prices.")

    @price.command()
    @discord.option(
        name = 'game_name',
        autocomplete = get_game_name_options,
        description = 'Choose a game title.'
    )
    async def lookup(self, ctx: discord.ApplicationContext, game_name: str):
        '''Gives price information on a game.'''
        await ctx.response.defer()
        appid = await get_game_appid(game_name)
        steam_app_details = await fetch_steam_app_details(appid)
        itad_app_details = await fetch_itad_game_overview(appid)
        embed = PriceInfo(itad_app_details, steam_app_details, appid).info_embed()
        await ctx.respond(embed = embed)

def setup(bot):
    bot.add_cog(Price(bot))