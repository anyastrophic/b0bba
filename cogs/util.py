import discord
import roblox
import asyncio
import psutil
import random

import os
import threading

from modules.enums import Enum
from modules.database_utils import Registration
from modules.requests import Request
from modules.exceptions import HttpException
from modules.loggers import Logger

from discord.ext import commands, tasks

from discord import app_commands

from discord import ChannelType

from typing import List


class Utility(commands.Cog, name="util"):
    def __init__(self, bot):
        self.bot = bot
        self.roblox_client: roblox.Client = (  # pylint:disable=no-member
            self.bot.ROBLOX_CLIENT
        )

        self.battery_debounce = False
        self.check_battery.start()  # pylint:disable=no-member

    @tasks.loop(seconds=30.0)
    async def check_battery(self):
        battery = psutil.sensors_battery()
        if battery is not None:
            if battery.percent > 10:
                self.battery_debounce = False

            if (
                battery.percent <= 10
                and not battery.power_plugged
                and not self.battery_debounce
            ):
                t = threading.Thread(
                    target=os.system, args=["ffplay alert.mp3 -autoexit -nodisp"]
                )

                t.start()

                self.battery_debounce = True

    WHITELISTED_ROLES = [1104813397574418474]
    WHITELISTED_ROLE_NAMES = ["Gamenight Pings"]

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id == 483011136006914078:
            POOKIE = discord.File("POOKIE.mp4", filename="POOKIE.mp3")
            if random.randint(1, 50) == 50:
                await message.reply(file=POOKIE)

        if (
            message.channel.id == 1054082338268647565
            and message.author.id != 1085454927259779093
        ):
            if message.attachments:
                thread = await message.channel.create_thread(
                    name=f"{message.author}'s creation",
                    message=message,
                    type=ChannelType.public_thread,
                )

                await thread.send("You can discuss this creation here!")

            else:
                await message.delete()

                try:
                    await message.author.send(
                        "Your message in <#1054082338268647565> was deleted because you haven't attached any files showing it off!"
                    )
                except:  # pylint:disable=bare-except
                    pass

            return

        if (
            message.channel.type == discord.ChannelType.public_thread
            and message.channel.parent.id == 1063317564207403008
            and message.author.id != 1085454927259779093
            and message == message.channel.starter_message
        ):
            try:
                user = await self.roblox_client.get_user_by_username(
                    message.channel.name
                )

                user_icon_url = await self.roblox_client.thumbnails.get_user_avatar_thumbnails(
                    [user],
                    roblox.AvatarThumbnailType.full_body,  # pylint:disable=no-member
                    size="720x720",
                )

                b0bba_link = await self.bot.db.links.find_one({"roblox_id": user.id})

                embed = discord.Embed(
                    title=f"Here's what I could find about {user.name}!",
                    description=f"[Profile link](https://www.roblox.com/users/{user.id}/profile)",
                    colour=Enum.Embeds.Colors.Info,
                )

                embed.set_thumbnail(url=user_icon_url[0].image_url)

                embed.add_field(name="Roblox ID", value=f"`{user.id}`", inline=False)

                embed.add_field(
                    name="Is user verified with B0BBA?",
                    value=f'Yes, <@{b0bba_link["discord_id"]}>' if b0bba_link else "No",
                    inline=False,
                )

                await message.channel.send(embed=embed)

            except roblox.UserNotFound:  # pylint:disable=no-member
                await message.channel.send(
                    f"{message.channel.owner.mention}, the user you specified as this post name was not found! This post will be deleted in 10 seconds."
                )

                await asyncio.sleep(10)
                await message.channel.delete()

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
                    colour=Enum.Embeds.Colors.Success,
                )

                await interaction.response.send_message(embed=embed)
            else:
                await interaction.user.remove_roles(role)

                embed = discord.Embed(
                    title="Role taken",
                    description=f"Role `{role}` was taken from you!",
                    colour=Enum.Embeds.Colors.Success,
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
    async def get_user_time(self, interaction: discord.Interaction, user: discord.User):
        """Get the local time of the user specified"""
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
        try:
            time_data = await Request().get(
                f"https://timeapi.io/api/Time/current/zone?timeZone={user_timezone}"
            )
        except HttpException:
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
        embed.add_field(name="Timezone", value=f"`{time_data['timeZone']}`")
        embed.set_author(
            name=f"{user.display_name}'s time", icon_url=user.display_avatar
        )

        await interaction.response.send_message(embed=embed)

    @time_commands.command()
    async def set_timezone(self, interaction: discord.Interaction, timezone: str):
        """Set your timezone"""
        try:
            await Request().get(
                f"https://timeapi.io/api/Time/current/zone?timeZone={timezone}"
            )
        except HttpException as exc:
            if exc.status == 400:
                embed = discord.Embed(
                    title="Error",
                    description="This timezone doesn't exist! Here's a list with existing timezones: <https://timeapi.io/api/TimeZone/AvailableTimeZones>\n*try a timezone in a format such as Etc/GMT+1 or Europe/Kyiv*",
                    colour=Enum.Embeds.Colors.Error,
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
            colour=Enum.Embeds.Colors.Success,
        )

        await interaction.response.send_message(embed=embed)

        Logger.Time.Timezone.UserSetTimezone(interaction.user, timezone)

    # @app_commands.command()
    # async def to_ub_markdown(self, interaction: discord.Interaction):
    #     messages = [await interaction.channel.history(limit=10)]
    #     markdown = messages[0].content

    #     filename = f'{secrets.token_hex(4)}.md'

    #     with open('./temp/{filename}', 'w') as f:
    #         f.write(markdown)
    #         f.close()

    #     with open('./temp/{filename}', 'r') as fin:
    #         rendered = mistletoe.markdown(fin)

    #         parsed_html = BeautifulSoup(rendered, features="html.parser")

    #         parsed_html.find_all()

    #         generated_ub_markdown = ""

    #         for tag in parsed_html.find_all():
    #             if tag.name == 'h1':
    #                 generated_ub_markdown += f'Mark.Title("{str(tag.string)}")'

    #     await interaction.response.send_message(
    #         f'```lua\n{generated_ub_markdown}\n```'
    #     )


async def setup(bot):
    await bot.add_cog(Utility(bot))
