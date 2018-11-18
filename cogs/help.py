from discord.ext import commands as cmd


class HelpFormatter(cmd.HelpFormatter):
    def __init__(self, show_hidden=False, show_check_failure=True):
        super().__init__(show_hidden, show_check_failure)

    def _signature(self, cmd):
        """Default signature function from the commands.Command class, but ignoring aliases."""
        result = []
        parent = cmd.full_parent_name

        name = cmd.name if not parent else parent + ' ' + cmd.name
        result.append(name)

        if cmd.usage:
            result.append(cmd.usage)
            return ' '.join(result)

        params = cmd.clean_params
        if not params:
            return ' '.join(result)

        for name, param in params.items():
            if param.default is not param.empty:
                # We don't want None or '' to trigger the [name=value] case and instead it should
                # do [name] since [name=None] or [name=] are not exactly useful for the user.
                should_print = param.default if isinstance(
                    param.default, str) else param.default is not None
                if should_print:
                    result.append('[%s=%s]' % (name, param.default))
                else:
                    result.append('[%s]' % name)
            elif param.kind == param.VAR_POSITIONAL:
                result.append('[%s...]' % name)
            else:
                result.append('<%s>' % name)

        return ' '.join(result)

    def get_command_signature(self):
        """Retrieves the signature portion of the help page."""
        prefix = self.clean_prefix
        cmd = self.command

        return prefix + self._signature(cmd)


def setup(bot):
    bot.formatter = HelpFormatter()
