import inspect
from pathlib import Path
from typing import Tuple

from discord import Embed
from discord.ext import commands

from bot.bot import SirRobin
from bot.constants import Client
from bot.converters import SourceConverter, SourceType


class BotSource(commands.Cog):
    """Displays information about the bot's source code."""

    def __init__(self, bot: SirRobin):
        self.bot = bot

    @commands.command(name="source", aliases=("src",))
    async def source_command(self, ctx: commands.Context, *, source_item: SourceConverter = None) -> None:
        """Display information and a GitHub link to the source code of a command or cog."""
        if not source_item:
            embed = Embed(title="Sir Robin's GitHub Repository")
            embed.add_field(name="Repository", value=f"[Go to GitHub]({Client.github_bot_repo})")
            embed.set_thumbnail(url="https://avatars1.githubusercontent.com/u/9919")
            await ctx.send(embed=embed)
            return

        # Check to short-circuit this command if the user requests the help command.
        # This should be removed upon implementation of a custom help command.
        if isinstance(source_item, commands.HelpCommand):
            embed = Embed(title="Help Command", description="We use Discord.py's default help command.")
            embed.add_field(name="Repository", value=f"[Go to GitHub]({Client.github_bot_repo})")
            embed.set_thumbnail(url="https://avatars1.githubusercontent.com/u/9919")
            await ctx.send(embed=embed)
            return

        embed = await self.build_embed(source_item)
        await ctx.send(embed=embed)

    def get_source_link(self, source_item: SourceType) -> Tuple[str, str, int | None]:
        """
        Build GitHub link of source item, return this link, file location and first line number.

        Raise BadArgument if `source_item` is a dynamically-created object (e.g. via internal eval).
        """
        if isinstance(source_item, commands.Command):
            source_item = inspect.unwrap(source_item.callback)
            src = source_item.__code__
            filename = src.co_filename
        else:
            src = type(source_item)
            try:
                filename = inspect.getsourcefile(src)
            except TypeError:
                raise commands.BadArgument("Cannot get source for a dynamically-created object.")

        if not isinstance(source_item, str):
            try:
                lines, first_line_no = inspect.getsourcelines(src)
            except OSError:
                raise commands.BadArgument("Cannot get source for a dynamically-created object.")

            lines_extension = f"#L{first_line_no}-L{first_line_no+len(lines)-1}"
        else:
            first_line_no = None
            lines_extension = ""

        file_location = Path(filename).relative_to(Path.cwd()).as_posix()

        url = f"{Client.github_bot_repo}/blob/main/{file_location}{lines_extension}"

        return url, file_location, first_line_no or None

    async def build_embed(self, source_object: SourceType) -> Embed | None:
        """Build embed based on source object."""
        url, location, first_line = self.get_source_link(source_object)

        if isinstance(source_object, commands.Command):
            description = source_object.short_doc
            title = f"Command: {source_object.qualified_name}"
        else:
            title = f"Cog: {source_object.qualified_name}"
            description = source_object.description.splitlines()[0]

        embed = Embed(title=title, description=description)
        embed.add_field(name="Source Code", value=f"[Go to GitHub]({url})")
        line_text = f":{first_line}" if first_line else ""
        embed.set_footer(text=f"{location}{line_text}")

        return embed


async def setup(bot: SirRobin) -> None:
    """Load the BotSource cog."""
    await bot.add_cog(BotSource(bot))
