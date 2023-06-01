import time
import asyncio
import discord
import aiodocker

import random

from discord import app_commands

from discord.ext import commands
from games.hangman.game import HangmanGame
from games.unscramble.game import UnscrambleGame
from games.wordle.game import WordleGame

from modules.loggers import Logger

words = []
with open(f"./games/words.txt", "r") as f:
    words = f.read().splitlines()

    f.close()

user_games = {}

class Fun(commands.Cog, name = "fun"):
    def __init__(self, bot):
        self.bot = bot

    async def create_game(self, game_class: object, interaction: discord.Interaction) -> None:
        """Creates a game loop

        Args:
            game_class (object): game class, such as HangmanGame, UnscrambleGame, or WordleGame
            interaction (discord.Interaction): discord.py interaction

        Returns:
            None: None
        """
        if interaction.user.id in user_games: await interaction.response.send_message("You already have a game running! Say `!cancel-game` to cancel any running game."); return
        
        game = game_class(interaction.user.name)
        user_games[interaction.user.id] = {"game": game}
        await interaction.response.send_message(await game.get_output())

        def game_check(message) -> bool:
            return (message.author == interaction.user and message.channel.id == interaction.channel.id)

        async def game_loop() -> None:
            msg = await self.bot.wait_for("message", check = game_check)

            guess_result = await game.guess(msg.content.lower())

            match guess_result:
                case "mid-game":
                    await interaction.followup.send(await game.get_output("mid-game"))
                    try:
                        await game_loop()
                    except:
                        return
                case _:
                    await interaction.followup.send(await game.get_output(guess_result))

                
        try:
            await game_loop()
        except:
            return
        
        if interaction.user.id in user_games:
            user_games.pop(interaction.user.id)

    @app_commands.command(name = "cancel_game")
    async def cancelgame(self, interaction: discord.Interaction) -> None:
        """Cancels a running game, app command

        Args:
            interaction (discord.Interaction): discord.py interaction
        """
        await asyncio.sleep(0.1)
        if interaction.user.id in user_games:
            user_games.pop(interaction.user.id)
        await interaction.response.send_message('If there was a running game, it was canceled.')

    @app_commands.command()
    @commands.guild_only()
    async def unscramble(self, interaction: discord.Interaction) -> None:
        """launches a game of unscramble"""
        
        await self.create_game(
            UnscrambleGame, 
            interaction
        )

    @app_commands.command()
    @commands.guild_only()
    async def hangman(self, interaction: discord.Interaction) -> None:
        """launches a game of hangman"""
        
        await self.create_game(
            HangmanGame, 
            interaction
        )

    @app_commands.command()
    @commands.guild_only()
    async def wordle(self, interaction: discord.Interaction) -> None:
        """launches a game of wordle"""
        
        await self.create_game(
            WordleGame, 
            interaction
        )

    @app_commands.command(name = "wpm_test")
    @commands.guild_only()
    async def wpm_test(self, interaction: discord.Interaction, word_count: int = 40) -> None:
        """starts a words per minute test"""
        
        def check(message) -> bool:
            return (message.author == interaction.user and message.channel.id == interaction.channel.id)
        
        test_list = random.choices(words, k = word_count)
        test = " ".join(test_list)

        countdown = 5
        message = await interaction.response.send_message("The typing test begins in: 5")

        while True:
            await asyncio.sleep(1)
            countdown -= 1
            await message.edit(content = f"The typing test begins in: {countdown}")
            if countdown == 0: break
            
        await message.edit(content = test)

        start_timestamp = time.time() + self.bot.latency

        msg = await self.bot.wait_for("message", check = check)
        msg_split = msg.content.split(" ")

        end_timestamp = time.time()
        minutes = (end_timestamp - start_timestamp) / 60

        correct_characters = 0
        total_characters = 0
        for i in range(len(test_list)):
            if test_list[i] == msg_split[i]:
                correct_characters += len(test_list[i]) + 1 # +1 for a space
            
            total_characters += len(test_list[i]) + 1

        wpm = (correct_characters / 5) / minutes
        raw_wpm = (total_characters / 5) / minutes

        accuracy = wpm/raw_wpm

        await interaction.followup.send(f"result:\nraw wpm: {round(raw_wpm, 2)}\nwpm: {round(wpm, 2)}\naccuracy: {round(accuracy * 100)}%\n\nnote: between you and the bot there is quite a lot of ping. if you want 100% accurate results, use a website like <https://monkeytype.com>")
        
    @app_commands.command(name = "impersonate")
    @app_commands.checks.cooldown(1, 120)
    @commands.guild_only()
    async def impersonate(self, interaction: discord.Interaction, member: discord.Member, text: str) -> None:
        if member.bot:
            await interaction.response.send_message(
                'Sorry, but you\'re not allowed to use `/impersonate` on bots!',
                ephemeral = True
            )
            
            return
        
        webhook = await interaction.channel.create_webhook(
            name = member.display_name
        )
        
        message = await webhook.send(
            f'{text}\n\n**this message is made up by {interaction.user} via the **`/impersonate` **command, please don\'t take it seriously**',
            allowed_mentions=discord.AllowedMentions.none(),
            username = member.display_name, 
            avatar_url = member.display_avatar,
            wait = True # apparently this is needed for it to return a WebhookMessage
        )
        
        Logger.Fun.Impersonate.UserImpersonated(
            interaction.user,
            member,
            message
        )
        
        await webhook.delete()
        
        await interaction.response.send_message(
            'Done!',
            ephemeral = True
        )


async def setup(bot):
    await bot.add_cog(Fun(bot))