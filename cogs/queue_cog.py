import json
import time

from discord import Interaction
from discord.ext import commands, tasks
import discord.utils as discord_utils
import datetime
import pytz

from active_context import command_prefix, queue_names, team_channels, read_json_data, write_json_data
from embeds import get_queue_embed
from views import QueueButtons

class QueueCog(commands.Cog):
    offset = 2
    queue_clear_time = datetime.time(hour=4 + offset)

    def __init__(self, client):
        self.client = client
        self.clear_queues_task.start()

    async def remove_roles(self):
        for guild in self.client.guilds:
            csgo_now_role = discord_utils.get(guild.roles, name="CSGO Now")
            csgo_later_role = discord_utils.get(guild.roles, name="CSGO Later")
            roles = [csgo_now_role, csgo_later_role]

            for member in guild.members:
                for role in roles:
                    await member.remove_roles(role)

    async def display_queue(self, ctx, display_text=''):
        embed = await get_queue_embed(ctx)
        queue_buttons = QueueButtons()
        queue_buttons.join_queue_button.callback = self.queue
        queue_buttons.leave_queue_button.callback = self.leave
        queue_buttons.ping_button.callback = self.ping
        await ctx.message.channel.send(display_text, view=queue_buttons, embed=embed)

    async def clear_queues(self, type="Automatic"):
        queue = await read_json_data('queue.json')
        
        for stack in queue_names:
            for user in queue[stack]:
                user = user.replace('<', '').replace('>', '').replace('@', '')
                await self.remove_roles()

        default_queue = {
            "stack": {},
            "team_stack": {}
        }
        
        await write_json_data('queue.json', default_queue)
        
        with open('queues_clear_timestamps.txt', 'a') as file:
            time = f'{datetime.datetime.now()} - {type}\n'
            file.write(time)

    @tasks.loop(time=queue_clear_time)
    async def clear_queues_task(self):
        await self.clear_queues()

    @commands.has_permissions(administrator=True)
    @commands.command()
    async def clear_all_queues(self, ctx):
        try:
            await self.clear_queues("Manual")
            await ctx.send("Queues cleared")
        except Exception as e:
            print(e)
    
    @commands.has_permissions(administrator=True)
    @commands.command()
    async def clear_queue(self, ctx, queue_name):
        queue = await read_json_data('queue.json')
    
        if queue_name in queue_names:
            queue[queue_name] = {}

            await write_json_data('queue.json', queue)
            await ctx.send("Queue cleared")
        else:
            await ctx.send(f"Options are {', '.join(queue_names)}")

    @commands.command()
    async def queue(self, ctx, given_time=None):
        if isinstance(ctx, Interaction):
            author = ctx.user
        else:
            author = ctx.message.author
            
        message = ctx.message
        author_id = str(author.id)
        users = await read_json_data('users.json')

        if not author_id in users.keys():
            message = f"User not registered. Please use the {command_prefix}register command"

            if isinstance(ctx, Interaction):
                await ctx.followup.send(message)
            else:
                await message.channel.send(message)
                return
        
        queues = await read_json_data('queue.json')
        user = users[author_id]
        mention = user["mention"]
        
        guild = message.guild
        csgo_now_role = discord_utils.get(guild.roles, name="CSGO Now")
        csgo_later_role = discord_utils.get(guild.roles, name="CSGO Later")

        stack = "team_stack" if ctx.channel.name in team_channels else "stack"
        timestamp = ''

        if given_time:
            try:
                given_time = given_time.split(':')
                hours = int(given_time[0])
                minutes = int(given_time[1])
            except Exception:
                message = 'Wrong format you donkey. HH:MM'
                if isinstance(ctx, Interaction):
                    await ctx.followup.send(message)
                else:
                    await message.channel.send(message)
                    return
                return

            user_timezone = pytz.timezone(user["timezone"])
            current_datetime = datetime.datetime.now()
            playtime = datetime.datetime.now().replace(hour=hours, minute=minutes)

            if current_datetime > playtime:
                playtime = playtime + datetime.timedelta(days=1)
            
            playtime_with_tz = playtime.astimezone(user_timezone)
            timestamp = f'<t:{int(time.mktime(playtime_with_tz.timetuple()))}:t>'

        if mention in queues[stack]:
            queues[stack][mention] = timestamp
        else:
            queues[stack].setdefault(mention, timestamp)

        await write_json_data('queue.json', queues)

        if given_time:
            await author.add_roles(csgo_later_role)
            display_text = f"{mention} plays from {timestamp}!"
        else:
            await author.add_roles(csgo_now_role)
            display_text = f"{mention} plays now!"
        
        if len(queues[stack].keys()) == 3:
            await self.ping(ctx)

        await self.display_queue(ctx, display_text=display_text)

    @commands.command()
    async def leave(self, ctx):
        if isinstance(ctx, Interaction):
            author = ctx.user
            await ctx.response.defer()
        else:
            author = ctx.message.author

        message = ctx.message
        author_mention = author.mention
        stack = "team_stack" if ctx.channel.name in team_channels else "stack"
        queues = await read_json_data('queue.json')
        
        if author_mention in queues[stack]:
            del queues[stack][str(author_mention)]
        else:
            message = f"User not in stack {stack}"
            if isinstance(ctx, Interaction):
                await ctx.followup.send(message)
            else:
                await message.channel.send(message)
            return
        
        await write_json_data('queue.json', queues)     
        await self.remove_roles()
        await self.display_queue(ctx)

    @commands.has_permissions(administrator=True)
    @commands.command()
    async def remove(self, ctx, user):
        queues = await read_json_data('queue.json')
        user_id = str(user)

        for queue_name in queue_names:
            if user_id in queues[queue_name]:
                del queues[queue_name][user_id]
        
        await write_json_data('queue.json', queues)
        await self.remove_roles()
        await self.display_queue(ctx)

    @commands.has_permissions(administrator=True)
    @commands.command()
    async def add(self, ctx, user, given_time=None):
        user_id = user.replace('<', '').replace('>', '').replace('@', '')
        ctx.message.author = self.client.get_user(int(user_id))
        await self.queue(ctx, given_time=given_time)

    @commands.command()
    async def show(self, ctx):
        await self.display_queue(ctx)

    @commands.command()
    async def ping(self, ctx):
        if isinstance(ctx, Interaction):
            await ctx.response.defer()

        stack = "team_stack" if ctx.channel.name in team_channels else "stack"
        if stack == 'team_stack':
            notifier_channel = discord_utils.get(ctx.guild.text_channels, name="team-stacks-notifier")
        else:
            notifier_channel = discord_utils.get(ctx.guild.text_channels, name="cs-stacks-notifier")

        csgo_now_role = discord_utils.get(ctx.guild.roles, name="CSGO Now")
        await notifier_channel.send(f"{csgo_now_role.mention} Let's play! 🔔🔔🔔")
        

async def setup(client):
    queue_utils = QueueCog(client)
    await client.add_cog(queue_utils)