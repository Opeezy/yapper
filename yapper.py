import discord
import os
import logging
import uuid
import sys
import sqlite3

from discord import Client
from discord.ext import commands
from discord.ext.commands import Context, Bot
from discord import app_commands
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv
from datetime import datetime
from logging import Logger
from register  import RegisterModal


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

        self.db_connect()
        self.logger.debug("Database connected")  

    async def on_ready(self):
       self.logger.info(f'{self.user} has connected to Discord!') 

    async def setup_hook(self):
        async for guild in self.fetch_guilds():
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)

    def add_commands(self) -> None:
        @self.tree.command(name='yap')
        async def yap(interaction: discord.Interaction):
            self.cursor.execute(f'SELECT UserName, APIKey FROM users WHERE id = {interaction.user.id}')
            user_info = self.cursor.fetchone()
            self.logger.debug(f'User info fetched: {user_info}')

            if user_info is None:
                await interaction.channel.send("User not found. Please register using `>register`")
            else:
                username = user_info[0]
                api_key = user_info[1]
                self.logger.debug(f"User {username} requested API key: {api_key}")
                await interaction.channel.send("Yap!")
        
        @self.tree.command(name='register', description='Register with ElevenLabs')
        async def register(interaction: discord.Interaction):
            register_modal = RegisterModal(self.cursor)
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

    def db_connect(self) -> None:
        if os.path.exists("yapper.db") == False:            
            self.db = sqlite3.connect('yapper.db')  
            self.cursor = self.db.cursor()      
            self.cursor.execute('CREATE TABLE users (id INTEGER PRIMARY KEY, UserName TEXT, APIKey TEXT)')
        else:
            self.db = sqlite3.connect('yapper.db')  
            self.cursor = self.db.cursor()


if  __name__ == '__main__':
    intents = discord.Intents.default()
    intents.message_content = True

    client = Yapper(
        intents=intents
    )

    client.run(TOKEN)