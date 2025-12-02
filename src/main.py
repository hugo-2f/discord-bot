import logging
import os
import asyncio

import discord
from discord.ext import commands
from dotenv import load_dotenv

import volume_manager
from constants import ROOT_DIR

# Logging config
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# Initialize bot
COMMAND_PREFIX = "!"
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=discord.Intents.all())
bot.remove_command("help")

# Initialize volumes
volume_manager.fetch_and_initialize_volumes()

# Start bot
dotenv_path = ROOT_DIR / ".env"
load_dotenv(dotenv_path)
TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN is None:
    raise RuntimeError("DISCORD_TOKEN not found in environment variables")


async def load_extensions():
    await bot.load_extension("event_handlers")
    await bot.load_extension("command_handlers")


async def main(token: str):
    async with bot:
        await load_extensions()
        await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main(TOKEN))
