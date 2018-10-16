from discord.ext import commands
import discord
from typing import Union
import copy

from utils import formatter


em = formatter.embed_message


class Admin:
    def __init__(self, bot):
        self.bot = bot

    async def __local_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @commands.command(aliases=["rl"], hidden=True)
    async def reload(self, ctx, ext=None):
        """Reload the whole bot or an extension"""
        if ext is None:
            for ext in self.bot.config.extensions:
                self.bot.unload_extension(ext)
                self.bot.load_extension(ext)

        else:
            try:
                self.bot.unload_extension(ext)
                self.bot.load_extension(ext)
            except:
                raise commands.CommandError(f"Unknown extension called **{ext}**.")

        await ctx.send(**em("Successfully reloaded extension(s)", type="success"))

    @commands.command(aliases=["su"], hidden=True)
    async def sudo(self, ctx, who: Union[discord.Member, discord.User], command: str):
        """Run a command as another user."""
        msg = copy.copy(ctx.message)
        msg.author = who
        msg.content = ctx.prefix + command
        new_ctx = await self.bot.get_context(msg)
        await self.bot.invoke(new_ctx)


def setup(bot):
    bot.add_cog(Admin(bot))