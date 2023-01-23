import discord
import os

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if "DEBUG_GUILD" in os.environ:
    DEBUG_GUILD = [os.getenv("DEBUG_GUILD")]
else:
    DEBUG_GUILD = None

intents = discord.Intents.default()
bot = discord.Bot(debug_guilds=DEBUG_GUILD, intents=intents)
