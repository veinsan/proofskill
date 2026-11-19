import { expect } from "chai";
import { network } from "hardhat";

const { ethers } = await network.create();

const ACTIVE = 1n;
const REVOKED = 2n;
const COMMITMENT = ethers.id("synthetic canonical payload + nonce");

async function deployWithIssuers() {
  const [admin, iss001, iss002, outsider] = await ethers.getSigners();
  const registry = await ethers.deployContract("ProofSkillRegistry");
  await registry.registerIssuer("ISS-001", iss001.address);
  await registry.registerIssuer("ISS-002", iss002.address);
  return { registry, admin, iss001, iss002, outsider };
}

describe("ProofSkillRegistry", () => {
  describe("registerIssuer (FR-01)", () => {
    it("lets only the platform admin register issuers", async () => {
      const { registry, outsider } = await deployWithIssuers();
      await expect(registry.connect(outsider).registerIssuer("ISS-003", outsider.address))
        .to.be.revertedWithCustomError(registry, "NotOwner");
    });

    it("rejects an issuer ID or account that is already registered", async () => {
      const { registry, iss001, outsider } = await deployWithIssuers();
      await expect(registry.registerIssuer("ISS-001", outsider.address))
        .to.be.revertedWithCustomError(registry, "IssuerAlreadyRegistered");
      await expect(registry.registerIssuer("ISS-003", iss001.address))
        .to.be.revertedWithCustomError(registry, "IssuerAlreadyRegistered");
    });

    it("exposes the account bound to an issuer ID", async () => {
      const { registry, iss001 } = await deployWithIssuers();
      expect(await registry.issuerAccountOf("ISS-001")).to.equal(iss001.address);
      expect(await registry.issuerAccountOf("ISS-404")).to.equal(ethers.ZeroAddress);
    });

    it("rejects an empty issuer ID", async () => {
      const { registry, outsider } = await deployWithIssuers();
      await expect(registry.registerIssuer("", outsider.address))
        .to.be.revertedWithCustomError(registry, "InvalidIssuer");
    });
  });

  describe("issueCredential (FR-04, TC-01)", () => {
    it("records commitment, issuer, active status, and time", async () => {
      const { registry, iss001 } = await deployWithIssuers();
      await expect(registry.connect(iss001).issueCredential("CRD-0001", COMMITMENT))
        .to.emit(registry, "CredentialIssued")
        .withArgs("CRD-0001", COMMITMENT, "ISS-001");

      const [commitment, issuerId, status, timestamp] = await registry.getRecord("CRD-0001");
      expect(commitment).to.equal(COMMITMENT);
      expect(issuerId).to.equal("ISS-001");
      expect(status).to.equal(ACTIVE);
      expect(timestamp > 0n).to.equal(true);
    });

    it("rejects an account that is not a registered issuer", async () => {
      const { registry, outsider } = await deployWithIssuers();
      await expect(registry.connect(outsider).issueCredential("CRD-0001", COMMITMENT))
        .to.be.revertedWithCustomError(registry, "IssuerNotRegistered");
    });

    it("rejects a credential ID that already exists", async () => {
      const { registry, iss001, iss002 } = await deployWithIssuers();
      await registry.connect(iss001).issueCredential("CRD-0001", COMMITMENT);
      await expect(registry.connect(iss002).issueCredential("CRD-0001", COMMITMENT))
        .to.be.revertedWithCustomError(registry, "CredentialExists");
    });
  });

  describe("revokeCredential (FR-07)", () => {
    it("sets the status to revoked when the original issuer revokes", async () => {
      const { registry, iss001 } = await deployWithIssuers();
      await registry.connect(iss001).issueCredential("CRD-0001", COMMITMENT);
      await expect(registry.connect(iss001).revokeCredential("CRD-0001"))
        .to.emit(registry, "CredentialRevoked")
        .withArgs("CRD-0001", "ISS-001");

      const [commitment, , status] = await registry.getRecord("CRD-0001");
      expect(status).to.equal(REVOKED);
      expect(commitment).to.equal(COMMITMENT);
    });

    it("TC-14: reverts when another issuer revokes, and the status stays active", async () => {
      const { registry, iss001, iss002 } = await deployWithIssuers();
      await registry.connect(iss001).issueCredential("CRD-0001", COMMITMENT);
      await expect(registry.connect(iss002).revokeCredential("CRD-0001"))
        .to.be.revertedWithCustomError(registry, "NotOriginalIssuer");

      const [, , status] = await registry.getRecord("CRD-0001");
      expect(status).to.equal(ACTIVE);
    });

    it("rejects a second revocation", async () => {
      const { registry, iss001 } = await deployWithIssuers();
      await registry.connect(iss001).issueCredential("CRD-0001", COMMITMENT);
      await registry.connect(iss001).revokeCredential("CRD-0001");
      await expect(registry.connect(iss001).revokeCredential("CRD-0001"))
        .to.be.revertedWithCustomError(registry, "AlreadyRevoked");
    });

    it("rejects an unknown credential", async () => {
      const { registry, iss001 } = await deployWithIssuers();
      await expect(registry.connect(iss001).revokeCredential("CRD-9999"))
        .to.be.revertedWithCustomError(registry, "CredentialNotFound");
    });
  });

  describe("deactivateIssuer (OD-2)", () => {
    it("TC-16: keeps the record but reports the issuer as no longer authorized", async () => {
      const { registry, iss001 } = await deployWithIssuers();
      await registry.connect(iss001).issueCredential("CRD-0001", COMMITMENT);
      expect((await registry.getRecord("CRD-0001"))[4]).to.equal(true);

      await expect(registry.deactivateIssuer("ISS-001"))
        .to.emit(registry, "IssuerDeactivated")
        .withArgs("ISS-001", iss001.address);

      const [commitment, issuerId, status, , issuerActive] = await registry.getRecord("CRD-0001");
      expect(commitment).to.equal(COMMITMENT);
      expect(issuerId).to.equal("ISS-001");
      expect(status).to.equal(ACTIVE);
      expect(issuerActive).to.equal(false);
    });

    it("stops a deactivated issuer from issuing", async () => {
      const { registry, iss001 } = await deployWithIssuers();
      await registry.deactivateIssuer("ISS-001");
      await expect(registry.connect(iss001).issueCredential("CRD-0001", COMMITMENT))
        .to.be.revertedWithCustomError(registry, "IssuerNotActive");
    });

    it("lets only the platform admin deactivate a registered issuer", async () => {
      const { registry, outsider } = await deployWithIssuers();
      await expect(registry.connect(outsider).deactivateIssuer("ISS-001"))
        .to.be.revertedWithCustomError(registry, "NotOwner");
      await expect(registry.deactivateIssuer("ISS-404"))
        .to.be.revertedWithCustomError(registry, "IssuerNotRegistered");
    });
  });

  describe("getRecord (FR-06)", () => {
    it("rejects an unknown credential", async () => {
      const { registry } = await deployWithIssuers();
      await expect(registry.getRecord("CRD-9999"))
        .to.be.revertedWithCustomError(registry, "CredentialNotFound");
    });
  });
});
