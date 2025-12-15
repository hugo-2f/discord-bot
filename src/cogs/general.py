import logging
import tomllib

import discord
from discord.ext import commands
from translate import Translator

from utils import constants

logger = logging.getLogger(__name__)
CONFIG_PATH = constants.ROOT_DIR / "variables.toml"
with open(CONFIG_PATH, "rb") as f:
    config = tomllib.load(f)
USER_IDS = config["USER_IDS"]
CHANNEL_IDS = config["CHANNEL_IDS"]
channel_name = config["SETTINGS"]["channel_name"]


class General(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx: commands.Context) -> None:
        """Show help message."""
        await ctx.reply(
            "Commands: play <name/id> (channel), stop_playing, join, leave, audios, vol <name> <volume>"
        )

    @commands.command()
    async def send(self, ctx, *, msg: str | None = None) -> None:
        """
        Command format: !send <msg> <people to mention separated by spaces>
        Sends msg and mentions user if not None
        Prints people that can be mentioned if msg is None

        See variables.toml for users
        Ex:
            !send -> reply with list of users
            !send asdf -> send 'asdf' in current channel
            !send asdf fsg -> send '@fsg asdf'
            !send asdf fsg, gaj -> send '@fsg @gaj asdf'
        """
        if not msg:
            await ctx.reply(str(set(USER_IDS.keys())))
            return

        channel = self.bot.get_channel(CHANNEL_IDS[channel_name])
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
            user_obj = await self.bot.fetch_user(USER_IDS[username])
            users_to_mention.append(user_obj.mention)
        await channel.send(f"{' '.join(users_to_mention)} {msg}")

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
        except Exception as e:
            logger.error(e)

    @commands.command()
    async def setChannel(self, ctx: commands.Context, new_channel: str) -> None:
        """
        Set the channel for the !send command.
        Args:
            ctx: The command context.
            new_channel: The name of the new channel.
        """
        global channel_name
        channel_name = new_channel
        logger.info(f"Current channel: {channel_name} - {CHANNEL_IDS[channel_name]}")

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
                except Exception as e:
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
