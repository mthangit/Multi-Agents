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
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'https://eyevi-backend.devsecopstech.click/:path*',
      },
    ];
  },
}

module.exports = nextConfig 