from discord.ext import commands as cmd
import asyncio
import discord

import math
from utils import helpers, checks


def create_permissions(**kwargs):
    permissions = discord.Permissions.none()
    permissions.update(**kwargs)
    return permissions


class ACLMenu:
    def __init__(self, ctx):
        self.ctx = ctx
        self.msg = None
        self.page = 1
        self.rolescount = 0
        self.pages = []
        
        pagecounter = -1
        for role in ctx.guild.roles:
            if not role.managed:
                if self.rolescount % 9 == 0:
                    pagecounter += 1
                    self.pages.append({'name': 'Choose which user is allowed to use me', 'options': []})
                self.pages[pagecounter]['options'].append([role.id, role.permissions.administrator])
                self.rolescount += 1

    async def update(self):
        await self.msg.edit(embed=self._create_embed())

    async def run(self):
        self.msg = await self.ctx.send(embed=self._create_embed())

        options = {
            **{f"{i + 1}\u20e3": self._switch_option(i) for i in range(9)},
            "◀": self._prev_page,
            "▶": self._next_page,
            "❎": self._cancel,
            "✅": self._finish,
        }

        for option in options:
            await self.msg.add_reaction(option)

        try:
            async for reaction, user in helpers.IterWaitFor(
                    self.ctx.bot,
                    event="reaction_add",
                    check=lambda r, u: u.id == self.ctx.author.id and
                                       r.message.id == self.msg.id and
                                       str(r.emoji) in options.keys(),
                    timeout=3 * 60
            ):
                self.ctx.bot.loop.create_task(self.msg.remove_reaction(reaction.emoji, user))

                if not await options[str(reaction.emoji)]():
                    try:
                        await self.msg.clear_reactions()
                    except Exception:
                        pass

                    return {name: value for page in self.pages for name, value in page["options"]}

                await self.update()
        except asyncio.TimeoutError:
            try:
                await self.msg.clear_reactions()
            except Exception:
                pass

            raise cmd.CommandError("**Canceled selection**, because you didn't do anything.")

    async def _next_page(self):
        if self.page < len(self.pages):
            self.page += 1

        return True

    async def _prev_page(self):
        if self.page > 1:
            self.page -= 1

        return True

    def _switch_option(self, option):
        async def predicate():
            try:
                self.pages[self.page - 1]["options"][option][1] = not self.pages[self.page - 1]["options"][option][1]
            except IndexError:
                pass

            return True

        return predicate

    async def _cancel(self):
        try:
            await self.msg.clear_reactions()
        except Exception:
            pass
        raise cmd.CommandError("You canceled the selection.")

    async def _finish(self):
        return False

    def _create_embed(self):
        page_options = self.pages[self.page - 1]
        embed = self.ctx.em("", title="Access Control List")["embed"]
        embed.title = page_options["name"].title()
        embed.set_footer(text="Enable / Disable options with the reactions and click ✅ when you are done")
        for i, (name, value) in enumerate(page_options["options"]):
            embed.description += f"{i + 1}\u20e3 **{discord.utils.get(self.ctx.guild.roles, id=name).name.title()}** -> {'✅' if value else '❌'}\n"

        return embed


class Acl(cmd.Cog, name="Security"):
    def __init__(self, bot):
        self.bot = bot

    @cmd.command(aliases=["acl"])
    @cmd.guild_only()
    @cmd.has_permissions(administrator=True)
    @cmd.cooldown(1, 10, cmd.BucketType.user)
    async def access(self, ctx):
        """
        Choose which role can access the functions of Xenon


        __Examples__

        ```{c.prefix}access```
        """
        menu = ACLMenu(ctx)
        options = await menu.run()
        return

        if options["@everyone"]:
            pass
# LETZTE ZEILE CODE HIER HIN


def setup(bot):
    bot.add_cog(Acl(bot))

