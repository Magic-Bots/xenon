from discord.ext import commands as cmd
import asyncio
import random
import logging
import discord

from utils import helpers

log = logging.getLogger(__name__)


async def check(ctx):
    idiottest = random.choice(list(ctx.config.idiottests.items()))

    answer = await ask_question(ctx, f"To continue, answer the following question:\nWhat is the missing letter in {idiottest[0]}?", 10)
    if answer.lower() != idiottest[1].lower():
        raise cmd.CommandError("**Canceled**, because your answer was incorrect")
    
    return True


async def ask_question(ctx, question, timeout):
    question_msg = await ctx.send(**ctx.em(question, type="wait_for"))
    
    try:
        msg = await ctx.bot.wait_for(
            event="message",
            check=lambda m: m.author == ctx.author and m.channel == ctx.channel,
            timeout=timeout
        )

    except asyncio.TimeoutError:
        raise cmd.CommandError("**Canceled**, because your response took too long.")
    
    return msg.content
