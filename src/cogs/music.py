import asyncio
import logging

import discord
from discord.ext import commands

from utils import audio_playback_handler, constants, volume_manager

logger = logging.getLogger(__name__)
command_lock = asyncio.Lock()


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def play(
        self, ctx: commands.Context, audio_name: str, channel: str | None = None
    ) -> None:
        """
        Play an audio file in a voice channel.
        Args:
            ctx: The command context.
            audio_name: The name of the audio to play.
            channel: Optional voice channel to join.
        """
        async with command_lock:
            if ctx.author.bot or not audio_playback_handler.resolve_audio_name(
                audio_name
            ):
                return

            # execute command after current audio finishes
            if (
                isinstance(ctx.voice_client, discord.VoiceClient)
                and ctx.voice_client.is_playing()
            ):
                await asyncio.sleep(1)

            author = ctx.author
            if isinstance(author, discord.Member) and author.voice:
                author_voice_channel = author.voice.channel
            else:
                author_voice_channel = None

            if channel:
                if not ctx.guild:
                    return
                voice_channel = discord.utils.get(
                    ctx.guild.voice_channels, name=channel
                )
            else:
                voice_channel = (
                    ctx.voice_client.channel
                    if isinstance(ctx.voice_client, discord.VoiceClient)
                    else author_voice_channel
                )

            if voice_channel is None:
                return

            # go back (or leave) to previous channel after playing audio
            bot_voice_client = ctx.voice_client
            if isinstance(bot_voice_client, discord.VoiceClient):
                prev_voice_channel = bot_voice_client.channel
            else:
                prev_voice_channel = None

            if (
                isinstance(bot_voice_client, discord.VoiceClient)
                and bot_voice_client.channel != voice_channel
            ):
                await bot_voice_client.move_to(voice_channel)
            elif not bot_voice_client:
                bot_voice_client = await voice_channel.connect()

            if isinstance(bot_voice_client, discord.VoiceClient):
                await audio_playback_handler.play_audio(bot_voice_client, audio_name)

                if prev_voice_channel is not None:
                    await bot_voice_client.move_to(prev_voice_channel)
                else:
                    await bot_voice_client.disconnect()

    @commands.command()
    async def replay(
        self, ctx: commands.Context, audio_name: str | None = None, count: int = 0
    ) -> None:
        """
        Replay an audio file multiple times.
        Args:
            ctx: The command context.
            audio_name: The name of the audio to replay.
            count: The number of times to replay.
        """
        if count == 0:
            return

        async with command_lock:
            if (
                ctx.author.bot
                or not audio_name
                or not audio_playback_handler.resolve_audio_name(audio_name)
            ):
                return
            # execute command after current audio finishes
            if (
                isinstance(ctx.voice_client, discord.VoiceClient)
                and ctx.voice_client.is_playing()
            ):
                await asyncio.sleep(1)

            author = ctx.author
            if isinstance(author, discord.Member) and author.voice:
                author_voice_channel = author.voice.channel
            else:
                author_voice_channel = None

            voice_channel = (
                ctx.voice_client.channel
                if isinstance(ctx.voice_client, discord.VoiceClient)
                else author_voice_channel
            )

            if voice_channel is None:
                return

            # go back (or leave) to previous channel after playing audio
            bot_voice_client = ctx.voice_client
            if isinstance(bot_voice_client, discord.VoiceClient):
                prev_voice_channel = bot_voice_client.channel
            else:
                prev_voice_channel = None

            if (
                isinstance(bot_voice_client, discord.VoiceClient)
                and bot_voice_client.channel != voice_channel
            ):
                await bot_voice_client.move_to(voice_channel)
            elif not bot_voice_client:
                bot_voice_client = await voice_channel.connect()

            try:
                if isinstance(bot_voice_client, discord.VoiceClient):
                    for _ in range(count):
                        keep_playing = await audio_playback_handler.play_audio(
                            bot_voice_client, audio_name
                        )
                        if not keep_playing:
                            logger.info("Replay stopped")
                            break
            finally:
                # Move back to previous channel or disconnect
                if isinstance(bot_voice_client, discord.VoiceClient):
                    if prev_voice_channel is not None:
                        await bot_voice_client.move_to(prev_voice_channel)
                    else:
                        await bot_voice_client.disconnect()

    @commands.command()
    async def join(self, ctx: commands.Context, channel: str | None = None) -> None:
        """
        Join a voice channel.
        Args:
            ctx: The command context.
            channel: Optional name of the channel to join.
        """
        if channel:
            if not ctx.guild:
                return
            voice_channel = discord.utils.get(ctx.guild.voice_channels, name=channel)

            if voice_channel is None:  # not a valid channel
                return
        else:
            author = ctx.author
            if isinstance(author, discord.Member) and author.voice:
                voice_channel = author.voice.channel
            else:
                voice_channel = None

            if voice_channel is None:
                return  # no channel and author not in a channel
        # check if the bot is already in a voice channel
        voice_client = ctx.voice_client
        if isinstance(voice_client, discord.VoiceClient):
            # if the bot is already in the specified voice channel, do nothing
            if voice_client.channel == voice_channel:
                return
            # if the bot is in a different voice channel, move it to the specified channel
            else:
                await voice_client.move_to(voice_channel)
        # if the bot is not in a voice channel, join the specified channel
        else:
            await voice_channel.connect()

    @commands.command()
    async def vol(self, ctx, audio_name: str, volume: float | None = None):
        resolved_name = audio_playback_handler.resolve_audio_name(audio_name)
        if not resolved_name:
            await ctx.reply(f"Audio '{audio_name}' not found.")
            return
        if volume is None:
            current_volume = volume_manager.get_volume(resolved_name)
            await ctx.reply(f"Current volume: {current_volume}")
        elif 0 <= volume <= 1:
            volume_manager.set_volume(resolved_name, volume)
            logger.info(f'"{resolved_name}" now has volume {volume}')

    @commands.command()
    async def audios(self, ctx: commands.Context) -> None:
        """List all available audio files."""
        await ctx.reply(constants.AUDIO_LIST)

    @commands.command()
    async def leave(self, ctx):
        # check if the bot is in a voice channel
        if ctx.author.bot or not ctx.voice_client:
            print("Bot is not currently in a voice channel.")
            return

        # disconnect the bot from the current voice channel
        if isinstance(ctx.voice_client, discord.VoiceClient):
            await ctx.voice_client.disconnect()

    @commands.command()
    async def stop(self, ctx):
        audio_playback_handler.set_stop_playing()

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


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Music(bot))
