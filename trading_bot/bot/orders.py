"""
Order placement orchestration layer.

Sits between the CLI and the raw Binance client:
- Calls validators before touching the network
- Formats and prints the request summary and response
- Returns a structured result dict for programmatic use
"""

from __future__ import annotations

import json
from typing import Any

from .client import BinanceFuturesClient, BinanceAPIError
from .validators import validate_all
from .logging_config import get_logger

logger = get_logger("orders")


# ---------------------------------------------------------------------------
# Pretty-print helpers
# ---------------------------------------------------------------------------

def _separator(char: str = "─", width: int = 60) -> str:
    return char * width


def _print_request_summary(params: dict) -> None:
    print()
    print(_separator())
    print("  ORDER REQUEST SUMMARY")
    print(_separator())
    print(f"  Symbol     : {params['symbol']}")
    print(f"  Side       : {params['side']}")
    print(f"  Type       : {params['order_type']}")
    print(f"  Quantity   : {params['quantity']}")
    if params.get("price") is not None:
        print(f"  Price      : {params['price']}")
    print(_separator())
    print()


def _print_order_response(response: dict) -> None:
    print(_separator())
    print("  ORDER RESPONSE")
    print(_separator())
    fields = [
        ("Order ID",       "orderId"),
        ("Client OID",     "clientOrderId"),
        ("Symbol",         "symbol"),
        ("Side",           "side"),
        ("Type",           "type"),
        ("Status",         "status"),
        ("Orig Qty",       "origQty"),
        ("Executed Qty",   "executedQty"),
        ("Avg Price",      "avgPrice"),
        ("Price",          "price"),
        ("Time in Force",  "timeInForce"),
        ("Update Time",    "updateTime"),
    ]
    for label, key in fields:
        val = response.get(key)
        if val not in (None, "", "0", "0.00000000", 0):
            print(f"  {label:<14}: {val}")
    print(_separator())
    print()


# ---------------------------------------------------------------------------
# Public order functions
# ---------------------------------------------------------------------------

def place_order(
    client: BinanceFuturesClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: float | str,
    price: float | str | None = None,
) -> dict[str, Any]:
    """
    Validate inputs, place an order, and return a result dict.

    Returns
    -------
    {
        "success": bool,
        "params":  dict,   # validated input parameters
        "response": dict,  # raw Binance response (or None on failure)
        "error":   str,    # error message (or None on success)
    }
    """
    result: dict[str, Any] = {
        "success": False,
        "params": {},
        "response": None,
        "error": None,
    }

    # --- Validate ---
    try:
        validated = validate_all(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
        )
    except ValueError as exc:
        result["error"] = str(exc)
        logger.warning("Validation failed: %s", exc)
        print(f"\n  [✗] Validation error: {exc}\n")
        return result

    result["params"] = validated
    _print_request_summary(validated)

    # --- Place order ---
    try:
        response = client.place_order(
            symbol=validated["symbol"],
            side=validated["side"],
            order_type=validated["order_type"],
            quantity=validated["quantity"],
            price=validated["price"],
        )
        result["success"] = True
        result["response"] = response
        _print_order_response(response)
        print(f"  [✓] Order placed successfully!  (orderId: {response.get('orderId')})\n")

    except BinanceAPIError as exc:
        result["error"] = str(exc)
        logger.error("BinanceAPIError during order placement: %s", exc)
        print(f"\n  [✗] Binance API error {exc.code}: {exc.message}\n")

    except Exception as exc:
        result["error"] = str(exc)
        logger.exception("Unexpected error during order placement")
        print(f"\n  [✗] Unexpected error: {exc}\n")

    return result
