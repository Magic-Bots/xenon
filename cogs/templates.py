from discord.ext import commands as cmd


class Templates:
    def __init__(self, bot):
        self.bot = bot

    @cmd.group(aliases=["temp"], invoke_without_command=True)
    async def template(self, ctx):
        pass

    @template.command(aliases=["c"])
    async def create(self, ctx):
        pass

    @template.command(aliases=["l"])
    @cmd.guild_only()
    @cmd.has_permissions(administrator=True)
    @cmd.bot_has_permissions(administrator=True)
    async def load(self, ctx):
        pass

    @template.command(aliases=["i", "inf"])
    async def info(self, ctx):
        pass


def setup(bot):
    bot.add_cog(Templates(bot))
