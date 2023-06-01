"""Context menus for the B0BBA bot"""

import time

from datetime import datetime

import discord
from discord.ext import commands
from discord import app_commands

from modules.database_utils import Registration
from modules.roblox_utils import User
from modules.enums import Enum


class ContextMenus(commands.Cog):
    """The class containing the context menu functions"""

    def __init__(self, bot: commands.Bot) -> None:
        """Constructor function for the ContextMenus class

        Args:
            bot (commands.Bot): The bot
        """
        self.bot = bot

        whois_ctx_menu = self.whois_context_menu

        self.whois_ctx_menu = app_commands.ContextMenu(
            name="whois",
            callback=whois_ctx_menu,
        )

        self.bot.tree.add_command(self.whois_ctx_menu)

    async def whois_context_menu(
        self, interaction: discord.Interaction, user: discord.User
    ) -> None:
        """Context menu for the whois command

        Args:
            interaction (discord.Interaction): The interaction object
            user (discord.User): The user object
        """

        user_id = user.id

        registration = await Registration(user_id).check_registration("links")

        if registration:
            user_discord = await self.bot.fetch_user(user_id)

            user_roblox = await User(registration["roblox_id"]).get_data()

            created_on = datetime.fromisoformat(user_roblox["created"])

            embed = discord.Embed(
                title=f"whois {user_discord.name}", colour=Enum.Embeds.Colors.Info
            )

            embed.add_field(
                name="Roblox",
                value=f"**ID:** `{registration['roblox_id']}`\n**Username:** `{user_roblox['name']}`\n**Registered On:** <t:{int(time.mktime(created_on.utctimetuple()))}:F> `({round((time.time() - time.mktime(created_on.utctimetuple())) / 86400)} days)`",
            )

            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("User is not verified")


async def setup(bot):
    """The setup function for the context menus module

    Args:
        bot (discord.Bot): The bot object
    """
    await bot.add_cog(ContextMenus(bot))
