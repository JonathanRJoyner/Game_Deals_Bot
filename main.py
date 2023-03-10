import discord
from discord.commands import option
from discord.ext import commands
from datetime import datetime
from discord.ext import pages

from wrappers import command_streaming
from price import game_autocomplete_options, price_lookup_response
from bot import bot, DISCORD_TOKEN
from alerts import (
    freetogame_alert,
    gamerpower_alert,
    gamepass_alert,
    delete_server_alerts,
    price_alert,
    update_server_count,
    local_giveaway_alert,
    steam_free_release_alert,
    update_local_giveaways,
    alert_check,
)
from models import (
    GiveawayAlerts,
    FreeToPlayAlerts,
    GamePassAlerts,
    PriceAlerts,
    Logs,
    LocalGiveaways,
    UpcomingSteamSales,
)

alert_tasks = [
    freetogame_alert,
    gamerpower_alert,
    gamepass_alert,
    price_alert,
    update_server_count,
    local_giveaway_alert,
    steam_free_release_alert,
    update_local_giveaways,
]


@bot.event
async def on_ready():
    for task in alert_tasks:
        task.start()


create = discord.SlashCommandGroup("create", "Alert creation commands")


@create.command()
@command_streaming()
async def giveaway_alert(ctx: discord.ApplicationContext):
    """Create a Giveaway alert."""
    await ctx.response.defer()
    response = await alert_check(ctx.guild.id, ctx.author.id)
    if response == True:
        GiveawayAlerts.add_alert(ctx)
        await ctx.respond("Giveaway alert created.")
    else:
        await ctx.respond(response, ephemeral = True)


@create.command()
@command_streaming()
async def f2p_alert(ctx: discord.ApplicationContext):
    """Create a free to play alert."""
    await ctx.response.defer()
    response = await alert_check(ctx.guild.id, ctx.author.id)
    if response == True:
        FreeToPlayAlerts.add_alert(ctx)
        await ctx.respond("Free to play alert created.")
    else:
        await ctx.respond(response, ephemeral = True)


@create.command()
@command_streaming()
async def game_pass_alert(ctx: discord.ApplicationContext):
    """Create a Xbox Game Pass alert."""
    await ctx.response.defer()
    response = await alert_check(ctx.guild.id, ctx.author.id)
    if response == True:
        GamePassAlerts.add_alert(ctx)
        await ctx.respond("Game Pass alert created.")
    else:
        await ctx.respond(response, ephemeral = True)


@create.command()
@discord.option(
    name="game_name",
    autocomplete=game_autocomplete_options,
    description="Choose a game title.",
)
@command_streaming()
async def price_alert(ctx: discord.ApplicationContext, game_name):
    """Create a game price alert."""
    await price_lookup_response(ctx, game_name)


@bot.slash_command()
@discord.option(
    name="game_name",
    autocomplete=game_autocomplete_options,
    description="Choose a game title.",
)
@command_streaming()
async def price_lookup(ctx: discord.ApplicationContext, game_name):
    """Look up a game price."""
    await price_lookup_response(ctx, game_name)


@bot.slash_command(guild_ids=bot.support_server)
@commands.is_owner()
@command_streaming()
async def check_logs(ctx: discord.ApplicationContext):
    await ctx.respond(Logs.latest_str(), ephemeral=True)


@bot.slash_command(guild_ids=bot.support_server)
@commands.is_owner()
@discord.option(
    name="app_id",
    description="Input a steam app id",
)
@discord.option(name="Key", description="Key for the game")
async def giveaway_creation(ctx: discord.ApplicationContext, app_id: str, key: str):
    LocalGiveaways.add_giveaway(app_id, key)
    await ctx.respond("Giveaway Created", ephemeral=True)


@bot.slash_command()
@option(
    "type",
    description="Remove active alerts.",
    choices=[
        "Delete Free to Play Alerts",
        "Delete Game Pass Alerts",
        "Delete Giveaway Alerts",
        "Delete Price Alert",
    ],
)
@command_streaming()
async def delete_alerts(ctx: discord.ApplicationContext, type: str):
    """Delete active alerts in your server."""
    if "Giveaway" in type:
        delete_server_alerts(ctx.guild.id, GiveawayAlerts)
        await ctx.respond(f"All Giveaway Alerts deleted.")
    elif "Game Pass" in type:
        delete_server_alerts(ctx.guild.id, GamePassAlerts)
        await ctx.respond(f"All Game Pass Alerts deleted.")
    elif "Free to Play" in type:
        delete_server_alerts(ctx.guild.id, FreeToPlayAlerts)
        await ctx.respond(f"All Free to Play Alerts deleted.")
    elif "Price" in type:
        await PriceAlerts.delete_alert_dropdown(ctx)
    else:
        await ctx.followup.send("There was an error. Check the support server.")


def alert_channel_str(alerts: list) -> str:
    """Creates a formatted strings for alerts. Used to send to embed fields."""
    if type(alerts[0]) == PriceAlerts:
        alert_channels = [
            f"<#{alert.channel}>: `{alert.game_name} under ${alert.price}`"
            for alert in alerts
        ]
    else:
        alert_channels = [f"<#{alert.channel}>" for alert in alerts]
    return "\n".join(alert_channels)


@bot.slash_command()
@command_streaming()
async def check_alerts(ctx: discord.ApplicationContext):
    """See all active alerts on your server."""
    alert_names = [
        (GiveawayAlerts, "__Giveaway Alerts__"),
        (FreeToPlayAlerts, "__Free to Play Alerts__"),
        (GamePassAlerts, "__Game Pass Alerts__"),
        (PriceAlerts, "__Price Alerts__"),
    ]
    await ctx.response.defer()
    embed = discord.Embed(title=f"Server Alerts: {ctx.guild.name}")
    for item in alert_names:
        alerts = item[0].get_alerts(ctx.guild.id)
        if alerts:
            embed.add_field(name=item[1], value=alert_channel_str(alerts), inline=False)
    await ctx.respond(embed=embed)


@bot.slash_command()
@command_streaming()
async def upcoming_steam_sales(ctx: discord.ApplicationContext):
    """See all upcoming steam sales."""
    paginator = pages.Paginator(pages=await UpcomingSteamSales.all_sales_embeds())
    await paginator.respond(ctx.interaction, ephemeral=False)


@bot.event
async def on_dbl_vote(data) -> None:
    """Sends a message to the votes channel when a user votes on the bot."""

    embed = discord.Embed(title=f"Thanks for the Vote!????", timestamp=datetime.now())
    channel = await bot.fetch_channel(bot.vote_channel)
    user = await bot.get_or_fetch_user(int(data["user"]))
    if user.avatar and user.name:
        embed.set_author(name=user.name, icon_url=user.avatar.url)
    user_info = f"User: <@{user.id}>\n" "Server: None"
    embed.add_field(name="User Info", value=user_info)
    await channel.send(embed=embed)


bot.add_application_command(create)
bot.run(DISCORD_TOKEN)
