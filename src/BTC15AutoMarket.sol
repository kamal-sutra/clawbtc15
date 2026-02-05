// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IERC20 {
    function transferFrom(address from, address to, uint amount) external returns (bool);
    function transfer(address to, uint amount) external returns (bool);
}

contract BTC15AutoMarket {

    IERC20 public immutable usdc;
    uint public constant SCALE = 1e6;

    enum Outcome { UNRESOLVED, YES, NO }

    struct Round {
        uint startTime;
        uint endTime;
        Outcome outcome;
        bool resolved;
    }

    uint public roundId;
    mapping(uint => Round) public rounds;

    mapping(uint => mapping(address => uint)) public yesShares;
    mapping(uint => mapping(address => uint)) public noShares;

    struct Offer {
        address seller;
        uint price;
        uint shares;
    }

    mapping(uint => Offer) public bestYesOffer;
    mapping(uint => Offer) public bestNoOffer;

    event NewRound(uint roundId, uint start, uint end);
    event Resolved(uint roundId, Outcome outcome);

    constructor(address _usdc) {
        usdc = IERC20(_usdc);
        _startNewRound();
    }

    // ============================
    // ROUND LOGIC (Polymarket-style)
    // ============================

    function _startNewRound() internal {
        roundId++;

        uint start;

        if (roundId == 1) {
            // Align first round to real 15-min boundary
            start = (block.timestamp / 900) * 900;
        } else {
            // Continue from previous round
            start = rounds[roundId - 1].endTime;
        }

        uint end = start + 900;

        rounds[roundId] = Round({
            startTime: start,
            endTime: end,
            outcome: Outcome.UNRESOLVED,
            resolved: false
        });

        emit NewRound(roundId, start, end);
    }

    function _ensureActiveRound() internal view {
        Round memory r = rounds[roundId];
        require(block.timestamp < r.endTime, "Round ended");
    }

    // ============================
    // MINTING
    // ============================

    function mintYes(uint usdcAmount) external {
        _ensureActiveRound();

        require(
            usdc.transferFrom(msg.sender, address(this), usdcAmount),
            "USDC transfer failed"
        );

        uint shares = usdcAmount / SCALE;
        yesShares[roundId][msg.sender] += shares;
    }

    function mintNo(uint usdcAmount) external {
        _ensureActiveRound();

        require(
            usdc.transferFrom(msg.sender, address(this), usdcAmount),
            "USDC transfer failed"
        );

        uint shares = usdcAmount / SCALE;
        noShares[roundId][msg.sender] += shares;
    }

    // ============================
    // ORDERBOOK
    // ============================

    function placeSellYes(uint price, uint shares) external {
        _ensureActiveRound();

        require(yesShares[roundId][msg.sender] >= shares, "Not enough YES");

        Offer storage o = bestYesOffer[roundId];

        if (o.seller == address(0) || price < o.price) {
            bestYesOffer[roundId] = Offer(msg.sender, price, shares);
        }
    }

    function placeSellNo(uint price, uint shares) external {
        _ensureActiveRound();

        require(noShares[roundId][msg.sender] >= shares, "Not enough NO");

        Offer storage o = bestNoOffer[roundId];

        if (o.seller == address(0) || price < o.price) {
            bestNoOffer[roundId] = Offer(msg.sender, price, shares);
        }
    }

    // ============================
    // TRADING
    // ============================

    function buyYes(uint maxPrice, uint usdcAmount) external {
        _ensureActiveRound();

        Offer storage offer = bestYesOffer[roundId];

        require(offer.seller != address(0), "No YES offers");
        require(offer.price <= maxPrice, "Price too high");

        uint sharesToBuy = usdcAmount / offer.price;
        require(sharesToBuy > 0, "Too small");
        require(sharesToBuy <= offer.shares, "Not enough liquidity");

        uint cost = sharesToBuy * offer.price;

        require(usdc.transferFrom(msg.sender, offer.seller, cost), "USDC failed");

        yesShares[roundId][offer.seller] -= sharesToBuy;
        yesShares[roundId][msg.sender] += sharesToBuy;

        offer.shares -= sharesToBuy;
    }

    function buyNo(uint maxPrice, uint usdcAmount) external {
        _ensureActiveRound();

        Offer storage offer = bestNoOffer[roundId];

        require(offer.seller != address(0), "No NO offers");
        require(offer.price <= maxPrice, "Price too high");

        uint sharesToBuy = usdcAmount / offer.price;
        require(sharesToBuy > 0, "Too small");
        require(sharesToBuy <= offer.shares, "Not enough liquidity");

        uint cost = sharesToBuy * offer.price;

        require(usdc.transferFrom(msg.sender, offer.seller, cost), "USDC failed");

        noShares[roundId][offer.seller] -= sharesToBuy;
        noShares[roundId][msg.sender] += sharesToBuy;

        offer.shares -= sharesToBuy;
    }

    // ============================
    // RESOLUTION
    // ============================

    function resolveCurrentRound(bool btcUp) external {
        Round storage r = rounds[roundId];

        require(block.timestamp >= r.endTime, "Round not ended");
        require(!r.resolved, "Already resolved");

        r.outcome = btcUp ? Outcome.YES : Outcome.NO;
        r.resolved = true;

        emit Resolved(roundId, r.outcome);

        _startNewRound();
    }

    function redeem(uint _roundId) external {
        Round storage r = rounds[_roundId];
        require(r.resolved, "Not resolved");

        uint payoutShares;

        if (r.outcome == Outcome.YES) {
            payoutShares = yesShares[_roundId][msg.sender];
            yesShares[_roundId][msg.sender] = 0;
        } else {
            payoutShares = noShares[_roundId][msg.sender];
            noShares[_roundId][msg.sender] = 0;
        }

        require(payoutShares > 0, "No winning shares");

        uint payout = payoutShares * SCALE;
        require(usdc.transfer(msg.sender, payout), "USDC payout failed");
    }

    // ============================
    // VIEW HELPERS
    // ============================

    function getBestYesOffer()
        external
        view
        returns (address seller, uint price, uint shares)
    {
        Offer memory o = bestYesOffer[roundId];
        return (o.seller, o.price, o.shares);
    }

    function getBestNoOffer()
        external
        view
        returns (address seller, uint price, uint shares)
    {
        Offer memory o = bestNoOffer[roundId];
        return (o.seller, o.price, o.shares);
    }
}

