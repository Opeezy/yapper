import discord
import os
import logging
import uuid
import sys
import sqlite3
import asyncio

from discord import Client, User
from discord.ext import commands
from discord.ext.commands import Context, Bot
from discord import app_commands
from elevenlabs import save, GetVoicesResponse
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv
from datetime import datetime
from logging import Logger
from modals  import RegisterModal, YapModal
from sqlite3 import Cursor
from typing import Tuple
from time import sleep


load_dotenv()

__version__ = "0.1.0"

# Constants
TOKEN = os.getenv('DISCORD_TOKEN')
FFMPEG = os.path.join(os.getcwd(), "ffmpeg\\ffmpeg.exe")

class Yapper(discord.Client):
    def __init__(self, intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.logger = None
        self.db = None
        self.cursor = None

        self.init_logger()
        self.logger.debug("Logger initialized")

        self.add_commands()
        self.logger.debug("Commands added")

        self.check_db()
        self.check_audio_dir()

    async def on_ready(self):
       self.logger.info(f'{self.user} has connected to Discord!') 

    async def setup_hook(self):
        async for guild in self.fetch_guilds():
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)

    def add_commands(self) -> None:
        @self.tree.command(name='voices', description='Get all voice ids for user')
        async def voices(interaction: discord.Interaction):
            cursor = self.get_cursor()
            cursor.execute(f'SELECT id, APIKey FROM users WHERE id = {interaction.user.id}')
            user_info = cursor.fetchone()

            if user_info is None:
                await interaction.response.send_message("You have not registered an api key.", ephemeral=True)
            else:
                client = ElevenLabs(
                    api_key=user_info[1]
                )
                voice_response = client.voices.get_all()
                voices = voice_response.dict()['voices']
                voice_string = "Here are a list of available voices:\n\n"
                
                for voice in voices:
                    voice_string += f'Name: {voice['name']} | ID: {voice['voice_id']}\n'
                
                await interaction.response.send_message(voice_string, ephemeral=True)    

        @self.tree.command(name='yap', description='Generate text using ElevenLabs API')
        async def yap(interaction: discord.Interaction):
            # Checking if we are already in a voice channel
            voice_clients = self.voice_clients
            if len(voice_clients) > 0:
                await interaction.response.send_message("Yapper is already in a channel.", ephemeral=True)
            else:
                # Here we check for if the user has registered an api key
                cursor = self.get_cursor()
                cursor.execute(f'SELECT * FROM users WHERE id = {interaction.user.id}')
                user_info  = cursor.fetchone()
                self.logger.debug(f'User info fetched: {user_info}')

                if user_info is None:
                    # If not, we tell them to register
                    await interaction.response.send_message("User not found. Please register using `>register`", ephemeral=True)
                else:
                    # Otherwise, gather their info
                    username = user_info[1]
                    api_key = user_info[2]
                    self.logger.debug(f"User {username} requested API key: {api_key}")

                    # Instantiate the modal for their prompt
                    yap_modal = YapModal()

                    # Send modal and wait for submition
                    await interaction.response.send_modal(yap_modal)
                    await yap_modal.wait()

                    # Validate if mp3 file was generated
                    audio_file, audio_generated = self.generate_audio(yap_modal.text.value, yap_modal.voice.value, api_key)
                    if audio_generated:
                        # If so, check if user is in a voice channel
                        voice_state = interaction.user.voice
                        if voice_state is not None:
                            # If so, we want to join the channel and play the audio to completion
                            self.logger.debug(f"User {username} is in a voice channel: {voice_state}")
                            voice_channel = voice_state.channel
                            voice_client = await voice_channel.connect() 
                            voice_client.play(discord.FFmpegPCMAudio(executable=FFMPEG, source=audio_file))

                            while voice_client.is_playing():
                                await asyncio.sleep(.1)
                            await voice_client.disconnect()
                            self.logger.debug(f"Removing file {audio_file}")
                            os.remove(audio_file)
                        else:
                            # Else, we tell them they need to be in voice
                            self.logger.debug(f"User {username} is not in a voice channel")
                            await interaction.followup.send("You need to be in a voice channel to use this command", ephemeral=True)

                    else:
                        self.logger.debug(f"Audio not generated for user {username}")

        
        @self.tree.command(name='register', description='Register with ElevenLabs')
        async def register(interaction: discord.Interaction, epehemeral: bool = True):
            cursor = self.get_cursor()
            cursor.execute(f'SELECT * FROM users WHERE id = {interaction.user.id}')
            if cursor.fetchone() is not None:
                await interaction.response.send_message("You have already registered!", ephemeral=True)
            else:
                register_modal = RegisterModal()
                await interaction.response.send_modal(register_modal)
            

    def init_logger(self) -> None:
        log_dir = os.path.join(os.getcwd(), 'logs')
        if os.path.exists(log_dir) == False:
            os.mkdir(log_dir)

        date = datetime.today().strftime('%Y-%m-%d')
        log_date_dir = os.path.join(log_dir, date)

        log_id = uuid.uuid4().hex

        if os.path.exists(log_date_dir) == False:
            os.mkdir(log_date_dir)

        log_id_dir = os.path.join(log_date_dir, log_id)
        os.mkdir(log_id_dir)

        log_file = os.path.join(log_id_dir, 'yapper.log')

        # Setting up our logging
        logger = logging.getLogger('yapper')
        logger.setLevel(logging.DEBUG)
        file_handler = logging.FileHandler(filename=log_file, encoding='utf-8', mode='w')
        file_handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s: %(message)s'))
        stream_handler = logging.StreamHandler(stream=sys.stdout)
        stream_handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s: %(message)s'))
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

        self.logger = logger

    def check_db(self) -> None:
        if os.path.exists("yapper.db") == False:  
            self.logger.debug("Database not found. Creating new database")          
            db = sqlite3.connect('yapper.db')  
            cursor = db.cursor()      
            cursor.execute(
                '''CREATE TABLE users(
                    id INTEGER PRIMARY KEY NOT NULL UNIQUE,
                    UserName TEXT NOT NULL,
                    APIKey TEXT NOT NULL UNIQUE
                );'''
            )   
        else:
            self.logger.debug("Database found.")         
        
    def get_cursor(self) -> Cursor:        
        db = sqlite3.connect('yapper.db')  
        cursor = db.cursor()
        
        return cursor
    
    def check_audio_dir(self):
        if os.path.exists('audio') == False:
            self.logger.debug("Audio directory not found. Creating new directory")
            os.mkdir('audio')
    
    def generate_audio(self, prompt: str, voice_id: str, api_key: str) -> Tuple[str, bool]:
        audio_id = uuid.uuid4().hex
        client = ElevenLabs(api_key=api_key)
        audio = client.generate(
            text=prompt,
            voice=voice_id,
            model="eleven_multilingual_v2"
        )

        audio_file = os.path.join('audio', f'{audio_id}.mp3')
        save(audio, audio_file)

        if os.path.exists(audio_file):
            self.logger.debug(f"Audio file generated: {audio_file}")
            return (audio_file, True)
        else:
            self.logger.debug(f"Audio file not generated: {audio_file}")
            return ("", False)

if  __name__ == '__main__':
    intents = discord.Intents.default()
    intents.message_content = True

    client = Yapper(
        intents=intents
    )

    client.run(TOKEN)