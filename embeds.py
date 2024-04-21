import discord
from active_context import command_prefix, team_channels, read_json_data


async def get_queue_embed(ctx):
    queue = await read_json_data('queue.json')

    stack = "team_stack" if ctx.channel.name in team_channels else "stack"
    queue = queue[stack]
    queue = sorted(queue.items(), key=lambda x:x[1])
    players = ''

    for player, timestamp in queue:
        if timestamp:
            players += f'{player} plays from {timestamp}\n'
        else:
            players += f'{player}\n'

    embed = discord.Embed(
        title="Queue" if stack == "stack" else "Team Queue"
    )
    embed.description = f"**Players - {str(len(queue))}**\n{players}"
    embed.colour = discord.Colour.light_grey()
    embed.set_footer(
        text=f"⌛ Queue ⌛\n\nDon't have time right now? You can specify "
        f"when you start playing!\nUsage: {command_prefix}queue HH:MM"
    )
    return embed