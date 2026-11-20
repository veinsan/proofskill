import type { NextConfig } from "next";

// The browser calls /api/v1 on this origin; Next.js proxies it to FastAPI, so no CORS is needed.
// The rewrite is fixed at build time, so a Vercel build without API_ORIGIN fails here instead of
// shipping a site that proxies to localhost (B-06).
if (process.env.VERCEL && !process.env.API_ORIGIN) {
  throw new Error("Set API_ORIGIN (the API's Vercel URL) in this Vercel project before building.");
}
const apiOrigin = (process.env.API_ORIGIN ?? "http://127.0.0.1:8000").replace(/\/+$/, "");

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  // No framing (clickjacking), no MIME sniffing, and share-link paths (/v/sk_…) never sent as a referrer.
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "Content-Security-Policy", value: "frame-ancestors 'none'; base-uri 'self'; object-src 'none'; form-action 'self'" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "no-referrer" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
        ],
      },
    ];
  },
  async rewrites() {
    return [{ source: "/api/v1/:path*", destination: `${apiOrigin}/api/v1/:path*` }];
  },
};

export default nextConfig;
