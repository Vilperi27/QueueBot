import discord
from discord.ui import View

class QueueButtons(View):
    def __init__(self, *, timeout=180):
        super().__init__(timeout=timeout)

    @discord.ui.button(label="Join queue",style=discord.ButtonStyle.primary)
    async def join_queue_button(self, button, interaction):
        await interaction.response.edit_message(
            content=f"This is an edited button response!"
        )

    @discord.ui.button(label="Leave queue",style=discord.ButtonStyle.gray)
    async def leave_queue_button(self, button, interaction):
        await interaction.response.edit_message(
            content=f"This is an edited button response!"
        )

    @discord.ui.button(label="Ping",style=discord.ButtonStyle.red)
    async def ping_button(self, button, interaction):
        await interaction.response.edit_message(
            content=f"This is an edited button response!"
        )