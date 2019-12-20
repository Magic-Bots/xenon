from discord.ext import commands as cmd
import asyncio
import discord

from utils import helpers, checks, antiidiot



class ACLMenu:
    def __init__(self, ctx, acldoc):
        self.ctx = ctx
        self.msg = None
        self.page = 1
        self.pages = []
        self.owner_only_pages = [{'name': 'ACL disabled: Disable owner only mode to reenable the ACL', 'options': [["owner_only", True]]}]
        self.begin_page = {'name': 'Choose which roles are allowed to use Xenon on this server', 'options': [["owner_only", False]]}
        self.rolescount = 0
        acl = acldoc['list']
        
        pagecounter = -1
        for role in ctx.guild.roles:
            if not role.managed and role.name != "@everyone" and role.permissions.manage_channels and role.permissions.manage_roles and not role.permissions.administrator:
                if self.rolescount % 8 == 0:
                    pagecounter += 1
                    self.pages.append(self.begin_page)

                self.pages[pagecounter]['options'].append([str(role.id), str(role.id) in acl and acl[str(role.id)]])
                self.rolescount += 1
        
        if self.rolescount == 0:
            pagecounter = 1
            self.pages.append(self.begin_page)
        
        self.pages_all = self.pages
        if 'owner_only' in acldoc and acldoc['owner_only']:
            self.owner_only_mode = True
            self.pages = self.owner_only_pages
        else:
            self.owner_only_mode = False

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
      
    def get_rolename(self, roleid):
        if roleid == "owner_only":
            return "[Owner only]"
        else:
            return discord.utils.get(self.ctx.guild.roles, id=int(roleid)).name

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
            if option == 0:
                if not self.owner_only_mode:
                    self.pages_all = self.pages
                    self.pages = self.owner_only_pages
                    self.page = 1
                else:
                    self.pages = self.pages_all
                self.owner_only_mode = not self.owner_only_mode
                return True

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
        embed = self.ctx.em("")["embed"]
        embed.title = page_options["name"]
        embed.set_footer(text="Enable / Disable options with the reactions and click ✅ when you are done\nAdministrative roles can't be excluded from the list! Use owner only mode instead.\nOnly roles with manage_channels and manage_roles permissions are selectable.")
        for i, (name, value) in enumerate(page_options["options"]):
            embed.description += f"{i + 1}\u20e3 **{self.get_rolename(name)}** -> {'✅' if value else '❌'}\n"

        return embed


class Acl(cmd.Cog, name="Security"):
    def __init__(self, bot):
        self.bot = bot

    @cmd.command(aliases=["acl"])
    @cmd.guild_only()
    @cmd.cooldown(1, 10, cmd.BucketType.user)
    async def access(self, ctx):
        """
        Change which roles have access to the bot

        __Examples__

        ```{c.prefix}access```
        """
        if ctx.author.id != ctx.guild.owner_id:
            raise cmd.CommandError("This command can be used by the **onwer** of this server **only**.")
        
        acldoc = await ctx.db.acl.find_one({'_id': ctx.guild.id})
        menu = ACLMenu(ctx, acldoc)
        options = await menu.run()

        warning = await ctx.send(
            **ctx.em("Are you sure you want to apply the changes?\n"
                     "**Think twice!** Misconfigurations could allow others to **destory** your server!\n",
                     type="warning"))
            
        await warning.add_reaction("❌")
        await warning.add_reaction("✅")
        try:
            reaction, user = await self.bot.wait_for(
                "reaction_add",
                check=lambda r, u: r.message.id == warning.id and u.id == ctx.author.id,
                timeout=60
            )
        except TimeoutError:
            await warning.delete()
            raise cmd.CommandError(
                "Please make sure to **click the ✅ reaction** in order to apply the changes."
            )
        if str(reaction.emoji) != "✅":
            await warning.delete()
            raise cmd.CommandError(
                "Please make sure to **click the ✅ reaction** in order to apply the changes."
            )
        
        await warning.delete()
        await antiidiot.check(ctx)

        if options["owner_only"]:
            del options['owner_only']
            await ctx.db.acl.update_one({'_id': ctx.guild.id}, {'$set': {'_id': ctx.guild.id, 'owner_only': True}}, upsert=True)
        else:
            del options['owner_only']
            await ctx.db.acl.update_one({'_id': ctx.guild.id}, {'$set': {'_id': ctx.guild.id, 'owner_only': False, 'list': options}}, upsert=True)

        await ctx.send(
                **ctx.em("Access Control List was applied successfully.",
                         type="info"))


def setup(bot):
    bot.add_cog(Acl(bot))

