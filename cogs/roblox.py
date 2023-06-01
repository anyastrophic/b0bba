"""The roblox module of B0BBA"""

import openai
import time as _time
import discord
import openpyxl
import secrets
import roblox
import os

from discord.ext import commands
from discord import app_commands
from modules.roblox_utils import Request, get_csrf
from modules.enums import Enum
from modules.database_utils import Registration, check_link

from modules.loggers import Logger

openai.api_key = "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"
openai.organization = "org-RgAxsUuotwCUDQdjpNfSOvCE"

linking_words = []
with open("./files/verify-words.txt", "r", encoding="utf-8") as f:
    linking_words = f.read().splitlines()

    f.close()


class Roblox(commands.Cog, name="roblox"):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.universe = self.bot.ROBLOX_UNIVERSE
        self.group = self.bot.ROBLOX_GROUP
        self.place = self.bot.ROBLOX_PLACE

        self.roblox_client: roblox.Client = self.bot.ROBLOX_CLIENT

        self.verification_universe: roblox.BaseUniverse = (
            await self.bot.verification_roblox_client.get_universe(4615409270)
        )

    @app_commands.command()
    async def whois(self, interaction: discord.Interaction, user: discord.User = None):
        """query bot's data about a DISCORD user"""

        snowflake_id = None

        if user == None:
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
                colour=Enum.Embeds.Colors.Info,
            )
            embed.add_field(
                name="Roblox",
                value=f"**ID:** `{registration['roblox_id']}`\n**Username:** `{target_user_roblox.name}`\n**Registered On:** <t:{int(_time.mktime(created_on.utctimetuple()))}:F> `({round((_time.time() - _time.mktime(created_on.utctimetuple())) / 86400)} days)`",
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

    @app_commands.command()
    @commands.guild_only()
    async def verify(self, interaction: discord.Interaction, username: str):
        """link your ROBLOX account to your DISCORD account"""

        user = await self.roblox_client.get_user_by_username(
            username, exclude_banned_users=True
        )

        if await Registration(interaction.user.id).check_registration(
            "links"
        ) or await Registration(user.id).check_registration("links"):
            await interaction.response.send_message("Your account is already verified!")
            return

        if (
            round((_time.time() - _time.mktime(user.created.utctimetuple())) / 86400)
            < 30
        ):
            await interaction.response.send_message(
                "I'm sorry, but you can't verify because your account's age is less than 30 days!"
            )
            return

        verification_code = secrets.token_urlsafe(2)
        verification_store = await self.verification_universe.get_standard_datastore(
            "Verification"
        )

        try:
            await verification_store.get_entry(user.id)

            await interaction.response.send_message(
                "This ROBLOX account already has a pending verification request!"
            )
            return
        except roblox.NotFound:
            pass

        await verification_store.set_entry(
            user.id,
            {
                "discord_id": str(interaction.user.id),
                "verification_code": verification_code,
            },
        )

        if not isinstance(interaction.channel, discord.channel.DMChannel):
            await interaction.response.send_message(
                "A DM has been sent to you for verification."
            )

        await interaction.user.send(
            f"""
            # B0BBA Verification

            ### To verify your account, please join the game below and enter the following code: `{verification_code}`

<https://www.roblox.com/games/7646362415>
        """
        )

    @app_commands.command(name="get_roles")
    @commands.guild_only()
    async def _get_roles(self, interaction: discord.Interaction):
        """run this command if you're already verified but don't have the UBer role"""

        link = await check_link(interaction.user.id)

        if not link:
            await interaction.response.send_message("You're not verified!")

            return

        group_member = self.group.get_member(link["roblox_id"])

        _group_role = await group_member.get_role()

        group_role = None

        if _group_role and _group_role.rank < 5:
            group_role = discord.utils.get(
                interaction.guild.roles, name=_group_role.name
            )

        roles_received = ""

        uber_role = interaction.guild.get_role(406997457709432862)
        if not uber_role in interaction.user.roles:
            roles_received += f"* **{uber_role}**\n"

            await interaction.user.add_roles(uber_role)

        if group_role:
            if not group_role in interaction.user.roles:
                roles_received += f"* **{group_role}**\n"

                await interaction.user.add_roles(group_role)

        if roles_received != "":
            embed = discord.Embed(
                title="Roles received",
                description=f"You got these roles: \n\n{roles_received}",
                colour=Enum.Embeds.Colors.Info,
            )
        else:
            embed = discord.Embed(
                title="No roles received",
                description="You didn't get any new roles",
                colour=Enum.Embeds.Colors.Warning,
            )

        await interaction.response.send_message(embed=embed)

    server_commands = app_commands.Group(name="servers", description="Server commands")

    @server_commands.command()
    @commands.guild_only()
    async def list(self, interaction: discord.Interaction):
        """Shows game servers"""

        servers = await self.place.get_instances()
        servers = servers.collection
        embed = discord.Embed(title="Game Servers", colour=Enum.Embeds.Colors.Info)

        for server in servers:
            embed.add_field(
                name=f"{server.id}", value=f"`{server.playing} Players`", inline=False
            )

        await interaction.response.send_message(embed=embed)

    @server_commands.command()
    @commands.guild_only()
    async def info(self, interaction: discord.Interaction, server_id: str):
        """retrieve game server info by id"""

        if server_id == "global":
            await interaction.response.send_message("no server with this id found")
            return

        await interaction.response.defer()

        result = await Request().get(f"http://localhost/servers/{server_id}")

        if not result["response"].status == 200:
            await interaction.followup.send("no server with this id found")
            return

        server_info = result["json"]
        players = server_info["players"]
        fps = server_info["fps"]
        age = server_info["age"]

        embed = discord.Embed(title="Game Server Info", colour=Enum.Embeds.Colors.Info)
        embed.add_field(name="Server ID", value=f"`{server_id}`", inline=False)
        embed.add_field(name="Max Players", value="`20`", inline=False)
        embed.add_field(
            name="Currently Playing", value=f"`{len(players)}`", inline=False
        )
        embed.add_field(name="Players", value=f"`{', '.join(players)}`")
        embed.add_field(name="FPS", value=f"`{round(fps, 2)}`", inline=False)
        embed.add_field(name="Age", value=f"`{round(age, 2)} hours`")

        await interaction.followup.send(embed=embed)

    report_commands = app_commands.Group(name="reports", description="Reports commands")

    @report_commands.command()
    @commands.guild_only()
    @app_commands.checks.has_any_role(
        Enum.Roles.UB_Admin,
        Enum.Roles.UB_Junior_Admin,
        Enum.Roles.UB_Senior_Admin,
        Enum.Roles.UB_Trial_Admin,
    )
    async def close(self, interaction: discord.Interaction, *, verdict: str):
        """close the report"""
        await Registration(interaction.user.id).admins()
        registration = await self.bot.db.admins.find_one(
            {"discord_id": interaction.user.id}
        )

        if interaction.channel.parent_id != 1063317564207403008:
            await interaction.response.send_message(
                "This is the wrong channel for this command! Use it in a post in <#1063317564207403008>"
            )
            return

        if interaction.channel.locked:
            await interaction.response.send_message("This report is already closed!")
            return

        embed = discord.Embed(
            title="Report closed",
            description=f"[Jump to report]({interaction.channel.jump_url})",
            colour=Enum.Embeds.Colors.Info,
        )

        embed.add_field(name="Admin", value=interaction.user.mention, inline=False)
        embed.add_field(
            name="Report creator",
            value=f"<@{interaction.channel.owner_id}>",
            inline=False,
        )
        embed.add_field(
            name="Reported user", value=interaction.channel.name, inline=False
        )
        embed.add_field(name="Verdict", value=verdict, inline=False)

        await self.bot.ub_channels["report-logs"].send(embed=embed)
        await interaction.channel.send(embed=embed)

        try:
            await interaction.channel.owner.send(embed=embed)
        except Exception:
            await interaction.channel.send(
                f"<@{interaction.channel.owner_id}>, your DMs are closed, so I pinged you for your report!"
            )

        starter_message = [
            message
            async for message in interaction.channel.history(limit=1, oldest_first=True)
        ][0]

        await Registration(interaction.user.id).reports(
            interaction.channel_id,
            starter_message.content,
            interaction.user,
            interaction.channel.owner,
            await self.roblox_client.get_user_by_username(interaction.channel.name),
        )

        registration["reports_closed"][str(interaction.channel_id)] = {"expired": False}

        await self.bot.db.admins.update_one(
            {"discord_id": interaction.user.id},
            {
                "$set": {
                    "payout": registration["payout"] + 10,
                    "reports_closed": registration["reports_closed"],
                }
            },
        )

        await interaction.channel.edit(locked=True, archived=True)

        Logger.Reports.ReportClosed(interaction.channel_id, interaction.user)

    management_commands = app_commands.Group(
        name="management", description="Commands for managers"
    )

    def is_payout_manager(self, author):
        return author.id in self.bot.SETUP["roblox"]["payout_managers"]

    @management_commands.command()
    async def add_admin(self, interaction: discord.Interaction, user: discord.User):
        """add an admin to the admins collection if they don't exist there already"""

        if not self.is_payout_manager(interaction.user):
            return

        await Registration(user.id).admins()

        await interaction.response.send_message("admin added")

    @management_commands.command()
    async def calculate_payout(
        self, interaction: discord.Interaction, admin: discord.User
    ):
        """calculate payout for specified admin"""

        if not self.is_payout_manager(interaction.user):
            return

        if not await Registration(admin.id).check_registration("admins"):
            await interaction.response.send_message(
                "This admin is not in the admin collection, please add them with the `/management add_admin` command, or wait until they have a report closed."
            )
            return

        registration = await self.bot.db.admins.find_one({"discord_id": admin.id})

        BONUSES = {
            6: 25,
            7: 50,
            8: 75,
            9: 100,
        }

        link = await check_link(admin.id)

        assert link != None, "link is None (is admin verified?)"

        group_member = self.group.get_member(link["roblox_id"])

        role_in_group = await group_member.get_role()

        if not role_in_group:
            await interaction.response.send_message("This user is not in the group!")

            return

        bonus = 0

        if role_in_group.rank in BONUSES:
            bonus = BONUSES[role_in_group.rank]

        await interaction.response.send_message(
            f"The calculated payout for this admin is:\n{registration['payout']} + {bonus} BONUS = __{registration['payout'] + bonus} Robux__"
        )

    @management_commands.command()
    async def payout(
        self,
        interaction: discord.Interaction,
        admin: discord.User,
        amount: int,
        notes: str = "No notes",
    ):
        """payout a specified admin in robux"""

        if not self.is_payout_manager(interaction.user):
            return

        if not await Registration(admin.id).check_registration("admins"):
            await interaction.response.send_message(
                "This user is not in the admin collection, please add them with the `/management add_admin` command, or wait until they have a report closed."
            )
            return

        link = await check_link(admin.id)

        if not link:
            await interaction.response.send_message(
                f"`{admin}` is not verified in B0BBA!"
            )
            return

        registration = await self.bot.db.admins.find_one({"discord_id": admin.id})

        for reportid, reportdata in registration["reports_closed"].items():
            registration["reports_closed"][reportid]["expired"] = True

        registration["payouts_received"][str(len(registration["payouts_received"]))] = {
            "manager": interaction.user.id,
            "amount": amount,
            "notes": notes,
        }

        csrf = await get_csrf()
        cookie = os.environ.get("ROBLOX_COOKIE")

        assert csrf != None, "CSRF token is None"
        assert cookie != None, "Cookie is None"

        result = await Request().post(
            "https://groups.roblox.com/v1/groups/11205637/payouts",
            headers={"Cookie": f".ROBLOSECURITY={cookie}", "x-csrf-token": csrf},
            json={
                "PayoutType": "FixedAmount",
                "Recipients": [
                    {
                        "recipientId": link["roblox_id"],
                        "recipientType": "User",
                        "amount": amount,
                    }
                ],
            },
        )

        if result["response"].status != 200:
            await interaction.response.send_message(
                f'Payout FAILURE: Response code {result["response"].status}'
            )

            Logger.Payout.Failure(
                interaction.user,
                admin,
                f"Roblox API didn't return 200. More info:\n{result['response'].status}\n{result['json']}",
            )

            return

        await self.bot.db.admins.update_one(
            {"discord_id": admin.id},
            {
                "$set": {
                    "payout": 0,
                    "reports_closed": registration["reports_closed"],
                    "payouts_received": registration["payouts_received"],
                }
            },
        )

        Logger.Payout.Success(interaction.user, admin)

        embed = discord.Embed(title="Admin payout", colour=Enum.Embeds.Colors.Info)
        embed.add_field(name="Admin", value=f"{admin}", inline=False)
        embed.add_field(
            name="Manager, who paid out", value=f"{interaction.user}", inline=False
        )
        embed.add_field(name="Amount", value=amount, inline=False)
        embed.add_field(name="Notes", value=notes, inline=False)

        await self.bot.ub_channels["payout-logs"].send(embed=embed)

        await interaction.response.send_message(embed=embed)

    @management_commands.command()
    async def get_reports_closed(
        self, interaction: discord.Interaction, admin: discord.User
    ):
        """get reports that were closed by this admin"""

        if not self.is_payout_manager(interaction.user):
            return

        if not await Registration(admin.id).check_registration("admins"):
            await interaction.response.send_message(
                "This user is not in the admin collection, please add them with the `/management add_admin` command, or wait until they have a report closed."
            )
            return

        registration = await self.bot.db.admins.find_one({"discord_id": admin.id})

        book = openpyxl.Workbook()
        sheet = book.active

        sheet.column_dimensions["A"].width = 20
        sheet.column_dimensions["B"].width = 20
        sheet.column_dimensions["C"].width = 100

        sheet.append(("Report ID", "Creator ID", "Verdict"))

        for reportid, reportdata in registration["reports_closed"].items():
            if reportdata["expired"] == False:
                report = await self.bot.db.reports.find_one({"report_id": reportid})

                if report:
                    sheet.append(
                        (str(reportid), str(report["creator"]), reportdata["verdict"])
                    )
                else:
                    sheet.append(
                        (
                            str(reportid),
                            str(reportdata["creator"]),
                            reportdata["verdict"],
                        )
                    )

        book.save(f"./temp/{admin.name}.xlsx")

        with open(f"./temp/{admin.name}.xlsx", "rb") as file:
            await interaction.response.send_message(
                file=discord.File(file, filename=f"{admin.name}.xlsx")
            )

            file.close()

    @management_commands.command()
    async def get_payouts_for_admins(self, interaction: discord.Interaction):
        """gets the payouts that are due for admins"""

        if not self.is_payout_manager(interaction.user):
            return

        admins = ""

        result = self.bot.db.admins.find({}, {})
        list = await result.to_list(100)

        for document in list:
            user = await self.bot.fetch_user(document["discord_id"])
            admins += f"Should you payout **{user}**: {document['payout']>0}\n"

        await interaction.response.send_message(admins)

    robloxmod_commands = app_commands.Group(
        name="robloxmod", description="Commands for Roblox moderations"
    )

    @robloxmod_commands.command()
    @commands.guild_only()
    @app_commands.checks.has_any_role(
        Enum.Roles.UB_Admin,
        Enum.Roles.UB_Junior_Admin,
        Enum.Roles.UB_Senior_Admin,
        Enum.Roles.UB_Trial_Admin,
        1003365453588070552,
    )  # 1003365453588070552 is manslaughter for testing
    async def globalmessage(
        self,
        interaction: discord.Interaction,
        message: str = "A default admin message sent from B0BBA bot",
    ):
        """sends a message accross every UB server"""

        verified = await check_link(interaction.user.id)

        if not verified:
            await interaction.response.send_message(
                "You can't run this command because your account isn't verified! Run `/verify` with your ROBLOX username"
            )
            return

        result = await self.universe.publish_message("globalMessage", message)

        if result == 200:
            Logger.RobloxMod.GlobalMessage.Success(interaction.user, message)

            embed = discord.Embed(
                title="Game Global Message",
                description=f"message `{message}` succesfully sent to every server",
                colour=Enum.Embeds.Colors.Success,
            )

            await interaction.response.send_message(embed=embed)
        else:
            Logger.RobloxMod.GlobalMessage.Failure(
                interaction.user,
                message,
                f"Roblox API didn't return 200. More info:\n{result['response'].status}\n{result['json']}",
            )

            embed = discord.Embed(
                title="Game Global Message",
                description=f"message send failure:\nstatus: {result.status}\n\n<@804066391614423061>",
                colour=Enum.Embeds.Colors.Error,
            )

            await interaction.response.send_message(embed=embed)

    @robloxmod_commands.command()
    @app_commands.checks.has_any_role(
        Enum.Roles.UB_Admin,
        Enum.Roles.UB_Junior_Admin,
        Enum.Roles.UB_Senior_Admin,
        Enum.Roles.UB_Trial_Admin,
        1003365453588070552,
    )
    @app_commands.choices(
        unit=[
            app_commands.Choice(name="second", value="1"),
            app_commands.Choice(name="minute", value="60"),
            app_commands.Choice(name="hour", value="3600"),
            app_commands.Choice(name="day", value="86400"),
            app_commands.Choice(name="week", value="604800"),
            app_commands.Choice(name="month", value="2678000"),
            app_commands.Choice(name="year", value="31540000"),
            app_commands.Choice(name="decade", value="315400000"),
            app_commands.Choice(name="century", value="3154000000"),
            app_commands.Choice(name="millenium", value="31540000000"),
        ]
    )
    async def gameban(
        self,
        interaction: discord.Interaction,
        target_user: str,
        reason: str,
        time: int,
        unit: app_commands.Choice[str],
    ):
        """gameban a user in UB"""

        verified = await check_link(interaction.user.id)
        if not verified:
            await interaction.response.send_message(
                "You can't run this command because your admin account isn't verified! Run `/verify` with your ROBLOX username"
            )
            return

        if not target_user.isnumeric():
            target_user = await self.roblox_client.get_user_by_username(target_user)
        else:
            target_user = await self.roblox_client.get_user(int(target_user))

        datastore = await self.universe.get_standard_datastore("Banned2")

        ban_duration = time * int(unit.value) + _time.time()

        await datastore.set_entry(target_user.id, [ban_duration, reason])

        target_username = target_user.name

        Logger.RobloxMod.GameBan.Success(
            interaction.user, target_username, target_user.id
        )

        await interaction.response.send_message(
            f"`{target_username}` succesfully gamebanned"
        )
        await self.universe.publish_message(
            "banUpdate", f"{target_username}:{ban_duration}:{reason}"
        )

        channel = interaction.guild.get_channel(1056047980861476945)

        embed = discord.Embed(
            title="Gamebanned a player", colour=Enum.Embeds.Colors.Info
        )
        embed.add_field(name="Player:", value=target_username, inline=False)
        embed.add_field(name="Duration:", value=f"{time} {unit.name}s", inline=False)
        embed.add_field(name="Reason:", value=reason, inline=False)

        admin = await self.roblox_client.get_user(verified["roblox_id"])

        thumbnails = await self.roblox_client.thumbnails.get_user_avatar_thumbnails(
            [admin], roblox.AvatarThumbnailType.headshot, is_circular=True
        )

        embed.set_author(name=admin.name, icon_url=thumbnails[0].image_url)

        await channel.send(embed=embed)

    @robloxmod_commands.command()
    @commands.guild_only()
    @app_commands.checks.has_any_role(
        Enum.Roles.UB_Admin,
        Enum.Roles.UB_Junior_Admin,
        Enum.Roles.UB_Senior_Admin,
        Enum.Roles.UB_Trial_Admin,
    )
    async def ungameban(
        self, interaction: discord.Interaction, target_user: str, reason: str
    ):
        """ungameban a user in UB"""

        verified = await check_link(interaction.user.id)
        if not verified:
            await interaction.response.send_message(
                "You can't run this command because your admin account isn't verified! Run `/verify` with your ROBLOX username"
            )
            return

        if not target_user.isnumeric():
            target_user = await self.roblox_client.get_user_by_username(target_user)
        else:
            target_user = await self.roblox_client.get_user(int(target_user))

        datastore = await self.universe.get_standard_datastore("Banned2")

        await datastore.set_entry(target_user.id, [0, reason])

        target_username = target_user.name

        Logger.RobloxMod.GameBan.Success(
            interaction.user, target_username, target_user.id
        )

        await interaction.response.send_message(
            f"`{target_username}` succesfully ungamebanned"
        )

        channel = interaction.guild.get_channel(1056047980861476945)

        embed = discord.Embed(
            title="Ungamebanned a player", colour=Enum.Embeds.Colors.Info
        )
        embed.add_field(name="Reason:", value=reason, inline=False)

        admin = await self.roblox_client.get_user(verified["roblox_id"])

        thumbnails = await self.roblox_client.thumbnails.get_user_avatar_thumbnails(
            [admin], roblox.AvatarThumbnailType.headshot, is_circular=True
        )

        embed.set_author(name=admin.name, icon_url=thumbnails[0].image_url)

        await channel.send(embed=embed)

    @robloxmod_commands.command()
    @commands.guild_only()
    @app_commands.checks.has_any_role(
        Enum.Roles.UB_Admin,
        Enum.Roles.UB_Junior_Admin,
        Enum.Roles.UB_Senior_Admin,
        Enum.Roles.UB_Trial_Admin,
        1003365453588070552,
    )
    async def get_ban_state(self, interaction: discord.Interaction, target_user: str):
        """get ban info about a user"""

        verified = await check_link(interaction.user.id)
        if not verified:
            await interaction.response.send_message(
                "You can't run this command because your admin account isn't verified! Run `/verify` with your ROBLOX username"
            )
            return

        if not target_user.isnumeric():
            target_user = await self.roblox_client.get_user_by_username(target_user)
        else:
            target_user = await self.roblox_client.get_user(int(target_user))

        datastore = await self.universe.get_standard_datastore("Banned2")

        entry = await datastore.get_entry(target_user.id)

        target_username = target_user.name

        embed = discord.Embed(
            title=f"{target_username}'s ban state", colour=Enum.Embeds.Colors.Info
        )

        embed.add_field(
            name="Banned until",
            value="`Not banned`" if (entry[0] == 0) else f"<t:{round(entry[0])}:F>",
            inline=False,
        )

        embed.add_field(name="Mod notes", value=f"`{entry[1]}`", inline=False)

        await interaction.response.send_message(embed=embed)

    @robloxmod_commands.command()
    @commands.guild_only()
    @app_commands.checks.has_any_role(
        Enum.Roles.UB_Admin,
        Enum.Roles.UB_Junior_Admin,
        Enum.Roles.UB_Senior_Admin,
        Enum.Roles.UB_Trial_Admin,
    )
    async def execute(
        self, interaction: discord.Interaction, server_id: str, *, command: str
    ):
        """runs the specified command on the specified instance of UB (roblox)"""

        verified = await check_link(interaction.user.id)
        if not verified:
            await interaction.response.send_message(
                "You can't run this command because your admin account isn't verified! Run `/verify` with your ROBLOX username"
            )
            return

        user = await self.roblox_client.get_user(verified["roblox_id"])

        await self.universe.publish_message(
            "global", f"{server_id}|{verified['roblox_id']}|{user.name}|/{command}"
        )

        embed = discord.Embed(
            title="Game Command",
            description=f"command `{command}` succesfully executed on server `{server_id}`",
            colour=Enum.Embeds.Colors.Success,
        )

        await interaction.response.send_message(embed=embed)

        channel = interaction.guild.get_channel(1096169064382087260)

        embed = discord.Embed(
            title="Game Command Ran",
            description=f"command `{command}` executed on server `{server_id}`",
            colour=Enum.Embeds.Colors.Info,
        )

        thumbnails = await self.roblox_client.thumbnails.get_user_avatar_thumbnails(
            [user], roblox.AvatarThumbnailType.headshot, is_circular=True
        )

        embed.set_author(name=user.name, icon_url=thumbnails[0].image_url)

        await channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Roblox(bot))
