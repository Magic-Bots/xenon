from discord.ext.commands import *
import traceback
import sys

from utils import formatter


em = formatter.embed_message


basic_formatter = {
    MissingRequiredArgument: "Missing the required argument **{error.param.name}**.",
    NoPrivateMessage: "This command **can't be used** in **private** messages.",
    DisabledCommand: "This command **is** currently **disabled**.",
    NotOwner: "This command can **only** be used by **the owner** of this bot."
}

ignore = [CommandNotFound, TooManyArguments]
catch_all = [CommandError]

class Errors:
    def __init__(self, bot):
        self.bot = bot

    async def on_command_error(self, ctx, error):
        error = getattr(error, 'original', error)
        catch_all = True

        for error_cls in ignore:
            if isinstance(error, error_cls):
                return

        for error_cls, format in basic_formatter.items():
            if isinstance(error, error_cls):
                await ctx.send(**em(format.format(error=error, ctx=ctx), type="error"))
                return

        if isinstance(error, BotMissingPermissions):
            await ctx.send(**em(f"The bot is **missing** the following **permissions** `{', '.join(error.missing_perms)}`.", type="error"))
            return

        if isinstance(error, MissingPermissions):
            await ctx.send(**em(f"You are **missing** the following **permissions** `{', '.join(error.missing_perms)}`.", type="error"))
            return

        if isinstance(error, CommandOnCooldown):
            # cba
            pass

        if isinstance(error, BadUnionArgument):
            # cba
            pass

        if isinstance(error, BadArgument):
            # A converter failed
            await ctx.send(**em(str(error), type="error"))

        if catch_all:
            if isinstance(error, CommandError):
                await ctx.send(**em(str(error), type="error"))

            else:
                traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
                error_message = traceback.format_exception(type(error), error, error.__traceback__)
                try:
                    await ctx.send(**em(error_message[:1900], type="unex_error"))
                except:
                    pass


def setup(bot):
    bot.add_cog(CommandError(bot))