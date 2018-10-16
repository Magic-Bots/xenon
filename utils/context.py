from discord.ext import commands

from utils import logging


class Context(commands.Context):
    def __init__(self, **attrs):
        super().__init__(**attrs)

    @property
    def log(self):
        return logging.logger