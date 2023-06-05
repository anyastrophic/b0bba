import discord
import modules.enums as Enum


class HelpCommand:
    def __init__(self, bot) -> None:
        self.bot = bot

    async def identify_command(self, command: str, tree):
        commands = tree.get_commands()

        for cmd in commands:
            if (
                type(cmd) == discord.app_commands.Group
                and cmd.qualified_name == command
            ):
                return "command-group"

            if cmd.qualified_name == command:
                return "command"

        for cmd in commands:
            if cmd.module[5:] == command:
                return "cog"

        return "everything"

    async def get_commands_in_cog(self, cog_name, commands):
        cmds = []

        for command in commands:
            if command.module[5:] == cog_name:
                cmds.append(command)

        return cmds

    async def get_group_from_commands(self, group_name, commands):
        for cmd in commands:
            if (
                type(cmd) == discord.app_commands.Group
                and cmd.qualified_name == group_name
            ):
                return cmd

    async def get_cog(self, name, cogs):
        for cog_name, cog in cogs.items():
            if cog_name == name:
                return cog

    async def get_help(self, command: str, cogs, tree):
        commands = tree.get_commands()

        command_type = await self.identify_command(command, tree)

        match command_type:
            case "everything":
                return await self.get_bot_help(cogs, tree)

            case "command":
                return await self.get_command_help(command, tree)

            case "command-group":
                return await self.get_group_help(command, tree)

            case "cog":
                return await self.get_cog_help(command, cogs)

    async def get_bot_help(self, cogs, tree):
        commands = tree.get_commands()

        embed = discord.Embed(title="Help", color=Enum.EmbedColors.INFO)

        for cog_name, cog in cogs.items():
            value = "\t".join(
                f"`{i.qualified_name}`"
                for i in await self.get_commands_in_cog(cog_name, commands)
            )

            if value == "":
                continue

            embed.add_field(name=cog.qualified_name, value=value, inline=False)

        return embed

    async def get_command_help(self, command, tree):
        command = tree.get_command(command)

        embed = discord.Embed(
            title=f"{command.qualified_name} help", color=Enum.EmbedColors.INFO
        )

        if command.description:
            embed.description = f"`{command.description}`"

        return embed

    async def get_group_help(self, group, tree):
        group = await self.get_group_from_commands(group, tree.get_commands())

        embed = discord.Embed(
            title=f"**{group.qualified_name}** subcommands",
            colour=Enum.EmbedColors.INFO,
        )
        if group.description:
            embed.description = f"{group.description}"

        for command in group.commands:
            embed.add_field(
                name=command.qualified_name,
                value=f"`{command.description}`" or "`No description`",
                inline=False,
            )

        return embed

    async def get_cog_help(self, cog, cogs):
        cog = await self.get_cog(cog, cogs)

        embed = discord.Embed(
            title=f"**{cog.qualified_name}** commands", colour=Enum.EmbedColors.INFO
        )
        if cog.description:
            embed.description = cog.description
        for command in cog.get_app_commands():
            embed.add_field(
                name=command.qualified_name,
                value=f"`{command.description}`" or "`No description`",
                inline=False,
            )

        return embed
