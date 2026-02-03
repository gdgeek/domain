# API 接口规范

## 1. API 基础信息

### 1.1 基本信息
- **Base URL**: `/api/v1`
- **Content-Type**: `application/json`
- **认证方式**: JWT Bearer Token
- **字符编码**: UTF-8

### 1.2 通用响应格式

**成功响应**:
```json
{
  "data": { ... }
}
```

**错误响应**:
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述"
  }
}
```

### 1.3 HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 204 | 删除成功（无内容） |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 409 | 资源冲突 |
| 500 | 服务器错误 |

## 2. 认证 API

### 2.1 管理员登录

**端点**: `POST /api/v1/auth/login`

**请求**:
```json
{
  "password": "admin123"
}
```

**响应** (200):
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "message": "登录成功"
}
```

**错误响应** (401):
```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "密码错误"
  }
}
```

## 3. 配置管理 API

### 3.1 获取配置列表

**端点**: `GET /api/v1/configs`

**查询参数**:
- `page` (可选): 页码，默认 1
- `pageSize` (可选): 每页大小，默认 20，最大 100
- `lang` (可选): 语言代码，如 `en-us`

**请求头**:
- `Accept-Language` (可选): 语言偏好，如 `en-US,zh-CN;q=0.9`
- `Authorization` (可选): Bearer Token

**响应** (200):
```json
{
  "data": [
    {
      "id": 1,
      "title": "示例配置",
      "author": "作者",
      "description": "描述",
      "keywords": "关键词1,关键词2",
      "links": {
        "home": "https://example.com"
      },
      "permissions": {
        "read": true,
        "write": false
      },
      "createdAt": "2026-01-01T00:00:00.000Z",
      "updatedAt": "2026-01-01T00:00:00.000Z"
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 20,
    "total": 100,
    "totalPages": 5
  }
}
```

### 3.2 获取单个配置

**端点**: `GET /api/v1/configs/:id`

**路径参数**:
- `id`: 配置 ID

**查询参数**:
- `lang` (可选): 语言代码

**请求头**:
- `Accept-Language` (可选): 语言偏好

**响应** (200):
```json
{
  "data": {
    "id": 1,
    "title": "示例配置",
    "author": "作者",
    "description": "描述",
    "keywords": "关键词1,关键词2",
    "links": {
      "home": "https://example.com"
    },
    "permissions": {
      "read": true,
      "write": false
    },
    "language": "zh-cn",
    "createdAt": "2026-01-01T00:00:00.000Z",
    "updatedAt": "2026-01-01T00:00:00.000Z"
  }
}
```

**响应头**:
- `X-Content-Language`: 返回内容的实际语言代码

### 3.3 创建配置

**端点**: `POST /api/v1/configs`

**认证**: 需要 Bearer Token

**请求**:
```json
{
  "title": "新配置",
  "author": "作者",
  "description": "描述",
  "keywords": "关键词1,关键词2",
  "links": {
    "home": "https://example.com"
  },
  "permissions": {
    "read": true,
    "write": false
  }
}
```

**响应** (201):
```json
{
  "data": {
    "id": 2,
    "title": "新配置",
    "author": "作者",
    "description": "描述",
    "keywords": "关键词1,关键词2",
    "links": {
      "home": "https://example.com"
    },
    "permissions": {
      "read": true,
      "write": false
    },
    "createdAt": "2026-01-01T00:00:00.000Z",
    "updatedAt": "2026-01-01T00:00:00.000Z"
  }
}
```

### 3.4 更新配置

**端点**: `PUT /api/v1/configs/:id`

**认证**: 需要 Bearer Token

**请求**:
```json
{
  "title": "更新的配置",
  "author": "作者",
  "description": "更新的描述",
  "keywords": "关键词1,关键词2,关键词3"
}
```

**响应** (200):
```json
{
  "data": {
    "id": 1,
    "title": "更新的配置",
    "author": "作者",
    "description": "更新的描述",
    "keywords": "关键词1,关键词2,关键词3",
    "links": null,
    "permissions": null,
    "createdAt": "2026-01-01T00:00:00.000Z",
    "updatedAt": "2026-01-01T01:00:00.000Z"
  }
}
```

### 3.5 部分更新配置

**端点**: `PATCH /api/v1/configs/:id`

**认证**: 需要 Bearer Token

**请求**:
```json
{
  "title": "只更新标题"
}
```

**响应** (200): 同 PUT

### 3.6 删除配置

**端点**: `DELETE /api/v1/configs/:id`

**认证**: 需要 Bearer Token

**响应** (204): 无内容

## 4. 域名管理 API

### 4.1 获取域名列表

**端点**: `GET /api/v1/domains`

**查询参数**:
- `page` (可选): 页码
- `pageSize` (可选): 每页大小
- `domain` (可选): 按域名查询（返回单个对象）
- `url` (可选): 同 domain（向后兼容）

**响应** (200) - 列表:
```json
{
  "data": [
    {
      "id": 1,
      "domain": "example.com",
      "homepage": "https://www.example.com",
      "configId": 1,
      "title": "示例配置",
      "createdAt": "2026-01-01T00:00:00.000Z",
      "updatedAt": "2026-01-01T00:00:00.000Z"
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 20,
    "total": 50,
    "totalPages": 3
  }
}
```

**响应** (200) - 单个域名:
```json
{
  "data": {
    "domain": "example.com",
    "config": {
      "id": 1,
      "title": "示例配置",
      "author": "作者",
      "description": "描述",
      "keywords": "关键词",
      "links": {},
      "permissions": {}
    }
  }
}
```

### 4.2 获取单个域名

**端点**: `GET /api/v1/domains/:id`

**响应** (200):
```json
{
  "data": {
    "id": 1,
    "domain": "example.com",
    "homepage": "https://www.example.com",
    "configId": 1,
    "config": {
      "id": 1,
      "title": "示例配置",
      "author": "作者",
      "description": "描述"
    },
    "createdAt": "2026-01-01T00:00:00.000Z",
    "updatedAt": "2026-01-01T00:00:00.000Z"
  }
}
```

### 4.3 创建域名

**端点**: `POST /api/v1/domains`

**认证**: 需要 Bearer Token

**请求**:
```json
{
  "domain": "example.com",
  "configId": 1,
  "homepage": "https://www.example.com"
}
```

**响应** (201):
```json
{
  "data": {
    "id": 2,
    "domain": "example.com",
    "homepage": "https://www.example.com",
    "configId": 1,
    "createdAt": "2026-01-01T00:00:00.000Z",
    "updatedAt": "2026-01-01T00:00:00.000Z"
  }
}
```

### 4.4 更新域名

**端点**: `PUT /api/v1/domains/:id`

**认证**: 需要 Bearer Token

**请求**:
```json
{
  "configId": 2,
  "homepage": "https://new.example.com"
}
```

**响应** (200): 同创建响应

### 4.5 删除域名

**端点**: `DELETE /api/v1/domains/:id`

**认证**: 需要 Bearer Token

**响应** (204): 无内容

## 5. 翻译管理 API

### 5.1 创建翻译

**端点**: `POST /api/v1/configs/:configId/translations`

**认证**: 需要 Bearer Token

**请求**:
```json
{
  "languageCode": "en-us",
  "title": "Example Config",
  "author": "Author",
  "description": "Description",
  "keywords": ["keyword1", "keyword2"]
}
```

**响应** (201):
```json
{
  "data": {
    "id": 1,
    "configId": 1,
    "languageCode": "en-us",
    "title": "Example Config",
    "author": "Author",
    "description": "Description",
    "keywords": ["keyword1", "keyword2"],
    "createdAt": "2026-01-01T00:00:00.000Z",
    "updatedAt": "2026-01-01T00:00:00.000Z"
  }
}
```

### 5.2 获取配置的所有翻译

**端点**: `GET /api/v1/configs/:configId/translations`

**响应** (200):
```json
{
  "data": [
    {
      "id": 1,
      "configId": 1,
      "languageCode": "en-us",
      "title": "Example Config",
      "author": "Author",
      "description": "Description",
      "keywords": ["keyword1", "keyword2"],
      "createdAt": "2026-01-01T00:00:00.000Z",
      "updatedAt": "2026-01-01T00:00:00.000Z"
    }
  ]
}
```

### 5.3 获取指定语言的翻译

**端点**: `GET /api/v1/configs/:configId/translations/:languageCode`

**响应** (200):
```json
{
  "data": {
    "id": 1,
    "configId": 1,
    "languageCode": "en-us",
    "title": "Example Config",
    "author": "Author",
    "description": "Description",
    "keywords": ["keyword1", "keyword2"],
    "createdAt": "2026-01-01T00:00:00.000Z",
    "updatedAt": "2026-01-01T00:00:00.000Z"
  }
}
```

### 5.4 更新翻译

**端点**: `PUT /api/v1/configs/:configId/translations/:languageCode`

**认证**: 需要 Bearer Token

**请求**:
```json
{
  "title": "Updated Title",
  "author": "Updated Author",
  "description": "Updated Description",
  "keywords": ["new", "keywords"]
}
```

**响应** (200): 同获取翻译响应

### 5.5 删除翻译

**端点**: `DELETE /api/v1/configs/:configId/translations/:languageCode`

**认证**: 需要 Bearer Token

**响应** (204): 无内容

## 6. 语言元数据 API

### 6.1 获取支持的语言列表

**端点**: `GET /api/v1/languages`

**响应** (200):
```json
{
  "default": "zh-cn",
  "supported": [
    {
      "code": "zh-cn",
      "name": "中文（简体）",
      "englishName": "Chinese (Simplified)"
    },
    {
      "code": "en-us",
      "name": "English (US)",
      "englishName": "English (US)"
    },
    {
      "code": "ja-jp",
      "name": "日本語",
      "englishName": "Japanese"
    }
  ]
}
```

## 7. 系统 API

### 7.1 健康检查

**端点**: `GET /health`

**响应** (200):
```json
{
  "status": "healthy",
  "timestamp": "2026-01-01T00:00:00.000Z",
  "services": {
    "database": "healthy",
    "redis": "healthy"
  }
}
```

### 7.2 监控指标

**端点**: `GET /metrics`

**响应** (200): Prometheus 格式的指标数据

## 8. 错误代码

| 错误代码 | 说明 |
|----------|------|
| VALIDATION_ERROR | 数据验证失败 |
| UNAUTHORIZED | 未认证 |
| FORBIDDEN | 无权限 |
| NOT_FOUND | 资源不存在 |
| CONFLICT | 资源冲突 |
| DATABASE_ERROR | 数据库错误 |
| INTERNAL_ERROR | 内部错误 |

## 9. 认证说明

### 9.1 获取 Token

通过登录接口获取 JWT Token。

### 9.2 使用 Token

在请求头中添加:
```
Authorization: Bearer <token>
```

### 9.3 Token 有效期

- 默认: 24 小时
- 过期后需要重新登录

## 10. 多语言支持

### 10.1 语言协商

优先级（从高到低）:
1. `lang` 查询参数
2. `Accept-Language` 请求头
3. 默认语言（zh-cn）

### 10.2 语言回退

如果请求的语言不存在，自动回退到默认语言。

### 10.3 支持的语言

- zh-cn: 简体中文
- zh-tw: 繁体中文
- en-us: 美式英语
- ja-jp: 日语
- th-th: 泰语

## 11. 下一步

阅读完本文档后，请继续阅读：

1. [核心模块](./AI_REBUILD_05_MODULES.md)
2. [中间件系统](./AI_REBUILD_06_MIDDLEWARE.md)
