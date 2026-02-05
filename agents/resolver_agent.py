import time
import datetime
import os
import requests
from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

RPC          = os.getenv("RPC")
MARKET       = Web3.to_checksum_address(os.getenv("MARKET"))
RESOLVER_KEY = os.getenv("RESOLVER_KEY")   # can reuse maker key

RESOLUTION_DELAY = 15  # seconds after round end before resolving

w3 = Web3(Web3.HTTPProvider(RPC))
acct = w3.eth.account.from_key(RESOLVER_KEY)
wallet = acct.address

print("✅ Resolver Wallet:", wallet)

ABI = [
    {
        "name": "roundId",
        "type": "function",
        "inputs": [],
        "outputs": [{"type": "uint256"}],
        "stateMutability": "view",
    },
    {
        "name": "rounds",
        "type": "function",
        "inputs": [{"type": "uint256"}],
        "outputs": [
            {"type": "uint256"},  # start
            {"type": "uint256"},  # end
            {"type": "uint8"},    # outcome
            {"type": "bool"},     # resolved
        ],
        "stateMutability": "view",
    },
    {
        "name": "resolveCurrentRound",
        "type": "function",
        "inputs": [{"type": "bool"}],
    },
    {
        "name": "redeem",
        "type": "function",
        "inputs": [{"type": "uint256"}],
    },
]

market = w3.eth.contract(address=MARKET, abi=ABI)


# ============================
# TX HELPER WITH NONCE CONTROL
# ============================

def send(fn, nonce):
    tx = fn.build_transaction({
        "from": wallet,
        "nonce": nonce,
        "gas": 300000,
        "gasPrice": int(w3.eth.gas_price * 2),
    })

    signed = acct.sign_transaction(tx)
    h = w3.eth.send_raw_transaction(signed.raw_transaction)

    print("✅ TX Sent:", h.hex())
    w3.eth.wait_for_transaction_receipt(h)
    return nonce + 1


# ============================
# BTC PRICE HELPERS
# ============================

def coinbase_price_at(ts):
    url = "https://api.exchange.coinbase.com/products/BTC-USD/candles"

    start_iso = datetime.datetime.fromtimestamp(
        ts, datetime.timezone.utc
    ).isoformat()

    end_iso = datetime.datetime.fromtimestamp(
        ts + 60, datetime.timezone.utc
    ).isoformat()

    try:
        candles = requests.get(
            url,
            params={
                "granularity": 60,
                "start": start_iso,
                "end": end_iso
            },
            timeout=10
        ).json()
    except Exception:
        return None

    if not candles:
        return None

    return float(candles[0][3])  # open price


# ============================
# MAIN LOOP
# ============================

print("\n✅ Resolver Agent Started")

while True:
    try:
        rid = market.functions.roundId().call()
        start, end, outcome, resolved = market.functions.rounds(rid).call()

        now = int(time.time())

        # Resolve automatically if round ended and not resolved
        if not resolved and now >= end + RESOLUTION_DELAY:
            print(f"\n🧠 Resolving round {rid}")

            open_price  = coinbase_price_at(start)
            close_price = coinbase_price_at(end)

            if open_price is None or close_price is None:
                print("⚠️ Price fetch failed, retrying...")
                time.sleep(10)
                continue

            print("Open:", open_price, "Close:", close_price)

            btc_up = close_price > open_price

            nonce = w3.eth.get_transaction_count(wallet, "pending")
            nonce = send(market.functions.resolveCurrentRound(btc_up), nonce)

            print("🏆 Outcome:", "YES" if btc_up else "NO")

            # Attempt redeem automatically
            try:
                print("💰 Redeeming round", rid)
                nonce = send(market.functions.redeem(rid), nonce)
            except Exception as e:
                print("ℹ️ Nothing to redeem:", e)

    except Exception as e:
        print("⚠️ Resolver error:", e)

    time.sleep(5)

