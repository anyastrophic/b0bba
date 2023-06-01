from discord.ext import commands


class RobloxUtilsError(commands.CommandError):
    def __init__(self, message="default error lol"):
        self.message = message
        super().__init__(self.message)
