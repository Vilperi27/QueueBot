from discord.ext import commands
import bot_intents

command_prefix = '/'
intents = bot_intents.get_bot_intents()
client = commands.Bot(
    command_prefix=command_prefix, intents=intents
)
team_channels = ['team-stacks', 'team-general', 'team-stacks-notifier']
queue_names = ["stack", "team_stack"]