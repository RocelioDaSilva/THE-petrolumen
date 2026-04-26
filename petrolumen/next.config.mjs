/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: false, // Ensure ESLint runs during build
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
