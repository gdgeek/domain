# AI 重建指南 06 - 中间件系统

## 概述

本文档详细说明项目的中间件系统实现，包括认证、日志、限流、错误处理、验证等核心中间件的设计和使用。

## 目录

- [中间件架构](#中间件架构)
- [认证中间件](#认证中间件)
- [日志中间件](#日志中间件)
- [限流中间件](#限流中间件)
- [错误处理中间件](#错误处理中间件)
- [验证中间件](#验证中间件)
- [其他中间件](#其他中间件)
- [中间件执行顺序](#中间件执行顺序)

---

## 中间件架构

### 中间件执行流程

```
请求 → 基础中间件 → 请求处理中间件 → 安全中间件 → 路由 → 错误处理
```

### 中间件分类

1. **基础中间件**: JSON 解析、URL 编码
2. **请求处理中间件**: 请求 ID、日志、限流、监控
3. **安全中间件**: CORS、JWT 认证
4. **验证中间件**: 请求数据验证
5. **错误处理中间件**: 全局错误捕获和响应

---

## 认证中间件

### 文件位置

`src/middleware/AuthMiddleware.ts`

### 功能说明

实现基于 JWT 的认证机制，区分读写操作的访问权限。

### 安全策略

- **GET 请求**: 公开访问，不需要认证
- **POST/PUT/DELETE 请求**: 需要有效的 JWT 令牌

### 核心函数

#### 1. 生成 JWT 令牌

```typescript
export function generateToken(): string {
  const payload: JwtPayload = {
    role: 'admin',
  };

  return jwt.sign(payload, JWT_SECRET, {
    expiresIn: JWT_EXPIRES_IN,  // 默认 24 小时
  });
}
```

#### 2. 验证 JWT 令牌

```typescript
export function verifyToken(token: string): JwtPayload | null {
  try {
    const decoded = jwt.verify(token, JWT_SECRET) as JwtPayload;
    return decoded;
  } catch (error: any) {
    logger.warn('JWT 令牌验证失败', { error: error.message });
    return null;
  }
}
```

#### 3. 认证中间件

```typescript
export function authMiddleware(req: Request, res: Response, next: NextFunction): void {
  const method = req.method;

  // GET 和 OPTIONS 请求：允许公开访问
  if (method === 'GET' || method === 'OPTIONS') {
    next();
    return;
  }

  // POST/PUT/DELETE 请求：需要认证
  const authHeader = req.headers.authorization;
  
  if (!authHeader) {
    res.status(401).json({
      error: {
        code: 'UNAUTHORIZED',
        message: '此操作需要管理员认证。请先登录获取令牌。',
      },
    });
    return;
  }

  // 验证令牌格式：Bearer <token>
  const parts = authHeader.split(' ');
  if (parts.length !== 2 || parts[0] !== 'Bearer') {
    res.status(401).json({
      error: {
        code: 'INVALID_TOKEN_FORMAT',
        message: '无效的认证令牌格式。格式应为: Bearer <token>',
      },
    });
    return;
  }

  const token = parts[1];

  // 验证 JWT 令牌
  const payload = verifyToken(token);
  
  if (!payload) {
    res.status(403).json({
      error: {
        code: 'INVALID_TOKEN',
        message: '无效或过期的认证令牌。请重新登录。',
      },
    });
    return;
  }

  // 认证通过，将用户信息附加到请求对象
  (req as any).user = payload;

  next();
}
```

### 环境变量配置

```bash
# JWT 密钥（如果未设置，使用管理员密码）
JWT_SECRET=your-secret-key

# JWT 过期时间（默认 24 小时）
JWT_EXPIRES_IN=24h
```

### 使用示例

```typescript
// 在 app.ts 中应用到特定路由
app.use(`${config.apiPrefix}/domains`, authMiddleware);
app.use(`${config.apiPrefix}/configs`, authMiddleware);
```

### CORS 中间件

```typescript
export function corsMiddleware(req: Request, res: Response, next: NextFunction): void {
  // 对所有请求设置 CORS 头
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  res.setHeader('Access-Control-Max-Age', '86400'); // 24小时

  // OPTIONS 预检请求
  if (req.method === 'OPTIONS') {
    res.status(204).end();
    return;
  }

  next();
}
```

---

## 日志中间件

### 文件位置

`src/middleware/LoggingMiddleware.ts`

### 功能说明

记录每个请求的详细信息，包括请求 ID、HTTP 方法、URL、客户端 IP、响应状态码和响应时间。

### 实现代码

```typescript
export function loggingMiddleware(
  req: Request,
  res: Response,
  next: NextFunction
): void {
  // 记录请求开始时间
  const startTime = Date.now();

  // 记录请求日志
  logger.info('Incoming request', {
    requestId: req.requestId,
    method: req.method,
    url: req.url,
    ip: req.ip,
    userAgent: req.get('user-agent'),
  });

  // 监听响应完成事件
  res.on('finish', () => {
    const duration = Date.now() - startTime;
    const logLevel = res.statusCode >= 400 ? 'warn' : 'info';

    // 记录响应日志
    logger.log(logLevel, 'Request completed', {
      requestId: req.requestId,
      method: req.method,
      url: req.url,
      statusCode: res.statusCode,
      duration: `${duration}ms`,
      ip: req.ip,
    });
  });

  next();
}
```

### 日志格式

```json
{
  "level": "info",
  "message": "Incoming request",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "requestId": "abc123",
  "method": "GET",
  "url": "/api/v1/domains/example.com",
  "ip": "127.0.0.1",
  "userAgent": "Mozilla/5.0..."
}
```

### 使用示例

```typescript
// 在 app.ts 中全局应用
app.use(loggingMiddleware);
```

---

## 限流中间件

### 文件位置

`src/middleware/RateLimitMiddleware.ts`

### 功能说明

提供 API 限流功能，防止滥用和保护系统资源。基于 IP 地址进行限流。

### 实现代码

```typescript
import rateLimit from 'express-rate-limit';
import { config } from '../config/env';

export const rateLimitMiddleware = rateLimit({
  // 时间窗口（毫秒）
  windowMs: config.rateLimitWindowMs,  // 默认 60000（1分钟）
  
  // 时间窗口内最大请求数
  max: config.rateLimitMax,  // 默认 100
  
  // 标准化错误响应格式
  handler: (_req, res) => {
    res.status(429).json({
      error: {
        code: 'RATE_LIMIT_EXCEEDED',
        message: '请求过于频繁，请稍后再试',
      },
    });
  },
  
  // 跳过成功的响应计数（false 表示所有请求都计数）
  skipSuccessfulRequests: false,
  
  // 跳过失败的响应计数（false 表示所有请求都计数）
  skipFailedRequests: false,
  
  // 标准化响应头
  standardHeaders: true,  // 返回 RateLimit-* 响应头
  legacyHeaders: false,   // 禁用 X-RateLimit-* 响应头
});
```

### 环境变量配置

```bash
# 限流时间窗口（毫秒），默认 60000（1分钟）
RATE_LIMIT_WINDOW_MS=60000

# 时间窗口内最大请求数，默认 100
RATE_LIMIT_MAX=100
```

### 响应头

当请求被限流时，响应会包含以下头部：

```
RateLimit-Limit: 100
RateLimit-Remaining: 0
RateLimit-Reset: 1640000000
```

### 使用示例

```typescript
// 在 app.ts 中全局应用
app.use(rateLimitMiddleware);
```

---

## 错误处理中间件

### 文件位置

`src/middleware/ErrorMiddleware.ts`

### 功能说明

提供全局错误处理和异步路由包装器，捕获所有错误并返回标准化的错误响应。

### 错误类型

项目定义了以下自定义错误类型：

1. **ValidationError**: 请求数据验证失败（400）
2. **NotFoundError**: 资源不存在（404）
3. **ConflictError**: 资源冲突（409）
4. **DatabaseError**: 数据库操作失败（500）

### 全局错误处理器

```typescript
export function errorHandler(
  err: Error,
  req: Request,
  res: Response,
  _next: NextFunction
): void {
  // 记录错误日志
  logError(err, {
    requestId: (req as any).requestId,
    method: req.method,
    url: req.url,
    ip: req.ip,
  });

  // 构建错误响应
  const errorResponse: ErrorResponse = {
    error: {
      code: 'INTERNAL_ERROR',
      message: '服务器内部错误',
    },
  };

  let statusCode = 500;

  // 根据错误类型设置响应
  if (err instanceof ValidationError) {
    statusCode = 400;
    errorResponse.error.code = err.code;
    errorResponse.error.message = err.message;
    if (err.details) {
      errorResponse.error.details = err.details;
    }
  } else if (err instanceof NotFoundError) {
    statusCode = 404;
    errorResponse.error.code = err.code;
    errorResponse.error.message = err.message;
  } else if (err instanceof ConflictError) {
    statusCode = 409;
    errorResponse.error.code = err.code;
    errorResponse.error.message = err.message;
  } else if (err instanceof DatabaseError) {
    statusCode = 500;
    errorResponse.error.code = err.code;
    errorResponse.error.message = err.message;
  }

  // 发送错误响应
  res.status(statusCode).json(errorResponse);
}
```

### 异步路由包装器

```typescript
export function asyncHandler(fn: AsyncRequestHandler): RequestHandler {
  return (req: Request, res: Response, next: NextFunction) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
}
```

### 使用示例

```typescript
// 在路由中使用 asyncHandler
router.get('/domains/:domain', asyncHandler(async (req, res) => {
  const domain = await service.getByDomain(req.params.domain);
  if (!domain) {
    throw new NotFoundError('域名不存在', 'DOMAIN_NOT_FOUND');
  }
  res.json({ data: domain });
}));

// 在 app.ts 中应用全局错误处理器（必须在所有路由之后）
app.use(errorHandler);
```

### 错误响应格式

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求数据验证失败",
    "details": {
      "errors": [
        {
          "field": "domain",
          "message": "domain is required",
          "type": "any.required"
        }
      ]
    }
  }
}
```

---

## 验证中间件

### 文件位置

`src/middleware/ValidationMiddleware.ts`

### 功能说明

提供请求数据验证中间件，支持验证请求体、查询参数和路径参数。使用 Joi 进行数据验证。

### 核心函数

#### 1. 通用验证函数

```typescript
export function validateRequest(
  schema: Joi.Schema,
  type: 'body' | 'query' | 'params'
): RequestHandler {
  return (req: Request, _res: Response, next: NextFunction): void => {
    // 获取要验证的数据
    const dataToValidate = req[type];

    // 执行验证
    const { error, value } = schema.validate(dataToValidate, {
      abortEarly: false,    // 收集所有错误
      stripUnknown: true,   // 移除未定义的字段
      convert: true,        // 自动类型转换
    });

    if (error) {
      // 将 Joi 错误转换为标准化的错误详情格式
      const errors = error.details.map((detail) => ({
        field: detail.path.join('.'),
        message: detail.message,
        type: detail.type,
      }));

      // 抛出 ValidationError
      return next(
        new ValidationError(
          '请求数据验证失败',
          'VALIDATION_ERROR',
          { errors }
        )
      );
    }

    // 将验证后的值替换原始数据
    req[type] = value;

    next();
  };
}
```

#### 2. 便捷函数

```typescript
// 验证请求体
export function validateBody(schema: Joi.Schema): RequestHandler {
  return validateRequest(schema, 'body');
}

// 验证查询参数
export function validateQuery(schema: Joi.Schema): RequestHandler {
  return validateRequest(schema, 'query');
}

// 验证路径参数
export function validateParams(schema: Joi.Schema): RequestHandler {
  return validateRequest(schema, 'params');
}
```

### 验证 Schema 示例

```typescript
// src/validation/schemas.ts
import Joi from 'joi';

// 创建域名的验证 schema
export const createDomainSchema = Joi.object({
  domain: Joi.string().required().min(1).max(255),
  configId: Joi.number().integer().positive().required(),
  homepage: Joi.string().uri().allow(null).optional(),
});

// 分页查询的验证 schema
export const paginationSchema = Joi.object({
  page: Joi.number().integer().min(1).default(1),
  pageSize: Joi.number().integer().min(1).max(100).default(10),
});

// 域名参数的验证 schema
export const domainParamSchema = Joi.object({
  domain: Joi.string().required(),
});
```

### 使用示例

```typescript
import { validateBody, validateQuery, validateParams } from '../middleware/ValidationMiddleware';
import { createDomainSchema, paginationSchema, domainParamSchema } from '../validation/schemas';

// 验证请求体
router.post('/domains', validateBody(createDomainSchema), handler);

// 验证查询参数
router.get('/domains', validateQuery(paginationSchema), handler);

// 验证路径参数
router.get('/domains/:domain', validateParams(domainParamSchema), handler);
```

---

## 其他中间件

### 1. RequestIdMiddleware

**文件**: `src/middleware/RequestIdMiddleware.ts`

**功能**: 为每个请求生成唯一的请求 ID，用于日志追踪

```typescript
export function requestIdMiddleware(
  req: Request,
  _res: Response,
  next: NextFunction
): void {
  req.requestId = uuidv4();
  next();
}
```

### 2. JsonResponseMiddleware

**文件**: `src/middleware/JsonResponseMiddleware.ts`

**功能**: 确保所有响应都是 JSON 格式

```typescript
export function jsonResponseMiddleware(
  _req: Request,
  res: Response,
  next: NextFunction
): void {
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  next();
}
```

### 3. MetricsMiddleware

**文件**: `src/middleware/MetricsMiddleware.ts`

**功能**: 收集 API 请求的监控指标（请求数、响应时间等）

```typescript
export function metricsMiddleware(
  req: Request,
  res: Response,
  next: NextFunction
): void {
  const startTime = Date.now();

  res.on('finish', () => {
    const duration = (Date.now() - startTime) / 1000;
    
    // 记录请求计数
    httpRequestsTotal.inc({
      method: req.method,
      route: req.route?.path || req.path,
      status: res.statusCode,
    });

    // 记录响应时间
    httpRequestDuration.observe(
      {
        method: req.method,
        route: req.route?.path || req.path,
        status: res.statusCode,
      },
      duration
    );
  });

  next();
}
```

### 4. WriteProtectionMiddleware

**文件**: `src/middleware/WriteProtectionMiddleware.ts`

**功能**: 保护特定资源不被修改或删除

```typescript
export function writeProtectionMiddleware(
  protectedIds: number[]
): RequestHandler {
  return (req: Request, res: Response, next: NextFunction): void {
    const id = parseInt(req.params.id);
    
    if (protectedIds.includes(id)) {
      res.status(403).json({
        error: {
          code: 'WRITE_PROTECTED',
          message: '此资源受保护，不能修改或删除',
        },
      });
      return;
    }

    next();
  };
}
```

---

## 中间件执行顺序

在 `src/app.ts` 中，中间件的执行顺序非常重要：

```typescript
export function createApp(): Express {
  const app = express();

  // 1. 基础中间件
  app.use(express.json());
  app.use(express.urlencoded({ extended: true }));

  // 2. 请求处理中间件（按顺序执行）
  app.use(requestIdMiddleware);        // 生成请求 ID
  app.use(jsonResponseMiddleware);     // 设置 JSON 响应头
  app.use(metricsMiddleware);          // 收集监控指标
  app.use(loggingMiddleware);          // 记录请求日志
  app.use(rateLimitMiddleware);        // 限流

  // 3. 安全中间件
  app.use(corsMiddleware);             // CORS
  app.use(`${config.apiPrefix}/domains`, authMiddleware);  // JWT 认证
  app.use(`${config.apiPrefix}/configs`, authMiddleware);

  // 4. API 路由
  app.use(`${config.apiPrefix}/domains`, domainRoutes);
  app.use(`${config.apiPrefix}/configs`, configRoutes);
  // ... 其他路由

  // 5. 静态文件服务
  app.use(express.static('public'));

  // 6. 404 处理
  app.use((_req: Request, res: Response) => {
    res.status(404).json({
      error: {
        code: 'NOT_FOUND',
        message: '请求的资源不存在',
      },
    });
  });

  // 7. 全局错误处理（必须在最后）
  app.use(errorHandler);

  return app;
}
```

### 执行顺序说明

1. **基础中间件**: 必须最先执行，解析请求体
2. **请求 ID**: 尽早生成，用于后续日志追踪
3. **日志和监控**: 在业务逻辑之前记录
4. **限流**: 在认证之前执行，节省资源
5. **认证**: 在路由之前验证权限
6. **路由**: 处理业务逻辑
7. **404 处理**: 在所有路由之后
8. **错误处理**: 必须在最后，捕获所有错误

---

## 测试建议

### 1. 认证中间件测试

- 测试 GET 请求无需认证
- 测试 POST/PUT/DELETE 请求需要认证
- 测试无效令牌被拒绝
- 测试过期令牌被拒绝

### 2. 验证中间件测试

- 测试有效数据通过验证
- 测试无效数据被拒绝
- 测试错误消息格式正确
- 测试类型转换功能

### 3. 错误处理测试

- 测试不同错误类型返回正确状态码
- 测试错误响应格式标准化
- 测试异步错误被正确捕获

---

## 相关文档

- [AI_REBUILD_04_API.md](./AI_REBUILD_04_API.md) - API 设计
- [AI_REBUILD_05_MODULES.md](./AI_REBUILD_05_MODULES.md) - 核心模块
- [AI_REBUILD_09_SECURITY.md](./AI_REBUILD_09_SECURITY.md) - 安全机制
