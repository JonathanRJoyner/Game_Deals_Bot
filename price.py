import aiohttp
from typing import Union
import os
from discord.ext import commands
from discord.commands import SlashCommandGroup
import discord
from sqlalchemy import select
from models import Session, SteamApps, PriceAlerts, G2AData, embed_listed_field, embed_cta
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

async def fetch_itad_game_plain(game_name: str) -> dict:
    '''Fetches price information using a game name.'''
    url = 'https://api.isthereanydeal.com/v02/search/search/'
    params = {'key': ITAD_API, 'q': game_name, 'limit': 1}
    result = await api_call(url, params)
    return result['data']['results'][0]['plain']

async def fetch_itad_overview(
    game_plains: Union[str, list[str]] = None
) -> dict:
    '''Fetches price information using steam app id.
    Used for showing game price info to users.'''
    if type(game_plains) == list:
        game_plains = ','.join(game_plains)
    url = 'https://api.isthereanydeal.com/v01/game/overview/'
    params = {'key': ITAD_API, 'plains': game_plains}
    result = await api_call(url, params)
    return result['data']

async def fetch_itad_info(
    game_plains: Union[str, list[str]] = None
) -> dict:
    '''Fetches price information using steam app id.
    Used for showing game price info to users.'''
    if type(game_plains) == list:
        game_plains = ','.join(game_plains)
    url = 'https://api.isthereanydeal.com/v01/game/info/'
    params = {'key': ITAD_API, 'plains': game_plains}
    result = await api_call(url, params)
    return result['data']

async def fetch_steam_app_details(app_ids: Union[int, list[int]]) -> dict:
    '''Fetches app info from steam. Used for showing game info to users.'''
    if type(app_ids) == list:
        ','.join(app_ids)
    url = 'https://store.steampowered.com/api/appdetails/'
    params = {'appids': app_ids}
    return await api_call(url, params)

async def get_steam_image(game_name: str) -> str:
    game_name = get_closest_names(game_name)[0]
    with Session() as session:
        stmt = select(SteamApps.appid).where(SteamApps.name == game_name)
        appid = session.execute(stmt).scalars().first()
    details = await fetch_steam_app_details(appid)
    return details[str(appid)]['data'].get('header_image')

def get_closest_names(game_str: str) -> list[str]:
    '''Matches the closest game name in the steam_apps table to the user input.
    Returns the 20 closest matches.'''
    with Session() as session:
        stmt = f'''SELECT name FROM steam_apps
            WHERE name % '{game_str}'
            ORDER BY name <-> '{game_str}'
            LIMIT 20;'''
        return session.execute(stmt).scalars().all()

async def game_autocomplete_options(
    ctx: discord.AutocompleteContext
) -> list[discord.OptionChoice]:
    '''Gets all of the matching game names from the steam app table. This is 
    used to autocomplete the options when users search for game prices.'''
    if not ctx.value:
        return ['Begin Typing']
    else:
        return get_closest_names(ctx.value)

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
        autocomplete = game_autocomplete_options,
        description = 'Choose a game title.'
    )
    async def lookup(self, ctx: discord.ApplicationContext, game_name: str):
        '''Gives price information on a game.'''
        await ctx.response.defer()
        game_name = get_closest_names(game_name)[0]
        try:
            game_plain = await fetch_itad_game_plain(game_name)            
            info = await PriceInfo.create_one(game_plain)
            embed = info.info_embed()
            view = CreateAlertView(info)
            await ctx.respond(embed = embed, view = view)
        except:
            print(traceback.format_exc())
            response = (
                'It looks like there was an issue getting that games price '
                'data. The error has been sent to the support server.'
            )
            await ctx.respond(response)

class PriceInfo:

    def __init__(
        self, 
        game_plain: str, 
        itad_overview,
        itad_info
    ):
        self.game_plain = game_plain

        #Parsing ITAD overview
        self.itad_overview = itad_overview
        self.current = self.itad_overview.get('price', {})
        self.lowest = self.itad_overview.get('lowest', {})
        self.price = self.current.get('price_formatted', 'None')
        self.price_cut = f"-{self.current.get('cut', '0')}%"
        self.price_store = self.current.get('store', 'None')
        self.price_url = self.current.get('url', 'None')
        self.lowest_price = self.lowest.get('price_formatted', 'None')
        self.lowest_cut = f"-{self.lowest.get('cut', '0')}%"
        self.lowest_store = self.lowest.get('store', 'None')
        self.lowest_url = self.lowest.get('url', 'None')

        #Parsing ITAD info
        self.itad_info = itad_info
        self.game_name = itad_info.get('title', 'None')
        self.image = itad_info.get('image')

    @staticmethod
    async def create_one(game_plain: str):
        itad_overview = await fetch_itad_overview(game_plain)
        itad_info = await fetch_itad_info(game_plain)
        itad_overview = itad_overview[game_plain]
        itad_info = itad_info[game_plain]
        self = PriceInfo(game_plain, itad_overview, itad_info)
        if not self.image:
            self.image = await get_steam_image(self.game_name)
        return self

    def _key_field(self) -> discord.EmbedField:
        with Session() as session:
            result = session.query(G2AData).filter(
                (G2AData.title.like(f'%{self.game_name}%'))
                &(G2AData.region == 'GLOBAL')
                &(G2AData.platform == 'Steam')
            ).first()
        if result:
            url = f'https://www.g2a.com{result.slug}?gtag=08045ab515'
            price = '${:.2f}'.format(result.minprice)
            price_str = f'`{price}` at [G2A]({url})'
            return embed_listed_field('Key Price', price_str)
        else:
            return None
    
    def info_embed(self) -> discord.Embed:
        embed = discord.Embed(title = self.game_name)
        current_str = f"`{self.price}({self.price_cut})` at [{self.price_store}]({self.price_url})"
        lowest_str = f"`{self.lowest_price}({self.lowest_cut})` at [{self.lowest_store}]({self.lowest_url})"
        key_field = self._key_field()
        price_info = {
            'Current Price': current_str,
            'Lowest Price': lowest_str
        }
        embed.append_field(embed_listed_field('Store Price', price_info))
        if key_field:
            embed.append_field(key_field)
        embed.append_field(embed_cta())
        if self.image:
            embed.set_image(url = self.image)
        return embed

class CreateAlertView(discord.ui.View):
    def __init__(self, info: PriceInfo):
        super().__init__()
        self.info = info
    
    @discord.ui.button(label = 'Create Alert', style = discord.ButtonStyle.red)
    async def alert_button(
        self, 
        button: discord.ui.Button, 
        interaction: discord.Interaction
    ):
        modal = CreateAlertModal(self.info)
        await interaction.response.send_modal(modal = modal)

class CreateAlertModal(discord.ui.Modal):
    def __init__(self, info: PriceInfo):
        super().__init__(
            discord.ui.InputText(
                label = 'Target Price',
                placeholder = '$20',
                min_length = 1,
                max_length = 4
            ),
            title = 'Price Alert'
        )
        self.info = info
    
    async def callback(self, interaction: discord.Interaction):
        price = self.children[0].value.replace('$', '')
        try:
            price = int(float(price))
            PriceAlerts.add_alert(
                interaction, 
                game_name = self.info.game_name, 
                image_url = self.info.image, 
                price = price, 
                game_plain = self.info.game_plain
            )            
        except ValueError:
            response = f'Target price must be a number. You input `{price}`.'
            await interaction.response.send_message(response, ephemeral = True)



def setup(bot):
    bot.add_cog(Price(bot))