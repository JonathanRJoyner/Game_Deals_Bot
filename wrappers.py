import discord
import functools
from datetime import datetime
import traceback

from bot import bot
from alerts import server_alert_count


def command_streaming():
    """Sends command usage to a channel and exceptions to a separate channel."""

    def wrapper(func):
        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            embed = discord.Embed(title="Command Used", timestamp=datetime.now())
            details = (
                f"Command: `{func.__name__}`\n"
                f"Server: `{args[0].guild.name}`\n"
                f"Channel: `{args[0].channel.name}`\n"
                f"Member: `{args[0].author.name}`\n"
            )
            embed.add_field(name="Details", value=details, inline=False)
            choices = "\n".join([f"{key}: `{value}`" for key, value in kwargs.items()])
            if choices:
                embed.add_field(name="Choices", value=choices, inline=False)
            channel = await bot.fetch_channel(bot.stream_channel)
            try:
                await channel.send(embed=embed)
                return await func(*args, **kwargs)
            except Exception as exc:
                response = (
                    "Something went wrong. An error message was sent "
                    "to the support server."
                )
                await args[0].respond(response, ephemeral=True)
                channel = await bot.fetch_channel(bot.exception_channel)
                exc_string = f"```{traceback.format_exc()[-1500:]}```"
                await channel.send(exc_string, embed=embed)

        return wrapped

    return wrapper


def alert_check():
    def wrapper(func):
        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            
            if type(args[0]) == discord.commands.context.ApplicationContext:
                interaction = args[0]
            else:
                interaction = args[2]
            
            alert_count = server_alert_count(interaction.guild.id)
            if alert_count >= 10:
                response = (
                    "You've reached the maximum allowed alerts for this server."
                    "Please delete an alert to set a new one."
                )
                await interaction.respond(response, ephemeral = True)
                return None
            
            elif alert_count >= 5:
                if not await bot.topggpy.get_user_vote(interaction.author.id):
                    response = (
                        "You've reached the alert limit for this server. "
                        "You can increase the alert limit by [voting on Top.gg]"
                        "(https://top.gg/bot/1028073862597967932/vote)"
                    )
                    await interaction.respond(response, ephemeral = True)
                    return None

        return wrapped
    return wrapper
