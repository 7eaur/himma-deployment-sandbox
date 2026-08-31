import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    unoptimized: false,
  },
  // API proxy is handled by src/app/api/[...path]/route.ts
  // which correctly forwards Set-Cookie headers (rewrites do not).
};

export default nextConfig;

