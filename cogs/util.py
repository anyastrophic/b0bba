"""The utility module of b0bba

W0212 - Protected Acess. Line 157
"""

import os
import threading
from typing import List

import discord
import psutil
import roblox
from aiohttp import ClientResponseError
from discord import ChannelType, app_commands
from discord.ext import commands, tasks

import modules.enums as Enum
from modules.database_utils import Registration
from modules.loggers import Logger


class Utility(commands.Cog, name="util"):
    """The utilities of B0BBA"""

    def __init__(self, bot):
        self.bot = bot
        self.roblox_client: roblox.Client = (  # pylint:disable=no-member
            self.bot.ROBLOX_CLIENT
        )

        self.battery_debounce = False
        self.check_battery.start()  # pylint:disable=no-member

    @tasks.loop(seconds=30.0)
    async def check_battery(self):
        """Checks the battery"""
        battery = psutil.sensors_battery()
        if battery is not None:
            if battery.percent > 10:
                self.battery_debounce = False

            if (
                battery.percent <= 10
                and not battery.power_plugged
                and not self.battery_debounce
            ):
                thread = threading.Thread(
                    target=os.system,
                    args=["ffplay ./files/alert.mp3 -autoexit -nodisp"],
                )

                thread.start()

                self.battery_debounce = True

    WHITELISTED_ROLES = [1104813397574418474]
    WHITELISTED_ROLE_NAMES = ["Gamenight Pings"]

    @commands.Cog.listener()
    async def on_message(self, message):
        """A function called when the bot sees a new message

        Args:
            message (discord.Message): The message
        """
        if (
            message.channel.id == 1054082338268647565
            and message.author.id != self.bot.user.id
        ):
            if message.attachments:
                thread = await message.channel.create_thread(
                    name=f"{message.author}'s creation",
                    message=message,
                    type=ChannelType.public_thread,
                )

                await message.add_reaction("<:UpVote:657837919272173579>")
                await message.add_reaction("<:DownVote:657837532385378305>")

                await thread.send("You can discuss this creation here!")

            else:
                await message.delete()

                try:
                    await message.author.send(
                        "Your message in <#1054082338268647565> was deleted"
                        + " because you haven't attached any files showing it off!"
                    )
                except discord.Forbidden:
                    pass

            return

        if (
            message.channel.id == 1115081544462250085
            and message.author.id != self.bot.user.id
        ):
            thread = await message.channel.create_thread(
                name="Discussion",
                message=message,
                type=ChannelType.public_thread,
            )

            await message.add_reaction("<:UpVote:657837919272173579>")
            await message.add_reaction("<:DownVote:657837532385378305>")

            await thread.send("You can discuss this feature here!")

    @app_commands.command()
    @commands.guild_only()
    async def self_role(self, interaction: discord.Interaction, role: str):
        """get specified role, such as gamenight pings"""

        role = discord.utils.get(interaction.guild.roles, name=role)

        if not role:
            await interaction.response.send_message("This role wasn't found!")

            return

        if role.id in self.WHITELISTED_ROLES:
            if not role in interaction.user.roles:
                await interaction.user.add_roles(role)

                embed = discord.Embed(
                    title="Role given",
                    description=f"Role `{role}` was given to you!",
                    colour=Enum.EmbedColors.SUCCESS.value,
                )

                await interaction.response.send_message(embed=embed)
            else:
                await interaction.user.remove_roles(role)

                embed = discord.Embed(
                    title="Role taken",
                    description=f"Role `{role}` was taken from you!",
                    colour=Enum.EmbedColors.SUCCESS.value,
                )

                await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Sorry, you can't have this role!")

            return

    @self_role.autocomplete("role")
    async def _self_role_autocomplete(
        self, _: discord.Interaction, current: str
    ) -> List[app_commands.Choice[str]]:
        item_list = self.WHITELISTED_ROLE_NAMES

        return [
            app_commands.Choice(name=item, value=item)
            for item in item_list
            if current.lower() in item.lower()
        ]

    @app_commands.command()
    async def help(self, interaction: discord.Interaction, command: str = ""):
        """HELP!!!!!!"""
        await interaction.response.send_message(
            embed=await self.bot._help_command.get_help(
                command, self.bot.cogs, self.bot.tree
            )
        )

    time_commands = app_commands.Group(
        name="time", description="Commands for time stuff"
    )

    @time_commands.command()
    async def get_user_time(
        self, interaction: discord.Interaction, user: discord.User = None
    ):
        """Get the local time of the user specified"""
        if not user:
            user = interaction.user

        user_data = await Registration(user.id).check_registration("time")

        if not user_data or not user_data.get("timezone"):
            embed = discord.Embed(
                title="Error",
                description="This user hasn't added their timezone"
                + " to the bot! ( `/time set_timezone` )",
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

    @time_commands.command()
    async def set_timezone(self, interaction: discord.Interaction, timezone: str):
        """Set your timezone"""
        try:
            await self.bot.http_client.get(
                "https://timeapi.io/api/Time/current/zone",
                params={"timeZone": timezone},
            )
        except ClientResponseError as exc:
            if exc.status == 400:
                embed = discord.Embed(
                    title="Error",
                    description="This timezone doesn't exist!"
                    + "Here's a list with existing timezones:"
                    + "<https://timeapi.io/api/TimeZone/AvailableTimeZones>\n"
                    + "*try a timezone in a format such as Etc/GMT+1 or Europe/Kyiv*",
                    colour=Enum.EmbedColors.ERROR.value,
                )
                await interaction.response.send_message(embed=embed)
                return

            await interaction.response.send_message(
                "Something went wrong while trying to get data from the time API"
            )

            return

        await Registration(interaction.user.id).time()

        await self.bot.db.time.update_one(
            {"discord_id": interaction.user.id}, {"$set": {"timezone": timezone}}
        )

        embed = discord.Embed(
            title="OK",
            description=f"Your timezone was set to `{timezone}`",
            colour=Enum.EmbedColors.SUCCESS.value,
        )

        await interaction.response.send_message(embed=embed)

        Logger.Time.Timezone.UserSetTimezone(interaction.user, timezone)


async def setup(bot):
    """A function that gets called upon setup of the cog

    Args:
        bot (discord.Bot): The bot
    """
    await bot.add_cog(Utility(bot))
