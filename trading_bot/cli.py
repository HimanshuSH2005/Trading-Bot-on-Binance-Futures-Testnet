#!/usr/bin/env python3
"""
cli.py – Command-line entry point for the Binance Futures Testnet trading bot.

Usage examples
--------------
# Market BUY
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

# Limit SELL
python cli.py --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.01 --price 2800

# Stop-Market SELL (bonus order type)
python cli.py --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.001 --price 58000

# Pass API credentials via CLI flags (override env vars)
python cli.py --api-key XXXX --api-secret YYYY --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
"""

from __future__ import annotations

import argparse
import os
import sys

from bot.logging_config import setup_logging
from bot.client import BinanceFuturesClient
from bot.orders import place_order


BANNER = r"""
  ╔══════════════════════════════════════════════════════╗
  ║   Binance Futures Testnet Trading Bot  (USDT-M)      ║
  ╚══════════════════════════════════════════════════════╝
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Place orders on Binance Futures Testnet (USDT-M).",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "Environment variables (fallback for credentials):\n"
            "  BINANCE_API_KEY      – Testnet API key\n"
            "  BINANCE_API_SECRET   – Testnet API secret\n\n"
            "Examples:\n"
            "  python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001\n"
            "  python cli.py --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.01 --price 2800\n"
            "  python cli.py --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.001 --price 58000\n"
        ),
    )

    # --- Credentials ---
    cred = parser.add_argument_group("credentials (env vars preferred)")
    cred.add_argument("--api-key",    default=None, help="Binance Testnet API key (overrides BINANCE_API_KEY env var)")
    cred.add_argument("--api-secret", default=None, help="Binance Testnet API secret (overrides BINANCE_API_SECRET env var)")

    # --- Order parameters ---
    order = parser.add_argument_group("order parameters")
    order.add_argument("--symbol",   required=True, help="Trading pair symbol, e.g. BTCUSDT")
    order.add_argument("--side",     required=True, choices=["BUY", "SELL"], help="Order side")
    order.add_argument(
        "--type", dest="order_type", required=True,
        choices=["MARKET", "LIMIT", "STOP_MARKET"],
        help="Order type",
    )
    order.add_argument("--quantity", required=True, type=float, help="Order quantity in base asset")
    order.add_argument("--price",    type=float, default=None,
                       help="Limit price (required for LIMIT / STOP_MARKET orders)")

    # --- Misc ---
    parser.add_argument("--log-level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        help="Console + file log level (default: INFO)")

    return parser


def resolve_credentials(args: argparse.Namespace) -> tuple[str, str]:
    """
    Resolve API credentials from CLI flags first, then environment variables.
    Exits with an informative message if neither is found.
    """
    api_key = args.api_key or os.getenv("BINANCE_API_KEY", "")
    api_secret = args.api_secret or os.getenv("BINANCE_API_SECRET", "")

    if not api_key or not api_secret:
        print(
            "\n  [✗] API credentials not found.\n"
            "  Set them via environment variables:\n"
            "      export BINANCE_API_KEY=your_key\n"
            "      export BINANCE_API_SECRET=your_secret\n"
            "  or pass --api-key / --api-secret flags.\n"
        )
        sys.exit(1)

    return api_key, api_secret


def main() -> None:
    print(BANNER)

    parser = build_parser()
    args = parser.parse_args()

    # Logging (file + console)
    logger = setup_logging(log_level=args.log_level)

    # Credentials
    api_key, api_secret = resolve_credentials(args)

    # Client
    client = BinanceFuturesClient(api_key=api_key, api_secret=api_secret)

    # Connectivity check
    try:
        server_time = client.get_server_time()
        logger.debug("Binance server time: %s ms", server_time)
    except Exception as exc:
        logger.error("Could not connect to Binance Testnet: %s", exc)
        print(f"\n  [✗] Cannot reach Binance Testnet: {exc}\n")
        sys.exit(1)

    # Place order
    result = place_order(
        client=client,
        symbol=args.symbol,
        side=args.side,
        order_type=args.order_type,
        quantity=args.quantity,
        price=args.price,
    )

    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
