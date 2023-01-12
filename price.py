import aiohttp
from typing import Union
import os
from discord.ext import commands
from discord.commands import SlashCommandGroup
import discord
from sqlalchemy import select
from models import Session, SteamApps, PriceInfo
import traceback

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

async def fetch_itad_game_plain(game_name: str) -> dict:
    '''Fetches price information using a game name.'''
    url = 'https://api.isthereanydeal.com/v02/search/search/'
    params = {'key': ITAD_API, 'q': game_name, 'limit': 1}
    result = await api_call(url, params)
    return result['data']['results'][0]['plain']

async def fetch_itad_game_overview(
    app_id: int = None, 
    game_plain: str = None
) -> dict:
    '''Fetches price information using steam app id.
    Used for showing game price info to users.'''
    url = 'https://api.isthereanydeal.com/v01/game/overview/'
    params = {'key': ITAD_API}
    if app_id:
        params['shop'] = 'steam'
        params['ids'] = f'app/{app_id}'
        result = await api_call(url, params)
        return result['data'][f'app/{app_id}']
    if game_plain:
        params['plains'] = game_plain
        result = await api_call(url, params)
        return result['data'][game_plain]

async def get_price_data(app_id: int, game_name: str) -> dict:
    data = await fetch_itad_game_overview(app_id=app_id)
    if not data['price']:
        plain = await fetch_itad_game_plain(game_name)
        data = await fetch_itad_game_overview(game_plain=plain)
    return data

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
        try:
            appid = await get_game_appid(game_name)
            steam_app_details = await fetch_steam_app_details(appid)
            itad_app_details = await get_price_data(appid, game_name)
            embed = PriceInfo(itad_app_details, steam_app_details, appid).info_embed()
            await ctx.respond(embed = embed)
        except Exception as exc:
            print(traceback.format_exc())
            response = (
                'It looks like there was an issue getting that games price '
                'data. The error has been sent to the support server.'
            )
            await ctx.respond(response)

def setup(bot):
    bot.add_cog(Price(bot))