import {
  loadConstructionSnapshot,
  constructionFreshness,
} from '@/lib/construction-snapshot';
export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';
export async function GET() {
  try {
    const { revision, data } = await loadConstructionSnapshot();
    return Response.json(
      {
        revision: `${revision}:${new Date().toISOString().slice(0, 10)}`,
        asOf: data.manifest.asOf,
        sources: constructionFreshness(data),
      },
      { headers: { 'Cache-Control': 'no-store' } },
    );
  } catch {
    return Response.json(
      { error: 'Published evidence is temporarily unavailable.' },
      { status: 503, headers: { 'Cache-Control': 'no-store' } },
    );
  }
}
