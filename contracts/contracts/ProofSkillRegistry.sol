// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

/// @title ProofSkillRegistry
/// @notice Local credential registry for ProofSkill (FR-01, FR-04, FR-06, FR-07).
/// It stores only the RegistryRecord fields of report Tabel 8.5 (commitment, issuerId,
/// status, timestamp) plus whether the issuer is still authorized (OD-2), never personal
/// data (NFR-02). Status changes are new transactions with events, so history is never
/// overwritten.
contract ProofSkillRegistry {
    enum Status {
        None,
        Active,
        Revoked
    }

    struct Record {
        bytes32 commitment;
        address issuer;
        Status status;
        uint64 timestamp; // time of the latest status change
    }

    /// @notice Platform admin account, the only one allowed to register issuers (API-01).
    address public immutable owner;

    mapping(address => string) private issuerIdOf;
    /// @notice Chain account bound to an issuer ID, or the zero address if it is not registered.
    mapping(string => address) public issuerAccountOf;
    mapping(address => bool) private deactivated;
    mapping(string => Record) private records;

    event IssuerRegistered(string issuerId, address indexed account);
    event IssuerDeactivated(string issuerId, address indexed account);
    event CredentialIssued(string credentialId, bytes32 commitment, string issuerId);
    event CredentialRevoked(string credentialId, string issuerId);

    error NotOwner();
    error InvalidIssuer();
    error IssuerAlreadyRegistered();
    error IssuerNotRegistered();
    error IssuerNotActive();
    error CredentialExists();
    error CredentialNotFound();
    error NotOriginalIssuer();
    error AlreadyRevoked();

    constructor() {
        owner = msg.sender;
    }

    /// @notice Binds an issuer ID such as ISS-001 to the chain account that signs for it.
    function registerIssuer(string calldata issuerId, address account) external {
        if (msg.sender != owner) revert NotOwner();
        if (bytes(issuerId).length == 0 || account == address(0)) revert InvalidIssuer();
        if (bytes(issuerIdOf[account]).length != 0 || issuerAccountOf[issuerId] != address(0)) {
            revert IssuerAlreadyRegistered();
        }
        issuerIdOf[account] = issuerId;
        issuerAccountOf[issuerId] = account;
        emit IssuerRegistered(issuerId, account);
    }

    /// @notice Withdraws an issuer's authorization. Its credentials then verify as
    /// ISSUER_UNAUTHORIZED (OD-2, TC-16). Their records and status are kept.
    function deactivateIssuer(string calldata issuerId) external {
        if (msg.sender != owner) revert NotOwner();
        address account = issuerAccountOf[issuerId];
        if (account == address(0)) revert IssuerNotRegistered();
        deactivated[account] = true;
        emit IssuerDeactivated(issuerId, account);
    }

    /// @notice Anchors a nonce-salted commitment for a new credential (T05, RGS.anchorCommitment).
    function issueCredential(string calldata credentialId, bytes32 commitment) external {
        string memory issuerId = issuerIdOf[msg.sender];
        if (bytes(issuerId).length == 0) revert IssuerNotRegistered();
        if (deactivated[msg.sender]) revert IssuerNotActive();
        if (records[credentialId].status != Status.None) revert CredentialExists();
        records[credentialId] = Record(commitment, msg.sender, Status.Active, uint64(block.timestamp));
        emit CredentialIssued(credentialId, commitment, issuerId);
    }

    /// @notice Revokes a credential. Only its original issuer may do so (T26, RGS.setStatus, TC-14).
    /// A deactivated issuer may still revoke, because revoking only lowers trust.
    function revokeCredential(string calldata credentialId) external {
        Record storage record = records[credentialId];
        if (record.status == Status.None) revert CredentialNotFound();
        if (record.issuer != msg.sender) revert NotOriginalIssuer();
        if (record.status == Status.Revoked) revert AlreadyRevoked();
        record.status = Status.Revoked;
        record.timestamp = uint64(block.timestamp);
        emit CredentialRevoked(credentialId, issuerIdOf[msg.sender]);
    }

    /// @notice Reads the registry record that verification compares against (T14, RGS.getRecord).
    function getRecord(string calldata credentialId)
        external
        view
        returns (bytes32 commitment, string memory issuerId, Status status, uint64 timestamp, bool issuerActive)
    {
        Record storage record = records[credentialId];
        if (record.status == Status.None) revert CredentialNotFound();
        return (
            record.commitment,
            issuerIdOf[record.issuer],
            record.status,
            record.timestamp,
            !deactivated[record.issuer]
        );
    }
}
