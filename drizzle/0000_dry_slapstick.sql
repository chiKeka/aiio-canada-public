CREATE TABLE `claim_evidence` (
	`claim_id` text NOT NULL,
	`source_id` text NOT NULL,
	`locator` text NOT NULL,
	`support_type` text NOT NULL,
	`note` text,
	PRIMARY KEY(`claim_id`, `source_id`, `locator`),
	FOREIGN KEY (`claim_id`) REFERENCES `claims`(`id`) ON UPDATE no action ON DELETE no action,
	FOREIGN KEY (`source_id`) REFERENCES `sources`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE INDEX `claim_evidence_source_idx` ON `claim_evidence` (`source_id`);--> statement-breakpoint
CREATE TABLE `claims` (
	`id` text PRIMARY KEY NOT NULL,
	`claim_text` text NOT NULL,
	`claim_type` text NOT NULL,
	`geography_id` text NOT NULL,
	`valid_from` text,
	`valid_to` text,
	`evidence_status` text NOT NULL,
	`confidence` text NOT NULL,
	`review_status` text NOT NULL,
	`reviewer` text,
	`release_id` text,
	`created_at` text NOT NULL,
	FOREIGN KEY (`release_id`) REFERENCES `releases`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE INDEX `claims_type_geo_idx` ON `claims` (`claim_type`,`geography_id`);--> statement-breakpoint
CREATE INDEX `claims_release_idx` ON `claims` (`release_id`);--> statement-breakpoint
CREATE TABLE `digest_editions` (
	`id` text PRIMARY KEY NOT NULL,
	`edition_date` text NOT NULL,
	`title` text NOT NULL,
	`summary` text NOT NULL,
	`status` text NOT NULL,
	`release_id` text,
	`published_at` text,
	`created_at` text NOT NULL,
	FOREIGN KEY (`release_id`) REFERENCES `releases`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE UNIQUE INDEX `digest_editions_date_unique` ON `digest_editions` (`edition_date`);--> statement-breakpoint
CREATE TABLE `digest_items` (
	`id` text PRIMARY KEY NOT NULL,
	`edition_id` text NOT NULL,
	`source_id` text NOT NULL,
	`category` text NOT NULL,
	`headline` text NOT NULL,
	`observed_change` text NOT NULL,
	`model_implication` text NOT NULL,
	`evidence_status` text NOT NULL,
	`sort_order` integer NOT NULL,
	FOREIGN KEY (`edition_id`) REFERENCES `digest_editions`(`id`) ON UPDATE no action ON DELETE no action,
	FOREIGN KEY (`source_id`) REFERENCES `sources`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE INDEX `digest_items_edition_order_idx` ON `digest_items` (`edition_id`,`sort_order`);--> statement-breakpoint
CREATE INDEX `digest_items_category_idx` ON `digest_items` (`category`);--> statement-breakpoint
CREATE TABLE `graph_edges` (
	`id` text NOT NULL,
	`release_id` text NOT NULL,
	`source_node_id` text NOT NULL,
	`target_node_id` text NOT NULL,
	`mechanism` text NOT NULL,
	`sign` integer NOT NULL,
	`weight_low` real NOT NULL,
	`weight_central` real NOT NULL,
	`weight_high` real NOT NULL,
	`lag_periods` integer NOT NULL,
	`absorption` real NOT NULL,
	`geography_id` text NOT NULL,
	`source_id` text,
	`evidence_status` text NOT NULL,
	`confidence` text NOT NULL,
	`metadata_json` text NOT NULL,
	PRIMARY KEY(`id`, `release_id`),
	FOREIGN KEY (`release_id`) REFERENCES `releases`(`id`) ON UPDATE no action ON DELETE no action,
	FOREIGN KEY (`source_id`) REFERENCES `sources`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE INDEX `graph_edges_source_target_idx` ON `graph_edges` (`source_node_id`,`target_node_id`);--> statement-breakpoint
CREATE INDEX `graph_edges_mechanism_idx` ON `graph_edges` (`mechanism`);--> statement-breakpoint
CREATE TABLE `graph_nodes` (
	`id` text NOT NULL,
	`release_id` text NOT NULL,
	`node_type` text NOT NULL,
	`label` text NOT NULL,
	`geography_id` text NOT NULL,
	`unit` text,
	`valid_from` text,
	`valid_to` text,
	`evidence_status` text NOT NULL,
	`source_id` text,
	`metadata_json` text NOT NULL,
	PRIMARY KEY(`id`, `release_id`),
	FOREIGN KEY (`release_id`) REFERENCES `releases`(`id`) ON UPDATE no action ON DELETE no action,
	FOREIGN KEY (`source_id`) REFERENCES `sources`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE INDEX `graph_nodes_type_idx` ON `graph_nodes` (`node_type`);--> statement-breakpoint
CREATE INDEX `graph_nodes_geo_idx` ON `graph_nodes` (`geography_id`);--> statement-breakpoint
CREATE TABLE `model_runs` (
	`id` text PRIMARY KEY NOT NULL,
	`scenario_id` text NOT NULL,
	`release_id` text NOT NULL,
	`random_seed` integer NOT NULL,
	`configuration_hash` text NOT NULL,
	`result_manifest_hash` text NOT NULL,
	`result_path` text NOT NULL,
	`status` text NOT NULL,
	`started_at` text NOT NULL,
	`completed_at` text,
	`validation_json` text NOT NULL,
	FOREIGN KEY (`scenario_id`) REFERENCES `scenarios`(`id`) ON UPDATE no action ON DELETE no action,
	FOREIGN KEY (`release_id`) REFERENCES `releases`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE INDEX `model_runs_scenario_idx` ON `model_runs` (`scenario_id`);--> statement-breakpoint
CREATE INDEX `model_runs_release_idx` ON `model_runs` (`release_id`);--> statement-breakpoint
CREATE TABLE `observations` (
	`id` text PRIMARY KEY NOT NULL,
	`indicator_id` text NOT NULL,
	`value` real NOT NULL,
	`unit` text NOT NULL,
	`geography_id` text NOT NULL,
	`period_start` text NOT NULL,
	`period_end` text NOT NULL,
	`source_id` text NOT NULL,
	`retrieval_id` text,
	`evidence_status` text NOT NULL,
	`transformation_id` text,
	`quality_flags_json` text NOT NULL,
	`release_id` text,
	`created_at` text NOT NULL,
	FOREIGN KEY (`source_id`) REFERENCES `sources`(`id`) ON UPDATE no action ON DELETE no action,
	FOREIGN KEY (`retrieval_id`) REFERENCES `retrievals`(`id`) ON UPDATE no action ON DELETE no action,
	FOREIGN KEY (`release_id`) REFERENCES `releases`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE INDEX `observations_indicator_geo_period_idx` ON `observations` (`indicator_id`,`geography_id`,`period_start`);--> statement-breakpoint
CREATE INDEX `observations_source_idx` ON `observations` (`source_id`);--> statement-breakpoint
CREATE INDEX `observations_release_idx` ON `observations` (`release_id`);--> statement-breakpoint
CREATE TABLE `projects` (
	`id` text PRIMARY KEY NOT NULL,
	`name` text NOT NULL,
	`project_class` text NOT NULL,
	`sector` text NOT NULL,
	`sponsor` text,
	`geography_id` text NOT NULL,
	`municipality` text,
	`latitude` real,
	`longitude` real,
	`announced_capex_cad` real,
	`currency_year` integer,
	`stage` text NOT NULL,
	`stage_probability` real,
	`construction_start` text,
	`construction_end` text,
	`operating_start` text,
	`power_mw` real,
	`source_id` text NOT NULL,
	`evidence_status` text NOT NULL,
	`release_id` text,
	`updated_at` text NOT NULL,
	FOREIGN KEY (`source_id`) REFERENCES `sources`(`id`) ON UPDATE no action ON DELETE no action,
	FOREIGN KEY (`release_id`) REFERENCES `releases`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE INDEX `projects_class_geo_idx` ON `projects` (`project_class`,`geography_id`);--> statement-breakpoint
CREATE INDEX `projects_stage_idx` ON `projects` (`stage`);--> statement-breakpoint
CREATE INDEX `projects_release_idx` ON `projects` (`release_id`);--> statement-breakpoint
CREATE TABLE `releases` (
	`id` text PRIMARY KEY NOT NULL,
	`version` text NOT NULL,
	`schema_version` text NOT NULL,
	`model_version` text NOT NULL,
	`published_at` text,
	`code_commit` text NOT NULL,
	`input_manifest_hash` text NOT NULL,
	`configuration_hash` text NOT NULL,
	`status` text NOT NULL,
	`notes` text,
	`created_at` text NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `releases_version_unique` ON `releases` (`version`);--> statement-breakpoint
CREATE INDEX `releases_status_idx` ON `releases` (`status`);--> statement-breakpoint
CREATE TABLE `retrievals` (
	`id` text PRIMARY KEY NOT NULL,
	`source_id` text NOT NULL,
	`retrieved_at` text NOT NULL,
	`effective_url` text NOT NULL,
	`http_status` integer,
	`content_hash` text NOT NULL,
	`content_type` text,
	`archive_path` text,
	`byte_length` integer,
	`result` text NOT NULL,
	`error_message` text,
	FOREIGN KEY (`source_id`) REFERENCES `sources`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE INDEX `retrievals_source_date_idx` ON `retrievals` (`source_id`,`retrieved_at`);--> statement-breakpoint
CREATE UNIQUE INDEX `retrievals_source_hash_unique` ON `retrievals` (`source_id`,`content_hash`);--> statement-breakpoint
CREATE TABLE `scenarios` (
	`id` text PRIMARY KEY NOT NULL,
	`name` text NOT NULL,
	`description` text NOT NULL,
	`geography_id` text NOT NULL,
	`baseline_release_id` text NOT NULL,
	`investment_total_cad` real NOT NULL,
	`currency_year` integer NOT NULL,
	`start_year` integer NOT NULL,
	`end_year` integer NOT NULL,
	`construction_share` real NOT NULL,
	`local_capture_share` real NOT NULL,
	`parameters_json` text NOT NULL,
	`author` text NOT NULL,
	`status` text NOT NULL,
	`created_at` text NOT NULL,
	FOREIGN KEY (`baseline_release_id`) REFERENCES `releases`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE INDEX `scenarios_geo_idx` ON `scenarios` (`geography_id`);--> statement-breakpoint
CREATE INDEX `scenarios_baseline_idx` ON `scenarios` (`baseline_release_id`);--> statement-breakpoint
CREATE TABLE `sources` (
	`id` text PRIMARY KEY NOT NULL,
	`title` text NOT NULL,
	`publisher` text NOT NULL,
	`canonical_url` text NOT NULL,
	`source_type` text NOT NULL,
	`geography` text NOT NULL,
	`publication_date` text,
	`licence_note` text NOT NULL,
	`access_method` text NOT NULL,
	`update_frequency` text,
	`status` text NOT NULL,
	`created_at` text NOT NULL,
	`updated_at` text NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `sources_url_unique` ON `sources` (`canonical_url`);--> statement-breakpoint
CREATE INDEX `sources_publisher_idx` ON `sources` (`publisher`);--> statement-breakpoint
CREATE INDEX `sources_status_idx` ON `sources` (`status`);