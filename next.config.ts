import type { NextConfig } from 'next';

const securityHeaders = [
  { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
  { key: 'X-Content-Type-Options', value: 'nosniff' },
  { key: 'X-Frame-Options', value: 'DENY' },
  {
    key: 'Permissions-Policy',
    value: 'camera=(), microphone=(), geolocation=()',
  },
  { key: 'Cross-Origin-Opener-Policy', value: 'same-origin' },
];

const nextConfig: NextConfig = {
  poweredByHeader: false,
  outputFileTracingIncludes: {
    '/api/construction/demand': ['./public/data/construction/snapshot.json'],
    '/': ['./public/data/construction/snapshot.json'],
    '/delivery': ['./public/data/construction/snapshot.json'],
    '/api/briefing': [
      './assets/presentations/alberta-briefing-template.pptx',
      './public/data/construction/snapshot.json',
    ],
    '/construction': ['./public/data/construction/snapshot.json'],
    '/api/construction/revision': ['./public/data/construction/snapshot.json'],
  },
  async headers() {
    return [{ source: '/:path*', headers: securityHeaders }];
  },
};

export default nextConfig;
