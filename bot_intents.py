import discord

def get_bot_intents():
    intents = discord.Intents.default()

    intents.guilds = True
    intents.members = True
    intents.message_content = True

    return intents