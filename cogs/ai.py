"""The AI module of B0BBA"""

import traceback
import logging
import secrets
import os

import discord

from discord import app_commands
from discord.ext import commands

from async_openai import OpenAI
from modules.enums import Enum
from modules.gpt_data import prompts as FED_DATA

FREE_MODELS = ["gpt-3.5-turbo"]
BLACKLISTED_WORDS = ["https://", "http://"]


class AI(commands.Cog, name="ai"):
    """AI features of B0BBA"""

    def __init__(self, bot):
        self.bot = bot

    async def multitoken_gpt(self, interaction, prompt, idx: int = 0):
        """Uses tokens specified below to answer to the prompt"""

        tokens = os.environ.get("OPENAI_KEYS", "").split(",")

        messages = FED_DATA
        messages = messages + [
            {
                "role": "user",
                "content": f"""
        My name is: "{interaction.user}".
        My profile picture is "{interaction.user.avatar}".""",
            }
        ]

        messages = messages + [{"role": "user", "content": prompt}]

        try:
            OpenAI.api_key = tokens[idx]

            return await OpenAI.chat.async_create(
                model="gpt-3.5-turbo",
                temperature=0,
                messages=messages,
            )

        except Exception:  # pylint: disable=broad-exception-caught
            if idx < len(tokens) - 1:
                await self.multitoken_gpt(
                    interaction=interaction, prompt=prompt, idx=idx + 1
                )
                return

            await interaction.followup.send("https://http.cat/429")

            logging.getLogger("b0bba.ai.gpt").error(
                "Error occured while trying to get a prompt! Traceback: %s",
                traceback.format_exc(),
            )

    @app_commands.command()
    @commands.guild_only()
    async def gpt(self, interaction: discord.Interaction, *, prompt: str) -> None:
        await interaction.response.defer()

        async with interaction.channel.typing():
            chat = await self.multitoken_gpt(interaction, prompt)

            result_string = chat.messages[0].content
            if len(result_string) >= 1900:
                filename = secrets.token_hex(4)

                with open(f"./temp/{filename}.txt", "w", encoding="utf-8") as file:
                    file.write(result_string)
                    file.close()

                with open(f"./temp/{filename}.txt", "rb") as file:
                    await interaction.followup.send(
                        f"The response was too long, so it's sent as a file. (Author: {interaction.user})",
                        file=discord.File(file, filename="result.txt"),
                    )

                os.remove(f"./temp/{filename}.txt")
            else:
                embed = discord.Embed(
                    title="Result",
                    description=result_string,
                    colour=Enum.Embeds.Colors.Success,
                )
                embed.set_author(
                    name="BIG Thanks to corrupted sackboye#6711 for helping to revive B0BBA GPT!"
                )
                embed.set_footer(text=f"Requested by: {interaction.user}")
                await interaction.followup.send(embed=embed)


async def setup(bot):
    """The setup function for the AI module

    Args:
        bot (discord.Bot): The bot object
    """
    await bot.add_cog(AI(bot))
