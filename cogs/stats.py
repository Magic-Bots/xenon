from discord.ext import commands
from prettytable import PrettyTable
from datetime import datetime

from utils import formatter
from utils.database import rdb, con


em = formatter.embed_message


class Stats:
    def __init__(self, bot):
        self.bot = bot
        self.start_time = datetime.utcnow()

    async def on_command(self, ctx):
        if ctx.command is None:
            return

        await rdb.table("stats").get("commands").update({ctx.command.name: (rdb.row[ctx.command.name] + 1).default(1)}).run(con)

    async def on_socket_response(self, msg):
        if msg.get("t") is None:
            return

        await rdb.table("stats").get("socket").update({msg.get("t"): (rdb.row[msg.get("t")] + 1).default(1)}).run(con)

    @commands.command(hidden=True)
    async def socketstats(self, ctx):
        socket_stats = await rdb.table("stats").get("socket").without("id").run(con)

        table = PrettyTable()
        table.field_names = ["Event", "Count"]
        table.align["Event"] = "l"
        table.align["Count"] = "r"
        for event, count in socket_stats.items():
            table.add_row([event, int(count)])

        for page in formatter.paginate(str(table), limit=1900):
            await ctx.send(f"```diff\n{page}```")

    @commands.command(hidden=True)
    async def commandstats(self, ctx):
        """Shows a list of executed command"""
        command_stats = await rdb.table("stats").get("commands").without("id").run(con)

        table = PrettyTable()
        table.field_names = ["Command", "Count"]
        table.align["Command"] = "l"
        table.align["Count"] = "r"
        for command, count in command_stats.items():
            table.add_row([command, int(count)])

        for page in formatter.paginate(str(table), limit=1900):
            await ctx.send(f"```diff\n{page}```")

    @commands.command()
    async def uptime(self, ctx):
        """Shows the uptime of the bot"""
        uptime = (datetime.utcnow() - self.start_time).seconds
        days, remainder = divmod(uptime, 60*60*24)
        hours, remainder = divmod(remainder, 60*60)
        minutes, seconds = divmod(remainder, 60)
        await ctx.send(**em(f"{days} days, {hours} hours and {minutes} minutes", embed_title="Uptime"))

    @commands.command(aliases=["ping"])
    @commands.bot_has_permissions(administrator=True)
    async def shards(self, ctx):
        """Shows a list of connected shards"""
        table = PrettyTable()
        table.field_names = ["Shard", "Status", "Latency"]
        for shard_id, latency in self.bot.latencies:
            table.add_row([shard_id, "Ready", f"{int(latency * 1000)} ms"])

        for page in formatter.paginate(str(table), limit=1900):
            await ctx.send(f"```diff\n{page}```")



def setup(bot):
    bot.add_cog(Stats(bot))