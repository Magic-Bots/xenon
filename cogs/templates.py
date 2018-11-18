from discord.ext import commands as cmd
from discord_backups import BackupInfo, BackupLoader

from utils import checks


class Templates:
    def __init__(self, bot):
        self.bot = bot

    @cmd.group(aliases=["temp"], invoke_without_command=True)
    async def template(self, ctx):
        await ctx.invoke(self.bot.get_command("help"), "template")

    @cmd.command()
    async def templates(self, ctx):
        await ctx.invoke(self.bot.get_command("template"), "list")

    @template.command(aliases=["ls"])
    async def list(self, ctx):
        pass

    @template.command(aliases=["c"])
    async def create(self, ctx, backup_id, name, *, description):
        name = name.lower().replace(" ", "_")
        backup = await ctx.db.rdb.table("backups").get(backup_id).run(ctx.db.con)
        if backup is None or backup.get("creator") != str(ctx.author.id):
            raise cmd.CommandError(f"You have **no backup** with the id `{backup_id}`.")

        already_exists = (await ctx.db.rdb.table("templates").get(name).run(ctx.db.con)) is not None
        if already_exists:
            raise cmd.CommandError(
                f"There is **already a template with that name**, please choose another one."
            )

        backup["backup"]["members"] = []

        warning = await ctx.send(**ctx.em("Are you sure you want to turn this backup into a template? **All templates are public!**", type="warning"))
        await warning.add_reaction("✅")
        await warning.add_reaction("❌")
        try:
            reaction, user = await self.bot.wait_for(
                "reaction_add",
                check=lambda r, u: r.message.id == warning.id and u.id == ctx.author.id,
                timeout=60
            )
        except TimeoutError:
            raise cmd.CommandError(
                "Please make sure to **click the ✅ reaction** in order to create a template."
            )
            await warning.delete()

        if str(reaction.emoji) != "✅":
            await warning.delete()
            return

        await ctx.db.rdb.table("templates").insert({
            "id": name,
            "creator": backup["creator"],
            "loaded": 0,
            "featured": False,
            "original": backup_id,
            "template": backup["backup"]
        }).run(ctx.db.con)
        await ctx.send(**ctx.em("Successfully **created template**.\n"
                                f"You can load the template with `{ctx.prefix}template load {name}`", type="success"))

    @template.command(aliases=["del", "rm", "remove"])
    async def delete(self, ctx, *, template_name):
        template_name = template_name.lower().replace(" ", "_")
        template = await ctx.db.rdb.table("templates").get(template_name).run(ctx.db.con)
        if template is None or template.get("creator") != str(ctx.author.id):
            raise cmd.CommandError(f"There is **no template** with the name `{template_name}`.")

        await ctx.db.rdb.table("templates").get(template_name).delete().run(ctx.db.con)
        await ctx.send(**ctx.em("Successfully **deleted template**.", type="success"))

    @template.command(aliases=["l"])
    @cmd.guild_only()
    @cmd.has_permissions(administrator=True)
    @cmd.bot_has_permissions(administrator=True)
    @checks.bot_has_managed_top_role()
    async def load(self, ctx, *, template_name):
        template_name = template_name.lower().replace(" ", "_")
        template = await ctx.db.rdb.table("templates").get(template_name).run(ctx.db.con)
        if template is None:
            raise cmd.CommandError(f"There is **no template** with the name `{template_name}`.")

        warning = await ctx.send(**ctx.em("Are you sure you want to load this template? **All channels and roles will get replaced!**", type="warning"))
        await warning.add_reaction("✅")
        await warning.add_reaction("❌")
        try:
            reaction, user = await self.bot.wait_for(
                "reaction_add",
                check=lambda r, u: r.message.id == warning.id and u.id == ctx.author.id,
                timeout=60)
        except TimeoutError:
            raise cmd.CommandError(
                "Please make sure to **click the ✅ reaction** in order to load the template."
            )
            await warning.delete()

        if str(reaction.emoji) != "✅":
            await warning.delete()
            return

        handler = BackupLoader(self.bot, self.bot.session, template["template"])
        await handler.load(ctx.guild, ctx.author, 0)

    @template.command(aliases=["i", "inf"])
    async def info(self, ctx, *, template_name):
        template_name = template_name.lower().replace(" ", "_")
        template = await ctx.db.rdb.table("templates").get(template_name).run(ctx.db.con)
        if template is None:
            raise cmd.CommandError(f"There is **no template** with the name `{template_name}`.")

        handler = BackupInfo(self.bot, template["template"])
        embed = ctx.em("")["embed"]
        embed.title = template_name
        embed.add_field(name="Creator", value=f"<@{template['creator']}>")
        embed.add_field(name="Created At", value="N/A", inline=False)
        embed.add_field(name="Channels", value=handler.channels(), inline=True)
        embed.add_field(name="Roles", value=handler.roles(), inline=True)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Templates(bot))
