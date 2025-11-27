import logging
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

import command_handlers
import event_handlers
import volume_manager
from constants import ROOT_DIR

# Logging config
logging.basicConfig(
    level=logging.INFO,
    format="[惊吓魔盒] %(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# Initialize bot
COMMAND_PREFIX = "!"
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=discord.Intents.all())
bot.remove_command("help")

# Set events and commands
event_handlers.set_events(bot)
command_handlers.set_commands(bot)

# Initialize volumes
volume_manager.fetch_and_initialize_volumes()

# Start bot
dotenv_path = ROOT_DIR / ".env"
load_dotenv(dotenv_path)
TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN is None:
    raise RuntimeError("DISCORD_TOKEN not found in environment variables")
bot.run(TOKEN)
