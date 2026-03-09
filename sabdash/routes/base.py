"""Base routes: index, commands with category grouping."""

import logging
import re

from flask import Blueprint, render_template, current_app

logger = logging.getLogger("sabdash.routes.base")

base_bp = Blueprint("base", __name__)

# ── Category definitions ──────────────────────────────────────────────
# Maps cog names (lowercased) to a category.  Cogs not listed land in "Other".
# Format: {cog_name_lower: category_key}

CATEGORY_DEFS = [
    {
        "key": "moderation",
        "name": "Moderation",
        "icon": "\U0001f6e1",
        "description": "Server moderation, warnings, bans, mutes, and filters.",
    },
    {
        "key": "music",
        "name": "Music & Audio",
        "icon": "\U0001f3b5",
        "description": "Music playback, playlists, and audio management.",
    },
    {
        "key": "fun",
        "name": "Fun & Games",
        "icon": "\U0001f3ae",
        "description": "Trivia, mini-games, jokes, and entertainment.",
    },
    {
        "key": "economy",
        "name": "Economy & Currency",
        "icon": "\U0001f4b0",
        "description": "Credits, banking, shop, and virtual economy.",
    },
    {
        "key": "utility",
        "name": "Utility & Tools",
        "icon": "\U0001f527",
        "description": "General-purpose utilities, lookups, and conversions.",
    },
    {
        "key": "ai",
        "name": "AI & Image Generation",
        "icon": "\U0001f916",
        "description": "AI chat, image generation, and smart features.",
    },
    {
        "key": "servermgmt",
        "name": "Server Management",
        "icon": "\U00002699",
        "description": "Server settings, roles, channels, and automation.",
    },
    {
        "key": "tags",
        "name": "Tags & Custom Content",
        "icon": "\U0001f4dd",
        "description": "Custom commands, tags, embeds, and user content.",
    },
    {
        "key": "emoji",
        "name": "Emoji & Reactions",
        "icon": "\U0001f60e",
        "description": "Emoji tools, reaction roles, and stickers.",
    },
    {
        "key": "social",
        "name": "Social & Profiles",
        "icon": "\U0001f465",
        "description": "User profiles, leveling, reputation, and social features.",
    },
    {
        "key": "feeds",
        "name": "Feeds & Notifications",
        "icon": "\U0001f514",
        "description": "RSS feeds, Twitch/YouTube alerts, and notifications.",
    },
    {
        "key": "logging",
        "name": "Logging & Statistics",
        "icon": "\U0001f4ca",
        "description": "Audit logs, message tracking, and server analytics.",
    },
    {
        "key": "core",
        "name": "Bot System & Core",
        "icon": "\U00002699\ufe0f",
        "description": "Core bot commands, settings, cog management, and owner tools.",
    },
    {
        "key": "other",
        "name": "Other",
        "icon": "\U0001f4e6",
        "description": "Miscellaneous cogs and commands.",
    },
]

COG_TO_CATEGORY = {
    # Moderation
    "mod": "moderation",
    "modlog": "moderation",
    "filter": "moderation",
    "automod": "moderation",
    "warnings": "moderation",
    "mutes": "moderation",
    "cleanup": "moderation",
    "reports": "moderation",
    "antispam": "moderation",
    "defender": "moderation",
    "warden": "moderation",
    "ban": "moderation",
    "kick": "moderation",
    "tempban": "moderation",
    "silence": "moderation",
    "antinuke": "moderation",
    "lockdown": "moderation",
    # Music
    "audio": "music",
    "music": "music",
    "playlist": "music",
    "voicemeister": "music",
    "sfx": "music",
    "soundboard": "music",
    # Fun & Games
    "trivia": "fun",
    "fun": "fun",
    "games": "fun",
    "memes": "fun",
    "casino": "fun",
    "hangman": "fun",
    "tictactoe": "fun",
    "rps": "fun",
    "8ball": "fun",
    "roll": "fun",
    "flip": "fun",
    "connect4": "fun",
    "battleship": "fun",
    "wordle": "fun",
    "dare": "fun",
    "truth": "fun",
    "wouldyourather": "fun",
    # Economy
    "economy": "economy",
    "bank": "economy",
    "shop": "economy",
    "credits": "economy",
    "slots": "economy",
    "heist": "economy",
    "gambling": "economy",
    "wallet": "economy",
    # Utility
    "general": "utility",
    "utility": "utility",
    "utils": "utility",
    "calc": "utility",
    "remindme": "utility",
    "remind": "utility",
    "poll": "utility",
    "translate": "utility",
    "weather": "utility",
    "urban": "utility",
    "wikipedia": "utility",
    "define": "utility",
    "afk": "utility",
    "highlights": "utility",
    "todo": "utility",
    "timezones": "utility",
    "timezone": "utility",
    "avatar": "utility",
    "userinfo": "utility",
    "serverinfo": "utility",
    "roleinfo": "utility",
    "google": "utility",
    "search": "utility",
    "qr": "utility",
    "color": "utility",
    "encode": "utility",
    "hash": "utility",
    "snipe": "utility",
    "stealemoji": "utility",
    "invitetracker": "utility",
    "giveaway": "utility",
    "giveaways": "utility",
    "tickettool": "utility",
    "tickets": "utility",
    "suggestion": "utility",
    "suggest": "utility",
    "roleplay": "utility",
    "nitrorole": "utility",
    # AI & Image
    "chatgpt": "ai",
    "openai": "ai",
    "aiart": "ai",
    "imagine": "ai",
    "dalle": "ai",
    "stablediffusion": "ai",
    "aiuser": "ai",
    "assistant": "ai",
    "aitools": "ai",
    # Server Management
    "admin": "servermgmt",
    "permissions": "servermgmt",
    "autorole": "servermgmt",
    "welcomer": "servermgmt",
    "welcome": "servermgmt",
    "leave": "servermgmt",
    "starboard": "servermgmt",
    "channelmanager": "servermgmt",
    "roletools": "servermgmt",
    "selfrole": "servermgmt",
    "servermanager": "servermgmt",
    "autoroom": "servermgmt",
    "tempchannels": "servermgmt",
    "backup": "servermgmt",
    "verification": "servermgmt",
    "captcha": "servermgmt",
    "application": "servermgmt",
    "forms": "servermgmt",
    # Tags & Custom Content
    "tags": "tags",
    "customcom": "tags",
    "cc": "tags",
    "customcommands": "tags",
    "embedutils": "tags",
    "embedcreator": "tags",
    "trigger": "tags",
    "retrigger": "tags",
    "autoresponder": "tags",
    # Emoji & Reactions
    "reactrole": "emoji",
    "reactionroles": "emoji",
    "emojimix": "emoji",
    "emojitools": "emoji",
    "emote": "emoji",
    "reactions": "emoji",
    # Social & Profiles
    "leveler": "social",
    "levelup": "social",
    "experience": "social",
    "xp": "social",
    "reputation": "social",
    "rep": "social",
    "profile": "social",
    "marry": "social",
    "birthday": "social",
    "birthdays": "social",
    "bday": "social",
    # Feeds & Notifications
    "rss": "feeds",
    "youtube": "feeds",
    "twitch": "feeds",
    "twitter": "feeds",
    "reddit": "feeds",
    "announcements": "feeds",
    "notifier": "feeds",
    "webhook": "feeds",
    "socialmedia": "feeds",
    # Logging
    "modlog": "logging",
    "logging": "logging",
    "messagelogs": "logging",
    "auditlog": "logging",
    "stats": "logging",
    "analytics": "logging",
    "cmdlog": "logging",
    "commandstats": "logging",
    # Core
    "core": "core",
    "owner": "core",
    "cog": "core",
    "cogmanager": "core",
    "downloader": "core",
    "info": "core",
    "set": "core",
    "alias": "core",
    "help": "core",
    "aboutcog": "core",
    "dashboard": "core",
    "api": "core",
    "config": "core",
}


def _slugify(text):
    """Make a URL-safe slug from text."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _flatten_commands(cmds, depth=0, parent_name="", prefix=""):
    """Recursively flatten a command tree into a list for table rendering.

    Each command dict has: {name, signature, short_description, description,
    aliases, privilege_level, user_permissions, subs: [...]}

    NOTE: RPC subcommand names already include parent prefix
    (e.g., "defender emergency" not just "emergency").
    So we extract the leaf name for display and use the parent as context.
    """
    flat = []
    for cmd in cmds:
        full_name = cmd.get("name", "")
        desc = cmd.get("short_description") or cmd.get("description") or ""

        # For subcommands, extract just the leaf portion for display.
        # e.g., "defender emergency" -> leaf is "emergency", parent is "defender"
        if depth > 0 and parent_name and full_name.startswith(parent_name + " "):
            leaf_name = full_name[len(parent_name) + 1 :]
        else:
            leaf_name = full_name

        flat.append(
            {
                "name": leaf_name,
                "full_name": full_name,
                "depth": depth,
                "parent_chain": parent_name if depth > 0 else "",
                "description": desc,
                "prefix": prefix,
            }
        )

        # Recurse into subcommands
        subs = cmd.get("subs", [])
        if subs:
            flat.extend(
                _flatten_commands(
                    subs, depth=depth + 1, parent_name=full_name, prefix=prefix
                )
            )

    return flat


def _count_commands(cmds):
    """Count total commands including all nested subcommands."""
    count = 0
    for cmd in cmds:
        count += 1
        subs = cmd.get("subs", [])
        if subs:
            count += _count_commands(subs)
    return count


def _build_categories(commands_data, prefix="[p]"):
    """Group cogs into categories and flatten command trees.

    commands_data format from RPC:
    {cog_name: {name, description, author, repo, commands: [...]}}
    """
    # Bucket cogs into categories
    cat_buckets = {}  # category_key -> list of cog dicts
    for cat_def in CATEGORY_DEFS:
        cat_buckets[cat_def["key"]] = []

    for cog_name, cog_data in commands_data.items():
        cog_lower = cog_name.lower()
        cat_key = COG_TO_CATEGORY.get(cog_lower, "other")
        # Ensure category exists
        if cat_key not in cat_buckets:
            cat_key = "other"

        raw_cmds = cog_data.get("commands", [])
        flat = _flatten_commands(raw_cmds, prefix=prefix)
        cmd_count = _count_commands(raw_cmds)

        cat_buckets[cat_key].append(
            {
                "name": cog_data.get("name", cog_name),
                "description": cog_data.get("description", ""),
                "cmd_count": cmd_count,
                "flat_commands": flat,
            }
        )

    # Build final categories list (skip empty ones)
    categories = []
    for cat_def in CATEGORY_DEFS:
        cogs = cat_buckets.get(cat_def["key"], [])
        if not cogs:
            continue
        # Sort cogs alphabetically
        cogs.sort(key=lambda c: c["name"].lower())
        total_cmds = sum(c["cmd_count"] for c in cogs)
        categories.append(
            {
                "name": cat_def["name"],
                "slug": _slugify(cat_def["name"]),
                "icon": cat_def["icon"],
                "description": cat_def["description"],
                "cog_count": len(cogs),
                "cmd_count": total_cmds,
                "cogs": cogs,
            }
        )

    return categories


# ── Routes ────────────────────────────────────────────────────────────


@base_bp.route("/")
def index():
    """Home page with bot stats."""
    app = current_app._get_current_object()
    bot = app.variables.get("bot", {})
    stats = app.variables.get("stats", {})
    connected = app.config.get("RPC_CONNECTED", False)

    return render_template(
        "pages/index.html",
        bot=bot,
        stats=stats,
        connected=connected,
    )


@base_bp.route("/commands")
def commands():
    """Bot commands listing with category grouping."""
    app = current_app._get_current_object()
    commands_data = app.variables.get("commands", {})
    connected = app.config.get("RPC_CONNECTED", False)

    # Get prefix for display
    bot = app.variables.get("bot", {})
    prefixes = bot.get("prefixes", [])
    prefix = prefixes[0] if prefixes else "[p]"

    categories = _build_categories(commands_data, prefix=prefix)
    cog_count = sum(c["cog_count"] for c in categories)
    cmd_count = sum(c["cmd_count"] for c in categories)

    return render_template(
        "pages/commands.html",
        categories=categories,
        cog_count=cog_count,
        cmd_count=cmd_count,
        connected=connected,
    )
