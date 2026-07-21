/** @type {import('next').NextConfig} */
import withPWA from 'next-pwa'
import path from 'path'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const nextConfig = {
  // ❌ REMOVA esta linha:
   output: 'export',
  trailingSlash: true,
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  turbopack: {
    root: path.join(process.cwd()),
  },
}

export default withPWA({
  dest: 'public',
  register: true,
  skipWaiting: true,
  disable: process.env.NODE_ENV === 'development',
})(nextConfig)