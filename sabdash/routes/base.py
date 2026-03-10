"""Base routes: index, commands with category grouping."""

import logging
import re

from flask import Blueprint, render_template, current_app

logger = logging.getLogger("sabdash.routes.base")

base_bp = Blueprint("base", __name__)

# ── Category definitions ──────────────────────────────────────────────
# Defines the available categories.  Cogs are assigned via:
#   1. Manual overrides in COG_TO_CATEGORY (highest priority)
#   2. Keyword matching in CATEGORY_KEYWORDS (automatic)
#   3. Fallback to "Other"
# Auto-categorization runs on every page render using fresh RPC data,
# so new cogs are categorized immediately without code changes.

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
        "key": "media",
        "name": "Image & Media",
        "icon": "\U0001f5bc",
        "description": "Image manipulation, media tools, and content lookups.",
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

# ── Manual overrides ───────────────────────────────────────────────────
# Cogs listed here always map to the specified category regardless of
# keyword matching.  Cog names are lowercased before lookup.
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
    "altdentifier": "moderation",
    "bancheck": "moderation",
    "banmessage": "moderation",
    "clearchannel": "moderation",
    "fakemod": "moderation",
    "globalban": "moderation",
    "inviteblocklist": "moderation",
    "lock": "moderation",
    "purge": "moderation",
    "security": "moderation",
    "extendedmodlog": "moderation",
    "sabhoneypot": "moderation",
    # Music & Audio
    "audio": "music",
    "music": "music",
    "playlist": "music",
    "voicemeister": "music",
    "sfx": "music",
    "soundboard": "music",
    "audioplayer": "music",
    "audiotrivia": "music",
    "smartlyrics": "music",
    "shazam": "music",
    "lastfm": "music",
    "spotify": "music",
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
    "adventure": "fun",
    "battleroyale": "fun",
    "cardsagainsthumanity": "fun",
    "compliment": "fun",
    "conversationgames": "fun",
    "crabrrave": "fun",
    "crabrave": "fun",
    "fastclickgame": "fun",
    "genshin": "fun",
    "hitormiss": "fun",
    "insult": "fun",
    "lenny": "fun",
    "lovecalc": "fun",
    "meme": "fun",
    "minesweeper": "fun",
    "partygames": "fun",
    "randomness": "fun",
    "riddles": "fun",
    "rolloutgame": "fun",
    "snake": "fun",
    "ttt": "fun",
    "typeracer": "fun",
    "uttt": "fun",
    "wordlegame": "fun",
    # Economy & Currency
    "economy": "economy",
    "bank": "economy",
    "shop": "economy",
    "credits": "economy",
    "slots": "economy",
    "heist": "economy",
    "gambling": "economy",
    "wallet": "economy",
    "economytrack": "economy",
    "extendedeconomy": "economy",
    "unbelievaboat": "economy",
    # Utility & Tools
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
    "anotherpingcog": "utility",
    "bigtext": "utility",
    "bookery": "utility",
    "calculator": "utility",
    "calendar": "utility",
    "catfact": "utility",
    "codesnippets": "utility",
    "coffeetime": "utility",
    "conversions": "utility",
    "converters": "utility",
    "dankutils": "utility",
    "deals": "utility",
    "dictionary": "utility",
    "easytranslate": "utility",
    "elements": "utility",
    "encoding": "utility",
    "exportchannel": "utility",
    "f1": "utility",
    "faceit": "utility",
    "fakeidentities": "utility",
    "firstmessage": "utility",
    "fivem": "utility",
    "flags": "utility",
    "forcemention": "utility",
    "googleit": "utility",
    "holiday": "utility",
    "hpapi": "utility",
    "httpcat": "utility",
    "linkquoter": "utility",
    "morseshark": "utility",
    "netspeed": "utility",
    "onlinestats": "utility",
    "pingsite": "utility",
    "pingtime": "utility",
    "recipes": "utility",
    "reminders": "utility",
    "sabdownloader": "utility",
    "system": "utility",
    "timestamp": "utility",
    "urlscan": "utility",
    "vrtutils": "utility",
    "whoplays": "utility",
    "ip": "utility",
    # AI & Image Generation
    "chatgpt": "ai",
    "openai": "ai",
    "aiart": "ai",
    "imagine": "ai",
    "dalle": "ai",
    "stablediffusion": "ai",
    "aiuser": "ai",
    "assistant": "ai",
    "aitools": "ai",
    "fluximggen": "ai",
    "imggen": "ai",
    # Image & Media
    "image": "media",
    "imagemaker": "media",
    "addimage": "media",
    "badges": "media",
    "bubble": "media",
    "inspirobot": "media",
    "notsobot": "media",
    "petpet": "media",
    "pfpimgen": "media",
    "coffeeani": "media",
    "holowiki": "media",
    "themoviedb": "media",
    "doujin": "media",
    "rydcog": "media",
    "ytd": "media",
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
    "autodelete": "servermgmt",
    "cartographer": "servermgmt",
    "events": "servermgmt",
    "eventconfig": "servermgmt",
    "freshmeat": "servermgmt",
    "guildlog": "servermgmt",
    "infochannel": "servermgmt",
    "maintenance": "servermgmt",
    "messagepinner": "servermgmt",
    "referrals": "servermgmt",
    "roleall": "servermgmt",
    "say": "servermgmt",
    "speak": "servermgmt",
    "sticky": "servermgmt",
    "stickymember": "servermgmt",
    "temproles": "servermgmt",
    "timechannel": "servermgmt",
    "serversupporters": "servermgmt",
    "forward": "servermgmt",
    "discordsearch": "servermgmt",
    "hideping": "servermgmt",
    "hider": "servermgmt",
    "namechanger": "servermgmt",
    "statusrole": "servermgmt",
    "stripeidentity": "servermgmt",
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
    "slashtags": "tags",
    "commandsbuttons": "tags",
    # Emoji & Reactions
    "reactrole": "emoji",
    "reactionroles": "emoji",
    "emojimix": "emoji",
    "emojitools": "emoji",
    "emote": "emoji",
    "reactions": "emoji",
    "emojieverywhere": "emoji",
    "emojigrabber": "emoji",
    "emojimixup": "emoji",
    "emojisteal": "emoji",
    "emotes": "emoji",
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
    "wordstats": "social",
    "teachme": "social",
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
    "rssnotifier": "feeds",
    "streams": "feeds",
    "status": "feeds",
    "pstreamstatus": "feeds",
    "gmail": "feeds",
    "githubcards": "feeds",
    "cloudflare": "feeds",
    "uptimeresponder": "feeds",
    # Logging & Statistics
    "logging": "logging",
    "messagelogs": "logging",
    "auditlog": "logging",
    "stats": "logging",
    "analytics": "logging",
    "cmdlog": "logging",
    "commandstats": "logging",
    "consolelogs": "logging",
    "guildstats": "logging",
    "imagelog": "logging",
    "invites": "logging",
    "stattrack": "logging",
    "tidbstats": "logging",
    # Bot System & Core
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
    "autodocs": "core",
    "categoryhelp": "core",
    "cogmanagerui": "core",
    "cyclestatus": "core",
    "dev": "core",
    "devutils": "core",
    "fifo": "core",
    "index": "core",
    "shell": "core",
    "sabby": "core",
    "bridge": "core",
    "fluxerbridge": "core",
    "rift": "core",
}


# ── Auto-categorization keywords ──────────────────────────────────────
# Each category has a list of keywords.  When a cog is NOT in the manual
# override dict, its name and description are scanned against these.
# The category with the most keyword hits wins.  Ties go to the first
# category in definition order.  Zero hits -> "other".
#
# Keywords are matched as whole words (word-boundary regex) against the
# lowercased cog name + description.  Keep them lowercase.
CATEGORY_KEYWORDS = {
    "moderation": [
        "ban",
        "kick",
        "mute",
        "warn",
        "filter",
        "spam",
        "nuke",
        "lockdown",
        "moderate",
        "moderation",
        "modlog",
        "automod",
        "punish",
        "infraction",
        "timeout",
        "quarantine",
        "raid",
        "honeypot",
        "blocklist",
        "purge",
        "silence",
        "censor",
    ],
    "music": [
        "music",
        "audio",
        "song",
        "playlist",
        "lyrics",
        "voice",
        "play",
        "queue",
        "now playing",
        "soundboard",
        "sfx",
        "spotify",
        "lastfm",
        "shazam",
        "listen",
        "track",
    ],
    "fun": [
        "game",
        "trivia",
        "joke",
        "meme",
        "random",
        "fun",
        "casino",
        "hangman",
        "tictactoe",
        "rps",
        "roll",
        "flip",
        "dare",
        "truth",
        "riddle",
        "battle",
        "snake",
        "wordle",
        "insult",
        "compliment",
        "lenny",
        "crab",
        "race",
        "entertainment",
        "minigame",
        "mini-game",
        "play",
    ],
    "economy": [
        "economy",
        "bank",
        "credit",
        "currency",
        "shop",
        "slot",
        "heist",
        "gambling",
        "wallet",
        "money",
        "coin",
        "balance",
        "pay",
        "deposit",
        "withdraw",
    ],
    "utility": [
        "utility",
        "tool",
        "convert",
        "translate",
        "weather",
        "remind",
        "poll",
        "timer",
        "calculator",
        "dictionary",
        "lookup",
        "search",
        "info",
        "ping",
        "qr",
        "encode",
        "decode",
        "hash",
        "snipe",
        "quote",
        "giveaway",
        "ticket",
        "suggest",
        "bookmark",
        "note",
        "export",
        "download",
        "speed",
        "scan",
        "fact",
    ],
    "ai": [
        "ai",
        "openai",
        "chatgpt",
        "gpt",
        "dall-e",
        "dalle",
        "stable diffusion",
        "generate image",
        "artificial intelligence",
        "machine learning",
        "neural",
        "llm",
        "prompt",
    ],
    "media": [
        "image",
        "photo",
        "picture",
        "gif",
        "video",
        "media",
        "movie",
        "anime",
        "manga",
        "pfp",
        "avatar",
        "badge",
        "petpet",
        "thumbnail",
        "artwork",
        "gallery",
        "film",
        "youtube",
        "download",
        "manipulation",
        "edit image",
    ],
    "servermgmt": [
        "server",
        "role",
        "channel",
        "welcome",
        "autorole",
        "permission",
        "backup",
        "verification",
        "captcha",
        "autoroom",
        "starboard",
        "application",
        "form",
        "sticky",
        "maintenance",
        "member",
        "join",
        "leave",
        "manage",
        "setup",
        "configure",
    ],
    "tags": [
        "tag",
        "custom command",
        "customcom",
        "embed",
        "trigger",
        "autorespond",
        "responder",
        "template",
        "slash tag",
    ],
    "emoji": [
        "emoji",
        "emote",
        "reaction",
        "react role",
        "sticker",
    ],
    "social": [
        "level",
        "xp",
        "experience",
        "reputation",
        "rep",
        "profile",
        "marry",
        "birthday",
        "social",
        "leaderboard",
        "rank",
    ],
    "feeds": [
        "feed",
        "rss",
        "twitch",
        "twitter",
        "reddit",
        "stream",
        "youtube",
        "notification",
        "alert",
        "announce",
        "webhook",
        "github",
        "uptime",
    ],
    "logging": [
        "log",
        "audit",
        "stat",
        "analytics",
        "track",
        "monitor",
        "record",
        "history",
    ],
    "core": [
        "core",
        "owner",
        "cog manager",
        "downloader",
        "alias",
        "help",
        "dashboard",
        "config",
        "dev",
        "debug",
        "shell",
        "bridge",
        "rift",
    ],
}

# Pre-compile keyword patterns for performance (word-boundary matching)
_KEYWORD_PATTERNS = {}
for _cat_key, _words in CATEGORY_KEYWORDS.items():
    _KEYWORD_PATTERNS[_cat_key] = [
        re.compile(r"\b" + re.escape(w) + r"\b", re.IGNORECASE) for w in _words
    ]


def _auto_categorize(cog_name, cog_description=""):
    """Determine category for a cog using manual overrides + keyword matching.

    Priority:
      1. Manual override dict (exact match on lowercased cog name)
      2. Keyword matching against cog name + description
      3. Fallback to "other"
    """
    cog_lower = cog_name.lower()

    # 1. Manual override
    if cog_lower in COG_TO_CATEGORY:
        return COG_TO_CATEGORY[cog_lower]

    # 2. Keyword matching: score each category
    text = "{} {}".format(cog_lower, (cog_description or "").lower())
    best_cat = "other"
    best_score = 0

    for cat_key, patterns in _KEYWORD_PATTERNS.items():
        score = sum(1 for p in patterns if p.search(text))
        if score > best_score:
            best_score = score
            best_cat = cat_key

    if best_score > 0:
        logger.debug(
            "Auto-categorized cog '{}' -> '{}' (score={})".format(
                cog_name, best_cat, best_score
            )
        )
    else:
        logger.info(
            "Cog '{}' unmatched by keywords, falling back to 'other'".format(cog_name)
        )

    return best_cat


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


def build_category_cache(app):
    """Build categorized command data and store it on the app object.

    Called by the task manager whenever GET_VARIABLES returns new data.
    This runs the auto-categorization + keyword matching once, and caches
    the full result so page renders just read the cache.
    """
    commands_data = app.variables.get("commands", {})
    if not commands_data:
        return

    bot = app.variables.get("bot", {})
    prefixes = bot.get("prefixes", [])
    prefix = prefixes[0] if prefixes else "[p]"

    categories = _build_categories(commands_data, prefix)
    cog_count = sum(c["cog_count"] for c in categories)
    cmd_count = sum(c["cmd_count"] for c in categories)

    app.cached_categories = categories
    app.cached_cog_count = cog_count
    app.cached_cmd_count = cmd_count

    logger.info(
        "Category cache rebuilt: %d categories, %d cogs, %d commands",
        len(categories),
        cog_count,
        cmd_count,
    )


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
        cog_desc = cog_data.get("description", "")
        cat_key = _auto_categorize(cog_name, cog_desc)
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
    connected = app.config.get("RPC_CONNECTED", False)

    # Use cached categories built by the task manager
    categories = getattr(app, "cached_categories", [])
    cog_count = getattr(app, "cached_cog_count", 0)
    cmd_count = getattr(app, "cached_cmd_count", 0)

    return render_template(
        "pages/commands.html",
        categories=categories,
        cog_count=cog_count,
        cmd_count=cmd_count,
        connected=connected,
    )
