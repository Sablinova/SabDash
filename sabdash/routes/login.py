"""Login routes: Discord OAuth2 flow."""

import logging
import os

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_user, logout_user

from ..auth import User, discord_get_token, discord_get_user

logger = logging.getLogger("sabdash.routes.login")

login_bp = Blueprint("login", __name__)


@login_bp.route("/")
def login_page():
    """Login page with Discord OAuth button."""
    if current_user.is_authenticated:
        return redirect(url_for("base.index"))

    return render_template("pages/login.html")


@login_bp.route("/discord")
def discord_redirect():
    """Redirect to Discord OAuth2 authorization."""
    app = current_app._get_current_object()
    application_id = app.variables.get("bot", {}).get("application_id")
    oauth_secret = app.config.get("OAUTH_SECRET")

    if not application_id or not oauth_secret:
        flash("OAuth is not configured. Please check bot settings.", "danger")
        return redirect(url_for("base.index"))

    # Generate state for CSRF protection
    state = os.urandom(16).hex()
    session["oauth_state"] = state

    # Build redirect URI
    redirect_uri = app.config.get("REDIRECT_URI")
    if not redirect_uri:
        redirect_uri = url_for("login.callback", _external=True)

    params = {
        "client_id": str(application_id),
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": app.config["DISCORD_OAUTH_SCOPE"],
        "state": state,
    }

    query = "&".join("{}={}".format(k, v) for k, v in params.items())
    auth_url = "{}/oauth2/authorize?{}".format(app.config["DISCORD_API_BASE"], query)
    return redirect(auth_url)


@login_bp.route("/callback")
def callback():
    """Handle Discord OAuth2 callback."""
    app = current_app._get_current_object()

    # Validate state
    state = request.args.get("state")
    if state != session.pop("oauth_state", None):
        flash("Invalid OAuth state. Please try again.", "danger")
        return redirect(url_for("login.login_page"))

    # Get authorization code
    code = request.args.get("code")
    if not code:
        flash("No authorization code received.", "danger")
        return redirect(url_for("login.login_page"))

    # Build redirect URI (must match the one used in authorization)
    redirect_uri = app.config.get("REDIRECT_URI")
    if not redirect_uri:
        redirect_uri = url_for("login.callback", _external=True)

    # Exchange code for access token
    access_token = discord_get_token(code, redirect_uri, app)
    if not access_token:
        flash("Failed to authenticate with Discord.", "danger")
        return redirect(url_for("login.login_page"))

    # Fetch user profile
    user_data = discord_get_user(access_token, app)
    if not user_data:
        flash("Failed to fetch user profile.", "danger")
        return redirect(url_for("login.login_page"))

    # Build avatar URL
    user_id = user_data["id"]
    avatar = user_data.get("avatar")
    if avatar:
        ext = "gif" if avatar.startswith("a_") else "png"
        avatar_url = "https://cdn.discordapp.com/avatars/{}/{}.{}".format(
            user_id, avatar, ext
        )
    else:
        avatar_url = None

    # Create or update user
    user = User(
        user_id=user_id,
        name=user_data.get("username", "Unknown"),
        global_name=user_data.get("global_name"),
        avatar_url=avatar_url,
    )

    # Log in
    login_user(user, remember=False)
    logger.info("User %s (%s) logged in", user.display_name, user.id)
    flash("Welcome, {}!".format(user.display_name), "success")

    # Redirect to original destination or index
    next_url = request.args.get("next") or url_for("base.index")
    return redirect(next_url)


@login_bp.route("/logout")
def logout():
    """Log out the current user."""
    if current_user.is_authenticated:
        logger.info(
            "User %s (%s) logged out", current_user.display_name, current_user.id
        )
        # Remove session token from user devices
        token = session.get("_user_id")
        if token and token in current_user.devices:
            current_user.devices.remove(token)
        logout_user()
        flash("You have been logged out.", "info")

    return redirect(url_for("base.index"))
