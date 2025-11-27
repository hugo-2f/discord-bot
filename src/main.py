import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

import command_handlers
import event_handlers
from constants import ROOT_DIR

# Initialize bot
dotenv_path = ROOT_DIR / ".env"
load_dotenv(dotenv_path)
TOKEN = os.getenv("DISCORD_TOKEN")

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
bot.remove_command("help")  # to define custom help command

# Set events and commands
event_handlers.set_events(bot)
command_handlers.set_commands(bot)

# Start bot
if TOKEN is None:
    raise RuntimeError("DISCORD_TOKEN not found in environment variables")
bot.run(TOKEN)
