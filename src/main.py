import asyncio
import logging
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from utils import channel_manager, volume_manager
from utils.constants import ROOT_DIR

# Logging config
logger = logging.getLogger(__name__)
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
    cogs_dir = ROOT_DIR / "src" / "cogs"
    for filename in os.listdir(cogs_dir):
        if filename.endswith(".py") and filename != "__init__.py":
            await bot.load_extension(f"cogs.{filename[:-3]}")


async def terminal_commands() -> None:
    await bot.wait_until_ready()

    while not bot.is_closed():
        command = await asyncio.to_thread(input, "bot> ")

        if command.startswith("send_emoji "):
            emoji_name = command.removeprefix("send_emoji ").strip()
            emojis = await bot.fetch_application_emojis()
            emoji = discord.utils.get(emojis, name=emoji_name)

            if emoji is None:
                logger.warning("Application emoji not found: %s", emoji_name)
            else:
                await channel_manager.send_to_current_channel(bot, str(emoji))
            continue

        if not command.startswith("send "):
            logger.warning(
                "Unknown terminal command. Use 'send <message>', "
                "or 'send_emoji <name>'."
            )
            continue

        message = command.removeprefix("send").strip()
        await channel_manager.send_to_current_channel(bot, message)


async def main(token: str):
    terminal_task = None
    try:
        await load_extensions()
        terminal_task = asyncio.create_task(terminal_commands())
        await bot.start(token)
    finally:
        if not bot.is_closed():
            await bot.close()
        if terminal_task is not None:
            terminal_task.cancel()
            await asyncio.gather(terminal_task, return_exceptions=True)


if __name__ == "__main__":
    try:
        asyncio.run(main(TOKEN))
    except KeyboardInterrupt:
        logger.info("Bot stopped")
