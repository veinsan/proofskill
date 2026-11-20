"use client";

import { useSyncExternalStore } from "react";
import { api, type AccessToken, type ApiResult, type Role } from "./api";

// One session per browser tab (sessionStorage), so one person can play several roles in
// separate tabs, as the prototype allows (report API-00).
export interface Session {
  token: string;
  role: Role;
  username: string;
  expiresAt: number;
}

const KEY = "proofskill.session";
const listeners = new Set<() => void>();
let cachedRaw: string | null | undefined;
let cachedSession: Session | null = null;

function read(): Session | null {
  let raw: string | null = null;
  try {
    raw = window.sessionStorage.getItem(KEY);
  } catch {
    raw = null;
  }
  if (raw !== cachedRaw) {
    cachedRaw = raw;
    try {
      const parsed = raw ? (JSON.parse(raw) as Session) : null;
      cachedSession = parsed && parsed.expiresAt > Date.now() ? parsed : null;
    } catch {
      cachedSession = null;
    }
  }
  return cachedSession;
}

function write(session: Session | null): void {
  try {
    if (session) window.sessionStorage.setItem(KEY, JSON.stringify(session));
    else window.sessionStorage.removeItem(KEY);
  } catch {
    // Storage blocked: the session lives only until reload.
  }
  cachedRaw = undefined;
  listeners.forEach((listener) => listener());
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

/** The signed-in session, `null` when signed out, `undefined` before the browser has been read. */
export function useSession(): Session | null | undefined {
  return useSyncExternalStore(subscribe, read, () => undefined);
}

export async function signIn(username: string, password: string): Promise<ApiResult<Session>> {
  const result = await api<AccessToken>("/auth/token", { method: "POST", body: { username, password } });
  if (!result.ok) return result;
  const session: Session = {
    token: result.data.accessToken,
    role: result.data.role,
    username,
    expiresAt: Date.now() + result.data.expiresIn * 1000,
  };
  write(session);
  return { ok: true, data: session };
}

export function signOut(): void {
  write(null);
}

export const HOME_BY_ROLE: Record<Role, string> = {
  issuer_admin: "/issuer",
  holder: "/holder",
  verifier: "/verifier",
  platform_admin: "/signin", // no portal: the sign-in page explains API-01 instead
};
