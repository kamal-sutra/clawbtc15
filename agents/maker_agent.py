import time
import os
from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

RPC       = os.getenv("RPC")
MARKET    = Web3.to_checksum_address(os.getenv("MARKET"))
USDC      = Web3.to_checksum_address(os.getenv("USDC"))
MAKER_KEY = os.getenv("MAKER_KEY")

w3 = Web3(Web3.HTTPProvider(RPC))
acct = w3.eth.account.from_key(MAKER_KEY)
wallet = acct.address

print("✅ Maker Wallet:", wallet)

ABI = [
    {"name":"mintYes","type":"function","inputs":[{"type":"uint256"}]},
    {"name":"mintNo","type":"function","inputs":[{"type":"uint256"}]},
    {"name":"placeSellYes","type":"function","inputs":[{"type":"uint256"},{"type":"uint256"}]},
    {"name":"placeSellNo","type":"function","inputs":[{"type":"uint256"},{"type":"uint256"}]},
    {"name":"roundId","type":"function","inputs":[],"outputs":[{"type":"uint256"}],"stateMutability":"view"},
    {
        "name":"rounds",
        "type":"function",
        "inputs":[{"type":"uint256"}],
        "outputs":[
            {"type":"uint256"},  # startTime
            {"type":"uint256"},  # endTime
            {"type":"uint8"},    # outcome
            {"type":"bool"}      # resolved
        ],
        "stateMutability":"view"
    },
    {
        "name":"yesShares",
        "type":"function",
        "inputs":[{"type":"uint256"},{"type":"address"}],
        "outputs":[{"type":"uint256"}],
        "stateMutability":"view"
    },
    {
        "name":"noShares",
        "type":"function",
        "inputs":[{"type":"uint256"},{"type":"address"}],
        "outputs":[{"type":"uint256"}],
        "stateMutability":"view"
    },
]

market = w3.eth.contract(address=MARKET, abi=ABI)


# ============================
# CONFIG
# ============================

TARGET_INVENTORY = 1     # shares per side
MINT_USDC        = 1_000_000  # 1 USDC
PRICE            = 750000     # 0.75


# ============================
# TX HELPER
# ============================

def send(fn):
    nonce = w3.eth.get_transaction_count(wallet)

    tx = fn.build_transaction({
        "from": wallet,
        "nonce": nonce,
        "gas": 300000,
        "gasPrice": int(w3.eth.gas_price * 2),
    })

    signed = acct.sign_transaction(tx)
    h = w3.eth.send_raw_transaction(signed.raw_transaction)

    print("✅ TX Sent:", h.hex())

    receipt = w3.eth.wait_for_transaction_receipt(h)
    time.sleep(3)  # extra buffer


print("\n✅ Maker Agent Started")

last_round = None
liquidity_posted = False

while True:
    try:
        round_id = market.functions.roundId().call()

        # Detect new round
        if round_id != last_round:
            print(f"\n🆕 New Round: {round_id}")
            last_round = round_id
            liquidity_posted = False

        # Check round timing
        start, end, outcome, resolved = market.functions.rounds(round_id).call()
        now = int(time.time())

        if now >= end:
            print("⏳ Round ended → waiting for next round")
            time.sleep(5)
            continue

        yes = market.functions.yesShares(round_id, wallet).call()
        no  = market.functions.noShares(round_id, wallet).call()

        print(f"🧾 Round {round_id} | YES={yes} NO={no}")

        # ============================
        # INVENTORY MANAGEMENT
        # ============================

        if yes < TARGET_INVENTORY:
            print("🔧 Minting YES")
            send(market.functions.mintYes(MINT_USDC))

        if no < TARGET_INVENTORY:
            print("🔧 Minting NO")
            send(market.functions.mintNo(MINT_USDC))

        # ============================
        # POST LIQUIDITY
        # ============================

        if not liquidity_posted and yes >= TARGET_INVENTORY and no >= TARGET_INVENTORY:
            print("📤 Posting liquidity")
            send(market.functions.placeSellYes(PRICE, 1))
            send(market.functions.placeSellNo(PRICE, 1))
            liquidity_posted = True

    except Exception as e:
        print("⚠️ Maker error:", e)

    time.sleep(20)
