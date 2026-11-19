// Typed client for the ProofSkill REST API (report Bab IX). Shapes and enums are verbatim.

export type Role = "platform_admin" | "issuer_admin" | "holder" | "verifier";
export type CredentialStatus = "active" | "revoked";
export type VerificationResultCode = "VALID" | "REVOKED" | "TAMPERED" | "ISSUER_UNAUTHORIZED";
export type ScopeField = "holderDisplayName" | "program.title" | "completedAt" | "program.criteria" | "skills";

export const SCOPE_FIELDS: { field: ScopeField; label: string }[] = [
  { field: "program.title", label: "Program" },
  { field: "completedAt", label: "Completed date" },
  { field: "skills", label: "Skills" },
  { field: "program.criteria", label: "Pass criteria" },
  { field: "holderDisplayName", label: "Your name" },
];

export interface ApiError {
  code: string;
  message: string;
  requestId: string;
}

export type ApiResult<T> = { ok: true; data: T } | { ok: false; status: number; error: ApiError };

export interface AccessToken {
  accessToken: string;
  tokenType: "Bearer";
  expiresIn: number;
  role: Role;
}

export interface IssuerRef {
  issuerId: string;
  name: string;
}

export interface SkillRef {
  skillId: string;
  label: string;
}

export interface Skill extends SkillRef {
  aliases: string[];
}

export interface Program {
  title: string;
  completedAt: string;
  criteria: string;
}

export interface ShareLinkSummary {
  linkId: string;
  url: string;
  scope: ScopeField[];
  expiresAt: string;
  revokedAt: string | null;
}

export interface CredentialView {
  credentialId: string;
  issuer: IssuerRef;
  holderRef: string;
  holderDisplayName: string;
  program: Program;
  skills: SkillRef[];
  status: CredentialStatus;
  commitment: string;
  txHash: string | null;
  issuedAt: string;
  revokedAt: string | null;
  revocationReason: string | null;
  shareLinks: ShareLinkSummary[] | null;
}

export interface CredentialSummary {
  credentialId: string;
  issuer: IssuerRef;
  holderRef: string;
  holderDisplayName: string;
  program: Program;
  status: CredentialStatus;
  issuedAt: string;
  revokedAt: string | null;
}

export interface Page<T> {
  items: T[];
  total: number;
}

export interface CredentialIssued {
  credentialId: string;
  issuerId: string;
  status: "active";
  commitment: string;
  txHash: string;
  issuedAt: string;
}

export interface IssueCredentialRequest {
  holderRef: string;
  holderDisplayName: string;
  program: Program;
  skills: string[];
}

export interface ShareLink {
  linkId: string;
  shareToken: string;
  url: string;
  scope: ScopeField[];
  expiresAt: string;
}

export interface RevocationResult {
  credentialId: string;
  status: "revoked";
  reason: string;
  revokedAt: string;
  txHash: string;
}

export interface VerificationResult {
  verificationId: string;
  result: VerificationResultCode;
  checks: { integrity: "PASS" | "FAIL"; issuerAuthorized: "PASS" | "FAIL"; status: "ACTIVE" | "REVOKED" };
  reason?: string;
  credential?: {
    credentialId: string;
    issuer: IssuerRef;
    holderDisplayName?: string;
    program?: Partial<Program>;
    skills?: SkillRef[];
  };
  chainRef: { txHash: string | null };
  verifiedAt: string;
}

export interface MatchingResult {
  matchingId: string;
  label: "REKOMENDASI";
  matchedSkills: { skill: string; requirement: string; similarity: number; reason: string }[];
  missingRequirements: { requirement: string; note: string }[];
  limitations: string[];
  modelVersion: string;
}

export interface AuditEvent {
  time: string;
  actorRole: string;
  operation: string;
  objectId: string | null;
  outcome: string;
}

const NETWORK_ERROR: ApiError = {
  code: "NETWORK_ERROR",
  message: "The ProofSkill API cannot be reached. Check that it is running.",
  requestId: "",
};

export async function api<T>(
  path: string,
  options: { method?: string; body?: unknown; token?: string | null } = {},
): Promise<ApiResult<T>> {
  const headers: Record<string, string> = {};
  if (options.body !== undefined) headers["Content-Type"] = "application/json";
  if (options.token) headers.Authorization = `Bearer ${options.token}`;
  let response: Response;
  try {
    response = await fetch(`/api/v1${path}`, {
      method: options.method ?? "GET",
      headers,
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
      cache: "no-store",
    });
  } catch {
    return { ok: false, status: 0, error: NETWORK_ERROR };
  }
  if (response.status === 204) return { ok: true, data: undefined as T };
  const payload: unknown = await response.json().catch(() => null);
  if (response.ok) return { ok: true, data: payload as T };
  const error = (payload as { error?: ApiError } | null)?.error;
  return {
    ok: false,
    status: response.status,
    error: error ?? { code: `HTTP_${response.status}`, message: response.statusText || "Request failed.", requestId: "" },
  };
}
