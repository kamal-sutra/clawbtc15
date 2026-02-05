// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/BTC15AutoMarket.sol";

contract BTC15AutoDeploy is Script {
    function run() external {
        vm.startBroadcast();

        // Base Sepolia USDC
        address usdc = 0x036CbD53842c5426634e7929541eC2318f3dCF7e;

        new BTC15AutoMarket(usdc);

        vm.stopBroadcast();
    }
}

