// Deploys ProofSkillRegistry to the local Hardhat node and records its address for the API (RGS).
// The deployer (Hardhat test account #0) becomes the platform admin that registers issuers.
import { mkdir, writeFile } from "node:fs/promises";
import { network } from "hardhat";

const { ethers, networkName } = await network.create();

const registry = await ethers.deployContract("ProofSkillRegistry");
await registry.waitForDeployment();

const deployment = {
  network: networkName,
  chainId: Number((await ethers.provider.getNetwork()).chainId),
  address: await registry.getAddress(),
  owner: await registry.owner(),
};

await mkdir("deployments", { recursive: true });
await writeFile(`deployments/${networkName}.json`, `${JSON.stringify(deployment, null, 2)}\n`);
console.log(`ProofSkillRegistry deployed to ${deployment.address} on ${networkName}`);
