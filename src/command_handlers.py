import asyncio
import configparser
import logging

import discord
from discord.ext import commands

import audio_playback_handler
import constants
import volume_manager

logger = logging.getLogger(__name__)
CONFIG_PATH = constants.ROOT_DIR / "variables.ini"
config = configparser.ConfigParser()
config.read(CONFIG_PATH)
USER_IDS = {key: int(value) for key, value in config["USER_IDS"].items()}
CHANNEL_IDS = {key: int(value) for key, value in config["CHANNEL_IDS"].items()}
channel_name = config["SETTINGS"]["channel_name"]

command_lock = asyncio.Lock()


def set_commands(bot: commands.Bot) -> None:
    """
    Register all command handlers for the bot.
    Args:
        bot: The Discord bot instance.
    """

    @bot.command()
    async def play(
        ctx: commands.Context, audio_name: str, channel: str | None = None
    ) -> None:
        """
        Play an audio file in a voice channel.
        Args:
            ctx: The command context.
            audio_name: The name of the audio to play.
            channel: Optional voice channel to join.
        """
        async with command_lock:
            if ctx.author.bot or not audio_playback_handler.audio_exists(audio_name):
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

    @bot.command()
    async def replay(
        ctx: commands.Context, audio_name: str | None = None, count: int = 0
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
                or audio_name not in constants.AUDIO_NAMES_SET
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

    @bot.command()
    async def join(ctx: commands.Context, channel: str | None = None) -> None:
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

    @bot.command()
    async def vol(ctx, audio_name: str, volume: float | None = None):
        if not audio_playback_handler.audio_exists(audio_name):
            await ctx.reply(f"Audio '{audio_name}' not found.")
            return
        if volume is None:
            current_volume = volume_manager.get_volume(audio_name)
            await ctx.reply(f"Current volume: {current_volume}")
        elif 0 <= volume <= 1:
            volume_manager.set_volume(audio_name, volume)
            logger.info(f'"{audio_name}" now has volume {volume}')

    @bot.command()
    async def audios(ctx: commands.Context) -> None:
        """List all available audio files."""
        await ctx.reply(constants.AUDIO_LIST)

    @bot.command()
    async def help(ctx: commands.Context) -> None:
        """Show help message."""
        await ctx.reply(
            "Commands: play <name/id> (channel), stop_playing, join, leave, audios, vol <name> <volume>"
        )

    @bot.command()
    async def leave(ctx):
        # check if the bot is in a voice channel
        if ctx.author.bot or not ctx.voice_client:
            print("Bot is not currently in a voice channel.")
            return

        # disconnect the bot from the current voice channel
        if isinstance(ctx.voice_client, discord.VoiceClient):
            await ctx.voice_client.disconnect()

    @bot.command()
    async def stop(ctx):
        audio_playback_handler.set_stop_playing()

    @bot.command()
    async def send(ctx, *, msg: str):
        """
        Command format: !send <msg> <people to mention separated by spaces>
        Sends msg and mentions user if not None
        Prints people that can be mentioned if msg is None

        See variables.ini for users
        Ex:
            !send asdf -> send 'asdf' in current channel
            !send asdf fsg -> send '@fsg asdf'
            !send asdf fsg, gaj -> send '@fsg @gaj asdf'
        """
        if not msg:
            await ctx.reply(str(set(USER_IDS.keys())))
            return

        channel = bot.get_channel(CHANNEL_IDS[channel_name])
        if not isinstance(channel, (discord.TextChannel, discord.DMChannel)):
            logger.error("Invalid channel")
            return

        users = None
        if "," in msg:
            msg, users = msg.rsplit(",", 1)

        if not users:
            await channel.send(f"{msg}")
            return

        users_to_mention = []
        for username in users.split():
            user_obj = await bot.fetch_user(USER_IDS[username])
            users_to_mention.append(user_obj.mention)
        await channel.send(f"{' '.join(users_to_mention)} {msg}")

    @bot.command()
    async def send_dm(ctx: commands.Context, *, msg: str) -> None:
        """
        Send a DM to a user.
        Format: !send_dm <msg>, <user>
        """
        if "," not in msg:
            logger.warning("No user selected")
            return
        msg, user = msg.rsplit(",", 1)
        user = user.strip().lower()
        if user not in USER_IDS:
            logger.warning(f"User {user} not found")
            return

        try:
            user_obj = bot.get_user(USER_IDS[user])
            if user_obj:
                await user_obj.send(msg)
            else:
                logger.warning(f"User object for {user} not found")
        except AttributeError as e:
            logger.error(
                "Likely error: the bot can only send to users that have shared a server with the bot"
            )
            logger.error(e)
        except Exception as e:
            logger.error(e)

    @bot.command()
    async def setChannel(ctx: commands.Context, new_channel: str) -> None:
        """
        Set the channel for the !send command.
        Args:
            ctx: The command context.
            new_channel: The name of the new channel.
        """
        global channel_name
        channel_name = new_channel
        logger.info(f"Current channel: {channel_name} - {CHANNEL_IDS[channel_name]}")
