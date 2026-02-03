# Technical Design Document

## Introduction

本文档描述轻量级域名配置服务的技术设计。该服务采用极简的两表架构（domains + configs），通过 `域名 + 语言` 映射到对应的配置。使用 Python + Flask 作为后端框架，PostgreSQL 作为数据库，Redis 作为可选缓存层。

**核心设计理念**：用户设置了就用，不设置也可以正常运行。

## Architecture Overview

### 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Layer                           │
│  ┌─────────────────┐  ┌─────────────────────────────────┐  │
│  │  Web Browser    │  │  External Applications (API)    │  │
│  │  (Admin UI)     │  │                                 │  │
│  └────────┬────────┘  └────────────────┬────────────────┘  │
└───────────┼────────────────────────────┼────────────────────┘
            │                            │
            ▼                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 Flask Application                    │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │   │
│  │  │ API Routes  │  │ Web Routes  │  │ Swagger UI  │  │   │
│  │  │ /api/*      │  │ /admin/*    │  │ /api/docs   │  │   │
│  │  └──────┬──────┘  └──────┬──────┘  └─────────────┘  │   │
│  │         │                │                          │   │
│  │         ▼                ▼                          │   │
│  │  ┌─────────────────────────────────────────────┐   │   │
│  │  │              Service Layer                   │   │   │
│  │  │  ┌─────────────────┐  ┌─────────────────┐   │   │   │
│  │  │  │  Domain Service │  │  Config Service │   │   │   │
│  │  │  └────────┬────────┘  └────────┬────────┘   │   │   │
│  │  └───────────┼────────────────────┼────────────┘   │   │
│  └──────────────┼────────────────────┼────────────────┘   │
└─────────────────┼────────────────────┼────────────────────┘
                  │                    │
                  ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                      Data Layer                             │
│  ┌─────────────────────┐  ┌─────────────────────────────┐  │
│  │     PostgreSQL      │  │     Redis (Optional)        │  │
│  │  ┌───────────────┐  │  │  ┌───────────────────────┐  │  │
│  │  │   domains     │  │  │  │  domain:{name}:       │  │  │
│  │  ├───────────────┤  │  │  │  lang:{language}      │  │  │
│  │  │   configs     │  │  │  │  TTL: 3600s           │  │  │
│  │  │ (with lang)   │  │  │  └───────────────────────┘  │  │
│  │  └───────────────┘  │  │                             │  │
│  └─────────────────────┘  └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 技术栈

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| 后端框架 | Flask 3.x | 轻量级 Python Web 框架 |
| 数据库 | PostgreSQL 15+ | 关系型数据库，支持 JSONB |
| 缓存 | Redis 7+ | 可选，用于提高查询性能 |
| ORM | SQLAlchemy 2.x | 数据库抽象层 |
| API文档 | Flask-RESTX | 自动生成 Swagger 文档 |
| 模板引擎 | Jinja2 | Flask 内置模板引擎 |
| 数据验证 | Marshmallow | 序列化和验证 |

## Data Models

### 数据库 Schema（两表设计）

```sql
-- 域名表
CREATE TABLE domains (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 配置表（包含语言字段）
CREATE TABLE configs (
    id SERIAL PRIMARY KEY,
    domain_id INTEGER NOT NULL REFERENCES domains(id) ON DELETE CASCADE,
    language VARCHAR(10) NOT NULL DEFAULT 'zh-CN',
    data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(domain_id, language)  -- 每个域名每种语言只能有一个配置
);

-- 索引
CREATE INDEX idx_domains_name ON domains(name);
CREATE INDEX idx_domains_active ON domains(is_active);
CREATE INDEX idx_configs_domain ON configs(domain_id);
CREATE INDEX idx_configs_language ON configs(language);
CREATE INDEX idx_configs_domain_language ON configs(domain_id, language);
```

### 实体关系图

```
┌─────────────────┐           ┌─────────────────────────┐
│     domains     │           │        configs          │
├─────────────────┤           ├─────────────────────────┤
│ id (PK)         │──────┐    │ id (PK)                 │
│ name (UNIQUE)   │      │    │ domain_id (FK)          │◀─┐
│ description     │      └───▶│ language (zh-CN, en...) │  │
│ is_active       │      1:N  │ data (JSONB)            │  │
│ created_at      │           │ created_at              │  │
│ updated_at      │           │ updated_at              │  │
└─────────────────┘           └─────────────────────────┘  │
                                                           │
                              UNIQUE(domain_id, language)──┘
```

### 配置数据结构示例

```json
{
  "title": "网站标题",
  "description": "网站描述",
  "keywords": ["关键词1", "关键词2"],
  "logo": "/images/logo.png",
  "theme": {
    "primaryColor": "#1890ff",
    "darkMode": false
  },
  "links": [
    {"name": "首页", "url": "/"},
    {"name": "关于", "url": "/about"}
  ],
  "custom": {}
}
```

### 查询逻辑（语言回退）

```
请求: GET /api/query?domain=example.com&lang=en

1. 查找域名 example.com
2. 查找该域名的 en 语言配置
3. 如果 en 配置不存在，回退到 zh-CN 配置
4. 如果 zh-CN 也不存在，返回空结果或 404
5. 返回配置数据，并标注实际返回的语言
```

## Components and Interfaces

### 1. 数据访问层 (Repository Layer)

#### Domain Repository
```python
class DomainRepository:
    def create(name: str, description: str = None) -> Domain
    def get_by_id(domain_id: int) -> Optional[Domain]
    def get_by_name(name: str) -> Optional[Domain]
    def get_all() -> List[Domain]
    def update(domain_id: int, name: str = None, description: str = None) -> Domain
    def delete(domain_id: int) -> bool
```

#### Config Repository
```python
class ConfigRepository:
    def create(domain_id: int, language: str, data: dict) -> Config
    def get_by_id(config_id: int) -> Optional[Config]
    def get_by_domain_and_language(domain_id: int, language: str) -> Optional[Config]
    def get_all_by_domain(domain_id: int) -> List[Config]
    def update(config_id: int, data: dict) -> Config
    def delete(config_id: int) -> bool
    def delete_by_domain_and_language(domain_id: int, language: str) -> bool
```

### 2. 缓存层 (Cache Layer)

#### Cache Service
```python
class CacheService:
    def get(domain_name: str, language: str) -> Optional[dict]
    def set(domain_name: str, language: str, data: dict, ttl: int = 3600) -> bool
    def invalidate(domain_name: str, language: str = None) -> bool
    def invalidate_all() -> bool
```

缓存键命名规范：
- `domain:{name}:lang:{language}` - 域名+语言配置缓存
- TTL: 3600秒（1小时）

缓存失效策略：
- 当配置被创建/修改/删除时，失效对应的缓存
- 当域名被删除时，失效该域名所有语言的缓存

### 3. 业务逻辑层 (Service Layer)

#### Domain Service
```python
class DomainService:
    def create_domain(name: str, description: str = None) -> Domain
    def get_domain(domain_id: int) -> Domain
    def get_domain_by_name(name: str) -> Domain
    def list_domains() -> List[Domain]
    def update_domain(domain_id: int, name: str = None, description: str = None) -> Domain
    def delete_domain(domain_id: int) -> bool
```

#### Config Service
```python
class ConfigService:
    def create_config(domain_id: int, language: str, data: dict) -> Config
    def get_config(domain_id: int, language: str) -> Config
    def get_config_with_fallback(domain_name: str, language: str) -> dict
    def list_configs_by_domain(domain_id: int) -> List[Config]
    def update_config(domain_id: int, language: str, data: dict) -> Config
    def delete_config(domain_id: int, language: str) -> bool
```

### 4. API层 (API Layer)

#### REST API Endpoints

**Domain Endpoints**:
- `POST /api/domains` - 创建域名
- `GET /api/domains` - 获取所有域名
- `GET /api/domains/{id}` - 获取指定域名
- `PUT /api/domains/{id}` - 更新域名
- `DELETE /api/domains/{id}` - 删除域名

**Config Endpoints**:
- `POST /api/domains/{id}/configs` - 为域名创建配置（指定语言）
- `GET /api/domains/{id}/configs` - 获取域名的所有配置（所有语言）
- `GET /api/domains/{id}/configs/{language}` - 获取域名指定语言的配置
- `PUT /api/domains/{id}/configs/{language}` - 更新域名指定语言的配置
- `DELETE /api/domains/{id}/configs/{language}` - 删除域名指定语言的配置

**Query Endpoint**:
- `GET /api/query?domain={domain_name}&lang={language}` - 查询域名配置（支持语言回退）

### 5. Web管理界面 (Admin Interface)

#### 页面结构
- `/admin/` - 首页（域名列表）
- `/admin/domains` - 域名管理
- `/admin/domains/new` - 创建域名
- `/admin/domains/{id}/edit` - 编辑域名
- `/admin/domains/{id}/configs` - 域名配置管理（多语言）
- `/admin/domains/{id}/configs/{language}/edit` - 编辑指定语言配置

## Correctness Properties

### Property 1: Domain CRUD Round-Trip Consistency
*For any* valid domain name, creating a domain, retrieving it by ID, updating it, and retrieving it again should return the updated domain with all changes preserved.
**Validates: Requirements 1.1, 1.4, 1.5**

### Property 2: Domain Name Validation
*For any* string that is empty or does not follow basic domain format rules, attempting to create a domain should be rejected with a validation error.
**Validates: Requirements 1.2**

### Property 3: Domain Deletion Cascade
*For any* domain with associated configs, deleting the domain should also delete all configs for that domain (CASCADE).
**Validates: Requirements 1.6, 1.7**

### Property 4: Domain List Completeness
*For any* set of created domains, querying the domain list should return all created domains and no others.
**Validates: Requirements 1.3**

### Property 5: Config Language Uniqueness
*For any* domain, attempting to create two configs with the same language should fail with a duplicate error.
**Validates: Requirements 2.2**

### Property 6: Config CRUD Round-Trip Consistency
*For any* valid domain and language, creating a config, retrieving it, updating it, and retrieving it again should return the updated config.
**Validates: Requirements 2.4, 2.5, 2.6**

### Property 7: Language Fallback
*For any* domain with only zh-CN config, querying with any other language should return the zh-CN config.
**Validates: Requirements 3.2, 3.3**

### Property 8: Query Response Language Indicator
*For any* query that falls back to default language, the response should indicate the actual language returned.
**Validates: Requirements 3.6**

### Property 9: Cache Invalidation on Update
*For any* config that is updated or deleted, the next query should return fresh data, not stale cached data.
**Validates: Requirements 5.4**

### Property 10: HTTP Error Status Codes
*For any* API request with validation errors (400), non-existent resources (404), or duplicate entries (409), the response should have the correct status code and consistent JSON error format.
**Validates: Requirements 7.1, 7.2, 7.3, 7.5**

## Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message"
  }
}
```

### Error Codes

- `VALIDATION_ERROR` (400) - 输入验证失败
- `NOT_FOUND` (404) - 资源不存在
- `DUPLICATE_ENTRY` (409) - 唯一性约束冲突
- `INTERNAL_ERROR` (500) - 服务器内部错误

## Testing Strategy

### 测试方法

本系统采用**双重测试策略**：
- **单元测试**: 验证特定示例和边缘情况
- **属性测试**: 使用 `hypothesis` 验证通用正确性

### 属性测试配置

- **测试库**: hypothesis
- **迭代次数**: 每个属性测试最少100次
- **标签格式**: `Feature: lightweight-domain-config, Property {number}: {property_text}`

## Deployment

### 环境变量

```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
REDIS_URL=redis://localhost:6379/0  # 可选
REDIS_TTL=3600
FLASK_ENV=production
SECRET_KEY=your-secret-key
```

### 启动命令

```bash
pip install -r requirements.txt
flask db upgrade
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```
