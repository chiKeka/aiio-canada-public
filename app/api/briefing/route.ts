import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { buildAlbertaBriefing } from '@/lib/alberta-briefing.mjs';
import { loadConstructionSnapshot } from '@/lib/construction-snapshot';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    const { data } = await loadConstructionSnapshot();
    const template = await readFile(
      path.join(
        process.cwd(),
        'assets/presentations/alberta-briefing-template.pptx',
      ),
    );
    const result = buildAlbertaBriefing(template, data);
    return new Response(new Uint8Array(result.bytes), {
      headers: {
        'Content-Type':
          'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'Content-Disposition': `attachment; filename="Alberta_Delivery_Briefing_${data.manifest.asOf}.pptx"`,
        'Cache-Control': 'no-store',
        'X-Briefing-Slides': String(result.slideCount),
        'X-Evidence-As-Of': data.manifest.asOf,
      },
    });
  } catch {
    return Response.json(
      {
        error:
          'The briefing could not be generated. The published evidence or template needs review. Please try again after the evidence is republished.',
      },
      { status: 503, headers: { 'Cache-Control': 'no-store' } },
    );
  }
}
