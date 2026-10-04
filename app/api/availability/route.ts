/** Liveness is independent of evidence freshness and research authorization. */
export const dynamic = 'force-dynamic';
export function GET() {
  return Response.json(
    { status: 'available', checked_at: new Date().toISOString() },
    {
      headers: {
        'Cache-Control': 'no-store',
        'X-Content-Type-Options': 'nosniff',
      },
    },
  );
}
