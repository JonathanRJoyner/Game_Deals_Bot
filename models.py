from sqlalchemy import (
    Column, 
    Integer,
    BIGINT,
    String, 
    Boolean, 
    DateTime,
    Float,
    JSON,
    select,
    create_engine
)
import discord
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os
from typing import Union
import json

CONNECTION_STRING = os.getenv('CONNECTION_STRING')

engine = create_engine(CONNECTION_STRING)
Base = declarative_base()
Session = sessionmaker(engine)

def embed_listed_field(name: str, values: Union[dict, str]) -> discord.EmbedField:
    '''Creates a easily readable and clean formatted field for discord embeds.'''
    name = f"__{name}__"

    if type(values) == str:
        content = values[0:1000]

    else:
        content = []
        for key, value in values.items():
            if '](' not in value:
                content.append(f"{key}: `{value}`")
            else:
                content.append(f"{key}: {value}")
        content = '\n'.join(content)

    return discord.EmbedField(name, content)

def embed_cta():
    '''Creates a standard call to action embed field.'''
    values = (
        "[Vote](https://top.gg/bot/1028073862597967932/vote) | "
        "[Invite](https://discord.com/api/oauth2/authorize?"
        "client_id=1028073862597967932&"
        "permissions=2147485696&"
        "scope=bot%20applications.commands) | "
        "[Support Server](https://discord.gg/KyKu575sg2)"
    )
    return embed_listed_field('Support Us', values)

#Giveaway tables
class GamerPowerData(Base):
    __tablename__ = 'gamerpower'

    id = Column(Integer, primary_key = True)
    title = Column(String)
    worth = Column(String)
    thumbnail = Column(String)
    image = Column(String)
    description = Column(String)
    instructions = Column(String)
    open_giveaway_url = Column(String)
    published_date = Column(String)
    type = Column(String)
    platforms = Column(String)
    end_date = Column(String)
    users = Column(Integer)
    status = Column(String)
    gamerpower_url = Column(String)
    open_giveaway = Column(String)
    alerted = Column(Boolean)

    def alert_embed(self) ->discord.Embed:
        '''Creates an alert embed which can be sent to discord channels.'''
        embed = discord.Embed(
            title = f'New Giveaway: {self.title}', 
            timestamp = datetime.now()
        )
        info_values = {
            'Giveaway Type': self.type,
            'Worth': self.worth,
            'Offer Ends': self.end_date,
            'Link': f"[GamerPower.com]({self.open_giveaway})"
        }
        embed.append_field(embed_listed_field('__Giveaway Info__', info_values))
        embed.append_field(embed_listed_field('Description', self.description))
        embed.append_field(embed_cta())
        embed.set_image(url = self.image)
        return embed

class GiveawayAlerts(Base):
    __tablename__ = 'giveaway_alerts'

    id = Column(Integer, primary_key = True)
    user = Column(BIGINT)
    server = Column(BIGINT)
    channel = Column(BIGINT)
    mentions = Column(JSON)    
    creation_time = Column(DateTime, default = datetime.now())

    @staticmethod
    def get_alerts(server: int) -> list:
        '''Gets all active alerts for a server.'''
        with Session() as session:
            stmt = select(GiveawayAlerts).where(GiveawayAlerts.server == server)
            results = session.execute(stmt).scalars().all()
        return results


    @staticmethod
    def add_alert(
        ctx: discord.ApplicationContext, 
        mentions: list[int] = None
    ) -> None:
        '''Creates an alert given a discord context.'''
        alert = GiveawayAlerts(
            user = ctx.user.id,
            server = ctx.guild.id,
            channel = ctx.channel.id,
            creation_time = datetime.now(),
            mentions = mentions
        )
        with Session() as session:
            session.add(alert)
            session.commit()

#Free to play tables
class FreeToPlayAlerts(Base):
    __tablename__ = 'freetoplay_alerts'

    id = Column(Integer, primary_key = True)
    user = Column(BIGINT)
    server = Column(BIGINT)
    channel = Column(BIGINT)
    mentions = Column(JSON)    
    creation_time = Column(DateTime)

    @staticmethod
    def get_alerts(server: int) -> list:
        '''Gets all active alerts for a server.'''
        with Session() as session:
            stmt = select(FreeToPlayAlerts).where(FreeToPlayAlerts.server == server)
            results = session.execute(stmt).scalars().all()
        return results

    @staticmethod
    def add_alert(
        ctx: discord.ApplicationContext, 
        mentions: list[int] = None
    ) -> None:
        '''Creates an alert given a discord context.'''
        alert = FreeToPlayAlerts(
            user = ctx.user.id,
            server = ctx.guild.id,
            channel = ctx.channel.id,
            creation_time = datetime.now(),
            mentions = mentions
        )
        with Session() as session:
            session.add(alert)
            session.commit()

class FreeToGameData(Base):
    __tablename__ = 'free_to_game'

    id = Column(Integer, primary_key = True)
    title = Column(String)
    thumbnail = Column(String)
    short_description = Column(String)
    game_url = Column(String)
    genre = Column(String)
    platform = Column(String)
    publisher = Column(String)
    developer = Column(String)
    release_date = Column(String)
    freetogame_profile_url = Column(String)
    alerted = Column(Boolean)

    def alert_embed(self) ->discord.Embed:
        '''Creates an alert embed which can be sent to discord channels.'''
        embed = discord.Embed(
            title = f'New F2P Game: {self.title}', 
            timestamp = datetime.now()
        )
        info_values = {
            'Genre': self.genre,
            'Platform': self.platform,
            'Release Date': self.release_date,
            'Link': f"[FreeToGame.com]({self.freetogame_profile_url})"
        }
        embed.append_field(embed_listed_field('Game Info', info_values))
        embed.append_field(embed_listed_field('Description', self.short_description))
        embed.append_field(embed_cta())
        embed.set_image(url = self.thumbnail)
        return embed

#Game Pass tables
class GamePassData(Base):
    __tablename__ = 'gamepass'

    id = Column(String, primary_key = True)
    title = Column(String)
    description = Column(String)
    image_url = Column(String)
    developer = Column(String)
    publisher = Column(String)
    category = Column(String)
    url = Column(String)
    status = Column(String)
    alerted = Column(Boolean, default = False)

    def alert_embed(self) ->discord.Embed:
        '''Creates an alert embed which can be sent to discord channels.'''
        embed = discord.Embed(
            title = f'New on Game Pass: {self.title}', 
            timestamp = datetime.now()
        )
        info_values = {
            'Genre': self.category,
            'Developer': self.developer,
            'Publisher': self.publisher,
            'Link': f"[Xbox.com]({self.url})"
        }
        embed.append_field(embed_listed_field('Game Info', info_values))
        embed.append_field(embed_listed_field('Description', self.description))
        embed.append_field(embed_cta())
        embed.set_image(url = self.image_url)
        return embed

class GamePassAlerts(Base):
    __tablename__ = 'gamepass_alerts'

    id = Column(Integer, primary_key = True)
    user = Column(BIGINT)
    server = Column(BIGINT)
    channel = Column(BIGINT)
    mentions = Column(JSON)    
    creation_time = Column(DateTime)

    @staticmethod
    def get_alerts(server: int) -> list:
        '''Gets all active alerts for a server.'''
        with Session() as session:
            stmt = select(GamePassAlerts).where(GamePassAlerts.server == server)
            results = session.execute(stmt).scalars().all()
        return results

    @staticmethod
    def add_alert(
        ctx: discord.ApplicationContext, 
        mentions: list[int] = None
    ) -> None:
        '''Creates an alert given a discord context.'''
        alert = GamePassAlerts(
            user = ctx.user.id,
            server = ctx.guild.id,
            channel = ctx.channel.id,
            creation_time = datetime.now(),
            mentions = mentions
        )
        with Session() as session:
            session.add(alert)
            session.commit()

#Price Tables
class PriceAlerts(Base):
    __tablename__ = 'price_alerts'

    id = Column(Integer, primary_key = True)
    user = Column(BIGINT)
    server = Column(BIGINT)
    channel = Column(BIGINT)
    mentions = Column(JSON)
    price = Column(Integer)
    game_plain = Column(Integer)    
    creation_time = Column(DateTime)

    @staticmethod
    def add_alert(
        ctx: discord.ApplicationContext,
        price: int,
        game_plain: str,
        mentions: list[int] = None
    ) -> None:
        '''Creates an alert given a discord context, ITAD game plain, and price
        setpoint. This is the primary way price alerts are recorded.'''
        alert = PriceAlerts(
            user = ctx.user.id,
            server = ctx.guild.id,
            channel = ctx.channel.id,
            price = price,
            game_plain = game_plain,
            creation_time = datetime.now(),
            mentions = mentions
        )
        with Session() as session:
            session.add(alert)
            session.commit()

class G2AData(Base):
    __tablename__ = 'g2a'

    id = Column(Integer, primary_key = True)
    g2a_id = Column(BIGINT)
    title = Column(String)
    slug = Column(String)
    minprice = Column(Float)
    region = Column(String)
    platform = Column(String)

class SteamApps(Base):
    __tablename__ = 'steam_apps'

    appid = Column(Integer, primary_key = True)
    name = Column(String)

Base.metadata.create_all(bind = engine)


#Non-table models
class PriceInfo:

    def __init__(
        self, 
        itad_overview: json, 
        steam_app_details: json, 
        appid: int, 
    ):
        #Parsing ITAD info
        self.itad_data = itad_overview
        self.current = self.itad_data.get('price', {})
        self.lowest = self.itad_data.get('lowest', {})
        self.price = self.current.get('price_formatted', 'None')
        self.price_cut = f"-{self.current.get('cut', '0')}%"
        self.price_store = self.current.get('store', 'None')
        self.price_url = self.current.get('url', 'None')
        self.lowest_price = self.lowest.get('price_formatted', 'None')
        self.lowest_cut = f"-{self.lowest.get('cut', '0')}%"
        self.lowest_store = self.lowest.get('store', 'None')
        self.lowest_url = self.lowest.get('url', 'None')

        #Parsing Steam info
        self.steam_data = steam_app_details[str(appid)]['data']
        self.game_name = self.steam_data.get('name', 'None')
        self.image = self.steam_data.get('header_image')
        self.metacritic = self.steam_data.get('metacritic', {}).get('score', 'None')

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