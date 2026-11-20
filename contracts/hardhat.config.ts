import { existsSync } from "node:fs";
import { configVariable, defineConfig } from "hardhat/config";
import hardhatEthers from "@nomicfoundation/hardhat-ethers";
import hardhatEthersChaiMatchers from "@nomicfoundation/hardhat-ethers-chai-matchers";
import hardhatMocha from "@nomicfoundation/hardhat-mocha";
import hardhatVerify from "@nomicfoundation/hardhat-verify";

// B-03: testnet settings (RPC URL, deployer key, Etherscan key) live only in the untracked
// ../.env.testnet; configVariable reads them when the baseSepolia network or verify runs.
const testnetEnv = new URL("../.env.testnet", import.meta.url);
if (existsSync(testnetEnv)) process.loadEnvFile(testnetEnv);

export default defineConfig({
  plugins: [hardhatEthers, hardhatEthersChaiMatchers, hardhatMocha, hardhatVerify],
  solidity: { version: "0.8.28" },
  networks: {
    // `pnpm chain` serves this node; only public Hardhat test accounts.
    localhost: { type: "http", url: "http://127.0.0.1:8545" },
    // Public testnet only (chainId 84532); never a mainnet (CLAUDE.md). The deployer becomes the
    // registry owner, the platform admin that registers issuers.
    baseSepolia: {
      type: "http",
      chainType: "op",
      chainId: 84532,
      url: configVariable("CHAIN_RPC_URL"),
      accounts: [configVariable("REGISTRY_OWNER_KEY")],
    },
  },
  verify: { etherscan: { apiKey: configVariable("ETHERSCAN_API_KEY") } },
});
