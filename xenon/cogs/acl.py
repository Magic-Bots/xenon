from discord.ext import commands as cmd
import asyncio
import discord

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
                    self.pages.append({'name': 'Choose which roles are allowed to use Xenon on this server', 'options': []})
                self.pages[pagecounter]['options'].append([str(role.id), role.permissions.administrator])
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
        embed.title = page_options["name"]
        embed.set_footer(text="Enable / Disable options with the reactions and click ✅ when you are done")
        for i, (name, value) in enumerate(page_options["options"]):
            embed.description += f"{i + 1}\u20e3 **{discord.utils.get(self.ctx.guild.roles, id=int(name)).name}** -> {'✅' if value else '❌'}\n"

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

        if options[str(discord.utils.get(ctx.guild.roles, name="@everyone").id)]:
            warning = await ctx.send(
                **ctx.em("Are you sure that you want to apply?\n"
                         "Everyone on the server would be able to backup/restore on this server!",
                         type="warning"))
            await warning.add_reaction("✅")
            await warning.add_reaction("❌")
            try:
                reaction, user = await self.bot.wait_for(
                    "reaction_add",
                    check=lambda r, u: r.message.id == warning.id and u.id == ctx.author.id,
                    timeout=60)
            except asyncio.TimeoutError:
                await warning.delete()
                raise cmd.CommandError(
                    "Please make sure to **click the ✅ reaction** in order to continue.")

            if str(reaction.emoji) != "✅":
                ctx.command.reset_cooldown(ctx)
                await warning.delete()
                return
        
        await ctx.db.acl.update_one({'_id': ctx.guild.id}, {'$set': {'_id': ctx.guild.id, 'list': options}}, upsert=True)
        await ctx.send(
                **ctx.em("Access Control List was applied successfully.",
                         type="info"))
# LETZTE ZEILE CODE HIER HIN


def setup(bot):
    bot.add_cog(Acl(bot))

