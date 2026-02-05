import time
import datetime
import requests
import os

from dotenv import load_dotenv
from web3 import Web3


# ============================
# CONFIG
# ============================

BUY_USD = 1

MIN_BET_PRICE = 0.69
MAX_BET_PRICE = 0.91

# BTC move zones
ZONE1_START     = 900
ZONE1_END       = 240
ZONE1_BTC_MOVE  = 60

ZONE2_START     = 240
ZONE2_END       = 30
ZONE2_BTC_MOVE  = 40

ZONE3_BTC_MOVE  = 20


# ============================
# INIT
# ============================

load_dotenv()

RPC        = os.getenv("RPC")
CONTRACT   = Web3.to_checksum_address(os.getenv("MARKET"))
TRADER_KEY = os.getenv("TRADER_KEY")

w3 = Web3(Web3.HTTPProvider(RPC))
acct = w3.eth.account.from_key(TRADER_KEY)
FUNDER = acct.address

print("✅ Trader Wallet:", FUNDER)


MARKET_ABI = [
    {"name":"roundId","type":"function","inputs":[],"outputs":[{"type":"uint256"}],"stateMutability":"view"},
    {
        "name":"rounds",
        "type":"function",
        "inputs":[{"type":"uint256"}],
        "outputs":[
            {"type":"uint256"},
            {"type":"uint256"},
            {"type":"uint8"},
            {"type":"bool"}
        ],
        "stateMutability":"view"
    },
    {
        "name":"getBestYesOffer",
        "inputs":[],
        "outputs":[
            {"type":"address"},
            {"type":"uint256"},
            {"type":"uint256"}
        ],
        "stateMutability":"view",
        "type":"function",
    },
    {
        "name":"getBestNoOffer",
        "inputs":[],
        "outputs":[
            {"type":"address"},
            {"type":"uint256"},
            {"type":"uint256"}
        ],
        "stateMutability":"view",
        "type":"function",
    },
    {
        "name":"buyYes",
        "inputs":[
            {"type":"uint256"},
            {"type":"uint256"}
        ],
        "type":"function",
    },
    {
        "name":"buyNo",
        "inputs":[
            {"type":"uint256"},
            {"type":"uint256"}
        ],
        "type":"function",
    },
]

market = w3.eth.contract(address=CONTRACT, abi=MARKET_ABI)

print("\n✅ BTC15 Trader Started")


# ============================
# HELPERS
# ============================

def log(msg):
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


def onchain_yes_price():
    seller, price, shares = market.functions.getBestYesOffer().call()
    if shares == 0:
        return 0.0
    return price / 1_000_000


def onchain_no_price():
    seller, price, shares = market.functions.getBestNoOffer().call()
    if shares == 0:
        return 0.0
    return price / 1_000_000


def coinbase_live_price():
    url = "https://api.exchange.coinbase.com/products/BTC-USD/ticker"
    return float(requests.get(url).json()["price"])


def coinbase_open_price(start_ts):
    url = "https://api.exchange.coinbase.com/products/BTC-USD/candles"

    start_iso = datetime.datetime.fromtimestamp(
        start_ts, datetime.timezone.utc
    ).isoformat()

    end_iso = datetime.datetime.fromtimestamp(
        start_ts + 120, datetime.timezone.utc
    ).isoformat()

    candles = requests.get(
        url,
        params={
            "granularity": 60,
            "start": start_iso,
            "end": end_iso
        }
    ).json()

    best = None
    for c in candles:
        ts, low, high, open_p, close, vol = c
        if ts <= start_ts:
            if best is None or ts > best[0]:
                best = c

    return float(best[3]) if best else None


def required_btc_move(seconds_left):
    if ZONE1_END < seconds_left <= ZONE1_START:
        return ZONE1_BTC_MOVE
    if ZONE2_END < seconds_left <= ZONE2_START:
        return ZONE2_BTC_MOVE
    return ZONE3_BTC_MOVE


def send_tx(fn):
    tx = fn.build_transaction({
        "from": FUNDER,
        "nonce": w3.eth.get_transaction_count(FUNDER, "pending"),
        "gas": 300000,
        "gasPrice": int(w3.eth.gas_price * 2),
    })

    signed = acct.sign_transaction(tx)
    h = w3.eth.send_raw_transaction(signed.raw_transaction)

    log(f"✅ TX Sent: {h.hex()}")
    w3.eth.wait_for_transaction_receipt(h)
    time.sleep(2)


def buy_yes(price):
    usdc_amount = int(BUY_USD * 1_000_000)
    max_price   = int(price * 1_000_000)
    log(f"🚀 BUY YES @ {price:.2f}")
    send_tx(market.functions.buyYes(max_price, usdc_amount))


def buy_no(price):
    usdc_amount = int(BUY_USD * 1_000_000)
    max_price   = int(price * 1_000_000)
    log(f"🚀 BUY NO @ {price:.2f}")
    send_tx(market.functions.buyNo(max_price, usdc_amount))


# ============================
# MAIN LOOP
# ============================

def run_forever():

    last_round = None
    btc_open = None

    while True:
        try:
            round_id = market.functions.roundId().call()
            start, end, outcome, resolved = market.functions.rounds(round_id).call()

            now = int(time.time())

            # New round detected
            if round_id != last_round:
                log(f"\n🆕 New Round {round_id}")
                btc_open = coinbase_open_price(start)
                log(f"📌 Open BTC = {btc_open:.2f}")
                last_round = round_id
                traded = False

            # Round ended
            if now >= end:
                log("⏳ Round ended → waiting for next round")
                time.sleep(3)
                continue

            seconds_left = end - now

            yes_price = onchain_yes_price()
            no_price  = onchain_no_price()

            btc_now = coinbase_live_price()
            move = btc_now - btc_open

            required_move = required_btc_move(seconds_left)

            log(
                f"TimeLeft={seconds_left}s | YES={yes_price:.2f} NO={no_price:.2f} | "
                f"BTC Move=${move:.2f} (need {required_move})"
            )

            if not traded:

                if abs(move) < required_move:
                    time.sleep(2)
                    continue

                if MIN_BET_PRICE <= no_price <= MAX_BET_PRICE:
                    log("✅ Trigger NO Bet")
                    buy_no(no_price)
                    traded = True

                elif MIN_BET_PRICE <= yes_price <= MAX_BET_PRICE:
                    log("✅ Trigger YES Bet")
                    buy_yes(yes_price)
                    traded = True

            time.sleep(2)

        except Exception as e:
            log(f"⚠️ Trader error: {e}")
            time.sleep(3)


if __name__ == "__main__":
    run_forever()

