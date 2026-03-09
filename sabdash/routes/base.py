"""Base routes: index, commands."""

import logging

from flask import Blueprint, render_template, current_app

logger = logging.getLogger("sabdash.routes.base")

base_bp = Blueprint("base", __name__)


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
    """Bot commands listing."""
    app = current_app._get_current_object()
    commands_data = app.variables.get("commands", {})
    connected = app.config.get("RPC_CONNECTED", False)

    return render_template(
        "pages/commands.html",
        commands=commands_data,
        connected=connected,
    )
