import asyncio
import json
import os
from collections import defaultdict

import discord
from discord import TextChannel
from discord.ext import commands
from dotenv import load_dotenv
from translate import Translator

import constants
import audio_handler

# ========== Setup ==========
# Initialize bot
load_dotenv()  # Load environment variables from .env file
TOKEN = os.getenv("DISCORD_TOKEN")  # Discord bot token
COMMAND_PREFIX = "!"
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=discord.Intents.all())
bot.remove_command("help")  # to define custom help command


# ========== Global variables ==========
DEFAULT_VOLUME = 0.4
TRANSLATE = True
JUAN = False
stop_playing = False

country_flags = {
    "🇺🇸": "en",
    "🇫🇷": "fr",
    "🇪🇸": "es",
    "🇯🇵": "ja",
    "🇨🇳": "zh-cn",
}


# ========== Setup bot events ==========
def set_events(bot):
    @bot.event
    async def on_ready():
        print(f"Logged in as {bot.user}")

    @bot.event
    async def on_raw_reaction_add(payload):
        user = await bot.fetch_user(payload.user_id)
        if user.bot:
            return
        channel = await bot.fetch_channel(payload.channel_id)
        if isinstance(channel, TextChannel):
            msg = await channel.fetch_message(payload.message_id)
        else:
            return

        if payload.emoji.name in country_flags and TRANSLATE:
            to_lang = country_flags[payload.emoji.name]
            print(f"Translating message to {to_lang}")
            translation = Translator(to_lang=to_lang).translate(msg.content)
            await msg.reply(translation)

    @bot.event
    async def on_voice_state_update(member, before, after):
        """
        When someone joins a channel, join them and play nihao.mp3
        """
        if member.bot or after.channel is None or before.channel == after.channel:
            return

        bot_voice_client = None
        for voice_client in bot.voice_clients:
            if (
                isinstance(voice_client, discord.VoiceClient)
                and voice_client.guild == member.guild
            ):
                bot_voice_client = voice_client
                break

        if (
            bot_voice_client and bot_voice_client.is_playing()
        ):  # wait until prev audio finishes
            await asyncio.sleep(1)

        prev_voice_channel = bot_voice_client.channel if bot_voice_client else None
        if bot_voice_client is None:
            bot_voice_client = await after.channel.connect()
        elif bot_voice_client.channel != after.channel:
            await bot_voice_client.move_to(after.channel)

        await asyncio.sleep(1.5)  # wait for them to connect to the channel
        await audio_handler.play_audio(bot_voice_client, "nihao")

        if prev_voice_channel is not None:
            await bot_voice_client.move_to(prev_voice_channel)
        else:
            await bot_voice_client.disconnect(force=True)

    @bot.event
    async def on_message(msg):
        if msg.author.bot:  # only react to humans
            return

        if msg.content.startswith(COMMAND_PREFIX):
            print(msg.content)
            command = msg.content.split()[0][len(COMMAND_PREFIX) :]
            if command in bot.all_commands:
                if (
                    any(c in command for c in ["play", "join", "leave", "stop"])
                    or command == "vol"
                    and len(msg.content.split()) > 2
                ):  # only when a volume is given
                    await msg.delete()
                await bot.process_commands(msg)
        elif JUAN:
            response = None
            if "别卷" in msg.content:
                response = "对啊就是"
            elif "卷" in msg.content:
                response = "ayayay别卷了"
            else:
                if msg.author.name == "dcm9":
                    response = "zhm别卷了来打吧"
            if response:
                await msg.reply(response)

    @bot.event
    async def on_message_delete(msg):
        # process human messages only
        if msg.author.bot:
            return

        # don't echo commands deleted by the bot
        if msg.content.startswith(bot.command_prefix):
            return
        deleted_message = f"{msg.author.display_name} just recalled:\n{msg.content}"
        await msg.channel.send(deleted_message)
