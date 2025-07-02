/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: false, // Changed to false
  },
  typescript: {
    ignoreBuildErrors: false, // Changed to false
  },
  images: {
    unoptimized: true,
  },
}

export default nextConfig
