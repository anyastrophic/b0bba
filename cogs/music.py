import os
import logging
import discord
import audio_metadata

from asyncio import sleep

from modules.enums import Enum

from modules.loggers import Logger

from discord.ext import commands
from discord import app_commands

from gtts import gTTS

def is_owner(user):
    return user.id in [804066391614423061]

class Music(commands.Cog, name = "music"):
    def __init__(self, bot):
        self.bot = bot
        self.song_metadata = {}
 
    @app_commands.command()
    async def song_info(self, interaction: discord.Interaction):
        """ Info about the currently playing song """

        title = f'Failed to fetch metadata! local storage file name: {self.audio_file_name}'
        album = title
        artist = album
        duration = artist

        try:
            title = self.song_metadata.tags.title[0]
            album = self.song_metadata.tags.album[0]
            artist = self.song_metadata.tags.artist[0]
            duration = self.song_metadata.streaminfo.duration
        except:
            pass

        embed = discord.Embed(
            title = f'Current Song: {title}',
            colour = Enum.Embeds.Colors.Info
        )

        embed.add_field(
            name = 'Title',
            value = title,
            inline = False
        )

        embed.add_field(
            name = 'Album',
            value = album,
            inline = False
        )

        embed.add_field(
            name = 'Artist',
            value = artist,
            inline = False
        )

        embed.add_field(
            name = 'Duration',
            value = f'{round(duration / 60, 1)} mins',
            inline = False
        )

        await interaction.response.send_message(
            embed = embed
        )

    async def play_file(self, path: str, sleep_time: float = 0.1):
        """This function is used to play a music file in the voice client the bot has assigned

        Args:
            path (str): music file path
            sleep_time (float, optional): how many seconds to wait until checking again if any music is playing. Defaults to 0.1.
        """
        self.vc.stop()

        self.vc.play(discord.FFmpegPCMAudio(
            path,
        ))

        while self.vc.is_playing():
            await sleep(sleep_time)

    @app_commands.command(
        name = 'play_file'
    )
    async def _play_file(self, interaction: discord.Interaction, filename: str):
        if not is_owner(interaction.user): 
            await interaction.response.send_message(
                'owneronly command'
            )

            return
        
        self.queue.append(rf'\\KEENETIC\Seagate Basic\Stuff\Music\{filename}')
        
        await self.vc.stop()


    @commands.Cog.listener()
    async def on_ready(self):
        return
        
        queue = os.listdir(r"\\KEENETIC\Seagate Basic\Stuff\Music")

        self.queue = []
        for i in queue:
            if i.endswith(".mp3"):
                self.queue.append(rf"\\KEENETIC\Seagate Basic\Stuff\Music\{i}")

        self.bot.UB_CHANNELS['b0bba-radio'] = self.bot.UB_GUILD.get_channel(1107239543511457814)

        self.vc = await self.bot.UB_CHANNELS['b0bba-radio'].connect()

        while True:
            song = self.queue[-1]

            self.queue.pop(-1)

            title = 'Fetching metadata failed!'
            artist = title

            try:
                self.song_metadata = audio_metadata.load(song)

                title = self.song_metadata.tags.title[0]
                artist = self.song_metadata.tags.artist[0]

                self.audio_file_name = song
            except:
                Logger.Music.FetchingMetadataFailed()
                
            await self.bot.change_presence(
                activity = discord.Activity(
                    type=discord.ActivityType.listening, 
                    name = f'{title} - {artist}'
                )
            )

            await self.play_file(song)
        

async def setup(bot):
    await bot.add_cog(Music(bot))