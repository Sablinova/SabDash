"""SabDash entry point — runs the Flask application via Waitress."""

import logging

from waitress import serve

from sabdash.app import create_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("sabdash")

if __name__ == "__main__":
    app = create_app()
    host = app.config.get("HOST", "0.0.0.0")
    port = app.config.get("PORT", 42356)
    logger.info("Starting SabDash on %s:%s", host, port)
    serve(app, host=host, port=port, threads=10)
