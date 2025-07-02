/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: true, // Temporarily ignore ESLint errors during build
  },
  typescript: {
    ignoreBuildErrors: false, // Changed to false
  },
  images: {
    unoptimized: true,
  },
  output: 'export',
}

export default nextConfig
