import os
import sys
import git
import discord

from discord.ext import commands
from discord import app_commands

from modules.database_utils import Registration
from modules.eval import Eval


def is_owner(user):
    return user.id in [804066391614423061]


class Owner(commands.Cog, name="owner"):
    def __init__(self, bot):
        self.bot = bot

    owner_commands = app_commands.Group(name="owner", description="Owner commands")

    @owner_commands.command()
    async def role(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        role: discord.Role,
    ) -> None:
        if not is_owner(interaction.user):
            return

        if role in member.roles:
            await member.remove_roles(role)
        else:
            await member.add_roles(role)

        await interaction.response.send_message("ok")

    @owner_commands.command()
    @commands.is_owner()
    async def blacklist(
        self,
        interaction: discord.Interaction,
        user: discord.User,
        *,
        reason: str = "No reason specified",
    ) -> None:
        if not is_owner(interaction.user):
            return

        registration = Registration(user.id)

        already_blacklisted = await registration.check_registration("blacklist")
        await registration.blacklist(reason)

        if already_blacklisted:
            await interaction.response.send_message(
                f"`{user}` is already blacklisted for `{already_blacklisted['reason']}`"
            )

        await interaction.response.send_message(
            f"`{user}` successfully blacklisted for `{reason}`"
        )

    @owner_commands.command()
    @commands.is_owner()
    async def restart(self, interaction: discord.Interaction):
        if not is_owner(interaction.user):
            return

        await interaction.response.send_message("Restarting")

        os.startfile("main.py")
        sys.exit()

    @owner_commands.command()
    @commands.is_owner()
    async def reload(self, interaction: discord.Interaction, module: str):
        if not is_owner(interaction.user):
            return

        msg = await interaction.response.send_message(f"Reloading {module}")

        await self.bot.unload_extension(f"cogs.{module}")
        await self.bot.load_extension(f"cogs.{module}")

        await msg.edit(content=f"Reloaded {module}")

    @owner_commands.command()
    @commands.is_owner()
    async def disable_command(self, interaction: discord.Interaction, command: str):
        if not is_owner(interaction.user):
            return

        cmd = self.bot.get_command(command)
        cmd.enabled = False

        await interaction.response.send_message(f"command {command} disabled")

    @owner_commands.command()
    @commands.is_owner()
    async def enable_command(self, interaction: discord.Interaction, command: str):
        if not is_owner(interaction.user):
            return

        cmd = self.bot.get_command(command)
        cmd.enabled = True

        await interaction.response.send_message(f"command {command} enabled")

    @commands.command(name="eval")
    async def eval_fn(self, ctx, *, code: str):
        if not is_owner(ctx.message.author):
            return

        eval_obj = Eval(code)
        result = await eval_obj.evaluate(ctx, self)

        await ctx.send(result)

    @commands.command()
    async def pull_and_restart(self, ctx):
        if not is_owner(ctx.message.author):
            return

        await ctx.reply("ok")

        g = git.cmd.Git(".")
        g.pull()

        os.startfile("main.py")

        pid = os.getpid()
        os.system(f"taskkill /F /PID {pid}")

    # @owner_commands.command()
    # @commands.is_owner()
    # async def run_as_user(self, interaction: discord.Interaction, user: discord.User, command: str, arg1: str = None):
    #     if not is_owner(interaction.user): return

    #     # NO MORE OWNER CHECKS AFTER THIS LINE!!! CAUTION !!!

    #     interaction.user = user

    #     if arg1:

    #         await self.bot.tree.get_command(command).callback(self, interaction, arg1)
    #     else:
    #         await self.bot.tree.get_command(command).callback(self, interaction)


async def setup(bot):
    await bot.add_cog(Owner(bot))
