"""Context menus for the B0BBA bot"""

import time
import roblox
import discord

from discord.ext import commands
from discord import app_commands
from aiohttp import ClientResponseError

from modules.database_utils import Registration

import modules.enums as Enum


class ContextMenus(commands.Cog):
    """The class containing the context menu functions"""

    def __init__(self, bot: commands.Bot) -> None:
        """Constructor function for the ContextMenus class

        Args:
            bot (commands.Bot): The bot
        """
        self.bot = bot
        self.roblox_client = bot.roblox_client

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
        self.bot.tree.add_command(self.gettime_ctx_menu)

    async def whois_context_menu(
        self, interaction: discord.Interaction, user: discord.User
    ) -> None:
        """Context menu for the whois command

        Args:
            interaction (discord.Interaction): The interaction object
            user (discord.User): The user object
        """

        snowflake_id = None

        if user is None:
            snowflake_id = interaction.user.id
        else:
            snowflake_id = user.id

        registration = await Registration(snowflake_id).check_registration("links")

        if registration:
            target_user_discord = await self.bot.fetch_user(snowflake_id)
            target_user_roblox = await self.roblox_client.get_user(
                registration["roblox_id"]
            )

            created_on = target_user_roblox.created

            embed = discord.Embed(
                title=f"whois {target_user_discord.name}",
                colour=Enum.EmbedColors.INFO.value,
            )
            embed.add_field(
                name="Roblox",
                value=f"**ID:** `{registration['roblox_id']}`\n" +
                f"**Profile link:** [Click me](https://www.roblox.com/users/{target_user_roblox.name}/profile)\n" + 
                f"**Username:** `{target_user_roblox.name}`\n" + 
                f"**Registered On:** <t:{int(time.mktime(created_on.utctimetuple()))}:F>" +
                f"`({round((time.time() - time.mktime(created_on.utctimetuple())) / 86400)} days)`",
            )

            user_icon_url = (
                await self.roblox_client.thumbnails.get_user_avatar_thumbnails(
                    [target_user_roblox],
                    roblox.AvatarThumbnailType.full_body,
                    size="720x720",
                )
            )

            embed.set_thumbnail(url=user_icon_url[0].image_url)

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
                description="This user hasn't added their timezone to the bot!" +
                "( `/time set_timezone` )",
                colour=Enum.EmbedColors.ERROR.value,
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
            result = await self.bot.http_client.get(
                "https://timeapi.io/api/Time/current/zone",
                params={"timeZone": user_timezone},
            )
        except ClientResponseError:
            await interaction.response.send_message(
                "Something went wrong while trying to get data from the time API"
            )

        time_data = result.json.as_object()

        embed = discord.Embed(
            title=time_data.time,
            colour=Enum.EmbedColors.INFO.value,
        )
        embed.add_field(name="Date", value=f"`{time_data.date}, {time_data.dayOfWeek}`")
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
