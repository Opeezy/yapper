import discord
import sqlite3
import os
import traceback

from discord import app_commands
from discord import Interaction



class RegisterModal(discord.ui.Modal, title="Register"):    

    api_key = discord.ui.TextInput(
        label="API Key",
        placeholder="Enter your API key"
    )      

    async def on_submit(self, interaction: Interaction):
        if os.path.exists('yapper.db') == False:
            raise Exception("Database not found")
        else:
            db = sqlite3.connect('yapper.db')
            cursor = db.cursor()
            
            params = (
                interaction.user.id,
                interaction.user.name,
                self.api_key.value
            )        

            cursor.execute("INSERT INTO users VALUES (?, ?, ?)", params)
            db.commit()    
            
            await interaction.response.send_message("You have registered successfully!", ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, exception: Exception):
        print(traceback.format_exc())
        await interaction.response.send_message(f"A problem occured registering.", ephemeral=True)


class YapModal(discord.ui.Modal, title="Yapper"): 
    def __init__(self):
        super().__init__()


    options = [
        discord.SelectOption(label="Rachel"),
        discord.SelectOption(label="Adam", default=True),
        discord.SelectOption(label="Alice")
    ]
    voice = discord.SelectMenu(
        options=options,
        min_values=3,
        max_values=3,
        disabled=False
    )

    text = discord.ui.TextInput(
        label="Your text",
        placeholder="Input your prompt here",
        style=discord.TextStyle.paragraph
    )      

    async def on_submit(self, interaction: Interaction):
            await interaction.response.send_message("Sending your prompt...", ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, exception: Exception):
        print(traceback.format_exc())
        await interaction.response.send_message(f"A problem occured sending your prompt.", ephemeral=True)
    

    