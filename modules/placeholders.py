import discord

class Placeholder:
    class Games:
        class Hangman:
            class GameResponses:
                MidGame = "{}'s hangman game!\nGuess the word: `{}`\nTries left: {}"
                Lose = "{}'s hangman game!\nYou lost! The word was: {}"
                Win = "{}'s hangman game!\nYou won! The word was: {}"

        class Unscramble:
            class GameResponses:
                MidGame = "{}'s unscramble game!\nGuess the word: `{}`\nTries left: {}"
                Lose = "{}'s unscramble game!\nYou lost! The word was: {}"
                Win = "{}'s unscramble game!\nYou won! The word was: {}"

    class Errors:
        class RobloxUtils:
            BadResponse = "Response status != 200.\nPlease contact Anya."

            UsernameNotFound = "The ROBLOX account with the username you provided wasn't found"