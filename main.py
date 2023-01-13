from models import GiveawayAlerts, FreeToPlayAlerts, GamePassAlerts, PriceAlerts, Session
import discord
from discord.commands import option
from alerts import freetogame_alert, gamerpower_alert, gamepass_alert, delete_server_alerts
from price import PriceAlertDropdown
from bot import bot, DISCORD_TOKEN


alert_tasks = [
    #freetogame_alert,
    #gamerpower_alert,
    #gamepass_alert
]

@bot.event
async def on_ready():
    for task in alert_tasks:
        task.start()

create = discord.SlashCommandGroup('create', 'Alert creation commands')

@create.command()
async def giveaway_alert(ctx: discord.ApplicationContext):
    '''Create a Giveaway alert.'''
    GiveawayAlerts.add_alert(ctx)
    await ctx.respond('Giveaway alert created.')

@create.command()
async def f2p_alert(ctx: discord.ApplicationContext):
    '''Create a free to play alert.'''
    FreeToPlayAlerts.add_alert(ctx)
    await ctx.respond('Free to play alert created.') 

@create.command()
async def game_pass_alert(ctx: discord.ApplicationContext):
    '''Create a Xbox Game Pass alert.'''
    GamePassAlerts.add_alert(ctx)
    await ctx.respond('Game Pass alert created.')    

@bot.slash_command()
@option(
    'type',
    description = 'Remove active alerts.',    
    choices = [
        'Delete Free to Play Alerts', 
        'Delete Game Pass Alerts',
        'Delete Giveaway Alerts',
        'Delete Price Alert'
    ]
)
async def delete_alerts(ctx: discord.ApplicationContext, type: str):
    '''Delete active alerts in your server.'''
    if 'Giveaway' in type:
        delete_server_alerts(ctx.guild.id, GiveawayAlerts)
        await ctx.respond(f'All Giveaway Alerts deleted.')
    elif 'Game Pass' in type:
        delete_server_alerts(ctx.guild.id, GamePassAlerts)
        await ctx.respond(f'All Game Pass Alerts deleted.')
    elif 'Free to Play' in type:
        delete_server_alerts(ctx.guild.id, FreeToPlayAlerts)
        await ctx.respond(f'All Free to Play Alerts deleted.')
    elif 'Price' in type:
        dropdown = PriceAlertDropdown(PriceAlerts.get_alerts(ctx.guild.id))
        view = discord.ui.View(dropdown)
        await ctx.respond(view = view)
    else:
        await ctx.followup.send('There was an error. Check the support server.')

def alert_channel_str(alerts: list) -> str:
    '''Creates a formatted strings for alerts. Used to send to embed fields.'''
    if type(alerts[0]) == PriceAlerts:
        alert_channels = [f'<#{alert.channel}>: `{alert.game_name} under ${alert.price}`' for alert in alerts]
    else:
        alert_channels = [f'<#{alert.channel}>' for alert in alerts]
    return '\n'.join(alert_channels)

@bot.slash_command()
async def check_alerts(ctx: discord.ApplicationContext):
    '''See all active alerts on your server.'''
    alert_names = [
        (GiveawayAlerts, '__Giveaway Alerts__'),
        (FreeToPlayAlerts, '__Free to Play Alerts__'),
        (GamePassAlerts, '__Game Pass Alerts__'),
        (PriceAlerts, '__Price Alerts__'),
    ]    
    await ctx.response.defer()
    embed = discord.Embed(title = f'Server Alerts: {ctx.guild.name}')
    for item in alert_names:
        alerts = item[0].get_alerts(ctx.guild.id)
        if alerts:
            embed.add_field(
                name = item[1], 
                value = alert_channel_str(alerts), 
                inline = False
            )
    await ctx.respond(embed = embed)

bot.load_extension('price')
bot.add_application_command(create)
bot.run(DISCORD_TOKEN)