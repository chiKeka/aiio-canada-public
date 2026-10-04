import graphData from '@/data/model/alberta_graph_v0.2.json';
import releaseData from '@/public/data/latest.json';

export type AssetId = keyof typeof ASSETS;
export type MetroId = keyof typeof METROS;

export const ASSETS = {
  hospital: {
    label: 'Hospital or health facility', archetype: 'institutional_buildings',
    outcome: 'SCHEDULE_HOSPITALS_DELAY_PRESSURE', proxy: 'Institutional buildings [62213]', publicAssetClass: 'health_facilities',
    profileNote: 'The current release has the same four component series for institutional buildings and schools. Asset selection changes the graph outcome, not this proxy profile.',
  },
  school: {
    label: 'School', archetype: 'schools', outcome: 'SCHEDULE_SCHOOLS_DELAY_PRESSURE', proxy: 'School', publicAssetClass: 'schools_and_postsecondary',
    profileNote: 'The current release has the same four component series for schools and institutional buildings. Asset selection changes the graph outcome, not this proxy profile.',
  },
  government: {
    label: 'Government facility', archetype: 'institutional_buildings', outcome: 'SCHEDULE_GOVERNMENT_DELAY_PRESSURE', proxy: 'Institutional buildings [62213]', publicAssetClass: 'government_and_civic_facilities',
    profileNote: 'The current release has the same four component series for institutional buildings and schools. Asset selection changes the graph outcome, not this proxy profile.',
  },
  municipal: {
    label: 'Municipal facility', archetype: 'municipal_operations_bus_depot', outcome: 'SCHEDULE_ROADS_MUNICIPAL_DELAY_PRESSURE', proxy: 'Bus depot with maintenance and repair facilities', publicAssetClass: 'municipal_water_and_resilience',
    profileNote: 'This model-building proxy does not represent the full mix of municipal civil, water or resilience work.',
  },
  road: {
    label: 'Road or civil project', archetype: 'municipal_operations_bus_depot', outcome: 'SCHEDULE_ROADS_MUNICIPAL_DELAY_PRESSURE', proxy: 'Bus-depot building proxy — limited civil fit', publicAssetClass: 'roads_transit_and_airports',
    profileNote: 'This is a building-price proxy with limited fit for road and civil work. It must not be read as a road-construction index.',
  },
  utility: {
    label: 'Regulated utility project', archetype: 'industrial_factory_proxy', outcome: 'SCHEDULE_UTILITIES_DELAY_PRESSURE', proxy: 'Factory building proxy — utility equipment excluded', publicAssetClass: 'power_sector_infrastructure',
    profileNote: 'This proxy excludes utility-specific equipment and must not be read as a transmission, distribution or generation cost index.',
  },
} as const;

export const METROS = {
  OTHER: 'Other / unknown region', CMA_825: 'Calgary region', CMA_835: 'Edmonton region' } as const;

const GRAPH_TO_LABOUR_ID: Record<string, string> = {
  TRADE_CONCRETE: 'trade_concrete', TRADE_ELECTRICIANS: 'trade_electricians',
  TRADE_HVAC: 'trade_hvac', TRADE_POWERLINE: 'trade_power_line',
};

export function boundedDisplayScore(rawScore: number) {
  return rawScore / (1 + rawScore);
}

export function buildDecisionAnalysis({ assetId, duration, metroId, startYear }: {
  assetId: AssetId; duration: number; metroId: MetroId; startYear: number;
}) {
  const asset = ASSETS[assetId];
  const endYear = startYear + duration - 1;
  const scenarioYears = releaseData.scenario.annual_flows.map((item) => item.year);
  const scenarioWindowYears = scenarioYears.filter((year) => year >= startYear && year <= endYear);
  const dominantPaths = releaseData.scenario.dominant_outcome_paths.filter(
    (path) => path.target_node_id === asset.outcome && path.calendar_year >= startYear && path.calendar_year <= endYear,
  );
  const dominantPathYears = Array.from(new Set(dominantPaths.map((path) => path.calendar_year).filter((year) => year >= startYear && year <= endYear))).sort((a, b) => a - b);
  const directEdges = graphData.edges.filter((edge) => edge.target === asset.outcome).sort((a, b) => b.weight_central - a.weight_central);
  const dominantNodeId = dominantPaths[0]?.node_path[1] ?? directEdges[0]?.source;
  const dominantNode = graphData.nodes.find((node) => node.node_id === dominantNodeId);
  const targetLabel = graphData.nodes.find((node) => node.node_id === asset.outcome)?.label ?? asset.label;
  const leadingPath = dominantPaths[0]
    ? dominantPaths[0].node_path.map((nodeId) => graphData.nodes.find((node) => node.node_id === nodeId)?.label ?? nodeId).join(' → ')
    : directEdges[0] ? `${dominantNode?.label ?? directEdges[0].source} → ${targetLabel}` : 'No declared direct path';
  const materials = releaseData.material_cost_screen.observations
    .filter((item) => item.geography_id === metroId && item.archetype === asset.archetype)
    .sort((a, b) => Math.abs(b.year_over_year_percent_change) - Math.abs(a.year_over_year_percent_change));
  const compositeIndicator = assetId === 'school' ? 'BCPI_SCHOOL_DIVISION_COMPOSITE' : 'BCPI_NON_RESIDENTIAL_BUILDINGS_622_DIVISION_COMPOSITE';
  const marketComposite = releaseData.baseline.construction_prices.find((item) => item.geography_id === metroId && item.indicator_id === compositeIndicator);
  const relevantGraphTradeIds = Array.from(new Set(directEdges.map((edge) => GRAPH_TO_LABOUR_ID[edge.source]).filter((value): value is string => Boolean(value))));
  const labourRows = releaseData.labour_pressure.trade_diagnostics.filter((item) => item.geography_id === 'PR_48' && relevantGraphTradeIds.includes(item.trade_node_id));
  const concurrentProjects = releaseData.public_project_exposure.projects.filter((project) =>
    project.asset_class === asset.publicAssetClass && project.start_year !== null && project.end_year !== null && project.start_year <= endYear && project.end_year >= startYear,
  );
  const publicAssetSummary = releaseData.public_project_exposure.asset_class_summaries.find((item) => item.asset_class === asset.publicAssetClass);
  return {
    analysisDate: releaseData.baseline.as_of_date, asset, concurrentProjectCount: concurrentProjects.length,
    directEdges, dominantNode, dominantPathYears, dominantPaths, endYear, labourRows, leadingPath,
    labourDates: { vacancy: releaseData.labour_pressure.vacancy_period_end, workforce: releaseData.labour_pressure.workforce_period_end },
    marketComposite, materials, metroId, powerEvidence: releaseData.power_evidence, publicAssetSummary,
    scenarioId: releaseData.scenario.scenario_id, startYear, scenarioWindowEnd: Math.max(...scenarioYears),
    scenarioWindowStart: Math.min(...scenarioYears), scenarioWindowYears,
    sourceIds: [releaseData.material_cost_screen.source_id, releaseData.labour_pressure.vacancy_source_id,
      releaseData.labour_pressure.workforce_source_id, releaseData.public_project_exposure.source_id,
      'AESO_DATA_CENTRE_UPDATE_2025_09', 'AESO_LARGE_LOAD_PROJECTS',
      'AESO_INTERIM_LARGE_LOAD_2025_06'],
  };
}
