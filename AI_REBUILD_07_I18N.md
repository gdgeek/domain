# AI 重建指南 07 - 国际化实现

## 概述

本文档详细说明项目的国际化（i18n）实现，包括多语言支持、语言解析、翻译管理和语言降级机制。

## 目录

- [架构设计](#架构设计)
- [数据库设计](#数据库设计)
- [语言解析器](#语言解析器)
- [翻译服务](#翻译服务)
- [API 集成](#api-集成)
- [语言降级机制](#语言降级机制)

---

## 架构设计

### 多语言架构

```
┌─────────────────────────────────────┐
│         HTTP Request                 │
│  Accept-Language: zh-CN,en;q=0.9    │
│  Query: ?lang=en-us                  │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      LanguageResolver                │
│  解析和规范化语言代码                 │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│     TranslationService               │
│  获取翻译（带缓存和降级）             │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      ConfigService                   │
│  合并配置和翻译                       │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│         JSON Response                │
│  { title: "...", language: "zh-cn" } │
└─────────────────────────────────────┘
```

### 核心组件

1. **LanguageResolver**: 从请求中解析语言代码
2. **TranslationService**: 管理翻译的 CRUD 操作
3. **ConfigService**: 合并配置和翻译数据
4. **RedisCacheManager**: 缓存翻译内容

---

## 数据库设计

### Translations 表

```sql
CREATE TABLE translations (
  id INT AUTO_INCREMENT PRIMARY KEY,
  config_id INT NOT NULL,
  language_code VARCHAR(10) NOT NULL,
  title VARCHAR(200) NOT NULL,
  author VARCHAR(100) NOT NULL,
  description VARCHAR(1000) NOT NULL,
  keywords TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY unique_config_language (config_id, language_code),
  FOREIGN KEY (config_id) REFERENCES configs(id) ON DELETE CASCADE
);
```

### 字段说明

- **config_id**: 关联的配置 ID（外键）
- **language_code**: 语言代码（如 'zh-cn', 'en-us'）
- **title**: 翻译后的标题（最大 200 字符）
- **author**: 翻译后的作者（最大 100 字符）
- **description**: 翻译后的描述（最大 1000 字符）
- **keywords**: 翻译后的关键词（TEXT 类型，存储为逗号分隔的字符串）

### 唯一约束

每个配置的每种语言只能有一条翻译记录：

```sql
UNIQUE KEY unique_config_language (config_id, language_code)
```

---

## 语言解析器

### LanguageResolver 类

**文件**: `src/services/LanguageResolver.ts`

**功能**: 从 HTTP 请求中解析语言代码，支持多种语言来源

### 语言来源优先级

1. **查询参数** (`?lang=en-us`) - 最高优先级
2. **Accept-Language 头** - 次优先级
3. **默认语言** - 最低优先级

### 核心方法

#### 1. 解析语言

```typescript
resolveLanguage(req: Request): string {
  // 1. 检查查询参数（最高优先级）
  if (req.query.lang && typeof req.query.lang === 'string') {
    const normalized = this.normalizeLanguageCode(req.query.lang);
    if (this.supportedLanguages.has(normalized)) {
      return normalized;
    }
  }

  // 2. 检查 Accept-Language 头
  const acceptLanguage = req.headers['accept-language'];
  if (acceptLanguage && typeof acceptLanguage === 'string') {
    const parsed = this.parseAcceptLanguage(acceptLanguage);
    if (parsed) {
      return parsed;
    }
  }

  // 3. 返回默认语言
  return this.defaultLanguage;
}
```

#### 2. 规范化语言代码

将语言代码转换为小写带连字符格式：

```typescript
normalizeLanguageCode(code: string): string {
  return code.toLowerCase().replace(/_/g, '-');
}

// 示例：
// zh_CN -> zh-cn
// ZH-CN -> zh-cn
// en_US -> en-us
```

#### 3. 解析 Accept-Language 头

```typescript
parseAcceptLanguage(header: string): string | null {
  // Accept-Language 格式示例：
  // "en-US,en;q=0.9,zh-CN;q=0.8"
  
  // 1. 解析语言和 quality 值
  const languages = header.split(',').map(lang => {
    const parts = lang.trim().split(';');
    const code = parts[0].trim();
    
    // 提取 quality 值（q 参数）
    const qMatch = parts[1]?.match(/q=([\d.]+)/);
    let quality = 1.0;
    if (qMatch) {
      const parsed = parseFloat(qMatch[1]);
      quality = isNaN(parsed) ? 1.0 : parsed;
    }
    
    return { code, quality };
  });

  // 2. 按 quality 值降序排序
  languages.sort((a, b) => b.quality - a.quality);

  // 3. 查找第一个支持的语言
  for (const lang of languages) {
    const normalized = this.normalizeLanguageCode(lang.code);
    if (this.supportedLanguages.has(normalized)) {
      return normalized;
    }
  }

  return null;
}
```

### 配置

通过环境变量配置支持的语言：

```bash
# 默认语言
DEFAULT_LANGUAGE=zh-cn

# 支持的语言列表（逗号分隔）
SUPPORTED_LANGUAGES=zh-cn,zh-tw,en-us,ja-jp,th-th
```

### 使用示例

```typescript
import { createDefaultLanguageResolver } from './services/LanguageResolver';

const languageResolver = createDefaultLanguageResolver();

// 在路由中使用
router.get('/configs/:id', async (req, res) => {
  const lang = languageResolver.resolveLanguage(req);
  const config = await configService.getConfigById(req.params.id, lang);
  res.json({ data: config });
});
```

---

## 翻译服务

### TranslationService 类

**文件**: `src/services/TranslationService.ts`

**功能**: 管理翻译的 CRUD 操作，支持缓存和语言降级

### 核心方法

#### 1. 创建翻译

```typescript
async createTranslation(data: CreateTranslationDTO): Promise<TranslationResponse> {
  // 1. 验证和规范化语言代码
  const normalizedLang = this.languageResolver.normalizeLanguageCode(data.languageCode);
  if (!this.languageResolver.isSupported(normalizedLang)) {
    throw new ValidationError(`Unsupported language: ${data.languageCode}`);
  }

  // 2. 验证必填字段
  this.validateRequiredFields(data);

  // 3. 验证字段长度
  this.validateFieldLengths(data);

  // 4. 检查重复
  const existing = await this.translationModel.findOne({
    where: { configId: data.configId, languageCode: normalizedLang },
  });
  if (existing) {
    throw new ConflictError('Translation already exists');
  }

  // 5. 创建翻译
  const translation = await this.translationModel.create({
    ...data,
    languageCode: normalizedLang,
  });

  // 6. 失效缓存
  await this.invalidateCache(data.configId, normalizedLang);

  return this.toResponse(translation);
}
```

#### 2. 获取翻译（带缓存）

```typescript
async getTranslation(configId: number, languageCode: string): Promise<TranslationResponse | null> {
  const normalizedLang = this.languageResolver.normalizeLanguageCode(languageCode);

  // 1. 尝试从缓存获取
  const cacheKey = this.getCacheKey(configId, normalizedLang);
  const cached = await this.cacheManager.get<TranslationResponse>(cacheKey);
  if (cached) {
    logger.debug('Translation cache hit', { configId, languageCode: normalizedLang });
    return cached;
  }

  // 2. 从数据库查询
  const translation = await this.translationModel.findOne({
    where: { configId, languageCode: normalizedLang },
  });

  if (!translation) {
    return null;
  }

  // 3. 缓存结果（TTL: 3600 秒）
  const response = this.toResponse(translation);
  await this.cacheManager.set(cacheKey, response, 3600);

  return response;
}
```

#### 3. 获取翻译（带降级）

```typescript
async getTranslationWithFallback(
  configId: number,
  languageCode: string
): Promise<{ translation: TranslationResponse; actualLanguage: string }> {
  const normalizedLang = this.languageResolver.normalizeLanguageCode(languageCode);

  // 1. 尝试获取请求的语言
  let translation = await this.getTranslation(configId, normalizedLang);
  if (translation) {
    return { translation, actualLanguage: normalizedLang };
  }

  // 2. 降级到默认语言
  const defaultLang = this.languageResolver.getDefaultLanguage();
  translation = await this.getTranslation(configId, defaultLang);

  if (!translation) {
    throw new NotFoundError(`No translation found for config ${configId}`);
  }

  // 3. 记录降级事件
  logger.info('Language fallback occurred', {
    configId,
    requestedLanguage: normalizedLang,
    returnedLanguage: defaultLang,
  });

  return { translation, actualLanguage: defaultLang };
}
```

#### 4. 更新翻译

```typescript
async updateTranslation(
  configId: number,
  languageCode: string,
  data: UpdateTranslationDTO
): Promise<TranslationResponse> {
  const normalizedLang = this.languageResolver.normalizeLanguageCode(languageCode);

  // 1. 查找翻译
  const translation = await this.translationModel.findOne({
    where: { configId, languageCode: normalizedLang },
  });
  if (!translation) {
    throw new NotFoundError('Translation not found');
  }

  // 2. 验证更新数据
  if (data.title !== undefined) {
    this.validateFieldLength('title', data.title, 200);
  }
  if (data.description !== undefined) {
    this.validateFieldLength('description', data.description, 1000);
  }

  // 3. 更新翻译
  await translation.update(data);

  // 4. 失效缓存
  await this.invalidateCache(configId, normalizedLang);

  return this.toResponse(translation);
}
```

#### 5. 删除翻译

```typescript
async deleteTranslation(configId: number, languageCode: string): Promise<void> {
  const normalizedLang = this.languageResolver.normalizeLanguageCode(languageCode);

  // 1. 检查是否为默认语言
  if (normalizedLang === this.languageResolver.getDefaultLanguage()) {
    const count = await this.translationModel.count({ where: { configId } });
    if (count > 1) {
      throw new ValidationError(
        'Cannot delete default language translation while other translations exist'
      );
    }
  }

  // 2. 删除翻译
  const deleted = await this.translationModel.destroy({
    where: { configId, languageCode: normalizedLang },
  });
  if (deleted === 0) {
    throw new NotFoundError('Translation not found');
  }

  // 3. 失效缓存
  await this.invalidateCache(configId, normalizedLang);
}
```

### 缓存键格式

```typescript
private getCacheKey(configId: number, languageCode: string): string {
  return `config:${configId}:lang:${languageCode}`;
}

// 示例：
// config:1:lang:zh-cn
// config:1:lang:en-us
// config:2:lang:ja-jp
```

### 缓存失效

```typescript
// 失效单个语言的缓存
await this.invalidateCache(configId, languageCode);

// 失效所有语言的缓存（配置删除时）
await this.invalidateAllCachesForConfig(configId);
// 使用模式匹配：config:123:lang:*
```

---

## API 集成

### ConfigService 集成

**文件**: `src/services/ConfigService.ts`

#### 通过 ID 获取配置（带翻译）

```typescript
async getConfigById(id: number, languageCode?: string): Promise<ConfigWithTranslation> {
  // 1. 获取基础配置
  const config = await this.configRepository.findById(id);
  if (!config) {
    throw new NotFoundError(`Config not found: ${id}`);
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

#### 合并配置和翻译

```typescript
private mergeConfigWithTranslation(
  config: ConfigAttributes,
  translation: TranslationResponse,
  language: string
): ConfigWithTranslation {
  return {
    id: config.id,
    // 非翻译字段（来自 configs 表）
    links: config.links,
    permissions: config.permissions,
    createdAt: config.createdAt!,
    updatedAt: config.updatedAt!,
    // 翻译字段（来自 translations 表）
    title: translation.title,
    author: translation.author,
    description: translation.description,
    keywords: translation.keywords,
    // 元数据
    language,
  };
}
```

### API 路由

**文件**: `src/routes/ConfigRoutes.ts`

```typescript
// 获取配置（支持多语言）
router.get('/:id', asyncHandler(async (req: Request, res: Response) => {
  const id = parseInt(req.params.id);
  const lang = languageResolver.resolveLanguage(req);
  
  const config = await configService.getConfigById(id, lang);
  
  res.json({ data: config });
}));

// 获取配置列表（支持多语言）
router.get('/', asyncHandler(async (req: Request, res: Response) => {
  const lang = languageResolver.resolveLanguage(req);
  
  const configs = await configService.listConfigs(lang);
  
  res.json({ data: configs });
}));
```

### 翻译管理 API

**文件**: `src/routes/TranslationRoutes.ts`

```typescript
// 创建翻译
router.post('/:id/translations', asyncHandler(async (req: Request, res: Response) => {
  const configId = parseInt(req.params.id);
  const translation = await translationService.createTranslation({
    configId,
    ...req.body,
  });
  res.status(201).json({ data: translation });
}));

// 更新翻译
router.put('/:id/translations/:lang', asyncHandler(async (req: Request, res: Response) => {
  const configId = parseInt(req.params.id);
  const lang = req.params.lang;
  const translation = await translationService.updateTranslation(configId, lang, req.body);
  res.json({ data: translation });
}));

// 获取所有翻译
router.get('/:id/translations', asyncHandler(async (req: Request, res: Response) => {
  const configId = parseInt(req.params.id);
  const translations = await translationService.getAllTranslations(configId);
  res.json({ data: translations });
}));

// 删除翻译
router.delete('/:id/translations/:lang', asyncHandler(async (req: Request, res: Response) => {
  const configId = parseInt(req.params.id);
  const lang = req.params.lang;
  await translationService.deleteTranslation(configId, lang);
  res.status(204).send();
}));
```

---

## 语言降级机制

### 降级策略

当请求的语言不存在时，系统会自动降级到默认语言：

```
请求语言 (ja-jp) → 不存在
    ↓
默认语言 (zh-cn) → 存在 ✓
    ↓
返回默认语言的翻译
```

### 降级流程

```typescript
async getTranslationWithFallback(configId, languageCode) {
  // 1. 尝试获取请求的语言
  let translation = await getTranslation(configId, languageCode);
  if (translation) {
    return { translation, actualLanguage: languageCode };
  }

  // 2. 降级到默认语言
  const defaultLang = getDefaultLanguage();
  translation = await getTranslation(configId, defaultLang);
  
  if (!translation) {
    throw new NotFoundError('No translation found');
  }

  // 3. 记录降级事件
  logger.info('Language fallback occurred', {
    requestedLanguage: languageCode,
    returnedLanguage: defaultLang,
  });

  return { translation, actualLanguage: defaultLang };
}
```

### 响应格式

响应中包含 `language` 字段，指示实际返回的语言：

```json
{
  "data": {
    "id": 1,
    "title": "示例网站",
    "author": "作者",
    "description": "描述",
    "keywords": ["关键词1", "关键词2"],
    "links": {},
    "permissions": {},
    "language": "zh-cn",
    "createdAt": "2024-01-01T00:00:00.000Z",
    "updatedAt": "2024-01-01T00:00:00.000Z"
  }
}
```

---

## 数据验证

### 必填字段验证

```typescript
private validateRequiredFields(data: CreateTranslationDTO): void {
  const requiredFields = ['title', 'author', 'description', 'keywords'];
  const missingFields: string[] = [];

  for (const field of requiredFields) {
    const value = data[field];
    if (value === undefined || value === null) {
      missingFields.push(field);
    } else if (typeof value === 'string' && value.trim() === '') {
      missingFields.push(field);
    } else if (Array.isArray(value) && value.length === 0) {
      missingFields.push(field);
    }
  }

  if (missingFields.length > 0) {
    throw new ValidationError('Required fields are missing', { missingFields });
  }
}
```

### 字段长度验证

```typescript
private validateFieldLengths(data: CreateTranslationDTO): void {
  this.validateFieldLength('title', data.title, 200);
  this.validateFieldLength('description', data.description, 1000);
}

private validateFieldLength(fieldName: string, value: string, maxLength: number): void {
  if (value.length > maxLength) {
    throw new ValidationError(
      `Field ${fieldName} exceeds maximum length of ${maxLength} characters`,
      {
        field: fieldName,
        maxLength,
        actualLength: value.length,
      }
    );
  }
}
```

### Keywords 格式验证

```typescript
private validateKeywordsFormat(keywords: any): void {
  if (!Array.isArray(keywords)) {
    throw new ValidationError('Keywords must be an array', { keywords });
  }

  for (let i = 0; i < keywords.length; i++) {
    if (typeof keywords[i] !== 'string') {
      throw new ValidationError('All keywords must be strings', {
        invalidKeyword: keywords[i],
        index: i,
      });
    }
  }
}
```

---

## 测试建议

### 1. LanguageResolver 测试

- 测试查询参数优先级
- 测试 Accept-Language 头解析
- 测试默认语言降级
- 测试语言代码规范化

### 2. TranslationService 测试

- 测试创建翻译（包括验证）
- 测试更新翻译
- 测试删除翻译（包括默认语言保护）
- 测试语言降级机制
- 测试缓存命中和未命中

### 3. 集成测试

- 测试完整的多语言请求流程
- 测试缓存失效
- 测试并发请求

---

## 相关文档

- [AI_REBUILD_03_DATABASE.md](./AI_REBUILD_03_DATABASE.md) - 数据库设计
- [AI_REBUILD_04_API.md](./AI_REBUILD_04_API.md) - API 设计
- [AI_REBUILD_05_MODULES.md](./AI_REBUILD_05_MODULES.md) - 核心模块
- [AI_REBUILD_08_CACHE.md](./AI_REBUILD_08_CACHE.md) - 缓存策略
