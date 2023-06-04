"""Context menus for the B0BBA bot"""

import time

from datetime import datetime

import discord
from discord.ext import commands
from discord import app_commands

from aiohttp import ClientResponseError

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
        gettime_ctx_menu = self.gettime_context_menu

        self.whois_ctx_menu = app_commands.ContextMenu(
            name="whois",
            callback=whois_ctx_menu,
        )

        self.gettime_ctx_menu = app_commands.ContextMenu(
            name="get local time",
            callback=gettime_ctx_menu,
        )

        self.bot.tree.add_command(self.whois_ctx_menu)
        self.bot.tree.add_command(self.gettime_context_menu)

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

    async def gettime_context_menu(
        self, interaction: discord.Interaction, user: discord.User
    ) -> None:
        """A context menu to get time of the user

        Args:
            interaction (discord.Interaction): The interaction object
            user (discord.User): The user object
        """

        user_data = await Registration(user.id).check_registration("time")

        if not user_data or not user_data.get("timezone"):
            embed = discord.Embed(
                title="Error",
                description="This user hasn't added their timezone to the bot! ( `/time set_timezone` )",
                colour=Enum.Embeds.Colors.Error,
            )

            await interaction.response.send_message(embed=embed)
            return

        user_timezone = user_data.get("timezone")
        old_timezone = user_timezone
        # improve UX by fixing the signs being replaced in the API
        if "+" in user_timezone:
            user_timezone = user_timezone.replace("+", "-")
        elif "-" in user_timezone:
            user_timezone = user_timezone.replace("-", "+")

        try:
            time_data = await self.bot.http_client.get(
                "https://timeapi.io/api/Time/current/zone",
                params={"timeZone": user_timezone},
            )
        except ClientResponseError:
            await interaction.response.send_message(
                "Something went wrong while trying to get data from the time API"
            )

        embed = discord.Embed(
            title=time_data["time"],
            colour=Enum.Embeds.Colors.Info,
        )
        embed.add_field(
            name="Date", value=f"`{time_data['date']}, {time_data['dayOfWeek']}`"
        )
        embed.add_field(name="Timezone", value=f"`{old_timezone}`")
        embed.set_author(
            name=f"{user.display_name}'s time", icon_url=user.display_avatar
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    """The setup function for the context menus module

    Args:
        bot (discord.Bot): The bot object
    """
    await bot.add_cog(ContextMenus(bot))
