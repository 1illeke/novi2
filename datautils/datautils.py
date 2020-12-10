import string
import unicodedata
from asyncio import TimeoutError as AsyncTimeoutError
from textwrap import shorten
from types import SimpleNamespace
from typing import Optional, Union

import discord
import tabulate
from redbot.core import checks, commands
from redbot.core.i18n import Translator, cog_i18n
from redbot.core.utils import AsyncIter
from redbot.core.utils import chat_formatting as chat
from redbot.core.utils.menus import DEFAULT_CONTROLS, menu
from redbot.core.utils.predicates import ReactionPredicate


def bool_emojify(bool_var: bool) -> str:
    return "✅" if bool_var else "❌"


T_ = Translator("DataUtils", __file__)
_ = lambda s: s

TWEMOJI_URL = "https://twemoji.maxcdn.com/v/latest/72x72"
APP_ICON_URL = "https://cdn.discordapp.com/app-icons/{app_id}/{icon_hash}.png"
NON_ESCAPABLE_CHARACTERS = string.ascii_letters + string.digits

GUILD_FEATURES = {
    "VIP_REGIONS": _("384kbps voice bitrate"),
    "VANITY_URL": _("Vanity invite URL"),
    "INVITE_SPLASH": _("Invite splash{splash}"),
    "VERIFIED": _("Verified"),
    "PARTNERED": _("Discord Partner"),
    "MORE_EMOJI": _("Extended emoji limit"),  # Non-boosted?
    "DISCOVERABLE": _("Shows in Server Discovery{discovery}"),
    # "FEATURABLE": _('Can be in "Featured" section of Server Discovery'),
    "COMMERCE": _("Store channels"),
    "NEWS": _("News channels"),
    "BANNER": _("Banner{banner}"),
    "ANIMATED_ICON": _("Animated icon"),
    "WELCOME_SCREEN_ENABLED": _("Welcome screen"),
    "PUBLIC_DISABLED": _("Cannot be public"),
    "ENABLED_DISCOVERABLE_BEFORE": _("Was in Server Discovery"),
    "COMMUNITY": _("Community server"),
    # Docs from https://github.com/vDelite/DiscordLists:
    "PREVIEW_ENABLED": _('Preview enabled ("Lurkable")'),
    "MEMBER_VERIFICATION_GATE_ENABLED": _("Member verification gate enabled"),
    "MEMBER_LIST_DISABLED": _("Member list disabled"),
    # im honestly idk what the fuck that shit means, and discord doesnt provides much docs,
    # so if you see that on your server while using my cog - idk what the fuck is that and how it got there,
    # ask discord to write fucking docs already
    "FORCE_RELAY": _(
        "Shards connections to the guild to different nodes that relay information between each other."
    ),
}

ACTIVITY_TYPES = {
    discord.ActivityType.playing: _("Playing"),
    discord.ActivityType.watching: _("Watching"),
    discord.ActivityType.listening: _("Listening to"),
    discord.ActivityType.competing: _("Competing in"),
}

CHANNEL_TYPE_EMOJIS = {
    discord.ChannelType.text: "\N{SPEECH BALLOON}",
    discord.ChannelType.voice: "\N{SPEAKER}",
    discord.ChannelType.category: "\N{BOOKMARK TABS}",
    discord.ChannelType.news: "\N{NEWSPAPER}",
    discord.ChannelType.store: "\N{SHOPPING TROLLEY}",
    discord.ChannelType.private: "\N{BUST IN SILHOUETTE}",
    discord.ChannelType.group: "\N{BUSTS IN SILHOUETTE}",
}
_ = T_


async def get_twemoji(emoji: str):
    emoji_unicode = []
    for char in emoji:
        char = hex(ord(char))[2:]
        emoji_unicode.append(char)
    if "200d" not in emoji_unicode:
        emoji_unicode = list(filter(lambda c: c != "fe0f", emoji_unicode))
    emoji_unicode = "-".join(emoji_unicode)
    return f"{TWEMOJI_URL}/{emoji_unicode}.png"


async def find_app_by_name(where: list, name: str):
    async for item in AsyncIter(where):
        for k, v in item.items():
            if v == name:
                return item


@cog_i18n(_)
class DataUtils(commands.Cog):
    """Commands for getting information about users or servers."""

    __version__ = "2.4.18"

    # noinspection PyMissingConstructor
    def __init__(self, bot):
        self.bot = bot
        self.TIME_FORMAT = _("%d.%m.%Y %H:%M:%S %Z")

    async def red_delete_data_for_user(self, **kwargs):
        return

    @commands.command(aliases=["info", "i"])
    @commands.guild_only()
    @checks.bot_has_permissions(embed_links=True)
    async def uinfo(self, ctx, *, member: discord.Member = None):
        """Information on a user"""
        if member is None:
            member = ctx.message.author
        em = discord.Embed(
            title=chat.escape(str(member), formatting=True),
            color=member.color.value and member.color or discord.Embed.Empty,
        )
        if member.nick:
            em.add_field(name=_("Nickname"), value=member.nick)
        else:
            em.add_field(name=_("Name"), value=member.name)
        em.add_field(
            name=_("Client"),
            value="📱: {}\n"
            "🖥: {}\n"
            "🌎: {}".format(
                str(member.mobile_status).capitalize(),
                str(member.desktop_status).capitalize(),
                str(member.web_status).capitalize(),
            ),
        )
        em.add_field(name=_("Joined server"), value=member.joined_at.strftime(self.TIME_FORMAT))
        em.add_field(name="ID", value=member.id)
        em.add_field(
            name=_("Exists since"),
            value=member.created_at.strftime(self.TIME_FORMAT),
        )
        if member.color.value:
            em.add_field(name=_("Color"), value=member.colour)
        if member.premium_since:
            em.add_field(
                name=_("Boosted server"),
                value=member.premium_since.strftime(self.TIME_FORMAT)
            ),
        
        if member.voice:
            em.add_field(name=_("In voice channel"), value=member.voice.channel.mention)
        em.add_field(
            name=_("Mention"),
            value=f"{member.mention}\n{chat.inline(member.mention)}",
            inline=False,
        )
        if roles := [role.name for role in member.roles if not role.is_default()]:
            em.add_field(
                name=_("Roles"),
                value=chat.escape("\n".join(roles), formatting=True),
                inline=False,
            )
        if member.public_flags.value:
            em.add_field(
                name=_("Public flags"),
                value="\n".join(
                    [
                        str(flag)[10:].replace("_", " ").capitalize()
                        for flag in member.public_flags.all()
                    ]
                ),
                inline=False,
            )
        await ctx.send(embed=em)
