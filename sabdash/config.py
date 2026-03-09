"""Application configuration for SabDash."""

import os


class Config:
    """Base configuration. Secret keys from bot RPC (secret_key,
    jwt_secret_key) are set dynamically after first GET_DATA call."""

    # Flask core
    SECRET_KEY = os.urandom(32).hex()
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    TEMPLATES_AUTO_RELOAD = True

    # Server
    HOST = "0.0.0.0"
    PORT = 42356

    # RPC connection to Red-DiscordBot
    RPC_HOST = "localhost"
    RPC_PORT = 6133
    RPC_POLL_INTERVAL = 15  # seconds between background polls
    RPC_CONNECTED = False

    # Discord OAuth2 (application_id comes from bot variables)
    DISCORD_API_BASE = "https://discord.com/api/v9"
    DISCORD_OAUTH_SCOPE = "identify"

    # JWT
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = 24

    # Session
    SESSION_COOKIE_NAME = "sabdash_session"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # CSRF
    WTF_CSRF_ENABLED = True
