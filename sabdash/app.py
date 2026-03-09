"""Flask application factory for SabDash."""

import copy
import datetime
import logging
import os

from flask import Flask
from flask_wtf.csrf import CSRFProtect

from .auth import login_manager
from .config import Config
from .rpc_client import RPCClient
from .task_manager import TaskManager

logger = logging.getLogger("sabdash.app")


def create_app():
    """Create and configure the Flask application."""
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "static"),
    )
    app.config.from_object(Config)

    # Application state (populated by TaskManager)
    app.data = {}  # From DASHBOARDRPC__GET_DATA
    app.variables = {}  # From DASHBOARDRPC__GET_VARIABLES
    app.launch_time = datetime.datetime.utcnow()

    # Initialize RPC client
    app.rpc = RPCClient(
        host=app.config["RPC_HOST"],
        port=app.config["RPC_PORT"],
    )

    # Initialize extensions
    csrf = CSRFProtect(app)
    login_manager.init_app(app)

    # Initialize TaskManager and fetch initial data
    app.task_manager = TaskManager(app)
    logger.info("Fetching initial data from bot...")
    if app.task_manager.fetch_initial_data():
        logger.info("Initial data fetched successfully")
    else:
        logger.warning("Could not fetch initial data - bot may not be running")

    # Start background polling threads
    app.task_manager.start()

    # Register blueprints
    _register_blueprints(app, csrf)

    # Register context processor
    _register_context(app)

    # Register error handlers
    _register_errors(app)

    return app


def _register_blueprints(app, csrf):
    """Register all route blueprints."""
    from .routes.base import base_bp
    from .routes.login import login_bp
    from .routes.api import api_bp

    app.register_blueprint(base_bp)
    app.register_blueprint(login_bp, url_prefix="/login")
    app.register_blueprint(api_bp, url_prefix="/api")

    # Exempt API webhook endpoint from CSRF
    csrf.exempt(api_bp)


def _register_context(app):
    """Register template context processor."""

    @app.context_processor
    def inject_variables():
        variables = copy.deepcopy(app.variables) if app.variables else {}
        bot = variables.get("bot", {})

        # Calculate uptime
        uptime_ts = variables.get("stats", {}).get("uptime")
        if uptime_ts:
            uptime_dt = datetime.datetime.utcfromtimestamp(uptime_ts)
            uptime_delta = datetime.datetime.utcnow() - uptime_dt
        else:
            uptime_delta = datetime.timedelta(seconds=0)

        return {
            "variables": variables,
            "bot": bot,
            "stats": variables.get("stats", {}),
            "rpc_connected": app.config.get("RPC_CONNECTED", False),
            "uptime": _format_uptime(uptime_delta),
            "uptime_delta": uptime_delta,
        }

    def _format_uptime(delta):
        """Format timedelta as human-readable string."""
        total = int(delta.total_seconds())
        if total < 60:
            return "{}s".format(total)
        days, remainder = divmod(total, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, _ = divmod(remainder, 60)
        parts = []
        if days:
            parts.append("{}d".format(days))
        if hours:
            parts.append("{}h".format(hours))
        if minutes:
            parts.append("{}m".format(minutes))
        return " ".join(parts) or "0m"


def _register_errors(app):
    """Register error handlers."""

    @app.errorhandler(403)
    def forbidden(e):
        return _render_error(
            403, "ACCESS DENIED", "You do not have permission to access this resource."
        ), 403

    @app.errorhandler(404)
    def not_found(e):
        return _render_error(
            404, "NOT FOUND", "The requested resource could not be located."
        ), 404

    @app.errorhandler(500)
    def internal_error(e):
        return _render_error(
            500, "SYSTEM ERROR", "An internal error occurred. Please try again later."
        ), 500


def _render_error(code, title, message):
    """Render an error page."""
    from flask import render_template

    try:
        return render_template(
            "errors/error.html", code=code, title=title, message=message
        )
    except Exception:
        # Fallback if template doesn't exist yet
        return "<h1>{} - {}</h1><p>{}</p>".format(code, title, message)
