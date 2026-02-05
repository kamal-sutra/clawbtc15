#!/bin/bash

echo "Stopping old agents..."
pkill -f maker_agent.py
pkill -f trader_agent.py
pkill -f resolver_agent.py

sleep 2

echo "Starting Maker..."
python3 maker_agent.py &

sleep 2

echo "Starting Trader..."
python3 trader_agent.py &

sleep 2

echo "Starting Resolver..."
python3 resolver_agent.py &

wait

