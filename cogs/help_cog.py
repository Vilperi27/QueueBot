import discord
from discord.ext import commands

from active_context import command_prefix

class HelpCog(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command()
    async def help(self, ctx):
        help_info = 'Public commands:\n'
        help_info += f'{command_prefix}register timezone - Registers users with timezone i.e. **{command_prefix}register Europe/Helsinki**\n'
        help_info += f'{command_prefix}queue - Enters the queue. i.e. **{command_prefix}queue 14:25**\n'
        help_info += f'{command_prefix}leave - Leaves the queue i.e. **{command_prefix}leave**\n'
        help_info += f'{command_prefix}show - Displays the current queue i.e. **{command_prefix}show**\n'
        help_info += f'{command_prefix}ping - Pings the specific stack channel i.e. **{command_prefix}ping**\n'
        help_info += f'\n\n'
        help_info += f'Admin commands:\n'
        help_info += f'{command_prefix}remove_user - Unregisters user by ID i.e. **{command_prefix}remove_user 1234567890**\n'
        help_info += f'{command_prefix}clear_all_queues - Clears all queues i.e. **{command_prefix}clear_all_queues**\n'
        help_info += f'{command_prefix}clear_queue - Clear a specific queue i.e. **{command_prefix}clear_queue team_stack**\n'
        help_info += f'{command_prefix}add - Adds a user to the queue with tag i.e. **{command_prefix}add @** or **{command_prefix}add @ 14:25**\n'
        help_info += f'{command_prefix}remove - Removes a user from queue with tag i.e. **{command_prefix}remove @**\n'

        help_embed = discord.Embed(color=discord.Color.blurple(), description=help_info)
        await ctx.send(embed=help_embed)


async def setup(client):
    help_cog = HelpCog(client)
    await client.add_cog(help_cog)