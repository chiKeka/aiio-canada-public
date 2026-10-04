import type { Metadata } from 'next';
import localFont from 'next/font/local';
import { Analytics } from '@vercel/analytics/next';
import { SpeedInsights } from '@vercel/speed-insights/next';
import './globals.css';

// Use the Geist assets bundled with the locked Next.js dependency for offline builds.
const geistSans = localFont({
  src: '../node_modules/next/dist/next-devtools/server/font/geist-latin.woff2',
  weight: '100 900',
  display: 'swap',
  variable: '--font-geist-sans',
});

const geistMono = localFont({
  src: '../node_modules/next/dist/next-devtools/server/font/geist-mono-latin.woff2',
  weight: '100 900',
  display: 'swap',
  variable: '--font-geist-mono',
});

export const metadata: Metadata = {
  metadataBase: new URL('https://aiio-canada.vercel.app'),
  title: 'AIIO Canada | AI Infrastructure Impact Observatory',
  description:
    'A public research program tracking how AI infrastructure investment changes the cost, capacity, and delivery of Canadian public infrastructure.',
  icons: { icon: '/favicon.svg' },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} min-h-screen antialiased`}
      >
        {children}
        <Analytics />
        <SpeedInsights />
      </body>
    </html>
  );
}
