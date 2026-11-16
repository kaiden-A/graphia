import path from "node:path";
import { fileURLToPath } from "node:url";

import type { NextConfig } from "next";

const apiOrigin = (process.env.API_ORIGIN ?? "http://localhost:8000").replace(/\/$/, "");
const rootDir = path.dirname(fileURLToPath(import.meta.url));

const nextConfig: NextConfig = {
  turbopack: {
    root: rootDir,
  },
  async rewrites() {
    return {
      afterFiles: [
        {
          source: "/api/:path*",
          destination: `${apiOrigin}/api/:path*`,
        },
      ],
    };
  },
};

export default nextConfig;
