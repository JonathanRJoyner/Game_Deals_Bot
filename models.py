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
    game_plain = Column(String)
    game_name = Column(String)
    image_url = Column(String)    
    creation_time = Column(DateTime)

    @staticmethod
    def get_alerts(server: int) -> list:
        '''Gets all active alerts for a server.'''
        with Session() as session:
            stmt = select(PriceAlerts).where(PriceAlerts.server == server)
            results = session.execute(stmt).scalars().all()
        return results

    @staticmethod
    def add_alert(
        ctx: discord.Interaction,
        game_name: str,
        image_url: str,
        price: int,
        game_plain: str,
        mentions: list[int] = None
    ) -> None:
        '''Creates an alert given a discord context, ITAD game plain, and price
        setpoint. This is the primary way price alerts are recorded.'''
        alert = PriceAlerts(
            user = ctx.user.id,
            server = ctx.guild.id,
            channel = ctx.channel_id,
            price = price,
            game_name = game_name,
            image_url = image_url,
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