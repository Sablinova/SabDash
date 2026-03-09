"""API routes: webhook receiver, stream endpoint."""

import logging

from flask import Blueprint, jsonify, request

logger = logging.getLogger("sabdash.routes.api")

api_bp = Blueprint("api", __name__)


@api_bp.route("/webhook", methods=["POST"])
def webhook():
    """Receive webhook payloads and forward to bot via RPC."""
    from flask import current_app

    app = current_app._get_current_object()
    payload = request.get_json(silent=True) or {}

    result = app.rpc.request(
        "DASHBOARDRPC_WEBHOOKS__WEBHOOK_RECEIVE",
        [{"payload": payload}],
    )

    return jsonify(result)


@api_bp.route("/status")
def status():
    """Health check endpoint."""
    from flask import current_app

    app = current_app._get_current_object()
    return jsonify(
        {
            "status": "ok",
            "rpc_connected": app.config.get("RPC_CONNECTED", False),
        }
    )
