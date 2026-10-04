import type { MetadataRoute } from 'next';

export default function sitemap(): MetadataRoute.Sitemap {
  const base = 'https://aiio-canada.vercel.app';
  return ['', '/evidence', '/pressure', '/scenario', '/methods', '/historical-analog', '/digest', '/downloads', '/research', '/status'].map((path) => ({ url: `${base}${path}`, changeFrequency: path === '/digest' ? 'weekly' : 'monthly', priority: path === '' ? 1 : 0.7 }));
}
