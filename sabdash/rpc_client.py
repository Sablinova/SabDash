"""WebSocket RPC client for communicating with Red-DiscordBot.

Uses websocket-client (synchronous) with JSON-RPC 2.0 protocol.
Thread-safe via threading.Lock.
"""

import json
import logging
import threading

import websocket

logger = logging.getLogger("sabdash.rpc")

# Exceptions that indicate a broken WebSocket connection
WS_EXCEPTIONS = (
    ConnectionRefusedError,
    websocket.WebSocketConnectionClosedException,
    ConnectionResetError,
    ConnectionAbortedError,
    BrokenPipeError,
    AttributeError,
    OSError,
)


class RPCClient:
    """Thread-safe JSON-RPC 2.0 client over WebSocket."""

    def __init__(self, host="localhost", port=6133):
        self.host = host
        self.port = port
        self.ws = None
        self.lock = threading.Lock()
        self._request_id = 0

    @property
    def url(self):
        return f"ws://{self.host}:{self.port}"

    @property
    def connected(self):
        return self.ws is not None and self.ws.connected

    def connect(self):
        """Establish WebSocket connection. Returns True on success."""
        with self.lock:
            return self._connect_locked()

    def _connect_locked(self):
        """Internal connect (must hold lock)."""
        try:
            if self.ws is not None:
                try:
                    self.ws.close()
                except Exception:
                    pass
            self.ws = websocket.WebSocket()
            self.ws.connect(self.url, timeout=10)
            logger.info("Connected to RPC at %s", self.url)
            return True
        except Exception as e:
            logger.warning("Failed to connect to RPC at %s: %s", self.url, e)
            self.ws = None
            return False

    def disconnect(self):
        """Close the WebSocket connection."""
        with self.lock:
            self._disconnect_locked()

    def _disconnect_locked(self):
        """Internal disconnect (must hold lock)."""
        if self.ws is not None:
            try:
                self.ws.close()
            except Exception:
                pass
            self.ws = None

    def request(self, method, params=None, retry=True):
        """Send a JSON-RPC 2.0 request and return the result.

        Args:
            method: RPC method name (e.g. "DASHBOARDRPC__GET_DATA")
            params: List of positional params or dict of named params
            retry: If True, retry once on connection failure

        Returns:
            dict with the result, or {"status": 1} on error
        """
        if params is None:
            params = []

        with self.lock:
            self._request_id += 1
            request_id = self._request_id

            payload = {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": method,
                "params": params,
            }

            try:
                if self.ws is None or not self.ws.connected:
                    if not self._connect_locked():
                        return {"status": 1, "error": "Not connected to bot"}

                self.ws.send(json.dumps(payload))
                raw = self.ws.recv()
                response = json.loads(raw)

                if "error" in response:
                    error = response["error"]
                    if "Method not found" in str(error):
                        logger.warning("RPC method not found: %s", method)
                        return {"status": 1, "error": "Method not found"}
                    logger.error("RPC error for %s: %s", method, error)
                    return {"status": 1, "error": str(error)}

                result = response.get("result", {})

                # Check for disconnected flag from rpc_check decorator
                if isinstance(result, dict) and result.get("disconnected"):
                    logger.warning("Bot reports disconnected for %s", method)
                    self._disconnect_locked()
                    return {"status": 1, "error": "Bot disconnected"}

                return result

            except WS_EXCEPTIONS as e:
                logger.warning("RPC connection error on %s: %s", method, e)
                self._disconnect_locked()

                if retry:
                    logger.info("Retrying RPC call %s...", method)
                    if self._connect_locked():
                        # Release lock concept not needed since we hold it;
                        # just retry inline
                        try:
                            self._request_id += 1
                            payload["id"] = self._request_id
                            self.ws.send(json.dumps(payload))
                            raw = self.ws.recv()
                            response = json.loads(raw)
                            if "error" in response:
                                return {"status": 1, "error": str(response["error"])}
                            result = response.get("result", {})
                            if isinstance(result, dict) and result.get("disconnected"):
                                self._disconnect_locked()
                                return {"status": 1, "error": "Bot disconnected"}
                            return result
                        except WS_EXCEPTIONS as e2:
                            logger.error("RPC retry failed for %s: %s", method, e2)
                            self._disconnect_locked()

                return {"status": 1, "error": "Connection lost"}

            except Exception as e:
                logger.error("Unexpected RPC error on %s: %s", method, e)
                self._disconnect_locked()
                return {"status": 1, "error": str(e)}
