import logging
import tomllib

import discord
from discord.ext import commands
from translate import Translator

from utils import channel_manager, constants

logger = logging.getLogger(__name__)
CONFIG_PATH = constants.ROOT_DIR / "variables.toml"
with open(CONFIG_PATH, "rb") as f:
    config = tomllib.load(f)
USER_IDS = config["USER_IDS"]
CHANNEL_IDS = config["CHANNEL_IDS"]
constants.CURRENT_CHANNEL_ID = CHANNEL_IDS[config["SETTINGS"]["default_channel"]]


class General(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx: commands.Context) -> None:
        """Show help message."""
        await ctx.reply(
            "Commands: play <name/id> (channel), stop_playing, join, leave, audios, vol <name> <volume>, send_emoji <name>"
        )

    @commands.command()
    async def send(self, ctx, *, msg: str | None = None) -> None:
        """
        Send a message, optionally mentioning configured users.

        Formats:
            !send <message>
            !send <message> --to <username> [<username> ...]

        Prints people that can be mentioned if msg is None

        See variables.toml for users
        Ex:
            !send -> reply with list of users
            !send asdf -> send 'asdf' in current channel
            !send asdf --to fsg -> send '@fsg asdf'
            !send asdf --to fsg gaj -> send '@fsg @gaj asdf'
        """
        if not msg:
            await ctx.reply(", ".join(USER_IDS.keys()))
            return

        message, separator, users_text = msg.partition("--to")
        message = message.strip()
        if not message:
            await ctx.reply("Please provide a message to send.")
            return

        if not separator:
            await channel_manager.send_to_current_channel(self.bot, message)
            return

        users_to_mention = []
        for username in users_text.split():
            user_id = USER_IDS.get(username.lower())
            if user_id is None:
                await ctx.reply(f"Unknown user '{username}'.")
                return
            user_obj = await self.bot.fetch_user(user_id)
            users_to_mention.append(user_obj.mention)
        await channel_manager.send_to_current_channel(
            self.bot, f"{' '.join(users_to_mention)} {message}"
        )

    @commands.command()
    async def send_emoji(self, ctx: commands.Context, emoji_name: str) -> None:
        """Send an application emoji by name to the current channel."""
        emojis = await self.bot.fetch_application_emojis()
        emoji = next((item for item in emojis if item.name == emoji_name), None)
        if emoji is None:
            await ctx.reply(f"Application emoji '{emoji_name}' not found.")
            return

        if await channel_manager.send_to_current_channel(self.bot, str(emoji)):
            await ctx.reply(f"Sent application emoji '{emoji_name}'.")

    @commands.command()
    async def send_dm(self, ctx: commands.Context, *, msg: str) -> None:
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
            user_obj = await self.bot.fetch_user(USER_IDS[user])
            await user_obj.send(msg)
        except discord.NotFound:
            logger.warning(f"User object for {user} not found")
        except discord.Forbidden:
            logger.warning(f"Cannot send DM to {user} (Forbidden)")
        except AttributeError as e:
            logger.error(
                "Likely error: the bot can only send to users that have shared a server with the bot"
            )
            logger.error(e)
        except discord.DiscordException as e:
            logger.error(e)

    @commands.command()
    async def set_channel(self, ctx: commands.Context, new_channel: str) -> None:
        """
        Set the channel for the !send command.
        Args:
            ctx: The command context.
            new_channel: The name of the new channel.
        """
        channel_id = CHANNEL_IDS[new_channel]
        constants.CURRENT_CHANNEL_ID = channel_id
        logger.info(f"Current channel: {new_channel} - {channel_id}")

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
    async def on_message(self, msg: discord.Message) -> None:
        """
        Handle incoming messages, process commands, and respond to certain keywords.
        Args:
            msg: The message object.
        """
        if msg.author.bot:
            return

        # Forward DMs to fsg
        if isinstance(msg.channel, discord.DMChannel):
            fsg_id = USER_IDS.get("fsg")
            if fsg_id and msg.author.id != fsg_id:
                try:
                    fsg_user = await self.bot.fetch_user(fsg_id)
                    if fsg_user:
                        sender_name = f"{msg.author.display_name} ({msg.author.name})"
                        content = msg.content
                        if not content and msg.attachments:
                            content = " ".join([a.url for a in msg.attachments])
                        elif msg.attachments:
                            content += "\n" + " ".join([a.url for a in msg.attachments])

                        if content:
                            await fsg_user.send(f"DM from {sender_name}: {content}")
                        else:
                            logger.warning(
                                f"Received empty DM from {sender_name} with no attachments"
                            )
                except discord.Forbidden:
                    logger.error(
                        "Failed to forward DM: Forbidden. Check if the target user has DMs enabled."
                    )
                except discord.DiscordException as e:
                    logger.error(f"Failed to forward DM: {e}")

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
    await bot.add_cog(General(bot))
