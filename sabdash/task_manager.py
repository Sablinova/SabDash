"""Background task manager for polling bot data via RPC.

Runs daemon threads that periodically fetch:
- GET_DATA: dashboard config (secrets, UI settings, custom pages, blacklisted IPs)
- GET_VARIABLES: bot runtime data (commands, stats, third_parties, bot info)
- CHECK_VERSION: detect cog reloads
- Connection monitor: track RPC connection state
"""

import logging
import threading
import time

logger = logging.getLogger("sabdash.tasks")


class TaskManager:
    """Manages background polling threads for RPC data."""

    def __init__(self, app):
        self.app = app
        self.rpc = app.rpc
        self.threads = []
        self._stop_event = threading.Event()
        self._version = None

    def start(self):
        """Start all background polling threads."""
        targets = [
            ("data-poller", self._poll_data),
            ("vars-poller", self._poll_variables),
            ("version-checker", self._check_version),
            ("conn-monitor", self._monitor_connection),
        ]
        for name, target in targets:
            t = threading.Thread(target=target, name=name, daemon=True)
            t.start()
            self.threads.append(t)
            logger.info("Started background thread: %s", name)

    def stop(self):
        """Signal all threads to stop."""
        self._stop_event.set()
        for t in self.threads:
            t.join(timeout=5)
        self.threads.clear()
        logger.info("All background threads stopped")

    def fetch_initial_data(self):
        """Blocking call to fetch data and variables once at startup.
        Returns True if both succeeded."""
        data_ok = self._do_fetch_data()
        vars_ok = self._do_fetch_variables()
        return data_ok and vars_ok

    def _do_fetch_data(self):
        """Fetch GET_DATA from bot and update app.data."""
        result = self.rpc.request("DASHBOARDRPC__GET_DATA")
        if isinstance(result, dict) and result.get("status") != 1:
            self.app.data = result
            # Update secret keys from bot config
            core = result.get("core", {})
            if core.get("secret_key"):
                self.app.config["SECRET_KEY"] = core["secret_key"]
            if core.get("jwt_secret_key"):
                self.app.config["JWT_SECRET_KEY"] = core["jwt_secret_key"]
            if core.get("secret"):
                self.app.config["OAUTH_SECRET"] = core["secret"]
            if core.get("redirect_uri"):
                self.app.config["REDIRECT_URI"] = core["redirect_uri"]

            self.app.config["RPC_CONNECTED"] = True
            logger.info("GET_DATA fetched successfully")
            return True
        else:
            logger.warning("GET_DATA failed: %s", result)
            self.app.config["RPC_CONNECTED"] = False
            return False

    def _do_fetch_variables(self):
        """Fetch GET_VARIABLES from bot and update app.variables."""
        result = self.rpc.request("DASHBOARDRPC__GET_VARIABLES")
        if isinstance(result, dict) and result.get("status") != 1:
            self.app.variables = result
            self.app.config["RPC_CONNECTED"] = True
            logger.info("GET_VARIABLES fetched successfully")

            # Rebuild category cache with fresh command data
            self._rebuild_category_cache()

            return True
        else:
            logger.warning("GET_VARIABLES failed: %s", result)
            return False

    def _rebuild_category_cache(self):
        """Rebuild the cached category/command data from current variables."""
        try:
            from sabdash.routes.base import build_category_cache

            build_category_cache(self.app)
        except Exception:
            logger.exception("Failed to rebuild category cache")

    def _poll_data(self):
        """Continuously poll GET_DATA."""
        while not self._stop_event.is_set():
            self._do_fetch_data()
            self._stop_event.wait(self.app.config.get("RPC_POLL_INTERVAL", 15))

    def _poll_variables(self):
        """Continuously poll GET_VARIABLES."""
        while not self._stop_event.is_set():
            self._do_fetch_variables()
            self._stop_event.wait(self.app.config.get("RPC_POLL_INTERVAL", 15))

    def _check_version(self):
        """Periodically check if the Dashboard cog was reloaded."""
        while not self._stop_event.is_set():
            result = self.rpc.request("DASHBOARDRPC__CHECK_VERSION")
            if isinstance(result, dict) and "version" in result:
                new_version = result["version"]
                if self._version is not None and new_version != self._version:
                    logger.info(
                        "Dashboard cog version changed (%s -> %s), reconnecting",
                        self._version,
                        new_version,
                    )
                    self.rpc.disconnect()
                    self.rpc.connect()
                    self._do_fetch_data()
                    self._do_fetch_variables()
                self._version = new_version
            self._stop_event.wait(30)

    def _monitor_connection(self):
        """Rapidly monitor WebSocket connection state."""
        was_connected = False
        while not self._stop_event.is_set():
            is_connected = self.rpc.connected
            if is_connected and not was_connected:
                logger.info("RPC connection established")
                self.app.config["RPC_CONNECTED"] = True
            elif not is_connected and was_connected:
                logger.warning("RPC connection lost, attempting reconnect")
                self.app.config["RPC_CONNECTED"] = False
                self.rpc.connect()
            was_connected = is_connected
            self._stop_event.wait(2)
