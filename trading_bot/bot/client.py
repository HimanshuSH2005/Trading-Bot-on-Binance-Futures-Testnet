"""
Low-level Binance Futures Testnet REST client.

Handles:
- HMAC-SHA256 request signing
- Timestamped query strings
- Response parsing and error surfacing
- Full request / response logging
"""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any
from urllib.parse import urlencode

import requests

from .logging_config import get_logger

logger = get_logger("client")

BASE_URL = "https://testnet.binancefuture.com"
RECV_WINDOW = 5000  # milliseconds


class BinanceAPIError(Exception):
    """Raised when the Binance API returns an error payload."""

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"Binance API error {code}: {message}")


class BinanceFuturesClient:
    """
    Thin wrapper around the Binance USDT-M Futures Testnet REST API.

    Usage
    -----
    client = BinanceFuturesClient(api_key="...", api_secret="...")
    response = client.place_order(symbol="BTCUSDT", side="BUY",
                                  order_type="MARKET", quantity=0.001)
    """

    def __init__(self, api_key: str, api_secret: str, base_url: str = BASE_URL):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "X-MBX-APIKEY": self.api_key,
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )
        logger.debug("BinanceFuturesClient initialised (base_url=%s)", self.base_url)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _timestamp(self) -> int:
        return int(time.time() * 1000)

    def _sign(self, params: dict) -> dict:
        """Append HMAC-SHA256 signature to *params* dict and return it."""
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        params["signature"] = signature
        return params

    def _request(self, method: str, endpoint: str, params: dict | None = None) -> Any:
        """
        Execute a signed HTTP request and return the parsed JSON body.

        Raises
        ------
        BinanceAPIError   – API returned a business-logic error.
        requests.Timeout  – Network timeout.
        requests.ConnectionError – Connectivity problem.
        """
        params = params or {}
        params["timestamp"] = self._timestamp()
        params["recvWindow"] = RECV_WINDOW
        params = self._sign(params)

        url = f"{self.base_url}{endpoint}"
        logger.debug("→ %s %s | params: %s", method.upper(), url, {k: v for k, v in params.items() if k != "signature"})

        try:
            if method.upper() == "POST":
                response = self.session.post(url, data=params, timeout=10)
            elif method.upper() == "GET":
                response = self.session.get(url, params=params, timeout=10)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, params=params, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
        except requests.Timeout as exc:
            logger.error("Request timed out: %s %s", method, endpoint)
            raise
        except requests.ConnectionError as exc:
            logger.error("Connection error: %s %s — %s", method, endpoint, exc)
            raise

        logger.debug("← HTTP %s | body: %s", response.status_code, response.text[:500])

        data = response.json()

        # Binance error payloads always contain a numeric "code" < 0
        if isinstance(data, dict) and data.get("code", 0) < 0:
            logger.error("Binance API error: code=%s msg=%s", data.get("code"), data.get("msg"))
            raise BinanceAPIError(data["code"], data.get("msg", "Unknown error"))

        return data

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    def get_server_time(self) -> int:
        """Return server time in ms (useful for connectivity checks)."""
        data = self.session.get(f"{self.base_url}/fapi/v1/time", timeout=5).json()
        return data["serverTime"]

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float | None = None,
        stop_price: float | None = None,
        time_in_force: str = "GTC",
    ) -> dict:
        """
        Place a new order on Binance Futures Testnet.

        Parameters
        ----------
        symbol       : Trading pair, e.g. "BTCUSDT"
        side         : "BUY" or "SELL"
        order_type   : "MARKET", "LIMIT", or "STOP_MARKET"
        quantity     : Order quantity in base asset
        price        : Limit price (required for LIMIT / STOP_MARKET)
        stop_price   : Trigger price for STOP_MARKET orders
        time_in_force: "GTC" (default), "IOC", "FOK" – ignored for MARKET
        """
        params: dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
        }

        if order_type == "LIMIT":
            if price is None:
                raise ValueError("price is required for LIMIT orders.")
            params["price"] = price
            params["timeInForce"] = time_in_force

        elif order_type == "STOP_MARKET":
            if stop_price is None and price is not None:
                stop_price = price  # allow --price to double as --stop-price
            if stop_price is None:
                raise ValueError("price/stop_price is required for STOP_MARKET orders.")
            params["stopPrice"] = stop_price

        logger.info(
            "Placing order → symbol=%s side=%s type=%s qty=%s price=%s",
            symbol, side, order_type, quantity, price or stop_price or "N/A",
        )

        result = self._request("POST", "/fapi/v1/order", params)

        logger.info(
            "Order placed ✓ → orderId=%s status=%s executedQty=%s avgPrice=%s",
            result.get("orderId"),
            result.get("status"),
            result.get("executedQty"),
            result.get("avgPrice"),
        )
        return result

    def cancel_order(self, symbol: str, order_id: int) -> dict:
        """Cancel an open order by orderId."""
        params = {"symbol": symbol, "orderId": order_id}
        logger.info("Cancelling order orderId=%s symbol=%s", order_id, symbol)
        return self._request("DELETE", "/fapi/v1/order", params)

    def get_order(self, symbol: str, order_id: int) -> dict:
        """Fetch order details by orderId."""
        params = {"symbol": symbol, "orderId": order_id}
        return self._request("GET", "/fapi/v1/order", params)

    def get_account_info(self) -> dict:
        """Return account balances and positions."""
        return self._request("GET", "/fapi/v2/account")
