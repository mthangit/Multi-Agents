const backendUrl = process.env.BACKEND_URL || 'https://eyevi-backend.devsecopstech.click';

/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    // Tắt ESLint trong quá trình build
    ignoreDuringBuilds: true,
  },
  // Cấu hình domains cho hình ảnh
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'product.hstatic.net',
      },
      {
        protocol: 'https',
        hostname: 'placehold.co',
      },
    ],
  },
  // Cấu hình timeout cho server
  experimental: {
    proxyTimeout: 300000, // 5 phút (300 giây) cho proxy timeout
  },
  // Cấu hình server timeout
  serverRuntimeConfig: {
    // Timeout cho API routes (milliseconds)
    apiTimeout: 300000, // 5 phút
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${backendUrl}/:path*`,
      },
    ];
  },
}

module.exports = nextConfig 