from discord.ext import tasks
from sqlalchemy import select, update, delete
from models import (
    Session,
    GamerPowerData,
    GiveawayAlerts,
    FreeToPlayAlerts,
    FreeToGameData,
    GamePassAlerts,
    GamePassData,
    PriceAlerts,
)
from typing import Union

from bot import bot
from price import price_comparison, get_itad_overviews, PriceInfo

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


async def send_alerts(data_table, alert_table) -> None:
    """Takes the active alerts in the data table and sends them to the
    channels in the alert table."""
    channels = get_alert_channels(alert_table)
    alerts = get_unalerted_rows(data_table)
    for item in alerts:
        embed = item.alert_embed()
        for channel_id in channels:
            try:
                channel = await bot.fetch_channel(channel_id)
                await channel.send(embed=embed)
            except Exception as exc:
                print(exc)
                delete_inactive_channel(channel_id)
    update_alert_status(data_table)


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


def update_alert_status(table) -> None:
    """Changes all alerted statuses to True.
    This is used after sending alerts."""
    with Session() as session:
        stmt = update(table).values(alerted=True)
        session.execute(stmt)
        session.commit()


async def send_price_alert(alert: PriceAlerts, overviews: dict) -> None:
    embed = PriceInfo.alert_embed(alert, overviews[alert.game_plain])
    channel = await bot.fetch_channel(alert.channel)
    await channel.send(embed=embed)


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
