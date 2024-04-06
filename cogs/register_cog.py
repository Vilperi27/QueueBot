import json
from discord.ext import commands
import pytz

class RegisterCog(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command()
    async def register(self, ctx, user_timezone):
        info_url = '<https://en.wikipedia.org/wiki/List_of_tz_database_time_zones>'

        if user_timezone not in pytz.all_timezones:
            await ctx.send(
                f'Timezone in wrong or in the wrong format, see the available formats in {info_url} within the **TZ identifier** column\nFor example !register Europe/Helsinki'
            )
        else:     
            with open('users.json', 'r') as file:
                users = json.load(file)

            author = ctx.message.author

            if str(author.id) in users.keys():
                await ctx.send("User already registered")
                return
            else:
                users.setdefault(
                    author.id, 
                    {"mention": author.mention, "timezone": user_timezone}
                )

            with open('users.json', 'w') as file:
                json.dump(users, file)

            await ctx.send(f"{author.mention} was registered!")

    @commands.command()
    async def remove_user(self, ctx, id):
        with open('users.json', 'r') as file:
            users = json.load(file)

        del users[str(id)]
        with open('users.json', 'w') as file:
            json.dump(users, file)

        await ctx.send(f"User with id {id} was removed.")


async def setup(client):
    register_cog = RegisterCog(client)
    await client.add_cog(register_cog)