import asyncio
import logging

import discord
from discord.ext import commands
from translate import Translator

import audio_playback_handler
import constants

logger = logging.getLogger(__name__)


class EventHandlers(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """Log when the bot is ready."""
        logger.info(f"Logged in as {self.bot.user}")

    @commands.Cog.listener()
    async def on_raw_reaction_add(
        self, payload: discord.RawReactionActionEvent
    ) -> None:
        """
        Translate a message when a country flag reaction is added.
        Args:
            payload: The raw reaction event payload.
        """
        user = await self.bot.fetch_user(payload.user_id)
        if user.bot:
            return
        channel = await self.bot.fetch_channel(payload.channel_id)
        if isinstance(channel, discord.TextChannel):
            msg = await channel.fetch_message(payload.message_id)
        else:
            return

        if payload.emoji.name in constants.COUNTRY_FLAGS:
            to_lang = constants.COUNTRY_FLAGS[payload.emoji.name]
            logger.info(f"Translating '{msg.content}' to {to_lang}")
            translation = Translator(to_lang=to_lang).translate(msg.content)
            await msg.reply(translation)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        """
        When someone joins a channel, join them and play nihao.mp3.
        """
        if member.bot or after.channel is None or before.channel == after.channel:
            return

        bot_voice_client: discord.VoiceClient | None = None
        for voice_client in self.bot.voice_clients:
            if (
                isinstance(voice_client, discord.VoiceClient)
                and voice_client.guild == member.guild
            ):
                bot_voice_client = voice_client
                break

        if bot_voice_client and bot_voice_client.is_playing():
            await asyncio.sleep(1)

        prev_voice_channel = bot_voice_client.channel if bot_voice_client else None
        if bot_voice_client is None:
            bot_voice_client = await after.channel.connect()
        elif bot_voice_client.channel != after.channel:
            await bot_voice_client.move_to(after.channel)

        await asyncio.sleep(1.5)  # wait for user to connect to voice channel
        await audio_playback_handler.play_audio(bot_voice_client, "nihao")

        if prev_voice_channel is not None:
            await bot_voice_client.move_to(prev_voice_channel)
        else:
            await bot_voice_client.disconnect(force=True)

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message) -> None:
        """
        Handle incoming messages, process commands, and respond to certain keywords.
        Args:
            msg: The message object.
        """
        if msg.author.bot:
            return

        ctx = await self.bot.get_context(msg)
        if ctx.valid:
            logger.info(f"Command received: {msg.content}")
            if ctx.command:
                command_name = ctx.command.name
                if command_name in ["play", "join", "leave", "stop"]:
                    await msg.delete()
                elif (
                    command_name == "vol" and len(msg.content.split()) > 2
                ):  # delete message if '!vol audio_name value'
                    await msg.delete()

    @commands.Cog.listener()
    async def on_message_delete(self, msg: discord.Message) -> None:
        """
        Echo deleted messages, except for bot commands.
        Args:
            msg: The deleted message object.
        """
        if msg.author.bot:
            return

        ctx = await self.bot.get_context(msg)
        if ctx.valid:
            return

        deleted_message = f"{msg.author.display_name} just recalled:\n{msg.content}"
        await msg.channel.send(deleted_message)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(EventHandlers(bot))
