/** @type {import('next').NextConfig} */
const nextConfig = {
  // produce a standalone server build so the app can run a local Node server
  output: 'standalone',
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    // Allow production builds even when type errors exist.
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
}

export default nextConfig
