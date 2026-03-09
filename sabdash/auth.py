"""Authentication: User model, JWT tokens, Flask-Login, Discord OAuth2."""

import datetime
import logging

import jwt
import requests
from flask import current_app
from flask_login import LoginManager, UserMixin

logger = logging.getLogger("sabdash.auth")

login_manager = LoginManager()
login_manager.session_protection = "strong"
login_manager.login_view = "login.login_page"


class User(UserMixin):
    """Dashboard user backed by Discord identity."""

    # Class-level user cache: {user_id: User}
    USERS = {}

    def __init__(self, user_id, name, global_name=None, avatar_url=None):
        self.id = str(user_id)
        self.name = name
        self.global_name = global_name
        self.avatar_url = avatar_url
        self.devices = []  # Active JWT session tokens
        User.USERS[self.id] = self

    @property
    def display_name(self):
        return self.global_name or self.name

    @property
    def display_avatar(self):
        if self.avatar_url:
            return self.avatar_url
        # Default Discord avatar
        default_idx = (int(self.id) >> 22) % 6
        return "https://cdn.discordapp.com/embed/avatars/{}.png".format(default_idx)

    @property
    def is_owner(self):
        """Check if this user is a bot owner."""
        app = current_app._get_current_object()
        owner_ids = app.variables.get("bot", {}).get("owner_ids", [])
        return int(self.id) in owner_ids

    @property
    def is_active(self):
        return not self.is_blacklisted

    @property
    def is_blacklisted(self):
        app = current_app._get_current_object()
        blacklisted = app.variables.get("bot", {}).get("blacklisted_users", [])
        return int(self.id) in blacklisted

    def get_id(self):
        """Generate a JWT token for Flask-Login session."""
        app = current_app._get_current_object()
        token = generate_token(
            app,
            user_id=self.id,
            action="login",
            expiration_hours=app.config.get("JWT_EXPIRATION_HOURS", 24),
        )
        # Track active sessions
        self.devices.append(token)
        # Keep only last 5 sessions
        if len(self.devices) > 5:
            self.devices = self.devices[-5:]
        return token

    @classmethod
    def get(cls, user_id):
        return cls.USERS.get(str(user_id))


def generate_token(app, user_id, action, expiration_hours=24, **extra):
    """Generate a JWT token."""
    payload = {
        "user_id": str(user_id),
        "action": action,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=expiration_hours),
    }
    payload.update(extra)
    secret = app.config.get("SECRET_KEY", "fallback-secret")
    return jwt.encode(
        payload, secret, algorithm=app.config.get("JWT_ALGORITHM", "HS256")
    )


def decode_token(app, token, action=None):
    """Decode and validate a JWT token.

    Returns (user, payload) or (None, None) on failure.
    """
    try:
        secret = app.config.get("SECRET_KEY", "fallback-secret")
        payload = jwt.decode(
            token, secret, algorithms=[app.config.get("JWT_ALGORITHM", "HS256")]
        )
        if action and payload.get("action") != action:
            return None, None
        user = User.get(payload.get("user_id"))
        return user, payload
    except jwt.ExpiredSignatureError:
        logger.debug("Token expired")
        return None, None
    except jwt.InvalidTokenError as e:
        logger.debug("Invalid token: %s", e)
        return None, None


@login_manager.user_loader
def load_user(token):
    """Flask-Login user loader — decodes JWT from session."""
    app = current_app._get_current_object()
    user, payload = decode_token(app, token, action="login")
    if user is None:
        return None
    if not user.is_active:
        return None
    if token not in user.devices:
        return None
    return user


def discord_get_token(code, redirect_uri, app):
    """Exchange OAuth2 code for Discord access token."""
    application_id = app.variables.get("bot", {}).get("application_id")
    oauth_secret = app.config.get("OAUTH_SECRET")

    if not application_id or not oauth_secret:
        logger.error("Missing application_id or oauth_secret for token exchange")
        return None

    data = {
        "client_id": str(application_id),
        "client_secret": oauth_secret,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
    }

    try:
        r = requests.post(
            "{}/oauth2/token".format(app.config["DISCORD_API_BASE"]),
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10,
        )
        r.raise_for_status()
        return r.json().get("access_token")
    except Exception as e:
        logger.error("Discord token exchange failed: %s", e)
        return None


def discord_get_user(access_token, app):
    """Fetch Discord user profile with access token."""
    try:
        r = requests.get(
            "{}/users/@me".format(app.config["DISCORD_API_BASE"]),
            headers={"Authorization": "Bearer {}".format(access_token)},
            timeout=10,
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error("Discord user fetch failed: %s", e)
        return None
