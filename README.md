# AI BTC Prediction Market (Maker–Trader–Resolver Agents)

This project demonstrates a fully autonomous prediction market powered by three cooperating agents that provide liquidity, trade, resolve outcomes, and settle value using onchain USDC.

The system runs continuously without human intervention and includes an **LLM-driven trading agent** that adapts to real-time market conditions.

---

## System Overview

Each round follows a fully autonomous lifecycle:

1. A Maker agent provides liquidity.
2. A Trader agent monitors BTC price movement and uses an **LLM-based decision engine**.
3. A Resolver agent settles the outcome using external price data.
4. The winning side is automatically redeemed.
5. USDC flows back into the system for the next round.

This creates a continuous, agent-native economic loop.

---

## Agents

### Maker Agent

Responsibilities:

* Mints YES and NO shares.
* Provides sell-side liquidity.
* Maintains balanced inventory.
* Reposts liquidity when inventory is consumed.

Goal:

Maintain a functional prediction market for other agents.

---

### Trader Agent (AI + LLM Powered)

Responsibilities:

* Monitors BTC price in real time.
* Tracks short-term volatility.
* Evaluates time remaining in the round.
* Sends market state to a large language model (LLM).
* Executes YES, NO, or HOLD decisions on-chain.

Strategy:

1. Record BTC opening price at round start.
2. Track live BTC price every few seconds.
3. Calculate short-term volatility.
4. Determine if price movement is significant.
5. Send market data to the LLM.
6. Execute the LLM’s decision on-chain.

Example LLM input:

```
BTC open: 64210
BTC now: 64262
Move: +52
Volatility: 18
Time left: 280s
YES price: 0.74
NO price: 0.26
```

LLM output:

```
YES
```

Goal:

Take adaptive, AI-driven directional positions using real-time data and LLM reasoning.

---

### Resolver Agent

Responsibilities:

* Detects round end.
* Fetches BTC open and close prices.
* Resolves the market outcome.
* Automatically redeems winnings.

Goal:

Ensure correct settlement and value distribution.

---

## Economic Loop

The system forms a continuous agent economy:

Maker → provides liquidity
Trader → takes LLM-driven positions
Resolver → settles outcome
Trader/Maker → receive USDC
Cycle repeats

All value is settled in USDC.

---

## Smart Contract

Core contract:

```
src/BTC15AutoMarket.sol
```

Features:

* 15-minute BTC direction rounds
* YES / NO share minting
* Onchain orderbook
* Autonomous resolution
* USDC settlement

---

## Project Structure

```
agents/
    maker_agent.py
    trader_agent.py
    resolver_agent.py
    run_all.sh

src/
    BTC15AutoMarket.sol

script/
    BTC15Deploy.s.sol

.env.example  
README.md  
foundry.toml  
```

---

## Setup

### 1) Install dependencies

Python:

```
pip install web3 python-dotenv requests
```

Optional (for contract deployment):

```
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

---

### 2) Configure environment

Copy the example file:

```
cp .env.example .env
```

Fill in:

```
RPC=<RPC URL>
MARKET=<DEPLOYED MARKET ADDRESS>
USDC=<USDC TOKEN ADDRESS>

MAKER_KEY=<PRIVATE KEY>
TRADER_KEY=<PRIVATE KEY>
RESOLVER_KEY=<PRIVATE KEY>

GROQ_API_KEY=<LLM API KEY>
```

⚠️ **Security Notice**

* Use **testnet or disposable wallets only**.
* Never use production private keys.
* The agents execute transactions automatically.

---

### 3) Run all agents

```
cd agents
./run_all.sh
```

Agents will:

* Detect new rounds
* Provide liquidity
* Trade using LLM decisions
* Resolve outcomes
* Redeem winnings

No manual interaction required.

---

## Example Lifecycle

1. New round starts.
2. Maker posts YES/NO liquidity.
3. Trader detects BTC move.
4. LLM decides YES, NO, or HOLD.
5. Trader executes the decision.
6. Round ends.
7. Resolver resolves outcome.
8. Winnings are redeemed automatically.

---

## Key Properties

### Fully Autonomous

No human steps required.

### LLM-Driven Decision Making

Trader uses real-time volatility signals and an LLM to determine positions.

### Real Economic Behavior

Agents:

* Provide liquidity
* Trade using LLM reasoning
* Settle value onchain

### Stable Settlement Layer

All value flows use USDC.

---

