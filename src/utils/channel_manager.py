import logging

import discord

from utils import constants

logger = logging.getLogger(__name__)


async def send_to_current_channel(bot: discord.Client, content: str) -> bool:
    channel = bot.get_channel(constants.CURRENT_CHANNEL_ID)
    if channel is None:
        channel = await bot.fetch_channel(constants.CURRENT_CHANNEL_ID)

    if not isinstance(channel, discord.abc.Messageable):
        logger.error("Current channel is not messageable")
        return False

    await channel.send(content)
    return True
