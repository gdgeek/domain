# AI 重建指南 05 - 核心模块实现

## 概述

本文档详细说明项目的核心模块实现，包括 Models（数据模型）、Repositories（数据访问层）和 Services（业务逻辑层）的三层架构设计。

## 目录

- [架构设计](#架构设计)
- [Models 层](#models-层)
- [Repositories 层](#repositories-层)
- [Services 层](#services-层)
- [依赖注入](#依赖注入)

---

## 架构设计

### 三层架构

```
┌─────────────────────────────────────┐
│         Routes (路由层)              │
│  处理 HTTP 请求和响应                 │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│       Services (业务逻辑层)          │
│  处理业务规则和数据转换               │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│    Repositories (数据访问层)         │
│  封装数据库操作                       │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│        Models (数据模型层)           │
│  定义数据结构和 ORM 映射              │
└─────────────────────────────────────┘
```

### 职责分离

- **Models**: 定义数据结构、字段类型、验证规则和表关联
- **Repositories**: 封装所有数据库操作（CRUD），提供统一的数据访问接口
- **Services**: 实现业务逻辑、数据转换、跨表操作和事务管理

---

## Models 层

### 1. Config 模型

**文件**: `src/models/Config.ts`

**功能**: 配置信息表，存储网站的元数据配置，可以被多个域名共享

**字段定义**:

```typescript
export interface ConfigAttributes {
  id: number;                    // 主键
  title: string | null;          // 网站标题
  author: string | null;         // 作者
  description: string | null;    // 描述
  keywords: string | null;       // 关键词
  links: object | null;          // 链接配置（JSON）
  permissions: object | null;    // 权限配置（JSON）
  createdAt?: Date;              // 创建时间
  updatedAt?: Date;              // 更新时间
}
```

**Sequelize 配置**:

```typescript
Config.init(
  {
    id: {
      type: DataTypes.INTEGER,
      autoIncrement: true,
      primaryKey: true,
    },
    title: {
      type: DataTypes.STRING(255),
      allowNull: true,
    },
    // ... 其他字段
    links: {
      type: DataTypes.JSON,
      allowNull: true,
    },
    permissions: {
      type: DataTypes.JSON,
      allowNull: true,
    },
  },
  {
    sequelize,
    tableName: 'configs',
    timestamps: true,
    underscored: true,  // 使用 snake_case 字段名
  }
);
```

### 2. Domain 模型

**文件**: `src/models/Domain.ts`

**功能**: 域名表，存储域名和配置的关联关系，多个域名可以关联到同一个配置

**字段定义**:

```typescript
export interface DomainAttributes {
  id: number;                    // 主键
  domain: string;                // 域名（唯一）
  configId: number;              // 关联的配置 ID（外键）
  homepage?: string | null;      // 首页 URL
  createdAt?: Date;              // 创建时间
  updatedAt?: Date;              // 更新时间
  config?: ConfigAttributes;     // 关联的配置对象
}
```

**关联关系**:

```typescript
// Domain 属于一个 Config
Domain.belongsTo(Config, {
  foreignKey: 'configId',
  as: 'config',
});

// Config 有多个 Domains
Config.hasMany(Domain, {
  foreignKey: 'configId',
  as: 'domains',
});
```

### 3. Translation 模型

**文件**: `src/models/Translation.ts`

**功能**: 翻译表，存储配置的多语言内容

**字段定义**:

```typescript
export interface TranslationAttributes {
  id: number;                    // 主键
  configId: number;              // 关联的配置 ID（外键）
  language: string;              // 语言代码（如 'en', 'zh-CN'）
  title: string;                 // 翻译后的标题
  author: string;                // 翻译后的作者
  description: string;           // 翻译后的描述
  keywords: string;              // 翻译后的关键词（逗号分隔）
  createdAt?: Date;              // 创建时间
  updatedAt?: Date;              // 更新时间
}
```

**唯一约束**:

```typescript
indexes: [
  {
    unique: true,
    fields: ['config_id', 'language'],  // 每个配置的每种语言只能有一条记录
  },
]
```

---

## Repositories 层

### 1. ConfigRepository

**文件**: `src/repositories/ConfigRepository.ts`

**功能**: 封装 configs 表的所有数据库操作

**核心方法**:

```typescript
export class ConfigRepository {
  // 创建配置
  async create(data: ConfigCreationAttributes): Promise<Config>
  
  // 通过 ID 查询配置
  async findById(id: number): Promise<Config | null>
  
  // 查询所有配置（分页）
  async findAll(pagination: Pagination): Promise<Config[]>
  
  // 统计配置总数
  async count(): Promise<number>
  
  // 更新配置
  async update(id: number, data: Partial<ConfigAttributes>): Promise<Config | null>
  
  // 删除配置
  async delete(id: number): Promise<boolean>
}
```

**错误处理**:

```typescript
try {
  const config = await Config.create(data);
  logger.info('配置创建成功', { configId: config.id });
  return config;
} catch (error: any) {
  logger.error('创建配置失败', { error: error.message, data });
  throw new DatabaseError('创建配置失败', 'DB_CREATE_ERROR', error);
}
```

### 2. DomainRepository

**文件**: `src/repositories/DomainRepository.ts`

**功能**: 封装 domains 表的所有数据库操作，支持关联查询 configs 表

**核心方法**:

```typescript
export class DomainRepository {
  // 创建域名
  async create(data: DomainCreationAttributes): Promise<Domain>
  
  // 通过 ID 查询域名（包含关联的配置）
  async findById(id: number): Promise<Domain | null>
  
  // 通过域名查询（包含关联的配置）
  async findByDomain(domain: string): Promise<Domain | null>
  
  // 查询所有域名（分页，包含关联的配置）
  async findAll(pagination: Pagination): Promise<Domain[]>
  
  // 统计域名总数
  async count(): Promise<number>
  
  // 更新域名
  async update(id: number, data: Partial<DomainAttributes>): Promise<Domain | null>
  
  // 删除域名
  async delete(id: number): Promise<boolean>
  
  // 查询使用指定配置的域名数量
  async countByConfigId(configId: number): Promise<number>
}
```

**关联查询示例**:

```typescript
async findByDomain(domain: string): Promise<Domain | null> {
  return await Domain.findOne({
    where: { domain },
    include: [{
      model: Config,
      as: 'config',  // 使用定义的别名
    }],
  });
}
```

---

## Services 层

### 1. ConfigService

**文件**: `src/services/ConfigService.ts`

**功能**: 处理配置相关的业务逻辑，支持多语言

**核心方法**:

```typescript
export class ConfigService {
  constructor(
    private configRepository: ConfigRepository,
    private domainRepository: DomainRepository,
    private translationService?: TranslationService,
    private languageResolver?: LanguageResolver
  ) {}

  // 通过 ID 获取配置（带翻译）
  async getConfigById(id: number, languageCode?: string): Promise<ConfigWithTranslation>
  
  // 通过域名获取配置（带翻译）
  async getConfigByDomain(domain: string, languageCode?: string): Promise<ConfigWithTranslation>
  
  // 获取配置列表（带翻译）
  async listConfigs(languageCode?: string): Promise<ConfigWithTranslation[]>
  
  // 创建配置（旧版 API）
  async create(input: ConfigInput): Promise<ConfigOutput>
  
  // 通过 ID 获取配置（旧版 API）
  async getById(id: number): Promise<ConfigOutput | null>
  
  // 获取配置列表（分页，旧版 API）
  async list(pagination: Pagination): Promise<PaginatedResult<ConfigOutput>>
  
  // 更新配置
  async update(id: number, input: Partial<ConfigInput>): Promise<ConfigOutput | null>
  
  // 删除配置
  async delete(id: number): Promise<boolean>
}
```

**多语言支持**:

```typescript
async getConfigById(id: number, languageCode?: string): Promise<ConfigWithTranslation> {
  // 1. 获取基础配置
  const config = await this.configRepository.findById(id);
  if (!config) {
    throw new NotFoundError(`Config not found: ${id}`, 'CONFIG_NOT_FOUND');
  }

  // 2. 确定语言
  const lang = languageCode || this.languageResolver.getDefaultLanguage();

  // 3. 获取翻译（带降级）
  const { translation, actualLanguage } = 
    await this.translationService.getTranslationWithFallback(id, lang);

  // 4. 合并配置和翻译
  return this.mergeConfigWithTranslation(config, translation, actualLanguage);
}
```

**业务规则**:

```typescript
async delete(id: number): Promise<boolean> {
  // 检查是否有域名正在使用此配置
  const domainCount = await this.domainRepository.countByConfigId(id);
  if (domainCount > 0) {
    throw new ConflictError(
      `无法删除配置，有 ${domainCount} 个域名正在使用此配置`,
      'CONFIG_IN_USE'
    );
  }

  // 如果启用了多语言支持，失效所有语言的缓存
  if (this.translationService) {
    await this.translationService.invalidateAllCachesForConfig(id);
  }

  const deleted = await this.configRepository.delete(id);
  if (!deleted) {
    throw new NotFoundError('配置不存在', 'CONFIG_NOT_FOUND');
  }

  return true;
}
```

### 2. DomainService

**文件**: `src/services/DomainService.ts`

**功能**: 处理域名相关的业务逻辑，支持智能域名匹配

**核心方法**:

```typescript
export class DomainService {
  constructor(
    private domainRepository: DomainRepository,
    private configRepository: ConfigRepository
  ) {}

  // 创建域名
  async create(input: DomainInput): Promise<DomainOutput>
  
  // 通过 ID 获取域名
  async getById(id: number): Promise<DomainOutput | null>
  
  // 通过域名获取（支持智能匹配）
  async getByDomain(input: string): Promise<any | null>
  
  // 获取域名列表（分页）
  async list(pagination: Pagination): Promise<PaginatedResult<DomainOutput>>
  
  // 更新域名
  async update(id: number, input: Partial<DomainInput>): Promise<DomainOutput | null>
  
  // 删除域名
  async delete(id: number): Promise<boolean>
}
```

**智能域名匹配**:

```typescript
async getByDomain(input: string): Promise<any | null> {
  // 1. 提取纯域名（移除协议、路径等）
  const cleanDomain = this.extractDomain(input);
  
  // 2. 首先尝试精确匹配
  let domainRecord = await this.domainRepository.findByDomain(cleanDomain);
  if (domainRecord) {
    return this.formatDomainResponse(domainRecord);
  }

  // 3. 如果精确匹配失败，尝试匹配根域名
  const rootDomain = this.extractRootDomain(cleanDomain);
  if (rootDomain !== cleanDomain) {
    domainRecord = await this.domainRepository.findByDomain(rootDomain);
    if (domainRecord) {
      return this.formatDomainResponse(domainRecord);
    }
  }

  return null;
}

// 从 URL 或域名字符串中提取纯域名
// 例如：https://www.baidu.com/a/v -> www.baidu.com
private extractDomain(input: string): string {
  let domain = input.trim().toLowerCase();
  domain = domain.replace(/^https?:\/\//i, '');  // 移除协议
  domain = domain.split('/')[0];                  // 移除路径
  domain = domain.split('?')[0];                  // 移除查询参数
  domain = domain.split('#')[0];                  // 移除锚点
  domain = domain.split(':')[0];                  // 移除端口号
  return domain;
}

// 从完整域名中提取根域名
// 例如：www.baidu.com -> baidu.com
private extractRootDomain(domain: string): string {
  const parts = domain.split('.');
  if (parts.length <= 2) {
    return domain;
  }
  return parts.slice(-2).join('.');
}
```

### 3. TranslationService

**文件**: `src/services/TranslationService.ts`

**功能**: 处理翻译相关的业务逻辑，支持语言降级和缓存

**核心方法**:

```typescript
export class TranslationService {
  constructor(
    private cacheService: CacheService,
    private languageResolver: LanguageResolver
  ) {}

  // 获取翻译（带降级）
  async getTranslationWithFallback(
    configId: number, 
    languageCode: string
  ): Promise<{ translation: TranslationResponse; actualLanguage: string }>
  
  // 创建或更新翻译
  async upsertTranslation(
    configId: number,
    languageCode: string,
    data: TranslationInput
  ): Promise<TranslationResponse>
  
  // 获取配置的所有翻译
  async getTranslationsByConfigId(configId: number): Promise<TranslationResponse[]>
  
  // 删除翻译
  async deleteTranslation(configId: number, languageCode: string): Promise<boolean>
  
  // 失效所有语言的缓存
  async invalidateAllCachesForConfig(configId: number): Promise<void>
}
```

**语言降级策略**:

```typescript
async getTranslationWithFallback(
  configId: number,
  languageCode: string
): Promise<{ translation: TranslationResponse; actualLanguage: string }> {
  // 1. 尝试获取请求的语言
  let translation = await this.getTranslation(configId, languageCode);
  if (translation) {
    return { translation, actualLanguage: languageCode };
  }

  // 2. 降级到默认语言
  const defaultLang = this.languageResolver.getDefaultLanguage();
  if (languageCode !== defaultLang) {
    translation = await this.getTranslation(configId, defaultLang);
    if (translation) {
      return { translation, actualLanguage: defaultLang };
    }
  }

  // 3. 如果默认语言也没有，抛出错误
  throw new NotFoundError(
    `No translation found for config ${configId}`,
    'TRANSLATION_NOT_FOUND'
  );
}
```

---

## 依赖注入

### 单例模式

每个 Service 和 Repository 都导出一个默认单例实例：

```typescript
// ConfigRepository.ts
export default new ConfigRepository();

// ConfigService.ts
export default new ConfigService(
  require('../repositories/ConfigRepository').default,
  require('../repositories/DomainRepository').default
);
```

### 依赖关系图

```
ConfigService
  ├── ConfigRepository
  ├── DomainRepository
  ├── TranslationService (可选)
  └── LanguageResolver (可选)

DomainService
  ├── DomainRepository
  └── ConfigRepository

TranslationService
  ├── CacheService
  └── LanguageResolver
```

---

## 实现要点

### 1. 错误处理

所有 Repository 方法都应该捕获数据库错误并转换为 `DatabaseError`：

```typescript
try {
  // 数据库操作
} catch (error: any) {
  logger.error('操作失败', { error: error.message });
  throw new DatabaseError('操作失败', 'DB_ERROR', error);
}
```

### 2. 日志记录

在关键操作点记录日志：

```typescript
logger.info('创建配置', { input });
// ... 执行操作
logger.info('配置创建成功', { configId: config.id });
```

### 3. 数据转换

Service 层负责将 Model 对象转换为 API 响应格式：

```typescript
private toOutput(config: ConfigAttributes): ConfigOutput {
  return {
    id: config.id,
    title: config.title,
    author: config.author,
    // ... 其他字段
  };
}
```

### 4. 业务验证

在 Service 层实现业务规则验证：

```typescript
// 检查域名是否已存在
const existing = await this.domainRepository.findByDomain(input.domain);
if (existing) {
  throw new ConflictError('域名已存在', 'DOMAIN_ALREADY_EXISTS');
}

// 检查配置是否存在
const config = await this.configRepository.findById(input.configId);
if (!config) {
  throw new NotFoundError('配置不存在', 'CONFIG_NOT_FOUND');
}
```

---

## 测试建议

### 1. Repository 测试

- 使用真实的测试数据库
- 测试所有 CRUD 操作
- 测试错误情况（如数据库连接失败）

### 2. Service 测试

- Mock Repository 依赖
- 测试业务逻辑
- 测试错误处理
- 测试数据转换

### 3. 集成测试

- 测试完整的请求流程
- 测试跨层交互
- 测试事务处理

---

## 相关文档

- [AI_REBUILD_03_DATABASE.md](./AI_REBUILD_03_DATABASE.md) - 数据库设计
- [AI_REBUILD_04_API.md](./AI_REBUILD_04_API.md) - API 设计
- [AI_REBUILD_06_MIDDLEWARE.md](./AI_REBUILD_06_MIDDLEWARE.md) - 中间件系统
- [AI_REBUILD_07_I18N.md](./AI_REBUILD_07_I18N.md) - 国际化实现
