import discord
import sqlite3

from discord import app_commands
from discord import Interaction

class RegisterModal(discord.ui.Modal, title="Register"):
    def __init__(self, cursor: sqlite3.Cursor):
        self.cursor = cursor

    api_key = discord.ui.TextInput(
        label="API Key",
        placeholder="Enter your API key"
    )      

    async def on_submit(self, interaction: Interaction):
        id = interaction.user.id
        user_name = interaction.user.name
        api_key = self.api_key.value

        self.cursor.execute(f"INSERT INTO users (id, UserName, APIKey) VALUES ({id}, {user_name}, {api_key})")
        await interaction.response.send_message("You have registered successfully!")

    async def on_error(self, interaction: discord.Interaction, exception: Exception):
        await interaction.response.send_message("An error occurred: {exception}")
    