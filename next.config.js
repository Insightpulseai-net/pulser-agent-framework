/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  experimental: {
    serverActions: {
      allowedOrigins: ['xkxyvboeubffxxbebsll.supabase.co'],
    },
  },
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'xkxyvboeubffxxbebsll.supabase.co',
        port: '',
        pathname: '/storage/v1/object/public/**',
      },
    ],
  },
}

module.exports = nextConfig
