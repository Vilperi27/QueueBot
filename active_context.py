import json
from discord.ext import commands
import bot_intents

command_prefix = '/'
intents = bot_intents.get_bot_intents()
client = commands.Bot(
    command_prefix=command_prefix, intents=intents
)
team_channels = ['team-stacks', 'team-general', 'team-stacks-notifier']
queue_names = ["stack", "team_stack"]

async def read_json_data(json_file):
    with open(json_file, 'r') as file:
        return json.load(file)
    
async def write_json_data(json_file, data):
    with open(json_file, 'w') as file:
        json.dump(data, file)