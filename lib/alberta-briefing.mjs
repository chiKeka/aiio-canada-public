import {
  summarizeAlbertaProjects,
  resolveConstructionBenchmark,
  constructionBenchmarkPeriods,
} from './alberta-evidence-summary.mjs';
import { unzipSync, zipSync, strFromU8, strToU8 } from 'fflate';
import { createHash } from 'node:crypto';

// Bind reviewed DrawingML layouts, preserving native tables, charts and their workbooks.
// The input is trusted, published evidence; this module never fetches external data.
const escape = (value) =>
  String(value).replace(
    /[&<>"']/g,
    (c) =>
      ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&apos;',
      })[c],
  );
const num = (value) =>
  value === null ? 'Not published' : Number(value).toLocaleString('en-CA');
const quarter = (date) =>
  `Q${Math.ceil(Number(date.slice(5, 7)) / 3)} ${date.slice(0, 4)}`;
const dateLabel = (date) =>
  new Date(`${date}T12:00:00Z`).toLocaleDateString('en-CA', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    timeZone: 'UTC',
  });
function setText(xml, value) {
  let first = true;
  return xml.replace(/<a:t(?:\s[^>]*)?>[\s\S]*?<\/a:t>/g, () => {
    const out = `<a:t>${first ? escape(value) : ''}</a:t>`;
    first = false;
    return out;
  });
}
function shape(xml, index, value) {
  let i = 0,
    found = false;
  const result = xml.replace(/<p:sp>[\s\S]*?<\/p:sp>/g, (part) => {
    if (i++ !== index) return part;
    found = true;
    return setText(part, value);
  });
  if (!found) throw new Error('Briefing template shape mismatch');
  return result;
}
function table(xml, values) {
  const rows = xml.match(/<a:tr\b[^>]*>[\s\S]*?<\/a:tr>/g);
  if (!rows || (values.length > 8 && values.length > rows.length))
    throw new Error('Briefing table layout needs review');
  const height = rows.reduce((s, r) => s + Number(r.match(/h="(\d+)"/)[1]), 0);
  const body = values
    .map((row, r) => {
      let col = 0;
      const template = rows[r === 0 ? 0 : r % 2 === 0 ? 2 : 1];
      return template
        .replace(/h="\d+"/, `h="${Math.floor(height / values.length)}"`)
        .replace(/<a:tc>[\s\S]*?<\/a:tc>/g, (cell) =>
          setText(cell, row[col++] ?? ''),
        );
    })
    .join('');
  return xml.replace(/<a:tr\b[^>]*>[\s\S]*<\/a:tr>/, body);
}

export function buildAlbertaBriefing(
  template,
  input,
  generatedAt = new Date(),
) {
  const { projects, benchmarks, evidence, manifest } = input;
  if (!projects.length || projects.length > 700)
    throw new Error(
      'Project inventory is empty or exceeds the reviewed export limit',
    );
  if (new Set(projects.map((p) => p.id)).size !== projects.length)
    throw new Error('Duplicate project IDs');
  for (const p of projects) {
    if (
      !p.name ||
      p.name.length > 150 ||
      !/^\d{4}-\d{2}-\d{2}$/.test(p.asOf) ||
      [p.cost, p.start, p.end].some(
        (v) => v !== null && (!Number.isFinite(v) || v < 0),
      )
    )
      throw new Error('Invalid project evidence');
  }
  const periods = constructionBenchmarkPeriods(benchmarks);
  const parameters = Object.fromEntries(
    benchmarks.parameters.map((p) => [p.id, p]),
  );
  const scalar = (id) => {
    const p = resolveConstructionBenchmark(benchmarks, id);
    if (
      !p ||
      !Number.isFinite(p.value) ||
      !/^(observed|published)/.test(p.status)
    )
      throw new Error(`Missing published benchmark: ${id}`);
    return p.value;
  };
  const source = (id) => {
    const s = benchmarks.sources.find((s) => s.id === id);
    if (!s) throw new Error(`Missing source: ${id}`);
    return `${s.period}. ${s.url}${s.document_url ? '\n' + s.document_url : ''}`;
  };
  const files = unzipSync(template);
  const get = (name) => {
    if (!files[name]) throw new Error(`Missing template part: ${name}`);
    return strFromU8(files[name]);
  };
  const put = (name, xml) => {
    files[name] = strToU8(xml);
  };
  const slide = (n, slots) => {
    const name = `ppt/slides/slide${n}.xml`;
    let xml = get(name);
    for (const [i, v] of Object.entries(slots)) xml = shape(xml, Number(i), v);
    put(name, xml);
  };
  const grid = (n, rows) => {
    const name = `ppt/slides/slide${n}.xml`;
    put(name, table(get(name), rows));
  };
  for (const [key, n] of [
    ['packages', 5],
    ['pathways', 11],
    ['mitigations', 12],
  ]) {
    const guidance = evidence.guidance[key];
    grid(n, [guidance.headers, ...guidance.rows]);
  }
  evidence.guidance.priorities.forEach(([title, description], i) => {
    slide(13, { [4 + i * 2]: title, [5 + i * 2]: description });
  });
  const provenance = `\nGenerated ${generatedAt.toISOString()}. Evidence release ${manifest.version}, ${manifest.asOf}.\nInput SHA-256: ${createHash('sha256').update(JSON.stringify(input)).digest('hex')}.\nSource file hashes: ${JSON.stringify(evidence.sourceHashes)}.`;
  const notes = (n, value) => {
    const name = `ppt/notesSlides/notesSlide${n}.xml`;
    put(
      name,
      get(name).replace(/<p:sp>[\s\S]*?<\/p:sp>/g, (part) =>
        part.includes('type="body"') ? setText(part, value + provenance) : part,
      ),
    );
  };
  function chart(n, categories, series, format = '#,##0') {
    if (
      !categories.length ||
      series.some(
        (s) =>
          s.values.length !== categories.length ||
          s.values.some((v) => !Number.isFinite(v)),
      )
    )
      throw new Error('Missing chart observations');
    const name = `ppt/slides/charts/chart${n}.xml`;
    let i = 0;
    const xml = get(name).replace(/<c:ser>[\s\S]*?<\/c:ser>/g, (part) => {
      const s = series[i++],
        col = String.fromCharCode(65 + i);
      if (!s) throw new Error('Chart series mismatch');
      const points = (values) =>
        `<c:ptCount val="${values.length}"/>` +
        values
          .map((v, j) => `<c:pt idx="${j}"><c:v>${escape(v)}</c:v></c:pt>`)
          .join('');
      return part
        .replace(
          /<c:tx>[\s\S]*?<\/c:tx>/,
          `<c:tx><c:v>${escape(s.name)}</c:v></c:tx>`,
        )
        .replace(
          /<c:cat>[\s\S]*?<\/c:cat>/,
          `<c:cat><c:strRef><c:f>'Chart Data'!$A$2:$A$${categories.length + 1}</c:f><c:strCache>${points(categories)}</c:strCache></c:strRef></c:cat>`,
        )
        .replace(
          /<c:val>[\s\S]*?<\/c:val>/,
          `<c:val><c:numRef><c:f>'Chart Data'!$${col}$2:$${col}$${categories.length + 1}</c:f><c:numCache><c:formatCode>${escape(format)}</c:formatCode>${points(s.values)}</c:numCache></c:numRef></c:val>`,
        );
    });
    if (i !== series.length) throw new Error('Chart template mismatch');
    put(name, n === 4 ? xml.replace(/<c:min val="0"\s*\/>/g, '') : xml);
    const workbook = `ppt/embeddings/chart-data-snapshot-${String(n).padStart(3, '0')}.xlsx`;
    const wb = unzipSync(files[workbook]);
    const rows = [
      ['Category', ...series.map((s) => s.name)],
      ...categories.map((c, j) => [c, ...series.map((s) => s.values[j])]),
    ];
    wb['xl/worksheets/sheet1.xml'] = strToU8(
      `<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><dimension ref="A1:${String.fromCharCode(65 + series.length)}${rows.length}"/><sheetData>${rows.map((r, j) => `<row r="${j + 1}">${r.map((v, k) => `<c r="${String.fromCharCode(65 + k)}${j + 1}"${typeof v === 'number' ? '' : ' t="inlineStr"'}>${typeof v === 'number' ? `<v>${v}</v>` : `<is><t>${escape(v)}</t></is>`}</c>`).join('')}</row>`).join('')}</sheetData></worksheet>`,
    );
    files[workbook] = zipSync(wb);
  }
  const dates = [...new Set(projects.map((p) => p.asOf))].sort((a, b) =>
    a.localeCompare(b),
  );
  const vintage =
    dates.length === 1
      ? dateLabel(dates[0])
      : `${dateLabel(dates[0])}–${dateLabel(dates.at(-1))}`;
  const projectRef = `Alberta Major Projects inventory, ${vintage}. https://www.majorprojects.alberta.ca/\nhttps://majorprojects.alberta.ca/methodology\nRecords may be phases or programmes, not unique campuses. Proposed status does not establish financing or a construction start. Reported investment scopes differ; missing values remain missing.`;
  slide(1, { 2: `Evidence briefing • ${dateLabel(manifest.asOf)}` });
  const stages = [...new Set(projects.map((p) => p.stage))];
  chart(1, stages, [
    {
      name: 'Data-centre records',
      values: stages.map((s) => projects.filter((p) => p.stage === s).length),
    },
  ]);
  slide(2, {
    0: 'Alberta data-centre pipeline and capital investment',
    1: `${projects.length} identified data-centre records sit alongside substantial infrastructure investment.`,
    2: `Sources: Alberta Major Projects, ${vintage}; Alberta fiscal update, ${periods.fiscalYear}`,
    4: `$${(scalar('public_capital_q1_fy2026_27') / 1000).toFixed(3)}B`,
    5: `Updated Alberta capital plan for ${periods.fiscalYear}`,
  });
  notes(
    2,
    projectRef +
      '\n' +
      source('AB_Q1') +
      '\nCapital plan includes multiple asset classes, not solely construction labour.',
  );
  const { costed, scheduled, costTotal } = summarizeAlbertaProjects(projects);
  const total = (costTotal ?? 0) / 1e9;
  const label = (p) =>
    p.name.length > 35 ? p.name.slice(0, 32) + '…' : p.name;
  chart(
    2,
    costed.length ? costed.slice(0, 7).map(label) : ['No reported costs'],
    [
      {
        name: 'Reported CAD billions',
        values: costed.length
          ? costed.slice(0, 7).map((p) => Number((p.cost / 1e9).toFixed(5)))
          : [0],
      },
    ],
    '0.00',
  );
  slide(3, {
    0: costed.length
      ? `${costed.length} reported costs total $${total.toFixed(2)}B`
      : 'Reported investment costs are unavailable',
    1:
      costed.length > 7
        ? 'Largest seven reported estimates, CAD billions. Full inventory in appendix.'
        : 'Reported investment estimates, CAD billions.',
    2: `Alberta Major Projects, ${vintage}. ${projects.length - costed.length} records have no reported cost.`,
  });
  notes(
    3,
    projectRef +
      `\nSum of ${costed.length} reported core costs: CAD ${total.toFixed(2)} billion. No assumed construction or labour share is applied. Chart shows up to seven largest estimates. Full names and values are in the appendix.`,
  );
  slide(4, {
    0: 'Reported completion years',
    1: `${scheduled.length} of ${projects.length} records report a completion year.${scheduled.length > 6 ? ' Earliest six shown; all records in appendix.' : ''}`,
    2: `Alberta Major Projects, ${vintage}. Reported years are estimates, not verified operating dates.`,
    4: `${projects.length - scheduled.length} records lack completion years. No dates or construction durations have been inferred.`,
  });
  grid(4, [
    ['Project / phase', 'Reported stage', 'Completion year'],
    ...(scheduled.length
      ? scheduled.slice(0, 6).map((p) => [p.name, p.stage, String(p.end)])
      : [['Not published', '—', '—']]),
  ]);
  notes(
    4,
    projectRef +
      '\nOnly reported end years are shown. No start date, midpoint, commissioning duration or delivery probability has been inferred.',
  );
  const occupations = [
    ['72200', 'Electricians, excluding industrial / power'],
    ['72201', 'Industrial electricians'],
    ['72202', 'Power-system electricians'],
    ['72203', 'Power-line and cable workers'],
    ['72402', 'HVAC mechanics'],
    ['73100', 'Concrete finishers'],
  ];
  const labour = occupations.map(([code, label]) => {
    const row = evidence.labour.find((r) => r.noc_code === code);
    if (!row || row.geography_id !== 'PR_48')
      throw new Error(`Missing Alberta occupation ${code}`);
    return { ...row, label };
  });
  if (
    new Set(labour.map((r) => r.vacancy_period_end)).size !== 1 ||
    new Set(labour.map((r) => r.workforce_period_end)).size !== 1
  )
    throw new Error('Mixed labour periods need review');
  slide(6, {
    0: 'Alberta electrical and HVAC workforce observations',
    2: 'Statistics Canada. E = use with caution; suppressed or missing vacancies are not zero.',
  });
  grid(6, [
    [
      'Occupation',
      `Employed, ${labour[0].workforce_period_end.slice(0, 4)}`,
      `Vacancies, ${quarter(labour[0].vacancy_period_end)}`,
    ],
    ...labour.map((r) => [
      r.label,
      num(r.workforce_stock),
      num(r.vacancies) +
        (r.vacancies !== null && r.vacancy_quality_flags.includes('status:E')
          ? ' E'
          : ''),
    ]),
  ]);
  notes(
    6,
    'Statistics Canada, Alberta. Census Table 98-10-0449-01: https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=9810044901\nJVWS Table 14-10-0444-01: https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1410044401\nEmployment is a historical stock, not available crews. Different periods do not support a current vacancy rate.\n' +
      JSON.stringify(labour),
  );
  const recruitment = scalar('recruitment_requirement_to2035'),
    entrants = scalar('first_time_local_entrants_to2035');
  chart(
    3,
    ['Recruitment requirement', 'First-time local entrants'],
    [{ name: 'Workers, cumulative forecast', values: [recruitment, entrants] }],
  );
  slide(7, {
    1: `BuildForce’s published Alberta construction outlook, ${periods.recruitment}.`,
    2: 'Source: BuildForce, published Alberta outlook. Forecasts describe the whole construction market.',
    4: num(scalar('retirements_to2035')),
    6: num(Math.max(0, recruitment - entrants)),
  });
  notes(
    7,
    source('BUILDFORCE') +
      `\nPublished forecast: recruitment ${recruitment} minus entrants ${entrants} gives potential shortfall ${Math.max(0, recruitment - entrants)}. Retirements are not additional demand to add to recruitment. This is not a data-centre-attributed gap or current spare capacity.`,
  );
  const components = [
    'concrete',
    'structural_steel_framing',
    'electrical_systems',
    'hvac',
  ];
  const priceSeries = [
    ['CMA_825', 'Calgary'],
    ['CMA_835', 'Edmonton'],
  ].map(([id, name]) => ({
    name,
    values: components.map((c) => {
      const r = evidence.prices.find(
        (r) => r.geography_id === id && r.component === c,
      );
      if (!r || r.year_over_year_percent_change === null)
        throw new Error('Missing price component');
      return Number(r.year_over_year_percent_change.toFixed(2));
    }),
  }));
  if (new Set(evidence.prices.map((r) => r.period_end)).size !== 1)
    throw new Error('Mixed price periods need review');
  slide(8, {
    0: 'Alberta construction component price changes',
    1: `Calgary and Edmonton industrial-factory components, ${quarter(evidence.prices[0].period_end)} year over year.`,
  });
  chart(
    4,
    ['Concrete', 'Structural steel', 'Electrical systems', 'HVAC'],
    priceSeries,
    '0.0"%"',
  );
  notes(
    8,
    `Statistics Canada, Table 18-10-0289-01: https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1810028901\n${quarter(evidence.prices[0].period_end)}. Contractor bid-price changes, not physical material volumes, supplier capacity or a data-centre-caused premium. Industrial factory is a proxy, not a data-centre price index.\n` +
      JSON.stringify(evidence.prices),
  );
  const capital = evidence.capital;
  const classes = [
    ['schools_and_postsecondary', 'School / postsecondary'],
    ['roads_transit_and_airports', 'Road / transit / airport'],
    ['health_facilities', 'Health'],
    ['power_sector_infrastructure', 'Power'],
    ['municipal_water_and_resilience', 'Water / resilience'],
    ['government_and_civic_facilities', 'Government / civic'],
  ];
  const capitalRows = classes.map(([id]) => {
    const r = capital.asset_class_summaries.find((r) => r.asset_class === id);
    if (!r) throw new Error('Missing capital category');
    return r;
  });
  chart(
    5,
    classes.map((c) => c[1]),
    [
      {
        name: 'Screened records',
        values: capitalRows.map((r) => r.project_count),
      },
    ],
  );
  slide(9, {
    1: `${capital.screened_project_count} screened records across infrastructure categories.`,
    2: `Alberta Major Projects, ${dateLabel(capital.as_of_date)}; analytical classification. Some private owners.`,
    4: num(capitalRows.reduce((s, r) => s + r.overlap_project_count, 0)),
    5: `records have known overlap with ${capital.window.start_year}–${capital.window.end_year}`,
  });
  notes(
    9,
    `Alberta Major Projects, ${capital.as_of_date}. https://www.majorprojects.alberta.ca/\nAnalytical classification. Missing schedules do not imply no overlap. Inventory counts are not committed spending and must not be added to the provincial capital plan. Shared packages suggest possible competition, not observed resource contention.\n` +
      JSON.stringify(capital),
  );
  const equipment = [
    [
      'cooling_tower',
      'Cooling towers',
      'Cooling configuration and installation window',
    ],
    [
      'air_cooled_chiller',
      'Air-cooled chillers',
      'Duty, redundancy and manufacturer selection',
    ],
    [
      'water_cooled_chiller',
      'Water-cooled chillers',
      'Cooling-system design and commissioning',
    ],
    [
      'ahu',
      'Air handling units',
      'Custom specification and controls integration',
    ],
    ['generator', 'Generators', 'Rating, approvals and site installation'],
    [
      'lv_switchgear',
      'Low-voltage switchgear',
      'Electrical design and approved submittals',
    ],
    [
      'mv_switchgear',
      'Medium-voltage switchgear',
      'Utility interface and technical specification',
    ],
    ['ups', 'UPS', 'Power architecture and testing requirements'],
  ];
  const procurementPeriod = source('SOURCEBLUE').match(/Q[1-4] \d{4}/)?.[0];
  if (!procurementPeriod)
    throw new Error('Procurement reference period needs review');
  slide(10, {
    2: `SourceBlue, ${procurementPeriod} US market ranges. Alberta delivery requires a product-specific supplier quotation.`,
  });
  grid(10, [
    ['Equipment', 'Published lead time', 'Delivery consideration'],
    ...equipment.map(([id, label, detail]) => {
      const p = parameters[`procurement_${id}`];
      if (
        !p ||
        p.status !== 'transfer_benchmark' ||
        !Array.isArray(p.value) ||
        p.value.length !== 2 ||
        p.value.some((v) => !Number.isFinite(v)) ||
        p.value[0] > p.value[1]
      )
        throw new Error('Missing published procurement range');
      return [
        label,
        `${p.value[0]}–${p.value[1]} weeks`,
        evidence.guidance.procurementConsiderations[label] ?? detail,
      ];
    }),
  ]);
  notes(
    10,
    source('SOURCEBLUE') +
      '\nUS equipment benchmarks, not Alberta delivery commitments. Confirm product-specific supplier quotes, release basis, freight, testing and installation. No project delay is calculated.',
  );
  // Appendix pagination uses the reviewed seven-row layout; every record is retained.
  const pages = Math.ceil(projects.length / 7),
    count = 13 + pages;
  const base = get('ppt/slides/slide14.xml'),
    baseNotes = get('ppt/notesSlides/notesSlide14.xml');
  const baseRel = get('ppt/slides/_rels/slide14.xml.rels'),
    baseNoteRel = get('ppt/notesSlides/_rels/notesSlide14.xml.rels');
  for (let page = 0; page < pages; page++) {
    const n = 14 + page,
      batch = projects.slice(page * 7, page * 7 + 7);
    put(`ppt/slides/slide${n}.xml`, base);
    put(`ppt/notesSlides/notesSlide${n}.xml`, baseNotes);
    put(
      `ppt/slides/_rels/slide${n}.xml.rels`,
      baseRel.replaceAll('notesSlide14.xml', `notesSlide${n}.xml`),
    );
    put(
      `ppt/notesSlides/_rels/notesSlide${n}.xml.rels`,
      baseNoteRel.replaceAll('slide14.xml', `slide${n}.xml`),
    );
    slide(n, {
      0: `Alberta pipeline reference ${page + 1} of ${pages}`,
      2: `Alberta Major Projects, ${vintage}. ? = missing year; — = missing cost. Estimated scope varies.`,
      3: String(n),
    });
    grid(n, [
      ['Project / phase', 'Stage', 'Reported years', 'CAD B'],
      ...batch.map((p) => [
        p.name,
        p.stage === 'Under Construction' ? 'Construction' : p.stage,
        `${p.start ?? '?'}–${p.end ?? '?'}`,
        p.cost === null ? '—' : (p.cost / 1e9).toFixed(2),
      ]),
    ]);
    notes(
      n,
      projectRef +
        '\n' +
        batch
          .map((p) => `${p.name}: ${p.source || 'Inventory source only'}`)
          .join('\n'),
    );
  }
  const rels = get('ppt/_rels/presentation.xml.rels')
    .replace(/<Relationship\b[^>]*Type="[^"]*\/slide"[^>]*\/>/g, '')
    .replace(
      '</Relationships>',
      Array.from(
        { length: count },
        (_, i) =>
          `<Relationship Id="briefingSlide${i + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="/ppt/slides/slide${i + 1}.xml"/>`,
      ).join('') + '</Relationships>',
    );
  put('ppt/_rels/presentation.xml.rels', rels);
  put(
    'ppt/presentation.xml',
    get('ppt/presentation.xml').replace(
      /<p:sldIdLst>[\s\S]*?<\/p:sldIdLst>/,
      `<p:sldIdLst>${Array.from({ length: count }, (_, i) => `<p:sldId xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" id="${256 + i}" r:id="briefingSlide${i + 1}"/>`).join('')}</p:sldIdLst>`,
    ),
  );
  let types = get('[Content_Types].xml').replace(
    /<Override\b[^>]*PartName="\/ppt\/(?:slides\/slide|notesSlides\/notesSlide)\d+\.xml"[^>]*\/>/g,
    '',
  );
  types = types.replace(
    '</Types>',
    Array.from(
      { length: count },
      (_, i) =>
        `<Override PartName="/ppt/slides/slide${i + 1}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/><Override PartName="/ppt/notesSlides/notesSlide${i + 1}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml"/>`,
    ).join('') + '</Types>',
  );
  put('[Content_Types].xml', types);
  for (const name of Object.keys(files)) {
    const match = name.match(
      /^ppt\/(?:slides|notesSlides)\/(?:_rels\/)?(?:slide|notesSlide)(\d+)\.xml(?:\.rels)?$/,
    );
    if (match && Number(match[1]) > count) delete files[name];
  }
  put(
    'docProps/app.xml',
    get('docProps/app.xml').replace(
      /<Slides>\d+<\/Slides>/,
      `<Slides>${count}</Slides>`,
    ),
  );
  // An absent observation must not become a zero-value chart or stale workbook.
  if (!costed.length) {
    put(
      'ppt/slides/slide3.xml',
      get('ppt/slides/slide3.xml').replace(
        /<p:graphicFrame>[\s\S]*?<\/p:graphicFrame>/g,
        '',
      ),
    );
    put(
      'ppt/slides/_rels/slide3.xml.rels',
      get('ppt/slides/_rels/slide3.xml.rels').replace(
        /<Relationship\b[^>]*Type="[^"]*\/chart"[^>]*\/>/g,
        '',
      ),
    );
    delete files['ppt/slides/charts/chart2.xml'];
    delete files['ppt/slides/charts/_rels/chart2.xml.rels'];
    delete files['ppt/embeddings/chart-data-snapshot-002.xlsx'];
    put(
      '[Content_Types].xml',
      get('[Content_Types].xml').replace(
        /<Override\b[^>]*PartName="\/ppt\/slides\/charts\/chart2.xml"[^>]*\/>/g,
        '',
      ),
    );
  }
  // Update creation and modification metadata for this generated snapshot.
  put(
    'docProps/core.xml',
    get('docProps/core.xml').replace(
      /(<dcterms:(?:created|modified)\b[^>]*>)[\s\S]*?(<\/dcterms:(?:created|modified)>)/g,
      `$1${generatedAt.toISOString()}$2`,
    ),
  );
  return {
    bytes: zipSync(files, { level: 6 }),
    slideCount: count,
    projectCount: projects.length,
  };
}
