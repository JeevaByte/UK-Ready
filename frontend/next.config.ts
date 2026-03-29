import type { NextConfig } from "next";

/**
 * Next.js configuration for UKReady frontend.
 *
 * Key configuration:
 * - API rewrites: /api/* proxied to the FastAPI backend, so the frontend
 *   never needs to make cross-origin requests (avoids CORS in development).
 * - INTERNAL_API_URL is used for server-side rewrites (Docker network name).
 * - NEXT_PUBLIC_API_URL is used by client-side code.
 */
const nextConfig: NextConfig = {
  // Strict mode helps catch React issues early
  reactStrictMode: true,

  // Proxy /api/* to the FastAPI backend
  // In Docker Compose, INTERNAL_API_URL=http://backend:8000
  // In local dev (non-Docker), INTERNAL_API_URL=http://localhost:8000
  async rewrites() {
    const apiUrl = process.env.INTERNAL_API_URL ?? "http://localhost:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${apiUrl}/:path*`,
      },
    ];
  },

  // Forward environment variables to the browser that are safe to expose
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
  },
};

export default nextConfig;
