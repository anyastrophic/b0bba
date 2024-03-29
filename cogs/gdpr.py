"""The discord module, a very important module."""
import discord
from discord import app_commands
from discord.ext import commands

from modules.database_utils import delete_data


class GDPR(commands.Cog, name="GDPR"):
    """Data deletion class"""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command()
    @app_commands.guild_only()
    async def delete_data(self, interaction: discord.Interaction):
        """deletes all of your data from the B0BBA bot"""

        def check(msg):
            return (
                msg.author.id == interaction.user.id
                and msg.channel == interaction.channel
            )

        await interaction.response.send_message(
            "Are you sure you want to delete your data?"
            + " **This action is irreversible, and will blacklist you from the bot**\n"
            + "To **confirm** data deletion,"
            + f"please type your discord username ({interaction.user})\n"
            + "To **cancel** data deletion, please send any message (except your discord username)"
        )

        message = await self.bot.wait_for("message", check=check)

        if (
            message.content
            == f"{interaction.user.name}#{interaction.user.discriminator}"
        ):
            await delete_data(interaction.user.id)

            uber_role = interaction.guild.get_role(406997457709432862)

            if uber_role in interaction.user.roles:
                await interaction.user.remove_roles(uber_role)

            await interaction.followup.send(
                "Your data has been successfully deleted. Farewell!"
            )

            return

        await message.reply("Data deletion request cancelled")


async def setup(bot):
    """The setup function for the moderation module

    Args:
        bot (discord.Bot): The bot object
    """
    await bot.add_cog(GDPR(bot))
