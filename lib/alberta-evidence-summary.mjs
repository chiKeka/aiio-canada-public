/**
 * Reported inventory aggregates shared by the dashboard and PowerPoint.
 * Null observations are excluded from sums, never converted into observations of zero.
 * @template {{cost: number|null, end: number|null, stage: string}} T
 * @param {T[]} projects
 */
export function summarizeAlbertaProjects(projects) {
  const costed = projects
    .filter((p) => p.cost !== null)
    .sort((a, b) => b.cost - a.cost);
  const scheduled = projects
    .filter((p) => p.end !== null)
    .sort((a, b) => a.end - b.end);
  return {
    costed,
    scheduled,
    costTotal: costed.length
      ? costed.reduce((sum, p) => sum + p.cost, 0)
      : null,
    stages: [...new Set(projects.map((p) => p.stage))].map((stage) => ({
      stage,
      count: projects.filter((p) => p.stage === stage).length,
    })),
    missingCosts: projects.length - costed.length,
    missingCompletionYears: projects.length - scheduled.length,
  };
}

/** Resolve rolling benchmark vintages without binding the display to a calendar year. */
export function resolveConstructionBenchmark(benchmarks, id) {
  let selected = id;
  if (
    /^(recruitment_requirement|first_time_local_entrants|retirements|potential_recruitment_shortfall)_to\d{4}$/.test(
      id,
    )
  ) {
    const horizon = benchmarks.parameters
      .filter((p) => /^recruitment_requirement_to\d{4}$/.test(p.id))
      .map((p) => Number(p.id.slice(-4)))
      .sort((a, b) => b - a)[0];
    if (horizon) selected = id.replace(/\d{4}$/, String(horizon));
  }
  if (id.startsWith('public_capital_q1_fy')) {
    selected =
      benchmarks.parameters
        .filter((p) => /^public_capital_q1_fy\d{4}_\d{2}$/.test(p.id))
        .map((p) => p.id)
        .sort((a, b) => b.localeCompare(a))[0] ?? id;
  }
  return benchmarks.parameters.find((p) => p.id === selected);
}

export function constructionBenchmarkPeriods(benchmarks) {
  const capital = resolveConstructionBenchmark(
    benchmarks,
    'public_capital_q1_fy2026_27',
  );
  const horizon = resolveConstructionBenchmark(
    benchmarks,
    'recruitment_requirement_to2035',
  )?.id.slice(-4);
  const period =
    benchmarks.sources
      .find((s) => s.id === 'BUILDFORCE')
      ?.period.split(';')
      .at(-1) ?? '';
  const years = period.match(/(\d{4}).*?(\d{4})/);
  return {
    fiscalYear: capital
      ? 'FY' + capital.id.replace('public_capital_q1_fy', '').replace('_', '–')
      : 'Not published',
    recruitment:
      years && years[2] === horizon
        ? `${years[1]}–${years[2]}`
        : horizon
          ? `Through ${horizon}`
          : 'Not published',
  };
}
