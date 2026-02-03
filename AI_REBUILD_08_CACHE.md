# AI 重建指南 08 - Redis 缓存策略

## 概述

本文档详细说明项目的 Redis 缓存实现，包括缓存架构、缓存管理器、缓存策略和最佳实践。

## 目录

- [缓存架构](#缓存架构)
- [Redis 配置](#redis-配置)
- [缓存管理器](#缓存管理器)
- [缓存策略](#缓存策略)
- [缓存失效](#缓存失效)
- [性能优化](#性能优化)

---

## 缓存架构

### 缓存层次结构

```
┌─────────────────────────────────────┐
│         API Request                  │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Service Layer                   │
│  (ConfigService, TranslationService) │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Cache Manager                   │
│  (RedisCacheManager)                 │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│         Redis                        │
│  (Key-Value Store)                   │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Database (MySQL)                │
│  (Fallback when cache miss)          │
└─────────────────────────────────────┘
```

### 缓存流程

```
1. 请求到达 Service 层
2. Service 检查 Cache Manager
3. Cache Hit → 直接返回缓存数据
4. Cache Miss → 查询数据库
5. 将数据库结果存入缓存
6. 返回数据
```

---

## Redis 配置

### 环境变量

```bash
# Redis 启用开关
REDIS_ENABLED=true

# Redis 连接配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your-password  # 可选
REDIS_DB=0                    # 数据库编号（0-15）

# 缓存 TTL（秒）
REDIS_TTL=3600                # 默认 1 小时
```

### Redis 客户端配置

**文件**: `src/config/redis.ts`

```typescript
import Redis from 'ioredis';
import { config } from './env';
import { logger } from './logger';

let redisClient: Redis | null = null;

/**
 * 连接 Redis
 */
export async function connectRedis(): Promise<Redis> {
  if (redisClient) {
    return redisClient;
  }

  if (!config.redisEnabled) {
    throw new Error('Redis is not enabled');
  }

  redisClient = new Redis({
    host: config.redisHost,
    port: config.redisPort,
    password: config.redisPassword || undefined,
    db: config.redisDb,
    retryStrategy: (times) => {
      const delay = Math.min(times * 50, 2000);
      return delay;
    },
    maxRetriesPerRequest: 3,
  });

  redisClient.on('connect', () => {
    logger.info('Redis 连接成功', {
      host: config.redisHost,
      port: config.redisPort,
      db: config.redisDb,
    });
  });

  redisClient.on('error', (error) => {
    logger.error('Redis 连接错误', { error: error.message });
  });

  return redisClient;
}

/**
 * 获取 Redis 客户端
 */
export function getRedisClient(): Redis | null {
  return redisClient;
}

/**
 * 检查 Redis 是否启用
 */
export function isRedisEnabled(): boolean {
  return config.redisEnabled;
}

/**
 * 断开 Redis 连接
 */
export async function disconnectRedis(): Promise<void> {
  if (redisClient) {
    await redisClient.quit();
    redisClient = null;
    logger.info('Redis 连接已断开');
  }
}
```

---

## 缓存管理器

### CacheManager 接口

**文件**: `src/services/CacheManager.ts`

```typescript
/**
 * 缓存管理器接口
 * 
 * 定义缓存操作的标准接口
 */
export interface CacheManager {
  /**
   * 获取缓存值
   * @param key 缓存键
   * @returns 缓存值，如果不存在返回 null
   */
  get<T>(key: string): Promise<T | null>;

  /**
   * 设置缓存值
   * @param key 缓存键
   * @param value 缓存值
   * @param ttl 过期时间（秒）
   */
  set(key: string, value: any, ttl: number): Promise<void>;

  /**
   * 删除缓存值
   * @param key 缓存键
   */
  delete(key: string): Promise<void>;

  /**
   * 删除匹配模式的所有缓存
   * @param pattern 匹配模式（如 "config:*:lang:*"）
   */
  deletePattern(pattern: string): Promise<void>;
}
```

### RedisCacheManager 实现

**文件**: `src/services/RedisCacheManager.ts`

```typescript
import Redis from 'ioredis';
import { CacheManager } from './CacheManager';
import { logger, logError } from '../config/logger';

export class RedisCacheManager implements CacheManager {
  constructor(private redisClient: Redis) {}

  /**
   * 获取缓存值
   */
  async get<T>(key: string): Promise<T | null> {
    try {
      const value = await this.redisClient.get(key);
      
      if (value === null) {
        logger.debug('Cache miss', { key });
        return null;
      }

      logger.debug('Cache hit', { key });
      return JSON.parse(value, this.reviver) as T;
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      logError(err, { context: 'Failed to get cache value', key });
      return null;  // 缓存错误不应影响业务流程
    }
  }

  /**
   * JSON reviver 函数
   * 处理特殊值（Infinity, -Infinity, NaN）
   */
  private reviver(_key: string, value: any): any {
    if (value === '__INFINITY__') return Infinity;
    if (value === '__NEG_INFINITY__') return -Infinity;
    if (value === '__NAN__') return NaN;
    return value;
  }

  /**
   * JSON replacer 函数
   * 转换特殊值为字符串表示
   */
  private replacer(_key: string, value: any): any {
    if (value === Infinity) return '__INFINITY__';
    if (value === -Infinity) return '__NEG_INFINITY__';
    if (Number.isNaN(value)) return '__NAN__';
    return value;
  }

  /**
   * 设置缓存值
   */
  async set(key: string, value: any, ttl: number): Promise<void> {
    try {
      const serialized = JSON.stringify(value, this.replacer);
      await this.redisClient.setex(key, ttl, serialized);
      
      logger.debug('Cache set successfully', { key, ttl });
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      logError(err, { context: 'Failed to set cache value', key });
      // 缓存错误不应影响业务流程
    }
  }

  /**
   * 删除缓存值
   */
  async delete(key: string): Promise<void> {
    try {
      await this.redisClient.del(key);
      logger.debug('Cache entry deleted', { key });
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      logError(err, { context: 'Failed to delete cache entry', key });
    }
  }

  /**
   * 删除匹配模式的所有缓存
   */
  async deletePattern(pattern: string): Promise<void> {
    try {
      // 查找所有匹配的键
      const keys = await this.redisClient.keys(pattern);
      
      if (keys.length === 0) {
        logger.debug('No cache entries found matching pattern', { pattern });
        return;
      }

      // 批量删除
      await this.redisClient.del(...keys);
      
      logger.debug('Cache entries deleted by pattern', { pattern, count: keys.length });
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      logError(err, { context: 'Failed to delete cache entries by pattern', pattern });
    }
  }
}
```

---

## 缓存策略

### 1. 翻译缓存

**缓存键格式**:

```
config:{configId}:lang:{languageCode}
```

**示例**:

```
config:1:lang:zh-cn
config:1:lang:en-us
config:2:lang:ja-jp
```

**TTL**: 3600 秒（1 小时）

**实现**:

```typescript
// TranslationService.ts
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

  // 3. 缓存结果
  const response = this.toResponse(translation);
  await this.cacheManager.set(cacheKey, response, 3600);

  return response;
}

private getCacheKey(configId: number, languageCode: string): string {
  return `config:${configId}:lang:${languageCode}`;
}
```

### 2. 域名配置缓存

**缓存键格式**:

```
domain:config:{domain}
```

**示例**:

```
domain:config:example.com
domain:config:www.baidu.com
```

**TTL**: 3600 秒（1 小时）

**实现**:

```typescript
// CacheService.ts
export const CACHE_KEY_PREFIX = 'domain:config:';

async get<T>(key: string): Promise<T | null> {
  if (!this.isEnabled()) {
    return null;
  }

  const client = getRedisClient();
  if (!client) {
    return null;
  }

  const cacheKey = `${CACHE_KEY_PREFIX}${key}`;

  try {
    const data = await client.get(cacheKey);
    
    if (data === null) {
      logger.debug('缓存未命中', { key: cacheKey });
      return null;
    }

    logger.debug('缓存命中', { key: cacheKey });
    return JSON.parse(data) as T;
  } catch (error) {
    logError(error, { context: '获取缓存数据失败', key: cacheKey });
    return null;
  }
}

async set<T>(key: string, value: T, ttl?: number): Promise<void> {
  if (!this.isEnabled()) {
    return;
  }

  const client = getRedisClient();
  if (!client) {
    return;
  }

  const cacheKey = `${CACHE_KEY_PREFIX}${key}`;
  const expireTime = ttl ?? config.redisTtl;

  try {
    const serialized = JSON.stringify(value);
    await client.setex(cacheKey, expireTime, serialized);
    
    logger.debug('缓存设置成功', { key: cacheKey, ttl: expireTime });
  } catch (error) {
    logError(error, { context: '设置缓存数据失败', key: cacheKey });
  }
}
```

---

## 缓存失效

### 1. 单个缓存失效

当翻译被更新或删除时，失效对应的缓存：

```typescript
// TranslationService.ts
async updateTranslation(
  configId: number,
  languageCode: string,
  data: UpdateTranslationDTO
): Promise<TranslationResponse> {
  // ... 更新逻辑

  // 失效缓存
  await this.invalidateCache(configId, normalizedLang);

  return this.toResponse(translation);
}

private async invalidateCache(configId: number, languageCode: string): Promise<void> {
  const cacheKey = this.getCacheKey(configId, languageCode);
  await this.cacheManager.delete(cacheKey);
}
```

### 2. 批量缓存失效

当配置被删除时，失效所有语言的缓存：

```typescript
// TranslationService.ts
async invalidateAllCachesForConfig(configId: number): Promise<void> {
  const pattern = `config:${configId}:lang:*`;
  await this.cacheManager.deletePattern(pattern);
  
  logger.info('Invalidated all caches for config', { configId });
}

// ConfigService.ts
async delete(id: number): Promise<boolean> {
  // ... 删除逻辑

  // 如果启用了多语言支持，失效所有语言的缓存
  if (this.translationService) {
    await this.translationService.invalidateAllCachesForConfig(id);
  }

  // ... 继续删除
}
```

### 3. 模式匹配删除

使用 Redis KEYS 命令查找匹配的键，然后批量删除：

```typescript
async deletePattern(pattern: string): Promise<void> {
  try {
    // 1. 查找所有匹配的键
    const keys = await this.redisClient.keys(pattern);
    
    if (keys.length === 0) {
      return;
    }

    // 2. 批量删除
    await this.redisClient.del(...keys);
    
    logger.debug('Cache entries deleted by pattern', { pattern, count: keys.length });
  } catch (error) {
    logError(error, { context: 'Failed to delete cache entries by pattern', pattern });
  }
}
```

**注意**: `KEYS` 命令在生产环境中可能影响性能，建议使用 `SCAN` 命令替代。

---

## 性能优化

### 1. 缓存预热

在应用启动时预加载热门数据：

```typescript
async function warmupCache() {
  logger.info('开始缓存预热');

  // 获取热门配置列表
  const hotConfigs = await getHotConfigs();

  // 预加载所有语言的翻译
  for (const config of hotConfigs) {
    for (const lang of supportedLanguages) {
      await translationService.getTranslation(config.id, lang);
    }
  }

  logger.info('缓存预热完成', { count: hotConfigs.length });
}
```

### 2. 缓存穿透防护

使用空值缓存防止缓存穿透：

```typescript
async getTranslation(configId: number, languageCode: string): Promise<TranslationResponse | null> {
  const cacheKey = this.getCacheKey(configId, languageCode);
  
  // 1. 检查缓存
  const cached = await this.cacheManager.get<TranslationResponse | 'NULL'>(cacheKey);
  if (cached === 'NULL') {
    // 缓存的空值，直接返回 null
    return null;
  }
  if (cached) {
    return cached;
  }

  // 2. 查询数据库
  const translation = await this.translationModel.findOne({
    where: { configId, languageCode },
  });

  if (!translation) {
    // 缓存空值，防止穿透（TTL 较短）
    await this.cacheManager.set(cacheKey, 'NULL', 60);
    return null;
  }

  // 3. 缓存结果
  const response = this.toResponse(translation);
  await this.cacheManager.set(cacheKey, response, 3600);

  return response;
}
```

### 3. 缓存雪崩防护

使用随机 TTL 防止缓存雪崩：

```typescript
async set(key: string, value: any, baseTtl: number): Promise<void> {
  // 添加随机偏移（±10%）
  const randomOffset = Math.floor(baseTtl * 0.1 * (Math.random() * 2 - 1));
  const ttl = baseTtl + randomOffset;

  const serialized = JSON.stringify(value, this.replacer);
  await this.redisClient.setex(key, ttl, serialized);
}
```

### 4. 批量操作优化

使用 Redis Pipeline 批量操作：

```typescript
async batchGet<T>(keys: string[]): Promise<Map<string, T | null>> {
  const pipeline = this.redisClient.pipeline();
  
  // 批量获取
  for (const key of keys) {
    pipeline.get(key);
  }

  const results = await pipeline.exec();
  const map = new Map<string, T | null>();

  for (let i = 0; i < keys.length; i++) {
    const [error, value] = results![i];
    if (error || value === null) {
      map.set(keys[i], null);
    } else {
      map.set(keys[i], JSON.parse(value as string) as T);
    }
  }

  return map;
}
```

---

## 监控和调试

### 1. 缓存命中率监控

```typescript
let cacheHits = 0;
let cacheMisses = 0;

async get<T>(key: string): Promise<T | null> {
  const value = await this.redisClient.get(key);
  
  if (value === null) {
    cacheMisses++;
    logger.debug('Cache miss', { key, hitRate: this.getHitRate() });
    return null;
  }

  cacheHits++;
  logger.debug('Cache hit', { key, hitRate: this.getHitRate() });
  return JSON.parse(value) as T;
}

private getHitRate(): number {
  const total = cacheHits + cacheMisses;
  return total === 0 ? 0 : (cacheHits / total) * 100;
}
```

### 2. 缓存大小监控

```typescript
async getCacheStats(): Promise<{
  keys: number;
  memory: string;
  hitRate: number;
}> {
  const info = await this.redisClient.info('stats');
  const memory = await this.redisClient.info('memory');
  
  // 解析 Redis INFO 输出
  const keys = await this.redisClient.dbsize();
  
  return {
    keys,
    memory: this.parseMemoryUsage(memory),
    hitRate: this.getHitRate(),
  };
}
```

### 3. 调试工具

```typescript
// 列出所有缓存键
async listAllKeys(): Promise<string[]> {
  return await this.redisClient.keys('*');
}

// 查看缓存内容
async inspectCache(key: string): Promise<{
  value: any;
  ttl: number;
}> {
  const value = await this.redisClient.get(key);
  const ttl = await this.redisClient.ttl(key);
  
  return {
    value: value ? JSON.parse(value) : null,
    ttl,
  };
}

// 清空所有缓存
async flushAll(): Promise<void> {
  await this.redisClient.flushdb();
  logger.warn('All cache entries flushed');
}
```

---

## 最佳实践

### 1. 错误处理

缓存错误不应影响业务流程：

```typescript
try {
  const cached = await cacheManager.get(key);
  if (cached) {
    return cached;
  }
} catch (error) {
  logger.error('Cache error, falling back to database', { error });
  // 继续从数据库查询
}
```

### 2. TTL 设置

根据数据更新频率设置合适的 TTL：

- **热门数据**: 3600 秒（1 小时）
- **冷门数据**: 7200 秒（2 小时）
- **空值缓存**: 60 秒（1 分钟）

### 3. 键命名规范

使用清晰的命名规范：

```
{namespace}:{entity}:{id}:{attribute}
```

示例：

```
config:1:lang:zh-cn
domain:config:example.com
user:session:abc123
```

### 4. 缓存更新策略

- **Cache Aside**: 先更新数据库，再删除缓存（推荐）
- **Write Through**: 同时更新数据库和缓存
- **Write Behind**: 先更新缓存，异步更新数据库

---

## 测试建议

### 1. 单元测试

- 测试缓存命中和未命中
- 测试缓存失效
- 测试错误处理

### 2. 集成测试

- 测试 Redis 连接
- 测试缓存和数据库一致性
- 测试并发访问

### 3. 性能测试

- 测试缓存命中率
- 测试响应时间改善
- 测试高并发场景

---

## 相关文档

- [AI_REBUILD_02_TECH_STACK.md](./AI_REBUILD_02_TECH_STACK.md) - 技术栈
- [AI_REBUILD_05_MODULES.md](./AI_REBUILD_05_MODULES.md) - 核心模块
- [AI_REBUILD_07_I18N.md](./AI_REBUILD_07_I18N.md) - 国际化实现
- [AI_REBUILD_10_DEPLOYMENT.md](./AI_REBUILD_10_DEPLOYMENT.md) - 部署指南
