/** @type {import('next').NextConfig} */
const nextConfig = {
  devIndicators: false,
  // Proxy /chat requests to the backend server
  async rewrites() {
    return [
      {
        source: "/chat",
        // Use environment variable for backend URL, fallback to localhost for development
        destination: process.env.BACKEND_URL || "http://127.0.0.1:8000/chat",
      },
    ];
  },
};

export default nextConfig;
