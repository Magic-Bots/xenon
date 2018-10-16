import asyncio
import logging
from logging.handlers import TimedRotatingFileHandler
import discord
from discord.ext import commands

from utils import database, logging
from bot import Xenon


async def prepare_bot(loop):
    await database.setup()
    bot = Xenon(logger=logging.logger, loop=loop)

    return bot


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    bot = loop.run_until_complete(prepare_bot(loop))
    bot.run()

