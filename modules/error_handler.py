import discord
from discord.ext import commands
from discord import app_commands

from modules import b0bba_error
from modules.enums import Enum

replies = []
async def error_handler(bot, interaction: discord.Interaction, error):
    description = f"```py\n{error}```"
    ephemeral = False

    if isinstance(error, b0bba_error.RobloxUtilsError):
        description = error.message

    #if isinstance(error, commands.ConversionError)

    if isinstance(error, app_commands.CommandOnCooldown):
        ephemeral = True
        
        time = error.retry_after
        day = time // (24 * 3600)
        time = time % (24 * 3600)
        hour = time // 3600
        time %= 3600
        minutes = time // 60
        time %= 60
        seconds = time
        
        timedict = {}
        timestring = "This command is on cooldown\nTime left: "

        if day > 0:
            timedict['days'] = round(day)

        if hour > 0:
            timedict['hours'] = round(hour)

        if minutes > 0:
            timedict['minutes'] = round(minutes)

        timedict['seconds'] = round(seconds)

        for k,v in timedict.items():
            timestring = timestring + f"`{v} {k}`, "

        description = timestring[:len(timestring) - 2]
    
    if isinstance(error, app_commands.CheckFailure):
        document = await bot.DB['blacklist'].find_one({"discord_id": interaction.user.id})
        
        if document is not None:
            if not interaction.user in replies:
                await interaction.response.send_message(f"You're blacklisted!\nReason: {document['reason']}\n")

                replies.append(interaction.user)
            return

    embed = discord.Embed(title = "Error", description = description, color=Enum.Embeds.Colors.Error)
    await interaction.response.send_message(
        embed = embed,
        ephemeral = ephemeral
    )

async def legacy_error_handler(bot, ctx, error):
    description = f"```py\n{error}```"

    
    if isinstance(error, commands.CommandNotFound):
        return

    if isinstance(error, b0bba_error.RobloxUtilsError):
        description = error.message

    #if isinstance(error, commands.ConversionError)

    if isinstance(error, app_commands.CommandOnCooldown):
        time = error.retry_after
        day = time // (24 * 3600)
        time = time % (24 * 3600)
        hour = time // 3600
        time %= 3600
        minutes = time // 60
        time %= 60
        seconds = time
        
        timedict = {}
        timestring = "This command is on cooldown\nTime left: "

        if day > 0:
            timedict['days'] = round(day)

        if hour > 0:
            timedict['hours'] = round(hour)

        if minutes > 0:
            timedict['minutes'] = round(minutes)

        timedict['seconds'] = round(seconds)

        for k,v in timedict.items():
            timestring = timestring + f"`{v} {k}`, "

        description = timestring[:len(timestring) - 2]

    embed = discord.Embed(title = "Error", description = description, color=Enum.Embeds.Colors.Error)
    await ctx.send(embed = embed)