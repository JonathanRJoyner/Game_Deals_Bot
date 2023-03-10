import discord
import os
import topgg

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if "DEBUG_GUILD" in os.environ:
    DEBUG_GUILD = [os.getenv("DEBUG_GUILD")]
    SUPPORT_SERVER = DEBUG_GUILD
else:
    DEBUG_GUILD = None
    SUPPORT_SERVER = [os.getenv("SUPPORT_SERVER")]

intents = discord.Intents.default()
bot = discord.Bot(debug_guilds=DEBUG_GUILD, intents=intents)
bot.support_server = SUPPORT_SERVER
bot.stream_channel = os.getenv("DISCORD_STREAMING_CHANNEL")
bot.exception_channel = os.getenv("DISCORD_EXCEPTION_CHANNEL")
bot.vote_channel = os.getenv("DISCORD_VOTE_CHANNEL")
bot.server_count_channel = os.getenv("DISCORD_SERVER_COUNT_CHANNEL")
if not bot.debug_guilds:
    bot.topggpy = topgg.DBLClient(bot, os.getenv("TOPGG_TOKEN"))
    bot.topgg_webhook = topgg.WebhookManager(bot).dbl_webhook(
        "/dblwebhook", os.getenv("TOPGG_AUTH")
    )
    bot.topgg_webhook.run(8000)
