"""The moderation module of B0BBA"""

import asyncio
from datetime import timedelta

from discord.ext import commands

reaction_cache = {}


class Moderation(commands.Cog, name="moderation"):
    """Moderation features of B0BBA"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """The function that gets called when a user reacts to a message

        Args:
            reaction (_type_): The reaction
            user (discord.User): The user
        """
        if not user in reaction_cache:
            reaction_cache[user] = 0

        reaction_cache[user] += 1

        if reaction_cache[user] > 5:
            reaction_cache[user] = 0

            await reaction.message.channel.send(
                f"`{user}` timed out for spamming reactions!", delete_after=5
            )

            await user.timeout(timedelta(minutes=1), reason="Reaction spam")

        await asyncio.sleep(20)

        reaction_cache[user] -= 1


async def setup(bot):
    """The setup function for the moderation module

    Args:
        bot (discord.Bot): The bot object
    """
    await bot.add_cog(Moderation(bot))
