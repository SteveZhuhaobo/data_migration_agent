# Requirements Document

## Introduction

This feature will create an automated dbt SQL generator that uses MCP servers to understand source (SQL Server) and destination (Databricks) schemas, reads mapping configuration files, and automatically generates dbt model SQL scripts for data transformation and migration. The system will analyze schema structures, apply mapping rules, and produce ready-to-use dbt models that can be copied into a dbt project.

## Requirements

### Requirement 1

**User Story:** As a data engineer, I want to define table mappings in a configuration file, so that I can specify how source tables should be transformed and loaded into destination tables.

#### Acceptance Criteria

1. WHEN a mapping configuration file is provided THEN the system SHALL parse table-to-table mappings with source and destination specifications
2. WHEN column mappings are defined THEN the system SHALL support field-level transformations including renaming, type casting, and default values
3. WHEN transformation rules are specified THEN the system SHALL support custom SQL expressions for calculated fields
4. IF no mapping is provided for a column THEN the system SHALL use direct column mapping with same name and compatible type conversion

### Requirement 2

**User Story:** As a data engineer, I want the system to automatically discover source and destination schemas using MCP servers, so that I can validate mappings against actual database structures.

#### Acceptance Criteria

1. WHEN source schema discovery is requested THEN the system SHALL use SQL Server MCP to retrieve table structures, column definitions, and data types
2. WHEN destination schema discovery is requested THEN the system SHALL use Databricks MCP to retrieve catalog, schema, and table information
3. WHEN schema information is retrieved THEN the system SHALL validate that mapped tables and columns exist in both source and destination
4. IF a mapped table or column does not exist THEN the system SHALL report validation errors with specific details

### Requirement 3

**User Story:** As a data engineer, I want the system to generate dbt model SQL scripts automatically, so that I can focus on business logic rather than writing boilerplate transformation code.

#### Acceptance Criteria

1. WHEN a valid mapping configuration is processed THEN the system SHALL generate dbt model SQL files for each destination table
2. WHEN generating SQL THEN the system SHALL include proper SELECT statements with column mappings and transformations
3. WHEN generating SQL THEN the system SHALL include dbt-specific configurations like materialization strategy and schema references
4. WHEN generating SQL THEN the system SHALL handle data type conversions between SQL Server and Databricks formats
5. WHEN custom transformations are specified THEN the system SHALL incorporate SQL expressions into the generated models

### Requirement 4

**User Story:** As a data engineer, I want the generated dbt models to include proper incremental loading logic, so that I can efficiently process only changed data.

#### Acceptance Criteria

1. WHEN incremental loading is configured THEN the system SHALL generate dbt models with incremental materialization
2. WHEN a timestamp column is specified THEN the system SHALL include proper incremental logic using the timestamp field
3. WHEN a primary key is defined THEN the system SHALL generate appropriate unique key configurations for upsert operations
4. IF no incremental configuration is provided THEN the system SHALL default to full table refresh materialization

### Requirement 5

**User Story:** As a data engineer, I want the system to generate dbt project structure and configuration files, so that I have a complete dbt project ready for deployment.

#### Acceptance Criteria

1. WHEN dbt project generation is requested THEN the system SHALL create proper dbt_project.yml configuration
2. WHEN models are generated THEN the system SHALL create appropriate directory structure following dbt conventions
3. WHEN source tables are referenced THEN the system SHALL generate sources.yml files with proper source definitions
4. WHEN schema tests are configured THEN the system SHALL include basic data quality tests in the generated models

### Requirement 6

**User Story:** As a data engineer, I want to validate generated SQL before copying to dbt, so that I can ensure the transformations will work correctly.

#### Acceptance Criteria

1. WHEN SQL is generated THEN the system SHALL provide syntax validation for Databricks SQL dialect
2. WHEN validation is performed THEN the system SHALL check that all referenced columns exist in source tables
3. WHEN data type conversions are applied THEN the system SHALL validate compatibility between source and destination types
4. IF validation errors are found THEN the system SHALL provide detailed error messages with suggested fixes

### Requirement 7

**User Story:** As a data engineer, I want to preview generated SQL and see execution plans, so that I can understand what transformations will be applied.

#### Acceptance Criteria

1. WHEN SQL generation is complete THEN the system SHALL provide a preview of all generated dbt models
2. WHEN preview is requested THEN the system SHALL show source-to-destination column mappings clearly
3. WHEN transformations are applied THEN the system SHALL highlight custom logic and calculated fields
4. WHEN requested THEN the system SHALL provide estimated row counts and data volume information using MCP server queries