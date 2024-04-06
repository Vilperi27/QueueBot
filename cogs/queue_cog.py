import json
import time

from discord.ext import commands, tasks
import discord.utils as discord_utils
import datetime
import pytz

from active_context import command_prefix, queue_names, team_channels
from embeds import get_queue_embed
from views import QueueButtons

class QueueCog(commands.Cog):
    offset = 2
    queue_clear_time = datetime.time(hour=4 + offset)

    def __init__(self, client):
        self.client = client
        self.clear_queues_task.start()

    async def clear_queues(self, type="Automatic"):
        with open('queue.json', 'w') as file:
            default_queue = {
                "stack": {},
                "team_stack": {}
            }
            file.write(json.dumps(default_queue))
        
        with open('queues_clear_timestamps.txt', 'a') as file:
            time = f'{datetime.datetime.now()} - {type}\n'
            file.write(time)

    @tasks.loop(time=queue_clear_time)
    async def clear_queues_task(self):
        await self.clear_queues()

    @commands.command()
    async def clear_all_queues(self, ctx):
        await self.clear_queues("Manual")
        await ctx.send("Queues cleared")
    
    @commands.command()
    async def clear_queue(self, ctx, queue_name):
        with open(f'queue.json', 'r') as file:
            queue = json.load(file)
    
        if queue_name in queue_names:
            queue[queue_name] = {}

            with open('queue.json', 'w') as file:
                json.dump(queue, file)

            await ctx.send("Queue cleared")
        else:
            await ctx.send(f"Options are {', '.join(queue_names)}")

    @commands.command()
    async def queue(self, ctx, hours=None, minutes=None):
        if hours is None and minutes is None:
            minutes = 0
            hours = 0
        elif hours is not None and minutes is not None:
            pass
        else:
            minutes = hours
            hours = 0

        message = ctx.message
        author = message.author
        author_id = str(author.id)

        with open(f'users.json', 'r') as file:
            users = json.load(file)

        if not author_id in users.keys():
            await ctx.send(
                f"User not registered. Please use the {command_prefix}register command"
            )
            return
        
        with open(f'queue.json', 'r') as file:
            queues = json.load(file)

        user = users[author_id]
        mention = user["mention"]
        user_timezone = pytz.timezone(user["timezone"])
        time_difference = datetime.timedelta(
            hours=int(hours), minutes=int(minutes)
        )

        playtime = datetime.datetime.now() + time_difference
        playtime_with_tz = playtime.astimezone(user_timezone)
        timestamp = f'<t:{int(time.mktime(playtime_with_tz.timetuple()))}:f>'

        guild = message.guild
        csgo_now_role = discord_utils.get(guild.roles, name="CSGO Now")
        csgo_later_role = discord_utils.get(guild.roles, name="CSGO Later")

        stack = "team_stack" if ctx.channel.name in team_channels else "stack"
        
        if mention in queues[stack]:
            queues[stack][mention] = timestamp
        else:
            queues[stack].setdefault(mention, timestamp)

        with open('queue.json', 'w') as file:
            json.dump(queues, file)

        if hours or minutes:
            await author.add_roles(csgo_later_role)
            await ctx.send(
                f"{mention} plays from {timestamp}!",view=QueueButtons()
            )
        else:
            await author.add_roles(csgo_now_role)
            await ctx.send(f"{mention} plays now!",view=QueueButtons())

        await self.display_queue(ctx)

    @commands.command()
    async def leave(self, ctx):
        author_mention = ctx.message.author.mention
        stack = "team_stack" if ctx.channel.name in team_channels else "stack"

        with open(f'queue.json', 'r') as file:
            queues = json.load(file)
        
        if author_mention in queues[stack]:
            del queues[stack][str(author_mention)]
        else:
            await ctx.send(f"User not in stack {stack}")
            return
        
        with open('queue.json', 'w') as file:
            json.dump(queues, file)
            
        await self.display_queue(ctx)

    @commands.command()
    async def remove(self, ctx, user):
        with open(f'queue.json', 'r') as file:
            queues = json.load(file)
        
        user_id = str(user)

        for queue_name in queue_names:
            if user_id in queues[queue_name]:
                del queues[queue_name][user_id]
            
        with open('queue.json', 'w') as file:
            json.dump(queues, file)

        await self.display_queue(ctx)

    async def display_queue(self, ctx):
        embed = await get_queue_embed(ctx)
        await ctx.send(embed=embed)

    @commands.command()
    async def show(self, ctx):
        await self.display_queue(ctx)
        

async def setup(client):
    queue_utils = QueueCog(client)
    await client.add_cog(queue_utils)