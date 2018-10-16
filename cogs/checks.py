from discord.ext import commands


class Checks:
    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(Checks(bot))