# AI 重建指南 09 - 安全机制

## 概述

本文档详细说明项目的安全机制实现，包括 JWT 认证、权限管理、数据验证、安全配置和最佳实践。

## 目录

- [安全架构](#安全架构)
- [JWT 认证](#jwt-认证)
- [权限管理](#权限管理)
- [数据验证](#数据验证)
- [安全配置](#安全配置)
- [安全最佳实践](#安全最佳实践)

---

## 安全架构

### 安全层次

```
┌─────────────────────────────────────┐
│         HTTP Request                 │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      CORS Middleware                 │
│  跨域访问控制                         │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Rate Limit Middleware           │
│  限流保护                             │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Auth Middleware                 │
│  JWT 认证（写操作）                   │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Validation Middleware           │
│  请求数据验证                         │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Business Logic                  │
│  业务逻辑处理                         │
└─────────────────────────────────────┘
```

### 安全策略

1. **读写分离**: GET 请求公开，POST/PUT/DELETE 需要认证
2. **JWT 认证**: 基于令牌的无状态认证
3. **限流保护**: 防止 API 滥用
4. **数据验证**: 严格的输入验证
5. **错误处理**: 不泄露敏感信息

---

## JWT 认证

### JWT 工作流程

```
1. 用户登录 → 验证密码
2. 生成 JWT 令牌 → 返回给客户端
3. 客户端存储令牌 → 后续请求携带
4. 服务器验证令牌 → 允许/拒绝访问
```

### 登录接口

**端点**: `POST /api/v1/sessions`

**请求**:

```json
{
  "password": "admin123"
}
```

**响应**:

```json
{
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expiresIn": "24h"
  }
}
```

**实现**:

```typescript
// src/routes/SessionRoutes.ts
router.post('/', validateBody(loginSchema), asyncHandler(async (req: Request, res: Response) => {
  const { password } = req.body;

  // 验证密码
  if (password !== config.adminPassword) {
    throw new ValidationError('密码错误', 'INVALID_PASSWORD');
  }

  // 生成 JWT 令牌
  const token = generateToken();

  res.json({
    data: {
      token,
      expiresIn: JWT_EXPIRES_IN,
    },
  });
}));
```

### JWT 令牌生成

```typescript
// src/middleware/AuthMiddleware.ts
import jwt from 'jsonwebtoken';

const JWT_SECRET = process.env.JWT_SECRET || config.adminPassword;
const JWT_EXPIRES_IN = process.env.JWT_EXPIRES_IN || '24h';

export interface JwtPayload {
  role: 'admin';
  iat?: number;
  exp?: number;
}

export function generateToken(): string {
  const payload: JwtPayload = {
    role: 'admin',
  };

  return jwt.sign(payload, JWT_SECRET, {
    expiresIn: JWT_EXPIRES_IN,
  });
}
```

### JWT 令牌验证

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

### 认证中间件

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

### 使用示例

```typescript
// 在 app.ts 中应用到特定路由
app.use(`${config.apiPrefix}/domains`, authMiddleware);
app.use(`${config.apiPrefix}/configs`, authMiddleware);

// 在客户端使用
const token = localStorage.getItem('token');
fetch('/api/v1/configs', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(data),
});
```

---

## 权限管理

### 权限模型

项目使用简单的角色权限模型：

- **公开访问**: GET 请求（读取数据）
- **管理员**: POST/PUT/DELETE 请求（写入数据）

### 权限配置字段

配置表包含 `permissions` 字段，用于存储细粒度权限：

```typescript
export interface ConfigAttributes {
  // ... 其他字段
  permissions: object | null;  // 权限配置（JSON）
}
```

**权限配置示例**:

```json
{
  "permissions": {
    "read": ["public"],
    "write": ["admin"],
    "delete": ["admin"],
    "features": {
      "translation": true,
      "cache": true
    }
  }
}
```

### 写保护中间件

保护特定资源不被修改或删除：

```typescript
// src/middleware/WriteProtectionMiddleware.ts
export function writeProtectionMiddleware(
  protectedIds: number[]
): RequestHandler {
  return (req: Request, res: Response, next: NextFunction): void => {
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

// 使用示例
router.delete('/:id', 
  writeProtectionMiddleware([1, 2, 3]),  // 保护 ID 1, 2, 3
  asyncHandler(async (req, res) => {
    // 删除逻辑
  })
);
```

---

## 数据验证

### Joi 验证 Schema

使用 Joi 库进行数据验证：

```typescript
// src/validation/schemas.ts
import Joi from 'joi';

// 创建配置的验证 schema
export const createConfigSchema = Joi.object({
  title: Joi.string().max(255).allow(null).optional(),
  author: Joi.string().max(255).allow(null).optional(),
  description: Joi.string().max(255).allow(null).optional(),
  keywords: Joi.string().max(255).allow(null).optional(),
  links: Joi.object().allow(null).optional(),
  permissions: Joi.object().allow(null).optional(),
});

// 创建域名的验证 schema
export const createDomainSchema = Joi.object({
  domain: Joi.string().required().min(1).max(255),
  configId: Joi.number().integer().positive().required(),
  homepage: Joi.string().uri().allow(null).optional(),
});

// 创建翻译的验证 schema
export const createTranslationSchema = Joi.object({
  languageCode: Joi.string().required().min(2).max(10),
  title: Joi.string().required().max(200),
  author: Joi.string().required().max(100),
  description: Joi.string().required().max(1000),
  keywords: Joi.array().items(Joi.string()).required(),
});

// 分页查询的验证 schema
export const paginationSchema = Joi.object({
  page: Joi.number().integer().min(1).default(1),
  pageSize: Joi.number().integer().min(1).max(100).default(10),
});

// 登录的验证 schema
export const loginSchema = Joi.object({
  password: Joi.string().required().min(1),
});
```

### 验证中间件

```typescript
// src/middleware/ValidationMiddleware.ts
export function validateRequest(
  schema: Joi.Schema,
  type: 'body' | 'query' | 'params'
): RequestHandler {
  return (req: Request, _res: Response, next: NextFunction): void => {
    const dataToValidate = req[type];

    const { error, value } = schema.validate(dataToValidate, {
      abortEarly: false,    // 收集所有错误
      stripUnknown: true,   // 移除未定义的字段
      convert: true,        // 自动类型转换
    });

    if (error) {
      const errors = error.details.map((detail) => ({
        field: detail.path.join('.'),
        message: detail.message,
        type: detail.type,
      }));

      return next(
        new ValidationError(
          '请求数据验证失败',
          'VALIDATION_ERROR',
          { errors }
        )
      );
    }

    req[type] = value;
    next();
  };
}
```

### 使用示例

```typescript
// 在路由中使用验证中间件
router.post('/configs', 
  validateBody(createConfigSchema),
  asyncHandler(async (req, res) => {
    const config = await configService.create(req.body);
    res.status(201).json({ data: config });
  })
);

router.post('/domains', 
  validateBody(createDomainSchema),
  asyncHandler(async (req, res) => {
    const domain = await domainService.create(req.body);
    res.status(201).json({ data: domain });
  })
);
```

---

## 安全配置

### 环境变量

```bash
# JWT 配置
JWT_SECRET=your-secret-key-change-in-production
JWT_EXPIRES_IN=24h

# 管理员密码
ADMIN_PASSWORD=admin123

# 限流配置
RATE_LIMIT_WINDOW_MS=60000  # 1 分钟
RATE_LIMIT_MAX=100          # 最大请求数

# CORS 配置
CORS_ORIGIN=*               # 生产环境应设置具体域名

# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your-db-password
DB_NAME=domain_config
```

### 生产环境配置

**重要**: 在生产环境中必须修改以下配置：

1. **JWT_SECRET**: 使用强随机密钥

```bash
# 生成随机密钥
openssl rand -base64 32
```

2. **ADMIN_PASSWORD**: 使用强密码

```bash
# 至少 12 位，包含大小写字母、数字和特殊字符
ADMIN_PASSWORD=MyStr0ng!P@ssw0rd2024
```

3. **CORS_ORIGIN**: 限制允许的域名

```bash
# 只允许特定域名
CORS_ORIGIN=https://yourdomain.com

# 允许多个域名（逗号分隔）
CORS_ORIGIN=https://yourdomain.com,https://admin.yourdomain.com
```

4. **限流配置**: 根据实际需求调整

```bash
# 更严格的限流
RATE_LIMIT_WINDOW_MS=60000
RATE_LIMIT_MAX=50
```

### HTTPS 配置

在生产环境中，必须使用 HTTPS：

```nginx
# Nginx 配置示例
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# HTTP 重定向到 HTTPS
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

---

## 安全最佳实践

### 1. 密码管理

- 使用环境变量存储密码
- 不要在代码中硬编码密码
- 定期更换密码
- 使用强密码策略

```typescript
// ❌ 错误：硬编码密码
const password = 'admin123';

// ✅ 正确：从环境变量读取
const password = process.env.ADMIN_PASSWORD;
```

### 2. JWT 密钥管理

- 使用强随机密钥
- 定期轮换密钥
- 不要在客户端存储密钥

```typescript
// ❌ 错误：使用弱密钥
const JWT_SECRET = 'secret';

// ✅ 正确：使用强随机密钥
const JWT_SECRET = process.env.JWT_SECRET || crypto.randomBytes(32).toString('hex');
```

### 3. 错误处理

- 不要在错误响应中泄露敏感信息
- 记录详细错误到日志
- 返回通用错误消息给客户端

```typescript
// ❌ 错误：泄露数据库错误
catch (error) {
  res.status(500).json({ error: error.message });
}

// ✅ 正确：返回通用错误
catch (error) {
  logger.error('Database error', { error });
  res.status(500).json({
    error: {
      code: 'INTERNAL_ERROR',
      message: '服务器内部错误',
    },
  });
}
```

### 4. SQL 注入防护

使用 ORM（Sequelize）自动防护 SQL 注入：

```typescript
// ✅ Sequelize 自动转义参数
const domain = await Domain.findOne({
  where: { domain: userInput },
});

// ❌ 不要使用原始 SQL 拼接
const query = `SELECT * FROM domains WHERE domain = '${userInput}'`;
```

### 5. XSS 防护

- 验证和清理用户输入
- 使用 Content-Security-Policy 头
- 转义输出内容

```typescript
// 设置 CSP 头
app.use((req, res, next) => {
  res.setHeader(
    'Content-Security-Policy',
    "default-src 'self'; script-src 'self' 'unsafe-inline' cdn.jsdelivr.net"
  );
  next();
});
```

### 6. CSRF 防护

对于有状态的应用，使用 CSRF 令牌：

```typescript
import csrf from 'csurf';

// 启用 CSRF 保护
const csrfProtection = csrf({ cookie: true });

app.post('/api/v1/configs', csrfProtection, (req, res) => {
  // 处理请求
});
```

### 7. 限流策略

根据不同端点设置不同的限流策略：

```typescript
// 登录接口：更严格的限流
const loginLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,  // 15 分钟
  max: 5,                     // 最多 5 次尝试
  message: '登录尝试次数过多，请稍后再试',
});

app.post('/api/v1/sessions', loginLimiter, loginHandler);

// 普通 API：宽松的限流
const apiLimiter = rateLimit({
  windowMs: 60 * 1000,  // 1 分钟
  max: 100,             // 最多 100 次请求
});

app.use('/api/v1', apiLimiter);
```

### 8. 日志安全

- 不要记录敏感信息（密码、令牌）
- 使用结构化日志
- 定期清理旧日志

```typescript
// ❌ 错误：记录密码
logger.info('User login', { password: req.body.password });

// ✅ 正确：不记录敏感信息
logger.info('User login attempt', { ip: req.ip });
```

### 9. 依赖安全

- 定期更新依赖
- 使用 npm audit 检查漏洞
- 使用 Dependabot 自动更新

```bash
# 检查漏洞
npm audit

# 自动修复
npm audit fix

# 更新依赖
npm update
```

### 10. Docker 安全

- 使用非 root 用户运行
- 使用最小化基础镜像
- 定期更新镜像

```dockerfile
# ✅ 使用非 root 用户
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

USER nodejs

# ✅ 使用 Alpine 最小化镜像
FROM node:24-alpine
```

---

## 安全检查清单

### 部署前检查

- [ ] 修改默认管理员密码
- [ ] 设置强 JWT 密钥
- [ ] 配置 HTTPS
- [ ] 限制 CORS 域名
- [ ] 启用限流
- [ ] 配置防火墙
- [ ] 设置日志轮转
- [ ] 更新所有依赖
- [ ] 运行安全扫描
- [ ] 备份数据库

### 运行时监控

- [ ] 监控异常登录尝试
- [ ] 监控 API 滥用
- [ ] 监控错误率
- [ ] 监控响应时间
- [ ] 定期审查日志
- [ ] 定期更新依赖
- [ ] 定期备份数据

---

## 相关文档

- [AI_REBUILD_04_API.md](./AI_REBUILD_04_API.md) - API 设计
- [AI_REBUILD_06_MIDDLEWARE.md](./AI_REBUILD_06_MIDDLEWARE.md) - 中间件系统
- [AI_REBUILD_10_DEPLOYMENT.md](./AI_REBUILD_10_DEPLOYMENT.md) - 部署指南
