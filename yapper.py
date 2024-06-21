import discord
import os
import logging
import uuid
import sys
import sqlite3

from discord.ext import commands
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

class Yapper(commands.Bot):
    def __init__(self, prefix, intents):
        super().__init__(command_prefix='>', intents=intents)
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
        async for guild in self.fetch_guilds():
            print(guild.name)
        self.logger.info(f'{self.user} has connected to Discord!') 

    def add_commands(self) -> None:
        @self.command(name='yap', pass_context=True)
        async def yap(ctx):
            self.cursor.execute(f'SELECT UserName, APIKey FROM users WHERE id = {ctx.author.id}')
            user_info = self.cursor.fetchone()
            self.logger.debug(f'User info fetched: {user_info}')

            if user_info is None:
                await ctx.channel.send("User not found. Please register using `>register`")
            else:
                username = user_info[0]
                api_key = user_info[1]
                self.logger.debug(f"User {username} requested API key: {api_key}")
                await ctx.channel.send("Yap!")
        
        @self.command(name='register', pass_context=True)
        async def register(ctx):
            register_modal = RegisterModal()
            await ctx.interaction.response.send_modal(register_modal)
            

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
        prefix='>',
        intents=intents
    )

    client.run(TOKEN)