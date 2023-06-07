import asyncio
import logging
import os
from datetime import datetime
from typing import Any, Coroutine

import discord
import discord.ext.commands
import motor.motor_asyncio
import roblox
from discord.flags import Intents
from uvicorn import Config, Server

import modules.requests
from cogs.webserver import app
from modules.error_handler import error_handler
from modules.get_setup import get_setup
from modules.help_command import HelpCommand
from modules.loggers import (
    DiscordWebhookHandler,
    Logger,
    _ColourFormatter,
    _DiscordColorFormatter,
)

UB_GUILD = discord.Object(id=406995309000916993)


class Bot(discord.ext.commands.Bot):
    def __init__(self) -> None:
        enabled_intents = Intents.all()
        enabled_intents.members = True
        enabled_intents.guilds = True
        enabled_intents.messages = True

        self.http_client = modules.requests.Client()

        super().__init__(command_prefix=["/", "jarvis "], intents=enabled_intents)

    async def sync_application_commands(self) -> Coroutine[Any, Any, None]:
        await self.wait_until_ready()
        await self.tree.sync()

        Logger.Main.AppCommandsSynced()

    async def setup_hook(self) -> Coroutine[Any, Any, None]:
        ROBLOX_CLIENT = roblox.Client(
            os.environ.get("ROBLOX_COOKIE"), os.environ.get("ROBLOX_API_KEY")
        )

        bot.SETUP = get_setup()

        bot.ROBLOX_CLIENT = ROBLOX_CLIENT
        bot.roblox_client = ROBLOX_CLIENT
        bot.verification_roblox_client = roblox.Client(
            os.environ.get("ROBLOX_COOKIE"),
            os.environ.get("ROBLOX_VERIFICATION_API_KEY"),
        )

        bot.ROBLOX_UNIVERSE = await ROBLOX_CLIENT.get_universe(2679509101)
        bot.roblox_universe = bot.ROBLOX_UNIVERSE
        bot.ROBLOX_GROUP = await ROBLOX_CLIENT.get_group(11205637)
        bot.ROBLOX_PLACE = await ROBLOX_CLIENT.get_place(6982988368)

        for file in os.listdir("cogs"):
            if file.endswith(".py"):
                await self.load_extension(f"cogs.{file[:-3]}")

        self.loop.create_task(self.sync_application_commands())


async def _check(interaction: discord.Interaction):
    document = await bot.db.blacklist.find_one({"discord_id": interaction.user.id})
    return document is None


bot = Bot()
bot.help_command = None
bot._help_command = HelpCommand(bot)
bot.tree.interaction_check = _check


@bot.event
async def on_application_command_error(ctx, error):
    """App command error handler

    Args:
        ctx (discord.Interaction): The interaction
        error (_type_): The error
    """
    await error_handler(bot, ctx, error)


@bot.event
async def on_ready():
    db_name = "b0bba" if os.environ.get("B0BBA_VERSION") == "test" else "b0bba"
    bot.db = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")[
        db_name
    ]

    config = Config(app=app, host="0.0.0.0", port=80)
    server = Server(config)

    bot.loop.create_task(server.serve())

    ub_guild = bot.get_guild(406995309000916993)

    channels = {}
    channels["report-logs"] = ub_guild.get_channel(1100245620612137022)
    channels["payout-logs"] = ub_guild.get_channel(1100275071186128987)
    channels["server-logs"] = ub_guild.get_channel(1054078855066964018)
    channels["bot-logs"] = ub_guild.get_channel(1109013973745016843)

    bot.ub_channels = channels
    bot.ub_guild = UB_GUILD

    bot.tree.on_error = on_application_command_error

    await bot.load_extension("jishaku")


if __name__ == "__main__":
    discord.utils.setup_logging(
        handler=logging.FileHandler(
            filename=rf"logs/{datetime.today().strftime('%Y-%m-%d %H-%M-%S')}.log",
            encoding="utf-8",
            mode="w",
        ),
    )

    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(_ColourFormatter())

    webhookHandler = DiscordWebhookHandler(os.environ.get("B0BBA_LOGGING_WEBHOOK"))
    webhookHandler.setFormatter(_DiscordColorFormatter())

    logging.getLogger().addHandler(streamHandler)

    if os.environ.get("B0BBA_VERSION") != "test":
        logging.getLogger().addHandler(webhookHandler)

    asyncio.run(bot.start(os.environ.get("B0BBA_BOT_TOKEN")))
