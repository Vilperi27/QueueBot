import os
import asyncio

import discord

from active_context import client
import bot_intents
from local_secrets import BOT_API_KEY


allowed_mentions = discord.AllowedMentions(everyone=True)
intents = bot_intents.get_bot_intents()
client.remove_command("help")
client.remove_command("register")

async def load_extensions():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await client.load_extension(f"cogs.{filename[:-3]}")
    print('Cogs loaded')
            
async def main():
    async with client:
        await load_extensions()
        await client.start(BOT_API_KEY)

asyncio.run(main())
