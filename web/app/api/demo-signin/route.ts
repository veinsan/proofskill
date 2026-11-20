import { DEMO_USERNAMES } from "@/lib/demo";

// One-click sign-in for the listed demo accounts (approved by the team on 2026-11-20, like SafeTrip's
// demo login). The browser sends only a username; this server adds the shared demo password from
// DEMO_PASSWORD and calls API-00, whose answer goes back unchanged. Anyone who opens the site can
// therefore act as these synthetic accounts. platform.admin is not listed and still needs the password.
const apiOrigin = (process.env.API_ORIGIN ?? "http://127.0.0.1:8000").replace(/\/+$/, "");

function error(status: number, code: string, message: string) {
  return Response.json({ error: { code, message, requestId: "" } }, { status, headers: { "Cache-Control": "no-store" } });
}

export async function POST(request: Request): Promise<Response> {
  const password = process.env.DEMO_PASSWORD;
  if (!password) return error(501, "", "One-click sign-in is off on this server. Use the demo password instead.");

  const body: unknown = await request.json().catch(() => null);
  const username = (body as { username?: unknown } | null)?.username;
  if (typeof username !== "string" || !DEMO_USERNAMES.includes(username)) {
    return error(401, "INVALID_CREDENTIALS", "Only the listed demo accounts sign in with one click.");
  }

  try {
    const response = await fetch(`${apiOrigin}/api/v1/auth/token`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
      cache: "no-store",
    });
    return new Response(await response.text(), {
      status: response.status,
      headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
    });
  } catch {
    return error(502, "", "The API could not be reached. Try again in a moment.");
  }
}
