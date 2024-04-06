import json
import discord
from active_context import command_prefix, team_channels


async def get_queue_embed(ctx):
    with open(f'queue.json', 'r') as file:
        queue = json.load(file)

    stack = "team_stack" if ctx.channel.name in team_channels else "stack"
    queue = queue[stack]
    players = '\n'.join(queue.keys())

    embed = discord.Embed(
        title="Queue" if stack == "stack" else "Team Queue"
    )
    embed.description = f"**Players - {str(len(queue))}**\n{players}"
    embed.colour = discord.Colour.light_grey()
    embed.set_footer(
        text=f"⌛ Queue ⌛\n\nDon't have time right now? You can specify "
        f"when you start playing!\nUsage: {command_prefix}queue [hours] "
        f"[minutes] or {command_prefix}queue [minutes]"
    )
    return embed