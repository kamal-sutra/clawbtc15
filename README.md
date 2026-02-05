# Autonomous BTC Prediction Market (Maker–Trader–Resolver Agents)

This project demonstrates a fully autonomous prediction market powered by three cooperating agents that provide liquidity, trade, resolve outcomes, and settle value using onchain USDC.

The system runs continuously without human intervention.

---

## System Overview

Each round follows a fully autonomous lifecycle:

1. A Maker agent provides liquidity.
2. A Trader agent observes BTC price movement and takes a directional position.
3. A Resolver agent settles the outcome using external price data.
4. The winning side is automatically redeemed.
5. USDC flows back into the system for the next round.

This creates a continuous, agent-native economic loop.

---

## Agents

### Maker Agent
Responsibilities:

- Mints YES and NO shares.
- Provides sell-side liquidity.
- Maintains balanced inventory.
- Reposts liquidity when inventory is consumed.

Goal:

Maintain a functional prediction market for other agents.

---

### Trader Agent
Responsibilities:

- Monitors BTC price movement.
- Evaluates time remaining in the round.
- Buys YES or NO when thresholds are met.

Strategy:

- Larger BTC moves trigger trades.
- Required move thresholds depend on time remaining.

Goal:

Take directional positions based on real-time price action.

---

### Resolver Agent
Responsibilities:

- Detects round end.
- Fetches BTC open and close prices.
- Resolves the market outcome.
- Automatically redeems winnings.

Goal:

Ensure correct settlement and value distribution.

---

## Economic Loop

The system forms a continuous agent economy:

Maker → provides liquidity  
Trader → takes positions  
Resolver → settles outcome  
Trader/Maker → receive USDC  
Cycle repeats  

All value is settled in USDC.

---

## Smart Contract

Core contract:

src/BTC15AutoMarket.sol

Features:

- 15-minute BTC direction rounds
- YES / NO share minting
- Onchain orderbook
- Autonomous resolution
- USDC settlement

---

## Project Structure

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

---

## Setup

### 1) Install dependencies

Python:

pip install web3 python-dotenv requests

Optional (for contract deployment):

curl -L https://foundry.paradigm.xyz | bash  
foundryup

---

### 2) Configure environment

Copy the example file:

cp .env.example .env

Fill in:

RPC=<RPC URL>  
MARKET=<DEPLOYED MARKET ADDRESS>  
USDC=<USDC TOKEN ADDRESS>  

MAKER_KEY=<PRIVATE KEY>  
TRADER_KEY=<PRIVATE KEY>  
RESOLVER_KEY=<PRIVATE KEY>  

---

### 3) Run all agents

cd agents  
./run_all.sh

Agents will:

- Detect new rounds
- Provide liquidity
- Trade autonomously
- Resolve outcomes
- Redeem winnings

No manual interaction required.

---

## Example Lifecycle

1. New round starts.
2. Maker posts YES/NO liquidity.
3. Trader detects BTC move.
4. Trader buys YES or NO.
5. Round ends.
6. Resolver resolves outcome.
7. Winnings are redeemed automatically.

---

## Key Properties

### Fully Autonomous
No human steps required.

### Real Economic Behavior
Agents:

- Provide liquidity
- Trade based on signals
- Settle value onchain

### Stable Settlement Layer
All value flows use USDC.

---

## Hackathon Tracks

Primary: Agentic Commerce  
Secondary: Most Novel Smart Contract  

---

## Summary

This project demonstrates a complete autonomous economic system:

- Agents provide liquidity
- Agents trade
- Agents resolve outcomes
- Agents settle value
- System repeats indefinitely

All without human control.
