import asyncio
from discord.ext import tasks
from sqlalchemy import select, update, delete, and_
from models import (
    Session,
    GamerPowerData,
    GiveawayAlerts,
    FreeToPlayAlerts,
    FreeToGameData,
    GamePassAlerts,
    GamePassData,
    PriceAlerts,
    LocalGiveaways,
    SteamFreeGamesCalendar,
)
from typing import Union
import traceback
from datetime import datetime
from sqlalchemy.inspection import inspect
import random

from bot import bot
from price import price_comparison, get_itad_overviews, PriceInfo
from views import VoteButton

alert_tables = [FreeToPlayAlerts, GiveawayAlerts, GamePassAlerts, PriceAlerts]


def delete_server_alerts(
    server_id: int,
    alert_type: Union[FreeToPlayAlerts, GiveawayAlerts, GamePassAlerts, PriceAlerts],
    channel: int = None,
    game_name: str = None,
    price: int = None,
) -> None:
    """Deletes all active alerts given a server id and alert table type.
    This is the primary way for users to delete active alerts."""
    if type(alert_type) == PriceAlerts:
        with Session() as session:
            stmt = delete(alert_type).where(
                (alert_type.server == server_id)
                & (alert_type.channel == channel)
                & (alert_type.like(f"{game_name}%"))
                & (alert_type.price == price)
            )
            session.execute(stmt)
            session.commit()
    else:
        with Session() as session:
            stmt = delete(alert_type).where(alert_type.server == server_id)
            session.execute(stmt)
            session.commit()


def delete_inactive_channel(channel_id: int) -> None:
    """Deletes a given channel from all of the alert tables. This is used to
    prune channels that were deleted or where bot messages are not allowed."""
    with Session() as session:
        for table in alert_tables:
            stmt = delete(table).where(table.channel == channel_id)
            session.execute(stmt)
            session.commit()


async def send_alerts(data_table, alert_table, view=None, alerts=None) -> None:
    """Takes the active alerts in the data table and sends them to the
    channels in the alert table."""
    channels = get_alert_channels(alert_table)
    if alerts == None:
        alerts = get_unalerted_rows(data_table)
    for item in alerts:
        if asyncio.iscoroutinefunction(item.alert_embed):
            embed = await item.alert_embed()
        else:
            embed = item.alert_embed()
        for channel_id in channels:
            try:
                channel = await bot.fetch_channel(channel_id)
                await channel.send(embed=embed, view=view)
            except:
                channel = await bot.fetch_channel(bot.exception_channel)
                exc_string = f"```{traceback.format_exc()[-1500:]}```"
                await channel.send(f"Send Alerts Error: {exc_string}")
                if not bot.debug_guilds:
                    delete_inactive_channel(channel_id)
        update_alert_status(data_table, item)


def get_alert_channels(table) -> list[int]:
    """Returns all channels for a given alert table."""
    with Session() as session:
        stmt = select(getattr(table, "channel")).distinct()
        channels = session.execute(stmt).scalars().all()
    return channels


def get_unalerted_rows(table) -> list:
    """Gets all un-alerted items in the chosen table.
    This is used to send alerts to channels."""
    with Session() as session:
        stmt = select(table).where(getattr(table, "alerted") == False)
        alerts = session.execute(stmt).scalars().all()
    return alerts


def update_alert_status(table, item) -> None:
    """Changes the alert status to True for a given row.
    This is used after sending alerts."""
    with Session() as session:
        stmt = update(table).values(alerted=True).where(table.id == item.id)
        print(stmt)
        session.execute(stmt)
        session.commit()


async def send_price_alert(alert: PriceAlerts, overviews: dict) -> None:
    embed = PriceInfo.alert_embed(alert, overviews[alert.game_plain])
    channel = await bot.fetch_channel(alert.channel)
    await channel.send(embed=embed)


@tasks.loop(hours=2)
async def steam_free_release_alert():
    """Gets all free games released since the last run and sends
    alerts to the free game alerts channels."""

    with Session() as session:
        new_releases = select(SteamFreeGamesCalendar)
        new_releases = new_releases.where(
            and_(
                SteamFreeGamesCalendar.release_date < datetime.now(),
                SteamFreeGamesCalendar.alerted == False,
            )
        )
        alerts = session.execute(new_releases).scalars().all()
        await send_alerts(SteamFreeGamesCalendar, FreeToPlayAlerts, alerts=alerts)


@tasks.loop(hours=4)
async def price_alert():
    with Session() as session:
        alerts = session.execute(select(PriceAlerts)).scalars().all()
    plains = list(set([alert.game_plain for alert in alerts]))
    overviews = await get_itad_overviews(plains)
    for item in alerts:
        if price_comparison(item, overviews):
            await send_price_alert(item, overviews)
            await PriceAlerts.delete_alert(item)
        else:
            continue


@tasks.loop(minutes=30)
async def gamerpower_alert() -> None:
    await send_alerts(GamerPowerData, GiveawayAlerts)


@tasks.loop(minutes=30)
async def freetogame_alert() -> None:
    await send_alerts(FreeToGameData, FreeToPlayAlerts)


@tasks.loop(minutes=30)
async def gamepass_alert() -> None:
    await send_alerts(GamePassData, GamePassAlerts)


@tasks.loop(minutes=30)
async def local_giveaway_alert() -> None:
    await send_alerts(LocalGiveaways, GiveawayAlerts, view=VoteButton())


@tasks.loop(minutes=30)
async def update_server_count():
    try:
        await bot.topggpy.post_guild_count()
        channel = await bot.fetch_channel(bot.server_count_channel)
        await channel.edit(name=f"SERVER COUNT: {len(bot.guilds)}")
    except:
        exc_string = f"```{traceback.format_exc()[-1500:]}```"
        channel = await bot.fetch_channel(bot.exception_channel)
        await channel.send(exc_string)

@tasks.loop(minutes = 30)
async def update_local_giveaways():
    with Session() as session:
        stmt = select(LocalGiveaways).where(
            and_(LocalGiveaways.end_time <= datetime.now(), 
                 LocalGiveaways.winner == None)
        )
        giveaway = session.execute(stmt).scalars().all()
        giveaway = giveaway[0]
    votes = await bot.topggpy.get_bot_votes()
    voter_ids = [voter['id'] for voter in votes]
    winner = random.choice(voter_ids)
    try:
        user = await bot.get_or_fetch_user(winner)
        message = (
            "Thanks for voting! You've won our giveaway!\n"
            f"Steam key: {giveaway.key}"
        )
        await user.send(message, embed = await giveaway.alert_embed())
        with Session() as session:
            stmt = update(LocalGiveaways).where(LocalGiveaways.id == giveaway.id).values(winner = winner)
            session.execute(stmt)
            session.commit()
    except:
        channel = await bot.fetch_channel(bot.exception_channel)
        exc_string = f"```{traceback.format_exc()[-1500:]}```"
        await channel.send(f'Giveaway error:\n{exc_string}')

