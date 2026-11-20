// Deploys ProofSkillRegistry and records its address for the API (RGS): to the local Hardhat node
// (`pnpm deploy:local`) or to the Base Sepolia testnet (`pnpm deploy:base-sepolia`, B-03). The deployer
// (Hardhat test account #0 locally, REGISTRY_OWNER_KEY on the testnet) becomes the platform admin.
import { mkdir, writeFile } from "node:fs/promises";
import { dirname } from "node:path";
import { network } from "hardhat";

const { ethers, networkName } = await network.create();

const registry = await ethers.deployContract("ProofSkillRegistry");
await registry.waitForDeployment();

const deployment = {
  network: networkName,
  chainId: Number((await ethers.provider.getNetwork()).chainId),
  address: await registry.getAddress(),
  owner: await registry.owner(),
  abi: JSON.parse(registry.interface.formatJson()),
  // Selectors let the API's minimal JSON-RPC client encode calls and name reverts without keccak.
  functions: {} as Record<string, string>,
  errors: {} as Record<string, string>,
};
registry.interface.forEachFunction((fn) => (deployment.functions[fn.format("sighash")] = fn.selector));
registry.interface.forEachError((error) => (deployment.errors[error.selector] = error.name));

// DEPLOYMENT_OUT lets the API tests deploy a fresh registry without touching the dev deployment.
const out = process.env.DEPLOYMENT_OUT ?? `deployments/${networkName}.json`;
await mkdir(dirname(out), { recursive: true });
await writeFile(out, `${JSON.stringify(deployment, null, 2)}\n`);
console.log(`ProofSkillRegistry deployed to ${deployment.address} on ${networkName} (${out})`);
