import discord
from discord.ext import commands
from discord.partial_emoji import PartialEmoji
from discord.ui import Button, View
from webserver import keep_alive
import datetime
from datetime import datetime, timedelta
import asyncio
import aiofiles
import json
import os
import auth

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
event = asyncio.Event()
lock = asyncio.Lock()
allowed_mentions = discord.AllowedMentions(everyone=True)
bot.remove_command("help")
queue_list_cs_stacks = []
queue_list_team_stacks = []
queue_dict_cs_stacks = {}
queue_dict_team_stacks = {}
r = 0
current_scheduled_reminder = None


@bot.event
async def on_ready():
    global queue_list_cs_stacks, queue_dict_cs_stacks, queue_list_team_stacks, queue_dict_team_stacks
    print("Bot online")
    last_clear_date = load_clear_date()
    queue_state_cs_stacks = load_queue_state("general")
    queue_list_cs_stacks = queue_state_cs_stacks["queue_list"]
    queue_dict_cs_stacks = {key: datetime.fromisoformat(str(value)) if value != "right now" else value for key, value in
                            queue_state_cs_stacks["queue_dict"].items()}

    queue_state_team_stacks = load_queue_state("team")
    queue_list_team_stacks = queue_state_team_stacks["queue_list"]
    queue_dict_team_stacks = {key: datetime.fromisoformat(str(value)) if value != "right now" else value for key, value
                              in
                              queue_state_team_stacks["queue_dict"].items()}

    async def silent_clear(guild):
        global queue_list_cs_stacks, queue_list_team_stacks
        global queue_dict_cs_stacks, queue_dict_team_stacks

        csgo_now_role = discord.utils.get(guild.roles, name="CSGO Now")
        csgo_later_role = discord.utils.get(guild.roles, name="CSGO Later")

        # Clear CS Stacks queue
        for player in queue_list_cs_stacks:
            await guild.get_member(int(player[2:-1])).remove_roles(csgo_now_role, csgo_later_role)
        queue_list_cs_stacks.clear()
        queue_dict_cs_stacks.clear()

        # Clear Team Stacks queue
        for player in queue_list_team_stacks:
            await guild.get_member(int(player[2:-1])).remove_roles(csgo_now_role, csgo_later_role)
        queue_list_team_stacks.clear()
        queue_dict_team_stacks.clear()

        print("Queue cleared automatically")
        print("Clearing queue in 86400 seconds")
        await save_clear_date()
        clear_queue_at_6(guild)

    def clear_queue_at_6(guild):
        now = datetime.now()
        six_am = now.replace(hour=6, minute=0, second=0, microsecond=0)
        if now > six_am:
            six_am += timedelta(days=1)
        delta = six_am - now
        print(f"Clearing queue in {delta.seconds} seconds")
        bot.loop.call_later(delta.seconds, lambda: asyncio.ensure_future(silent_clear(guild)))

    if last_clear_date is None or last_clear_date.date() != datetime.now().date():
        await silent_clear(bot.guilds[0])  # clear the queue if the script was restarted on a new day
    else:
        clear_queue_at_6(bot.guilds[0])


@bot.command(name="queue", description="Enter the queue")
async def queue(ctx, hours: int = 0, minutes: int = 0):
    global r
    r = 0
    if hours > 12:
        minutes = hours
        hours = 0
    if ctx.channel.name == 'team-stacks' or ctx.channel.name == 'team-general' or ctx.channel.name == 'team-stacks-notifier':
        await queue_update(ctx, ctx.author.mention, hours, minutes, "queue", "add", 'team')
        await save_queue_state('team')
    else:
        await queue_update(ctx, ctx.author.mention, hours, minutes, "queue", "add", 'general')
        await save_queue_state('general')


@bot.command(name="leave", description="Leave the queue")
async def leave(ctx):
    global r
    r = 0
    if ctx.channel.name == 'team-stacks' or ctx.channel.name == 'team-general' or ctx.channel.name == 'team-stacks-notifier':
        await queue_update(ctx, ctx.author.mention, 0, 0, "leave", "remove", 'team')
        await save_queue_state('team')
    else:
        await queue_update(ctx, ctx.author.mention, 0, 0, "leave", "remove", 'general')
        await save_queue_state('general')


@bot.command(name="add", description="Adds someone to the queue")
async def add(ctx, player: discord.Member, hours: int = 0, minutes: int = 0):
    global r
    r = 0
    if hours > 12:
        minutes = hours
        hours = 0
    player_mention = "<@" + str(player.id) + ">"
    if ctx.channel.name == 'team-stacks' or ctx.channel.name == 'team-general' or ctx.channel.name == 'team-stacks-notifier':
        await queue_update(ctx, player_mention, hours, minutes, "add", "add", 'team')
        await save_queue_state('team')
    else:
        await queue_update(ctx, player_mention, hours, minutes, "add", "add", 'general')
        await save_queue_state('general')


@bot.command(name="remove", description="Removes someone from the queue")
async def remove(ctx, player: discord.Member):
    global r
    r = 0
    player_mention = "<@" + str(player.id) + ">"
    if ctx.channel.name == 'team-stacks' or ctx.channel.name == 'team-general' or ctx.channel.name == 'team-stacks-notifier':
        await queue_update(ctx, player_mention, 0, 0, "remove", "remove", 'team')
        await save_queue_state('team')
    else:
        await queue_update(ctx, player_mention, 0, 0, "remove", "remove", 'general')
        await save_queue_state('general')


@bot.command(name="clear", description="Clear the queue")
async def clear(ctx):
    csgo_now_role = discord.utils.get(ctx.guild.roles, name="CSGO Now")
    csgo_later_role = discord.utils.get(ctx.guild.roles, name="CSGO Later")
    queue_type = 'team' if ctx.channel.name == 'team-stacks' or ctx.channel.name == 'team-general' or ctx.channel.name == 'team-stacks-notifier' else 'general'
    if queue_type == 'team':
        for player in queue_list_team_stacks:
            await ctx.guild.get_member(int(player[2:-1])).remove_roles(csgo_now_role, csgo_later_role)
        queue_list_team_stacks.clear()
        queue_dict_team_stacks.clear()
        embed = update_embed(queue_list_team_stacks, queue_dict_team_stacks, queue_type)
    else:
        for player in queue_list_cs_stacks:
            await ctx.guild.get_member(int(player[2:-1])).remove_roles(csgo_now_role, csgo_later_role)
        queue_list_cs_stacks.clear()
        queue_dict_cs_stacks.clear()
        embed = update_embed(queue_list_cs_stacks, queue_dict_cs_stacks, queue_type)
    emoji = await fetch_emoji(ctx)
    view = buttons(ctx, emoji, queue_list_cs_stacks, queue_dict_cs_stacks)
    if ctx.channel.name == 'team-stacks' or ctx.channel.name == 'team-general' or ctx.channel.name == 'team-stacks-notifier':
        await ctx.send("The team queue has been cleared", embed=embed, view=view)
    else:
        await ctx.send("The queue has been cleared", embed=embed, view=view)
    await save_queue_state(queue_type)


@bot.command(name="show", description="Show the queue", aliases=['list'])
async def show(ctx):
    queue_type = 'team' if ctx.channel.name == 'team-stacks' or ctx.channel.name == 'team-general' or ctx.channel.name == 'team-stacks-notifier' else 'general'
    if queue_type == 'team':
        queue_list = queue_list_team_stacks
        queue_dict = queue_dict_team_stacks
    else:
        queue_list = queue_list_cs_stacks
        queue_dict = queue_dict_cs_stacks
    embed = update_embed(queue_list, queue_dict, queue_type)
    emoji = await fetch_emoji(ctx)
    view = buttons(ctx, emoji, queue_list, queue_dict)
    if queue_type == 'team':
        await ctx.send("Here's the current team queue:", embed=embed, view=view)
    else:
        await ctx.send("Here's the current queue:", embed=embed, view=view)


async def queue_update(ctx, player, hours, minutes, command, action, queue_type):
    global current_scheduled_reminder
    play_from = datetime.now() + timedelta(hours=hours, minutes=minutes)
    time_str = play_from.strftime("%I:%M %p")
    csgo_now_role = discord.utils.get(ctx.guild.roles, name="CSGO Now")
    csgo_later_role = discord.utils.get(ctx.guild.roles, name="CSGO Later")
    queue_list = queue_list_team_stacks if queue_type == 'team' else queue_list_cs_stacks
    queue_dict = queue_dict_team_stacks if queue_type == 'team' else queue_dict_cs_stacks

    if action == "add":
        if player in queue_list:
            if queue_dict[player] == "right now" and hours == 0 and minutes == 0:
                if command == "queue":
                    await ctx.send("You're already in the queue dumbass")
                    return
                else:
                    await ctx.send("{} is already in the queue!".format(player))
                    return
            else:
                queue_dict[player] = "right now" if hours == 0 and minutes == 0 else play_from
                emoji = await fetch_emoji(ctx)
                view = buttons(ctx, emoji, queue_list, queue_dict)
                embed = update_embed(queue_list, queue_dict, queue_type)
                if hours == 0 and minutes == 0:
                    await ctx.guild.get_member(int(player[2:-1])).add_roles(csgo_now_role)
                    await ctx.guild.get_member(int(player[2:-1])).remove_roles(csgo_later_role)
                    await ctx.send(f"{player} has updated their time to play right now.", embed=embed, view=view)
                else:
                    await ctx.guild.get_member(int(player[2:-1])).add_roles(csgo_later_role)
                    await ctx.guild.get_member(int(player[2:-1])).remove_roles(csgo_now_role)
                    await ctx.send(f"{player} has updated their time to play from {time_str} CET.", embed=embed, view=view)
                    max_play_from = max((time for _, time in queue_dict.items() if time != "right now"), default=None)
                    if max_play_from == play_from:
                        if current_scheduled_reminder is not None:
                            current_scheduled_reminder.cancel()
                        current_scheduled_reminder = asyncio.create_task(schedule_stack_reminder(ctx, play_from))
        else:
            queue_list.append(player)
            if hours == 0 and minutes == 0:
                await ctx.guild.get_member(int(player[2:-1])).add_roles(csgo_now_role)
                await ctx.guild.get_member(int(player[2:-1])).remove_roles(csgo_later_role)
                queue_dict[player] = "right now"
                emoji = await fetch_emoji(ctx)
                view = buttons(ctx, emoji, queue_list, queue_dict)
                embed = update_embed(queue_list, queue_dict, queue_type)
                await ctx.send("{} has joined the queue!".format(player), embed=embed, view=view)
            else:
                await ctx.guild.get_member(int(player[2:-1])).add_roles(csgo_later_role)
                await ctx.guild.get_member(int(player[2:-1])).remove_roles(csgo_now_role)
                queue_dict[player] = play_from
                emoji = await fetch_emoji(ctx)
                view = buttons(ctx, emoji, queue_list, queue_dict)
                embed = update_embed(queue_list, queue_dict, queue_type)
                await ctx.send("{} plays from {}".format(player, time_str) + " CET!", embed=embed, view=view)
                max_play_from = max((time for _, time in queue_dict.items() if time != "right now"), default=None)
                if max_play_from == play_from:
                    if current_scheduled_reminder is not None:
                        current_scheduled_reminder.cancel()
                    current_scheduled_reminder = asyncio.create_task(schedule_stack_reminder(ctx, play_from))
    elif action == "remove":
        if player not in queue_list:
            await ctx.send("{} is not in the queue".format(ctx.author.mention))
        else:
            queue_list.remove(player)
            del queue_dict[player]
            await ctx.guild.get_member(int(player[2:-1])).remove_roles(csgo_now_role, csgo_later_role)

            embed = update_embed(queue_list, queue_dict, queue_type)
            emoji = await fetch_emoji(ctx)
            view = buttons(ctx, emoji, queue_list, queue_dict)
            await ctx.send("{} has left the queue".format(player), embed=embed, view=view)


async def stack_reminder(ctx):
    async with lock:
        await _stack_reminder_recursive(ctx)
        event.set()

    event.clear()
    await event.wait()


async def _stack_reminder_recursive(ctx):
    global r
    reminder_time = 3600 * r
    queue_dict = queue_dict_team_stacks if ctx.channel.name == 'team-stacks' or ctx.channel.name == 'team-general' or ctx.channel.name == 'team-stacks-notifier' else queue_dict_cs_stacks
    await asyncio.sleep(reminder_time+1)
    available_players = fetch_available_players(queue_dict)
    now = datetime.now()
    if len(available_players) == 4 and now.replace(hour=9, minute=0, second=0, microsecond=0) < now < now.replace(hour=22, minute=30, second=0, microsecond=0):
        csgo_role = discord.utils.get(ctx.guild.roles, name="CSGO")
        await ctx.send(content=f"+1 {csgo_role.mention} `🔥 Can we get another game going? 🔥`", allowed_mentions=allowed_mentions)
        r += 1
        await _stack_reminder_recursive(ctx)


async def schedule_stack_reminder(ctx, play_from):
    await asyncio.sleep((play_from - datetime.now()).total_seconds())
    await stack_reminder(ctx)


async def save_queue_state(queue_type):
    state = {
        "queue_list": queue_list_cs_stacks if queue_type == "general" else queue_list_team_stacks,
        "queue_dict": {
            key: value.isoformat() if isinstance(value, datetime) else value
            for key, value in
            (queue_dict_cs_stacks.items() if queue_type == "general" else queue_dict_team_stacks.items())
        }
    }
    async with aiofiles.open(f"queue_{queue_type}.json", "w") as f:
        await f.write(json.dumps(state))


def load_queue_state(queue_type):
    if not os.path.exists(f"queue_{queue_type}.json"):
        return {"queue_list": [], "queue_dict": {}}

    with open(f"queue_{queue_type}.json", "r") as f:
        if not f.read():
            return {"queue_list": [], "queue_dict": {}}

    with open(f"queue_{queue_type}.json", "r") as f:
        state = json.load(f)
        state["queue_dict"] = {key: datetime.fromisoformat(value) if value != "right now" else value for key, value in state["queue_dict"].items()}
        return state


async def save_clear_date():
    with open("last_clear_date.txt", "w") as f:
        f.write(datetime.now().isoformat())


def load_clear_date():
    if not os.path.exists("last_clear_date.txt"):
        return None

    with open("last_clear_date.txt", "r") as f:
        last_clear_date = f.read()
        return datetime.fromisoformat(last_clear_date)


async def fetch_emoji(ctx):
    return await ctx.guild.fetch_emoji(1102034805480243300)


def fetch_available_players(queue_dict):
    return [player for player, time in queue_dict.items() if
            time == "right now" or time <= datetime.now()]


def get_next_game_time(sorted_queue):
    if len(sorted_queue) >= 5:
        return sorted_queue[4][1]
    else:
        return None


def update_embed(queue_list, queue_dict, queue_type):
    sorted_queue = sorted(queue_dict.items(), key=lambda x: (x[1] != "right now", x[1]))
    available_players = fetch_available_players(queue_dict)
    if queue_type == 'team':
        embed = discord.Embed(title="Team Queue")
    else:
        embed = discord.Embed(title="Queue")
    embed.description = "**Players -** `" + str(len(queue_list)) + "`\n"
    if len(queue_list) == 0:
        embed.description = "The queue is empty"
        embed.colour = discord.Colour.red()
    elif len(available_players) == 5:
        embed.colour = discord.Colour.green()
        embed.set_footer(
            text="🔥 GO GO GO 🔥\n\n"
                 "Usage: !queue [hours] [minutes]\n"
                 "Don't have time right now? You can specify when you start playing!")
    elif len(available_players) > 5:
        embed.colour = discord.Colour.orange()
        embed.set_footer(
            text="⌛ Game ongoing... ⌛\n\n"
                 "Usage: !queue [hours] [minutes]\n"
                 "Don't have time right now? You can specify when you start playing!")
    else:
        next_game_time = get_next_game_time(sorted_queue)
        if next_game_time is not None:
            time_str = next_game_time.strftime('%I:%M %p')
            embed.colour = discord.Colour.yellow()
            embed.set_footer(
                text=f"⌛ Next game at {time_str} ⌛\n\n"
                     f"Usage: !queue [hours] [minutes]\n"
                     f"Don't have time right now? You can specify when you start playing!")
        else:
            embed.colour = discord.Colour.yellow()
            embed.set_footer(
                text="Can we get another game going? 👀\n\n"
                     "Usage: !queue [hours] [minutes]\n"
                     "Don't have time right now? You can specify when you start playing!")
    for player, time in sorted_queue:
        if time != "right now" and datetime.now() > time:
            queue_dict[player] = "right now"
            time = "right now"
        if time == "right now":
            embed.description += f"{player}\n"
        else:
            embed.description += f"{player} plays from {time.strftime('%I:%M %p')} CET\n"
    return embed


def buttons(ctx, emoji, queue_list, queue_dict):
    queue_type = 'team' if ctx.channel.name == 'team-stacks' or ctx.channel.name == 'team-general' or ctx.channel.name == 'team-stacks-notifier' else 'general'

    async def join_queue(interaction: discord.Interaction):
        ctx.author = interaction.user
        if "<@" + str(interaction.user.id) + ">" not in queue_list or queue_dict[ctx.author.mention] != "right now":
            await interaction.response.defer()
            await add(ctx, interaction.user)
        else:
            await interaction.response.send_message(content="You're already in the queue dumbass", ephemeral=True)

    async def leave_queue(interaction: discord.Interaction):
        ctx.author = interaction.user
        if "<@" + str(interaction.user.id) + ">" in queue_list:
            await interaction.response.defer()
            await remove(ctx, interaction.user)
        else:
            await interaction.response.send_message(content="You are not in the queue!", ephemeral=True)

    async def ping_csgo_now(interaction: discord.Interaction):
        ctx.author = interaction.user
        if "<@" + str(interaction.user.id) + ">" in queue_list:
            csgo_now_role = discord.utils.get(ctx.guild.roles, name="CSGO Now")
            await interaction.response.defer()
            if queue_type == 'team':
                notifier_channel = discord.utils.get(ctx.guild.text_channels, name="team-stacks-notifier")
            else:
                notifier_channel = discord.utils.get(ctx.guild.text_channels, name="cs-stacks-notifier")
            await notifier_channel.send(content=f"{csgo_now_role.mention} Let's play! <:jokudinkdonk:1102034805480243300><:jokudinkdonk:1102034805480243300><:jokudinkdonk:1102034805480243300>", allowed_mentions=allowed_mentions)
        else:
            await interaction.response.send_message(content="You are not in the queue!", ephemeral=True)

    available_players = fetch_available_players(queue_dict)
    partial_emoji = PartialEmoji.from_dict({'id': emoji.id, 'name': emoji.name, 'animated': emoji.animated})

    join_button = Button(label="Join queue", style=discord.ButtonStyle.primary)
    leave_button = Button(label="Leave queue", style=discord.ButtonStyle.secondary)
    notification_button = Button(label=None, style=discord.ButtonStyle.red, emoji=partial_emoji)

    join_button.callback = join_queue
    leave_button.callback = leave_queue
    notification_button.callback = ping_csgo_now
    view = View(timeout=86400.0)
    view.add_item(join_button)
    view.add_item(leave_button)
    if available_players:
        view.add_item(notification_button)
    return view


keep_alive()
bot.run(auth.Token)
