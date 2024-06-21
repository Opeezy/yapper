import discord
import os
import logging
import uuid
import sys

from discord.ext import commands
from discord.ext.commands import Bot
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv
from datetime import datetime
from logging import Logger


load_dotenv()

__version__ = "0.1.0"

# Constants
TOKEN = os.getenv('DISCORD_TOKEN')

class Yapper(commands.Bot):
    def __init__(self, prefix, intents):
        super().__init__(command_prefix=prefix, intents=intents)
        self.logger = None

        self.add_commands()
        self.init_logger()

    def add_commands(self):
        @self.command(name='ping', pass_context=True)
        async def ping(ctx):
            await ctx.channel.send('Pong!') 

    def init_logger(self):
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


if  __name__ == '__main__':
    intents = discord.Intents.default()
    intents.message_content = True

    bot = Yapper(
        prefix=">", 
        intents=intents
    )

    bot.run(TOKEN)