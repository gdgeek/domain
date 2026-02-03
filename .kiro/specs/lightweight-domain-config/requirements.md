# Requirements Document

## Introduction

本文档定义了轻量级域名配置服务的需求。该服务采用极简的两表设计（domains + configs），通过 `域名 + 语言` 映射到对应的配置，实现多语言支持。

**核心理念**：用户设置了就用，不设置也可以正常运行。

## Glossary

- **Domain**: 域名，系统管理的网站域名（如 example.com）
- **Config**: 配置，与域名和语言关联的配置数据
- **Language**: 语言代码，支持 zh-CN（默认）、en、ja、zh-TW、th
- **Fallback**: 回退，当请求的语言配置不存在时，返回默认语言（zh-CN）的配置

## Requirements

### Requirement 1: 域名管理

**User Story:** 作为管理员，我希望能够管理域名，以便维护系统中的域名列表。

#### Acceptance Criteria

1.1 THE System SHALL provide an API endpoint to create a new domain with a unique domain name
1.2 WHEN a domain is created, THE System SHALL validate that the domain name is not empty
1.3 THE System SHALL provide an API endpoint to retrieve a list of all domains
1.4 THE System SHALL provide an API endpoint to retrieve a specific domain by its identifier
1.5 THE System SHALL provide an API endpoint to update an existing domain's information
1.6 THE System SHALL provide an API endpoint to delete a domain
1.7 WHEN a domain is deleted, THE System SHALL also delete all configs associated with that domain (CASCADE)

### Requirement 2: 配置管理（含多语言）

**User Story:** 作为管理员，我希望能够为域名创建不同语言的配置，以便支持多语言内容。

#### Acceptance Criteria

2.1 THE System SHALL store configs with domain_id and language fields
2.2 THE System SHALL enforce unique constraint on (domain_id, language) combination
2.3 THE System SHALL use zh-CN as the default language
2.4 THE System SHALL provide an API endpoint to create a config for a domain in a specific language
2.5 THE System SHALL provide an API endpoint to update a config for a domain in a specific language
2.6 THE System SHALL provide an API endpoint to delete a config for a domain in a specific language
2.7 THE System SHALL provide an API endpoint to retrieve all configs for a domain (all languages)
2.8 THE System SHALL store config data as JSONB (title, description, keywords, links, etc.)

### Requirement 3: 配置查询（语言回退）

**User Story:** 作为应用程序，我希望通过域名和语言查询配置，如果指定语言不存在则返回默认语言配置。

#### Acceptance Criteria

3.1 THE System SHALL provide an API endpoint to query config by domain name and optional language parameter
3.2 WHEN language parameter is provided, THE System SHALL first try to find config in that language
3.3 WHEN requested language config does not exist, THE System SHALL fallback to default language (zh-CN) config
3.4 WHEN neither requested language nor default language config exists, THE System SHALL return 404
3.5 THE System SHALL return config data in JSON format
3.6 THE System SHALL include the actual language returned in the response (for fallback awareness)

### Requirement 4: 数据持久化

**User Story:** 作为系统，我需要持久化存储数据，以便在服务重启后数据不丢失。

#### Acceptance Criteria

4.1 THE System SHALL use PostgreSQL to store data
4.2 THE System SHALL use a two-table schema: domains and configs
4.3 THE System SHALL implement a one-to-many relationship: one domain has many configs (different languages)
4.4 THE System SHALL enforce foreign key constraint: configs.domain_id references domains.id
4.5 THE System SHALL enforce unique constraint on configs (domain_id, language)

### Requirement 5: Redis缓存（可选）

**User Story:** 作为系统，我希望使用缓存来提高查询性能。

#### Acceptance Criteria

5.1 THE System SHALL support Redis as an optional caching layer
5.2 THE System SHALL work normally without Redis (graceful degradation)
5.3 WHEN Redis is available, THE System SHALL cache query results with key format: `domain:{name}:lang:{language}`
5.4 WHEN a config is created, updated, or deleted, THE System SHALL invalidate related cache entries
5.5 THE System SHALL set cache TTL to 1 hour (3600 seconds)

### Requirement 6: Web管理界面

**User Story:** 作为管理员，我希望有一个简单的Web界面来管理域名和配置。

#### Acceptance Criteria

6.1 THE Admin_Interface SHALL provide a page to list all domains
6.2 THE Admin_Interface SHALL provide forms to create, update, and delete domains
6.3 THE Admin_Interface SHALL provide an interface to manage configs for each domain
6.4 THE Admin_Interface SHALL allow selecting language when creating/editing configs
6.5 THE Admin_Interface SHALL display which languages have configs for each domain
6.6 THE Admin_Interface SHALL display validation errors clearly
6.7 THE Admin_Interface SHALL use simple HTML/CSS without complex JavaScript frameworks

### Requirement 7: 错误处理

**User Story:** 作为开发者，我希望系统能够优雅地处理错误。

#### Acceptance Criteria

7.1 WHEN validation fails, THE System SHALL return 400 status code with error details
7.2 WHEN resource not found, THE System SHALL return 404 status code
7.3 WHEN duplicate entry, THE System SHALL return 409 status code
7.4 WHEN server error, THE System SHALL return 500 status code and log the error
7.5 THE System SHALL return errors in consistent JSON format: `{"error": {"code": "...", "message": "..."}}`

### Requirement 8: API文档

**User Story:** 作为开发者，我希望有API文档来了解如何使用接口。

#### Acceptance Criteria

8.1 THE System SHALL provide Swagger/OpenAPI documentation
8.2 THE Swagger documentation SHALL be accessible at /api/docs
8.3 THE Swagger documentation SHALL include all endpoints with descriptions and examples

### Requirement 9: 简化架构

**User Story:** 作为开发者，我希望系统架构简单易维护。

#### Acceptance Criteria

9.1 THE System SHALL NOT implement authentication (all endpoints are public)
9.2 THE System SHALL NOT implement rate limiting
9.3 THE System SHALL NOT implement monitoring (no Prometheus)
9.4 THE System SHALL use Python + Flask for simplicity
9.5 THE System SHALL minimize dependencies
9.6 THE System SHALL support zero-config startup (sensible defaults)
