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

    voice = discord.ui.TextInput(
        label="Voice ID",
        placeholder="Voice ID here",
        style=discord.TextStyle.short
    ) 

    similarity = discord.ui.TextInput(
        label="Similarity boost",
        placeholder="0.5",
        style=discord.TextStyle.short
    )

    stability = discord.ui.TextInput(
        label="Stability",
        placeholder="0.5",
        style=discord.TextStyle.short
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