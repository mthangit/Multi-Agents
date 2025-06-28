/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    // Tắt ESLint trong quá trình build
    ignoreDuringBuilds: true,
  },
  // Tắt cảnh báo về việc sử dụng thẻ img
  images: {
    domains: ['*'],
  },
}

module.exports = nextConfig 