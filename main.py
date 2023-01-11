from models import GiveawayAlerts, FreeToPlayAlerts, GamePassAlerts
import discord
from discord.commands import option
from alerts import freetogame_alert, gamerpower_alert, gamepass_alert, delete_server_alerts
from bot import bot, DISCORD_TOKEN


alert_tasks = [
    freetogame_alert,
    gamerpower_alert,
    gamepass_alert
]

@bot.event
async def on_ready():
    for task in alert_tasks:
        task.start()

giveaway = discord.SlashCommandGroup('giveaway', 'Giveaway commands')
freetoplay = discord.SlashCommandGroup('free_to_play', 'Free to play commands')
gamepass = discord.SlashCommandGroup('gamepass', 'Xbox Game Pass commands')

@giveaway.command()
async def alert(ctx: discord.ApplicationContext):
    '''Create a Giveaway alert.'''
    await ctx.respond('Giveaway alert created.')
    GiveawayAlerts.add_alert(ctx)

@freetoplay.command()
async def alert(ctx: discord.ApplicationContext):
    '''Create a free to play alert.'''
    await ctx.respond('Free to play alert created.') 
    FreeToPlayAlerts.add_alert(ctx)

@gamepass.command()
async def alert(ctx: discord.ApplicationContext):
    '''Create a Xbox Game Pass alert.'''
    await ctx.respond('Game Pass alert created.')    
    GamePassAlerts.add_alert(ctx)

@bot.slash_command()
@option(
    'type',
    description = 'Remove active alerts.',    
    choices = [
        'Delete Free to Play Alerts', 
        'Delete Game Pass Alerts',
        'Delete Giveaway Alerts'
    ]
)
async def delete_alert(ctx: discord.ApplicationContext, type: str):
    '''Delete active alerts in your server.'''
    await ctx.respond(f'All {type} deleted.')
    if 'Giveaway' in type:
        delete_server_alerts(ctx.guild.id, GiveawayAlerts)
    elif 'Game Pass' in type:
        delete_server_alerts(ctx.guild.id, GamePassAlerts)
    elif 'Free to Play' in type:
        delete_server_alerts(ctx.guild.id, FreeToPlayAlerts)
    else:
        await ctx.followup.send('There was an error. Check the support server.')

bot.load_extension('price')
bot.add_application_command(giveaway)
bot.add_application_command(freetoplay)
bot.add_application_command(gamepass)
bot.run(DISCORD_TOKEN)