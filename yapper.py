import discord
import os
import logging
import uuid
import sys
import sqlite3

from discord import Client, User
from discord.ext import commands
from discord.ext.commands import Context, Bot
from discord import app_commands
from elevenlabs import save
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv
from datetime import datetime
from logging import Logger
from modals  import RegisterModal, YapModal
from sqlite3 import Cursor


load_dotenv()

__version__ = "0.1.0"

# Constants
TOKEN = os.getenv('DISCORD_TOKEN')

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
        @self.tree.command(name='yap', description='Generate text using ElevenLabs API')
        async def yap(interaction: discord.Interaction):
            cursor = self.get_cursor()
            cursor.execute(f'SELECT * FROM users WHERE id = {interaction.user.id}')
            user_info  = cursor.fetchone()
            self.logger.debug(f'User info fetched: {user_info}')

            if user_info is None:
                await interaction.response.send_message("User not found. Please register using `>register`", ephemeral=True)
            else:
                username = user_info[1]
                api_key = user_info[2]
                self.logger.debug(f"User {username} requested API key: {api_key}")
                
                yap_modal = YapModal()
                
                await interaction.response.send_modal(yap_modal)
                await yap_modal.wait()

                audio_generated = self.generate_audio(yap_modal.text.value, api_key)
                if audio_generated:
                    voice_state = interaction.user.voice
                    if voice_state is not None:
                        self.logger.debug(f"User {username} is in a voice channel: {voice_state}")
                        await voice_state.channel.connect()
                        self.logger.debug(client.voice_clients)
                    else:
                        self.logger.debug(f"User {username} is not in a voice channel")
                        await interaction.followup.send("You need to be in a voice channel to use this command", ephemeral=True)
    
                else:
                    self.logger.debug(f"Audio not generated for user {username}")

        
        @self.tree.command(name='register', description='Register with ElevenLabs')
        async def register(interaction: discord.Interaction, epehemeral: bool = True):
            cursor = self.get_cursor()
            cursor.execute(f'SELECT * FROM users WHERE id = {interaction.user.id}')
            if cursor.fetchone() is not None:
                await interaction.response.send_message("You have already registered!")
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
    
    def generate_audio(self, prompt: str, api_key: str) -> bool:
        audio_id = uuid.uuid4().hex
        client = ElevenLabs(api_key=api_key)
        audio = client.generate(
            text=prompt,
            voice="Rachel",
            model="eleven_multilingual_v2"
        )

        audio_file = os.path.join('audio', f'{audio_id}.mp3')
        save(audio, audio_file)

        if os.path.exists(audio_file):
            self.logger.debug(f"Audio file generated: {audio_file}")
            return True
        else:
            self.logger.debug(f"Audio file not generated: {audio_file}")
            return False

if  __name__ == '__main__':
    intents = discord.Intents.default()
    intents.message_content = True

    client = Yapper(
        intents=intents
    )

    client.run(TOKEN)