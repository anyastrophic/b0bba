"""The fun module of B0BBA"""

import asyncio
import os
import random
import time
from io import BytesIO
from typing import List

import aiofiles
import discord
from discord import app_commands
from discord.ext import commands
from PIL import Image, ImageDraw

from games.hangman.game import HangmanGame
from games.unscramble.game import UnscrambleGame
from games.wordle.game import WordleGame
from modules.loggers import Logger

words = []
with open("./games/words.txt", "r", encoding="utf-8") as f:
    words = f.read().splitlines()

    f.close()

user_games = {}


class Fun(commands.Cog, name="fun"):
    """The class containing the fun-ctions haha get it"""

    def __init__(self, bot):
        self.bot = bot

    async def create_game(
        self, game_class: object, interaction: discord.Interaction
    ) -> None:
        """Creates a game loop

        Args:
            game_class (object): game class, such as HangmanGame, UnscrambleGame, or WordleGame
            interaction (discord.Interaction): discord.py interaction

        Returns:
            None: None
        """
        if interaction.user.id in user_games:
            await interaction.response.send_message(
                "You already have a game running! Say `!cancel-game` to cancel any running game."
            )
            return

        game = game_class(interaction.user.name)
        user_games[interaction.user.id] = {"game": game}
        await interaction.response.send_message(await game.get_output())

        def game_check(message) -> bool:
            return (
                message.author == interaction.user
                and message.channel.id == interaction.channel.id
            )

        async def game_loop() -> None:
            msg = await self.bot.wait_for("message", check=game_check)

            guess_result = await game.guess(msg.content.lower())

            match guess_result:
                case "mid-game":
                    await interaction.followup.send(await game.get_output("mid-game"))
                    try:
                        await game_loop()
                    except:  # pylint:disable=bare-except
                        return
                case _:
                    await interaction.followup.send(await game.get_output(guess_result))

        try:
            await game_loop()
        except:  # pylint:disable=bare-except
            return

        if interaction.user.id in user_games:
            user_games.pop(interaction.user.id)

    @app_commands.command(name="cancel_game")
    async def cancelgame(self, interaction: discord.Interaction) -> None:
        """Cancels a running game, app command

        Args:
            interaction (discord.Interaction): discord.py interaction
        """
        if interaction.user.id in user_games:
            user_games.pop(interaction.user.id)

        await interaction.response.send_message(
            "If there was a running game, it was canceled."
        )

    @app_commands.command()
    @commands.guild_only()
    async def unscramble(self, interaction: discord.Interaction) -> None:
        """launches a game of unscramble"""

        await self.create_game(UnscrambleGame, interaction)

    @app_commands.command()
    @commands.guild_only()
    async def hangman(self, interaction: discord.Interaction) -> None:
        """launches a game of hangman"""

        await self.create_game(HangmanGame, interaction)

    @app_commands.command()
    @commands.guild_only()
    async def wordle(self, interaction: discord.Interaction) -> None:
        """launches a game of wordle"""

        await self.create_game(WordleGame, interaction)

    @app_commands.command(name="wpm_test")
    @commands.guild_only()
    async def wpm_test(
        self, interaction: discord.Interaction, word_count: int = 40
    ) -> None:
        """starts a words per minute test"""

        def check(message) -> bool:
            return (
                message.author == interaction.user
                and message.channel.id == interaction.channel.id
            )

        test_list = random.choices(words, k=word_count)
        test = " ".join(test_list)

        countdown = 5
        message = await interaction.response.send_message(
            "The typing test begins in: 5"
        )

        while True:
            await asyncio.sleep(1)
            countdown -= 1
            await message.edit(content=f"The typing test begins in: {countdown}")
            if countdown == 0:
                break

        await message.edit(content=test)

        start_timestamp = time.time() + self.bot.latency

        msg = await self.bot.wait_for("message", check=check)
        msg_split = msg.content.split(" ")

        end_timestamp = time.time()
        minutes = (end_timestamp - start_timestamp) / 60

        correct_characters = 0
        total_characters = 0
        for i, test_lists in enumerate(test_list):
            if test_lists == msg_split[i]:
                correct_characters += len(test_lists) + 1  # +1 for a space

            total_characters += len(test_lists) + 1

        wpm = (correct_characters / 5) / minutes
        raw_wpm = (total_characters / 5) / minutes

        accuracy = wpm / raw_wpm

        await interaction.followup.send(
            f"result:\nraw wpm: {round(raw_wpm, 2)}\n" + 
            f"wpm: {round(wpm, 2)}\naccuracy: {round(accuracy * 100)}%\n" + 
            "\nnote: between you and the bot there is quite a lot of ping." + 
            "if you want 100% accurate results," + 
            "use a website like <https://monkeytype.com>"
        )

    @app_commands.command(name="impersonate")
    @app_commands.checks.cooldown(1, 120)
    @commands.guild_only()
    async def impersonate(
        self, interaction: discord.Interaction, member: discord.Member, text: str
    ) -> None:
        """Impersonates someone"""
        if member.bot:
            await interaction.response.send_message(
                "Sorry, but you're not allowed to use `/impersonate` on bots!",
                ephemeral=True,
            )

            return

        webhook = await interaction.channel.create_webhook(name=member.display_name)

        message = await webhook.send(
            f"{text}\n\n**this message is made up by {interaction.user} via the" + 
            "**`/impersonate` **command, please don't take it seriously**",
            allowed_mentions=discord.AllowedMentions.none(),
            username=member.display_name,
            avatar_url=member.display_avatar,
            wait=True,  # apparently this is needed for it to return a WebhookMessage
        )

        Logger.Fun.Impersonate.UserImpersonated(interaction.user, member, message)

        await webhook.delete()

        await interaction.response.send_message("Done!", ephemeral=True)

    async def save_image(self, path: str, image: memoryview) -> None:
        """Asynchronously save an image

        Args:
            path (str): The path to the image
            image (memoryview): The image
        """
        async with aiofiles.open(path, "wb") as file:
            await file.write(image)

    async def circle_overlay(self, image, overlay_image, mask=None, size: int = 0):
        """Circle overlay"""
        old_size = image.size
        new_size = (265 + size, 265 + size)
        overlay_image = overlay_image.resize(new_size)
        new_im = overlay_image
        box = tuple((n - o) // 2 for n, o in zip(new_size, old_size))
        new_im.paste(image, box, mask=mask)

        return new_im

    async def add_pfp_border(
        self,
        pfp,
        border,
        size,
    ):
        """Add an image border around another image

        Args:
            pfp (Image): The first image (pfp)
            border (Image): The border
            size (int): The size to add

        Returns:
            Image: The result image
        """
        width, height = pfp.size
        length = (width - height) // 2
        img_cropped = pfp.crop((length, 0, length + height, height))
        mask = Image.new("L", img_cropped.size)
        mask_draw = ImageDraw.Draw(mask)
        width, height = img_cropped.size
        mask_draw.ellipse((0, 0, width, height), fill=255)
        img_cropped.putalpha(mask)

        overlayed_image = await self.circle_overlay(
            img_cropped, border.convert("RGB"), mask=mask, size=size
        )

        return overlayed_image

    async def pfp_command(self, interaction, border_size, border_image_name: str):
        """Adds a transgender border to your profile picture"""
        if border_size > 500:
            await interaction.response.send_message(
                "That border size is a little too much!"
            )
            return

        filename = interaction.user.id
        image_path = f"./temp/{filename}.png"

        await interaction.user.avatar.save(image_path)

        img = Image.open(image_path).convert("RGB").resize((265, 265))
        img = await self.add_pfp_border(
            img, Image.open(f"./files/pride_flags/{border_image_name}"), border_size
        )

        buffer = BytesIO()
        img.save(buffer, format="PNG")

        await self.save_image(  # pylint: disable=too-many-function-args
            image_path,  # pylint: disable=too-many-function-args
            buffer.getbuffer(),  # pylint: disable=too-many-function-args
        )  # pylint: disable=too-many-function-args

        await interaction.response.send_message(file=discord.File(image_path))

    pfp_commands = app_commands.Group(name="pfp", description="PFP border commands")

    flag_list = os.listdir("./files/pride_flags")

    @pfp_commands.command()
    @app_commands.checks.cooldown(1, 10)
    async def pride(
        self, interaction: discord.Interaction, flag: str, border_size: int = 20
    ):
        """Adds a pride flag border of your choice to your profile picture"""
        if flag not in self.flag_list:
            await interaction.response.send_message(
                "This flag doesn't exist in the bot!"
            )
            return

        await self.pfp_command(interaction, border_size, flag)

    @pride.autocomplete("flag")
    async def _flag_autocomplete(
        self, _: discord.Interaction, current: str
    ) -> List[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=item[:-4].capitalize(), value=item)
            for item in self.flag_list
            if current.lower() in item.lower()
        ]


async def setup(bot):
    """The setup function for the moderation module

    Args:
        bot (discord.Bot): The bot object
    """
    await bot.add_cog(Fun(bot))
