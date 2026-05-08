# Binance Futures Testnet Trading Bot

A clean, structured Python CLI application for placing orders on Binance Futures Testnet (USDT-M). Built as part of the PrimetradAI application task.

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py          # Package exports
│   ├── client.py            # Binance REST API client (signing, requests, errors)
│   ├── orders.py            # Order placement orchestration + formatted output
│   ├── validators.py        # Input validation (symbol, side, type, qty, price)
│   └── logging_config.py   # Structured logging setup (file + console)
├── cli.py                   # CLI entry point (argparse)
├── logs/                    # Auto-created; one timestamped .log file per run
│   ├── trading_bot_market_order_sample.log
│   └── trading_bot_limit_order_sample.log
├── README.md
└── requirements.txt
```

---

## Setup

### 1. Prerequisites

- Python 3.8 or higher
- A Binance Futures **Testnet** account: https://testnet.binancefuture.com

### 2. Generate Testnet API Credentials

1. Go to https://testnet.binancefuture.com
2. Log in (GitHub account required)
3. Navigate to **API Key** section
4. Click **Generate Key** – copy both the API Key and Secret immediately (secret shown once)

### 3. Install dependencies

```bash
# From the project root
pip install -r requirements.txt
```

### 4. Set your API credentials

The bot reads credentials from environment variables (recommended) **or** CLI flags.

**Linux / macOS:**
```bash
export BINANCE_API_KEY=your_testnet_api_key
export BINANCE_API_SECRET=your_testnet_api_secret
```

**Windows (PowerShell):**
```powershell
$env:BINANCE_API_KEY = "your_testnet_api_key"
$env:BINANCE_API_SECRET = "your_testnet_api_secret"
```

Alternatively pass them inline (not recommended for production):
```bash
python cli.py --api-key YOUR_KEY --api-secret YOUR_SECRET --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

---

## How to Run

### Syntax

```
python cli.py --symbol SYMBOL --side {BUY,SELL} --type {MARKET,LIMIT,STOP_MARKET} --quantity QTY [--price PRICE]
```

### Examples

**Market BUY:**
```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

**Limit SELL (price required):**
```bash
python cli.py --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.01 --price 2800
```

**Stop-Market SELL (bonus order type):**
```bash
python cli.py --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.001 --price 58000
```

**Verbose debug logging:**
```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001 --log-level DEBUG
```

---

## Sample Output

```
  ╔══════════════════════════════════════════════════════╗
  ║   Binance Futures Testnet Trading Bot  (USDT-M)      ║
  ╚══════════════════════════════════════════════════════╝

────────────────────────────────────────────────────────────
  ORDER REQUEST SUMMARY
────────────────────────────────────────────────────────────
  Symbol     : BTCUSDT
  Side       : BUY
  Type       : MARKET
  Quantity   : 0.001
────────────────────────────────────────────────────────────

────────────────────────────────────────────────────────────
  ORDER RESPONSE
────────────────────────────────────────────────────────────
  Order ID      : 4028584553
  Symbol        : BTCUSDT
  Side          : BUY
  Type          : MARKET
  Status        : FILLED
  Orig Qty      : 0.001
  Executed Qty  : 0.001
  Avg Price     : 57832.40
────────────────────────────────────────────────────────────

  [✓] Order placed successfully!  (orderId: 4028584553)
```

---

## Logging

Each run creates a new timestamped log file in the `logs/` directory, e.g.:

```
logs/trading_bot_20250710_142201.log
```

- **File handler**: captures DEBUG and above (full request/response detail)
- **Console handler**: INFO and above (clean human-readable output)

Sample log files for a market order and a limit order are included in `logs/`.

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| Missing/invalid CLI input | Argparse error + usage hint |
| Validation failure (bad symbol, qty ≤ 0, etc.) | Clear error message, non-zero exit |
| Binance API error (e.g. insufficient balance) | Prints error code + message, logs it |
| Network timeout / connection error | Logs and prints error, exits with code 1 |
| Missing credentials | Instructions to set env vars, exits |

---

## Supported Order Types

| Type | Description |
|---|---|
| `MARKET` | Executes immediately at best available price |
| `LIMIT` | Executes at specified price or better (`--price` required) |
| `STOP_MARKET` | *(Bonus)* Triggers a market order when `--price` (stop price) is hit |

---

## Assumptions

- All orders use the default `positionSide=BOTH` (one-way mode, the testnet default).
- `timeInForce` for LIMIT orders defaults to `GTC` (Good Till Cancelled).
- Quantity precision must match the symbol's step size; if the testnet rejects an order due to precision, adjust `--quantity` accordingly (e.g. use `0.001` not `0.0001` for BTCUSDT).
- The bot does **not** manage open positions or leverage settings; it is purely an order-placement tool.

---

## Dependencies

```
requests>=2.31.0
```

No third-party Binance SDK is used – all API calls are made via `requests` with HMAC-SHA256 signing, keeping the dependency footprint minimal.
