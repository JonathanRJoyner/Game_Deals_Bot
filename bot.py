import discord
import os
import topgg

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if "DEBUG_GUILD" in os.environ:
    DEBUG_GUILD = [os.getenv("DEBUG_GUILD")]
else:
    DEBUG_GUILD = None

intents = discord.Intents.default()
bot = discord.Bot(debug_guilds=DEBUG_GUILD, intents=intents)
bot.stream_channel = os.getenv("DISCORD_STREAMING_CHANNEL")
bot.exception_channel = os.getenv("DISCORD_EXCEPTION_CHANNEL")
bot.vote_channel = os.getenv("DISCORD_VOTE_CHANNEL")
bot.server_count_channel = os.getenv("DISCORD_SERVER_COUNT_CHANNEL")
bot.topggpy = topgg.DBLClient(bot, os.getenv("TOPGG_TOKEN"))
bot.topgg_webhook = topgg.WebhookManager(bot).dbl_webhook("/dblwebhook", os.getenv("TOPGG_AUTH"))
bot.topgg_webhook.run(8000)
