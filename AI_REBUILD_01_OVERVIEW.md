# 项目概述

## 1. 项目简介

### 1.1 项目名称
域名配置服务 (Domain Configuration Service)

### 1.2 项目描述
一个基于 Node.js + TypeScript 的 RESTful API 服务，用于管理域名和配置信息的关联关系，支持多语言内容管理。

### 1.3 核心价值
- 统一管理多个域名的配置信息
- 支持配置共享（多个域名使用同一配置）
- 完整的多语言内容支持
- 高性能缓存机制
- 企业级安全和监控

## 2. 核心特性

### 2.1 功能特性
- ✅ RESTful API 设计
- ✅ 三表架构（domains + configs + translations）
- ✅ 完整的 CRUD 操作
- ✅ 分页查询支持
- ✅ 多语言内容管理（i18n）
- ✅ 自动语言协商
- ✅ Web 管理界面

### 2.2 技术特性
- ✅ TypeScript 类型安全
- ✅ Redis 缓存层
- ✅ JWT 认证
- ✅ 请求限流
- ✅ Prometheus 监控
- ✅ Swagger API 文档
- ✅ Docker 容器化
- ✅ 完整的测试覆盖（895 个测试用例）

### 2.3 性能特性
- ✅ Redis 缓存提升查询性能
- ✅ 数据库连接池
- ✅ 请求限流防止滥用
- ✅ 异步处理
- ✅ 优化的数据库查询

## 3. 系统架构

### 3.1 整体架构

```
┌─────────────────────────────────────────────────┐
│                   Client Layer                   │
│  (Web Browser / API Client / Mobile App)        │
└─────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│                 API Gateway Layer                │
│  - CORS Middleware                               │
│  - Rate Limiting                                 │
│  - Request ID                                    │
│  - Logging                                       │
└─────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│              Authentication Layer                │
│  - JWT Verification                              │
│  - Admin Password Auth                           │
└─────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│                 Route Layer                      │
│  - Domain Routes                                 │
│  - Config Routes                                 │
│  - Translation Routes                            │
│  - Admin Routes                                  │
└─────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│                Service Layer                     │
│  - DomainService                                 │
│  - ConfigService                                 │
│  - TranslationService                            │
│  - LanguageResolver                              │
└─────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│              Repository Layer                    │
│  - DomainRepository                              │
│  - ConfigRepository                              │
│  - Translation Model (Sequelize)                 │
└─────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│                 Data Layer                       │
│  ┌──────────────┐         ┌──────────────┐     │
│  │   MySQL DB   │         │  Redis Cache │     │
│  └──────────────┘         └──────────────┘     │
└─────────────────────────────────────────────────┘
```



### 3.2 分层架构说明

#### 3.2.1 Client Layer（客户端层）
- Web 浏览器访问管理界面
- API 客户端调用 RESTful 接口
- 移动应用或第三方集成

#### 3.2.2 API Gateway Layer（API 网关层）
- **CORS Middleware**: 处理跨域请求
- **Rate Limiting**: 防止 API 滥用
- **Request ID**: 请求追踪
- **Logging**: 结构化日志记录
- **Metrics**: Prometheus 监控指标

#### 3.2.3 Authentication Layer（认证层）
- **JWT Verification**: 验证 Bearer Token
- **Admin Password Auth**: 管理员密码认证
- **Public/Private Routes**: 区分公开和受保护的路由

#### 3.2.4 Route Layer（路由层）
- **Domain Routes**: 域名管理接口
- **Config Routes**: 配置管理接口
- **Translation Routes**: 翻译管理接口
- **Admin Routes**: 管理员认证接口
- **Session Routes**: 会话管理接口

#### 3.2.5 Service Layer（服务层）
- **DomainService**: 域名业务逻辑
- **ConfigService**: 配置业务逻辑
- **TranslationService**: 翻译业务逻辑
- **LanguageResolver**: 语言协商逻辑
- **CacheService**: 缓存管理逻辑

#### 3.2.6 Repository Layer（仓库层）
- **DomainRepository**: 域名数据访问
- **ConfigRepository**: 配置数据访问
- **Translation Model**: 翻译数据模型（Sequelize ORM）

#### 3.2.7 Data Layer（数据层）
- **MySQL Database**: 主数据存储
  - domains 表
  - configs 表
  - translations 表
- **Redis Cache**: 缓存层
  - 配置缓存
  - 翻译内容缓存
  - 会话缓存

## 4. 数据流

### 4.1 读取流程（带缓存）

```
Client Request
    │
    ▼
Middleware (Auth, Rate Limit, Logging)
    │
    ▼
Route Handler
    │
    ▼
Service Layer
    │
    ├─► Check Redis Cache
    │   ├─► Cache Hit → Return Cached Data
    │   └─► Cache Miss ↓
    │
    ▼
Repository Layer
    │
    ▼
MySQL Database
    │
    ▼
Store in Redis Cache
    │
    ▼
Return to Client
```

### 4.2 写入流程

```
Client Request (with JWT Token)
    │
    ▼
Middleware (Auth, Validation, Rate Limit)
    │
    ▼
Route Handler
    │
    ▼
Service Layer
    │
    ▼
Repository Layer
    │
    ▼
MySQL Database (Transaction)
    │
    ▼
Invalidate Redis Cache
    │
    ▼
Return Success Response
```

### 4.3 多语言查询流程

```
Client Request (with Accept-Language header)
    │
    ▼
Language Resolver
    │
    ├─► Parse Accept-Language header
    ├─► Check query parameter (lang=xx-xx)
    └─► Determine best language match
    │
    ▼
Check Redis Cache (config:id:lang)
    │
    ├─► Cache Hit → Return Cached Translation
    └─► Cache Miss ↓
    │
    ▼
Query translations table
    │
    ├─► Translation Found → Return Translation
    └─► Not Found → Fallback to Default Language
    │
    ▼
Store in Redis Cache
    │
    ▼
Return Localized Content
```

## 5. 项目目录结构

```
domain-config-service/
├── src/
│   ├── config/              # 配置模块
│   │   ├── database.ts      # 数据库配置
│   │   ├── redis.ts         # Redis 配置
│   │   ├── env.ts           # 环境变量
│   │   ├── logger.ts        # 日志配置
│   │   ├── metrics.ts       # 监控指标
│   │   └── swagger.ts       # API 文档配置
│   │
│   ├── middleware/          # 中间件
│   │   ├── AuthMiddleware.ts           # JWT 认证
│   │   ├── AdminAuthMiddleware.ts      # 管理员认证
│   │   ├── CorsMiddleware.ts           # CORS 处理
│   │   ├── ErrorMiddleware.ts          # 错误处理
│   │   ├── LoggingMiddleware.ts        # 日志记录
│   │   ├── RateLimitMiddleware.ts      # 限流
│   │   ├── MetricsMiddleware.ts        # 监控指标
│   │   ├── RequestIdMiddleware.ts      # 请求 ID
│   │   ├── ValidationMiddleware.ts     # 数据验证
│   │   └── JsonResponseMiddleware.ts   # JSON 响应格式化
│   │
│   ├── models/              # 数据模型
│   │   ├── Config.ts        # 配置模型
│   │   ├── Domain.ts        # 域名模型
│   │   └── Translation.ts   # 翻译模型
│   │
│   ├── repositories/        # 数据访问层
│   │   ├── ConfigRepository.ts
│   │   └── DomainRepository.ts
│   │
│   ├── services/            # 业务逻辑层
│   │   ├── ConfigService.ts
│   │   ├── DomainService.ts
│   │   ├── TranslationService.ts
│   │   ├── LanguageResolver.ts
│   │   ├── CacheService.ts
│   │   └── RedisCacheManager.ts
│   │
│   ├── routes/              # 路由层
│   │   ├── ConfigRoutes.ts
│   │   ├── DomainRoutes.ts
│   │   ├── TranslationRoutes.ts
│   │   ├── AdminRoutes.ts
│   │   └── SessionRoutes.ts
│   │
│   ├── validation/          # 验证规则
│   │   ├── schemas.ts       # Joi 验证模式
│   │   └── validator.ts     # 验证器
│   │
│   ├── errors/              # 自定义错误
│   │   ├── NotFoundError.ts
│   │   ├── ValidationError.ts
│   │   ├── ConflictError.ts
│   │   └── DatabaseError.ts
│   │
│   ├── types/               # TypeScript 类型定义
│   │   ├── express.d.ts
│   │   └── index.d.ts
│   │
│   ├── test-utils/          # 测试工具
│   │   └── setupTestDatabase.ts
│   │
│   ├── app.ts               # Express 应用配置
│   └── index.ts             # 应用入口
│
├── public/                  # 静态文件
│   ├── admin-bootstrap.html # 管理界面
│   ├── admin.html           # 旧版管理界面
│   └── admin-v2.html        # V2 管理界面
│
├── migrations/              # 数据库迁移脚本
│   ├── 001_add_permissions_field.sql
│   ├── 002_split_to_two_tables.sql
│   ├── 003_add_homepage_to_domains.sql
│   ├── 004_create_translations_table.sql
│   ├── 005_migrate_config_data_to_translations.sql
│   ├── init_fresh_database.sql
│   └── init_with_translations.sql
│
├── docs/                    # 文档
│   ├── api/                 # API 文档
│   ├── architecture/        # 架构文档
│   ├── deployment/          # 部署文档
│   └── testing/             # 测试文档
│
├── scripts/                 # 工具脚本
│   ├── migrate.sh           # 数据库迁移
│   ├── docker-quickstart.sh # Docker 快速启动
│   └── test-all-apis.sh     # API 测试
│
├── .env                     # 环境变量
├── .env.example             # 环境变量示例
├── docker-compose.yml       # Docker Compose 配置
├── Dockerfile               # Docker 镜像配置
├── package.json             # 项目依赖
├── tsconfig.json            # TypeScript 配置
├── jest.config.js           # Jest 测试配置
└── README.md                # 项目说明
```

## 6. 核心概念

### 6.1 三表架构

项目使用三表架构来管理数据：

1. **domains 表**: 存储域名信息
   - 每个域名关联一个配置
   - 支持主页 URL 配置

2. **configs 表**: 存储配置内容
   - 包含默认语言的内容
   - 可被多个域名共享
   - 包含权限和链接配置

3. **translations 表**: 存储多语言翻译
   - 每个配置可有多个语言版本
   - 支持标题、作者、描述、关键词的翻译
   - 使用 (config_id, language_code) 作为唯一键

### 6.2 多语言支持

- **语言协商**: 根据 Accept-Language 请求头自动选择语言
- **语言回退**: 请求的语言不存在时，回退到默认语言（zh-cn）
- **支持的语言**: zh-cn, zh-tw, en-us, ja-jp, th-th
- **缓存策略**: 每种语言的内容独立缓存

### 6.3 缓存策略

- **配置缓存**: 缓存配置基本信息
- **翻译缓存**: 缓存每种语言的翻译内容
- **缓存键格式**: `config:{id}:{lang}`
- **缓存失效**: 更新或删除时自动失效相关缓存

### 6.4 认证机制

- **公开接口**: GET 请求无需认证
- **受保护接口**: POST/PUT/DELETE 需要 JWT Token
- **管理员登录**: 使用密码获取 JWT Token
- **Token 有效期**: 24 小时

## 7. 关键设计决策

### 7.1 为什么使用三表架构？

- ✅ 配置共享：多个域名可以使用同一配置
- ✅ 数据一致性：配置更新自动影响所有关联域名
- ✅ 多语言支持：独立的翻译表便于管理
- ✅ 性能优化：可以独立缓存配置和翻译

### 7.2 为什么使用 Redis 缓存？

- ✅ 减少数据库查询
- ✅ 提升响应速度
- ✅ 支持高并发访问
- ✅ 灵活的缓存失效策略

### 7.3 为什么使用 TypeScript？

- ✅ 类型安全，减少运行时错误
- ✅ 更好的 IDE 支持
- ✅ 代码可维护性更高
- ✅ 接口定义清晰

### 7.4 为什么使用 Sequelize ORM？

- ✅ 类型安全的数据库操作
- ✅ 自动处理连接池
- ✅ 支持事务
- ✅ 迁移管理方便

## 8. 性能指标

### 8.1 响应时间

- 缓存命中: < 10ms
- 数据库查询: < 50ms
- 复杂查询: < 100ms

### 8.2 并发能力

- 支持 100+ 并发请求
- 请求限流: 100 请求/分钟/IP

### 8.3 测试覆盖

- 单元测试: 895 个测试用例
- 代码覆盖率: > 80%
- 集成测试: 完整的 API 测试

## 9. 下一步

阅读完本文档后，请继续阅读：

1. [技术栈详解](./AI_REBUILD_02_TECH_STACK.md)
2. [数据库设计](./AI_REBUILD_03_DATABASE.md)
3. [API 规范](./AI_REBUILD_04_API.md)

