import {
  index,
  integer,
  primaryKey,
  real,
  sqliteTable,
  text,
  uniqueIndex,
} from 'drizzle-orm/sqlite-core';

export const releases = sqliteTable(
  'releases',
  {
    id: text('id').primaryKey(),
    version: text('version').notNull(),
    schemaVersion: text('schema_version').notNull(),
    modelVersion: text('model_version').notNull(),
    publishedAt: text('published_at'),
    codeCommit: text('code_commit').notNull(),
    inputManifestHash: text('input_manifest_hash').notNull(),
    configurationHash: text('configuration_hash').notNull(),
    status: text('status', { enum: ['draft', 'review', 'published', 'superseded'] }).notNull(),
    notes: text('notes'),
    createdAt: text('created_at').notNull(),
  },
  (table) => [
    uniqueIndex('releases_version_unique').on(table.version),
    index('releases_status_idx').on(table.status),
  ],
);

export const sources = sqliteTable(
  'sources',
  {
    id: text('id').primaryKey(),
    title: text('title').notNull(),
    publisher: text('publisher').notNull(),
    canonicalUrl: text('canonical_url').notNull(),
    sourceType: text('source_type').notNull(),
    geography: text('geography').notNull(),
    publicationDate: text('publication_date'),
    licenceNote: text('licence_note').notNull(),
    accessMethod: text('access_method').notNull(),
    updateFrequency: text('update_frequency'),
    status: text('status', { enum: ['candidate', 'active', 'paused', 'retired'] }).notNull(),
    createdAt: text('created_at').notNull(),
    updatedAt: text('updated_at').notNull(),
  },
  (table) => [
    uniqueIndex('sources_url_unique').on(table.canonicalUrl),
    index('sources_publisher_idx').on(table.publisher),
    index('sources_status_idx').on(table.status),
  ],
);

export const retrievals = sqliteTable(
  'retrievals',
  {
    id: text('id').primaryKey(),
    sourceId: text('source_id').notNull().references(() => sources.id),
    retrievedAt: text('retrieved_at').notNull(),
    effectiveUrl: text('effective_url').notNull(),
    httpStatus: integer('http_status'),
    contentHash: text('content_hash').notNull(),
    contentType: text('content_type'),
    archivePath: text('archive_path'),
    byteLength: integer('byte_length'),
    result: text('result', { enum: ['success', 'not_modified', 'failed'] }).notNull(),
    errorMessage: text('error_message'),
  },
  (table) => [
    index('retrievals_source_date_idx').on(table.sourceId, table.retrievedAt),
    uniqueIndex('retrievals_source_hash_unique').on(table.sourceId, table.contentHash),
  ],
);

export const observations = sqliteTable(
  'observations',
  {
    id: text('id').primaryKey(),
    indicatorId: text('indicator_id').notNull(),
    value: real('value').notNull(),
    unit: text('unit').notNull(),
    geographyId: text('geography_id').notNull(),
    periodStart: text('period_start').notNull(),
    periodEnd: text('period_end').notNull(),
    sourceId: text('source_id').notNull().references(() => sources.id),
    retrievalId: text('retrieval_id').references(() => retrievals.id),
    evidenceStatus: text('evidence_status', {
      enum: ['observed', 'corroborated', 'inferred', 'assumed', 'scenario'],
    }).notNull(),
    transformationId: text('transformation_id'),
    qualityFlagsJson: text('quality_flags_json').notNull(),
    releaseId: text('release_id').references(() => releases.id),
    createdAt: text('created_at').notNull(),
  },
  (table) => [
    index('observations_indicator_geo_period_idx').on(
      table.indicatorId,
      table.geographyId,
      table.periodStart,
    ),
    index('observations_source_idx').on(table.sourceId),
    index('observations_release_idx').on(table.releaseId),
  ],
);

export const projects = sqliteTable(
  'projects',
  {
    id: text('id').primaryKey(),
    name: text('name').notNull(),
    projectClass: text('project_class').notNull(),
    sector: text('sector').notNull(),
    sponsor: text('sponsor'),
    geographyId: text('geography_id').notNull(),
    municipality: text('municipality'),
    latitude: real('latitude'),
    longitude: real('longitude'),
    announcedCapexCad: real('announced_capex_cad'),
    currencyYear: integer('currency_year'),
    stage: text('stage').notNull(),
    stageProbability: real('stage_probability'),
    constructionStart: text('construction_start'),
    constructionEnd: text('construction_end'),
    operatingStart: text('operating_start'),
    powerMw: real('power_mw'),
    sourceId: text('source_id').notNull().references(() => sources.id),
    evidenceStatus: text('evidence_status', {
      enum: ['observed', 'corroborated', 'inferred', 'assumed', 'scenario'],
    }).notNull(),
    releaseId: text('release_id').references(() => releases.id),
    updatedAt: text('updated_at').notNull(),
  },
  (table) => [
    index('projects_class_geo_idx').on(table.projectClass, table.geographyId),
    index('projects_stage_idx').on(table.stage),
    index('projects_release_idx').on(table.releaseId),
  ],
);

export const claims = sqliteTable(
  'claims',
  {
    id: text('id').primaryKey(),
    claimText: text('claim_text').notNull(),
    claimType: text('claim_type').notNull(),
    geographyId: text('geography_id').notNull(),
    validFrom: text('valid_from'),
    validTo: text('valid_to'),
    evidenceStatus: text('evidence_status', {
      enum: ['observed', 'corroborated', 'inferred', 'assumed', 'scenario'],
    }).notNull(),
    confidence: text('confidence', { enum: ['low', 'medium', 'high'] }).notNull(),
    reviewStatus: text('review_status', { enum: ['draft', 'reviewed', 'published', 'withdrawn'] }).notNull(),
    reviewer: text('reviewer'),
    releaseId: text('release_id').references(() => releases.id),
    createdAt: text('created_at').notNull(),
  },
  (table) => [
    index('claims_type_geo_idx').on(table.claimType, table.geographyId),
    index('claims_release_idx').on(table.releaseId),
  ],
);

export const claimEvidence = sqliteTable(
  'claim_evidence',
  {
    claimId: text('claim_id').notNull().references(() => claims.id),
    sourceId: text('source_id').notNull().references(() => sources.id),
    locator: text('locator').notNull(),
    supportType: text('support_type', { enum: ['supports', 'qualifies', 'contradicts'] }).notNull(),
    note: text('note'),
  },
  (table) => [
    primaryKey({ columns: [table.claimId, table.sourceId, table.locator] }),
    index('claim_evidence_source_idx').on(table.sourceId),
  ],
);

export const graphNodes = sqliteTable(
  'graph_nodes',
  {
    id: text('id').notNull(),
    releaseId: text('release_id').notNull().references(() => releases.id),
    nodeType: text('node_type').notNull(),
    label: text('label').notNull(),
    geographyId: text('geography_id').notNull(),
    unit: text('unit'),
    validFrom: text('valid_from'),
    validTo: text('valid_to'),
    evidenceStatus: text('evidence_status', {
      enum: ['observed', 'corroborated', 'inferred', 'assumed', 'scenario'],
    }).notNull(),
    sourceId: text('source_id').references(() => sources.id),
    metadataJson: text('metadata_json').notNull(),
  },
  (table) => [
    primaryKey({ columns: [table.id, table.releaseId] }),
    index('graph_nodes_type_idx').on(table.nodeType),
    index('graph_nodes_geo_idx').on(table.geographyId),
  ],
);

export const graphEdges = sqliteTable(
  'graph_edges',
  {
    id: text('id').notNull(),
    releaseId: text('release_id').notNull().references(() => releases.id),
    sourceNodeId: text('source_node_id').notNull(),
    targetNodeId: text('target_node_id').notNull(),
    mechanism: text('mechanism').notNull(),
    sign: integer('sign').notNull(),
    weightLow: real('weight_low').notNull(),
    weightCentral: real('weight_central').notNull(),
    weightHigh: real('weight_high').notNull(),
    lagPeriods: integer('lag_periods').notNull(),
    absorption: real('absorption').notNull(),
    geographyId: text('geography_id').notNull(),
    sourceId: text('source_id').references(() => sources.id),
    evidenceStatus: text('evidence_status', {
      enum: ['observed', 'corroborated', 'inferred', 'assumed', 'scenario'],
    }).notNull(),
    confidence: text('confidence', { enum: ['low', 'medium', 'high'] }).notNull(),
    metadataJson: text('metadata_json').notNull(),
  },
  (table) => [
    primaryKey({ columns: [table.id, table.releaseId] }),
    index('graph_edges_source_target_idx').on(table.sourceNodeId, table.targetNodeId),
    index('graph_edges_mechanism_idx').on(table.mechanism),
  ],
);

export const scenarios = sqliteTable(
  'scenarios',
  {
    id: text('id').primaryKey(),
    name: text('name').notNull(),
    description: text('description').notNull(),
    geographyId: text('geography_id').notNull(),
    baselineReleaseId: text('baseline_release_id').notNull().references(() => releases.id),
    investmentTotalCad: real('investment_total_cad').notNull(),
    currencyYear: integer('currency_year').notNull(),
    startYear: integer('start_year').notNull(),
    endYear: integer('end_year').notNull(),
    constructionShare: real('construction_share').notNull(),
    localCaptureShare: real('local_capture_share').notNull(),
    parametersJson: text('parameters_json').notNull(),
    author: text('author').notNull(),
    status: text('status', { enum: ['draft', 'review', 'published', 'retired'] }).notNull(),
    createdAt: text('created_at').notNull(),
  },
  (table) => [
    index('scenarios_geo_idx').on(table.geographyId),
    index('scenarios_baseline_idx').on(table.baselineReleaseId),
  ],
);

export const modelRuns = sqliteTable(
  'model_runs',
  {
    id: text('id').primaryKey(),
    scenarioId: text('scenario_id').notNull().references(() => scenarios.id),
    releaseId: text('release_id').notNull().references(() => releases.id),
    randomSeed: integer('random_seed').notNull(),
    configurationHash: text('configuration_hash').notNull(),
    resultManifestHash: text('result_manifest_hash').notNull(),
    resultPath: text('result_path').notNull(),
    status: text('status', { enum: ['queued', 'running', 'passed', 'failed'] }).notNull(),
    startedAt: text('started_at').notNull(),
    completedAt: text('completed_at'),
    validationJson: text('validation_json').notNull(),
  },
  (table) => [
    index('model_runs_scenario_idx').on(table.scenarioId),
    index('model_runs_release_idx').on(table.releaseId),
  ],
);

export const digestEditions = sqliteTable(
  'digest_editions',
  {
    id: text('id').primaryKey(),
    editionDate: text('edition_date').notNull(),
    title: text('title').notNull(),
    summary: text('summary').notNull(),
    status: text('status', { enum: ['draft', 'review', 'published'] }).notNull(),
    releaseId: text('release_id').references(() => releases.id),
    publishedAt: text('published_at'),
    createdAt: text('created_at').notNull(),
  },
  (table) => [uniqueIndex('digest_editions_date_unique').on(table.editionDate)],
);

export const digestItems = sqliteTable(
  'digest_items',
  {
    id: text('id').primaryKey(),
    editionId: text('edition_id').notNull().references(() => digestEditions.id),
    sourceId: text('source_id').notNull().references(() => sources.id),
    category: text('category').notNull(),
    headline: text('headline').notNull(),
    observedChange: text('observed_change').notNull(),
    modelImplication: text('model_implication').notNull(),
    evidenceStatus: text('evidence_status', {
      enum: ['observed', 'corroborated', 'inferred', 'assumed', 'scenario'],
    }).notNull(),
    sortOrder: integer('sort_order').notNull(),
  },
  (table) => [
    index('digest_items_edition_order_idx').on(table.editionId, table.sortOrder),
    index('digest_items_category_idx').on(table.category),
  ],
);
