import discord
from discord import app_commands

class RegisterModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Register")

        self.user_name = discord.ui.TextInput(
            label="Username",
            placeholder="Enter your username"
        )

        self.api_key = discord.ui.TextInput(
            label="API Key",
            placeholder="Enter your API key"
        )      

        async def on_submit(self, interaction: discord.Interaction):
            await interaction.response.send_message("You have registered successfully!")
            self.stop()

        async def on_error(self, interaction: discord.Interaction, exception: Exception):
            await interaction.response.send_message("An error occurred: {exception}")
            self.stop()
    