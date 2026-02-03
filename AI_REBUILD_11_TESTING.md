# AI 重建指南 11 - 测试指南

## 概述

本文档详细说明项目的测试策略，包括单元测试、集成测试、属性测试和测试覆盖率。

## 目录

- [测试架构](#测试架构)
- [测试框架](#测试框架)
- [单元测试](#单元测试)
- [集成测试](#集成测试)
- [属性测试](#属性测试)
- [测试覆盖率](#测试覆盖率)

---

## 测试架构

### 测试金字塔

```
        ┌─────────────┐
        │  E2E Tests  │  少量
        └─────────────┘
       ┌───────────────┐
       │ Integration   │  适量
       │    Tests      │
       └───────────────┘
      ┌─────────────────┐
      │   Unit Tests    │  大量
      └─────────────────┘
```

### 测试类型

1. **单元测试**: 测试单个函数或类
2. **集成测试**: 测试多个模块的交互
3. **属性测试**: 测试通用属性和不变量
4. **E2E 测试**: 测试完整的用户流程

---

## 测试框架

### 技术栈

```json
{
  "jest": "^29.7.0",           // 测试框架
  "ts-jest": "^29.1.1",        // TypeScript 支持
  "supertest": "^6.3.3",       // HTTP 测试
  "fast-check": "^3.15.0",     // 属性测试
  "@types/jest": "^29.5.11",   // Jest 类型定义
  "@types/supertest": "^6.0.2" // Supertest 类型定义
}
```

### Jest 配置

**文件**: `jest.config.js`

```javascript
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/src'],
  testMatch: ['**/__tests__/**/*.ts', '**/?(*.)+(spec|test).ts'],
  transform: {
    '^.+\\.ts$': 'ts-jest',
  },
  collectCoverageFrom: [
    'src/**/*.ts',
    '!src/**/*.d.ts',
    '!src/**/*.test.ts',
    '!src/**/*.spec.ts',
  ],
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'lcov', 'html'],
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testTimeout: 10000,
};
```

### 测试脚本

**文件**: `package.json`

```json
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "test:property": "jest --testPathPattern=property",
    "test:unit": "jest --testPathPattern=unit",
    "test:integration": "jest --testPathPattern=integration"
  }
}
```

---

## 单元测试

### 测试结构

```typescript
describe('ModuleName', () => {
  describe('functionName', () => {
    it('should do something when condition', () => {
      // Arrange
      const input = 'test';
      
      // Act
      const result = functionName(input);
      
      // Assert
      expect(result).toBe('expected');
    });
  });
});
```

### Repository 测试示例

**文件**: `src/repositories/ConfigRepository.test.ts`

```typescript
import { ConfigRepository } from './ConfigRepository';
import { Config } from '../models/Config';
import { setupTestDatabase, teardownTestDatabase } from '../test-utils/setupTestDatabase';

describe('ConfigRepository', () => {
  let repository: ConfigRepository;

  beforeAll(async () => {
    await setupTestDatabase();
  });

  afterAll(async () => {
    await teardownTestDatabase();
  });

  beforeEach(() => {
    repository = new ConfigRepository();
  });

  afterEach(async () => {
    await Config.destroy({ where: {}, truncate: true });
  });

  describe('create', () => {
    it('should create a new config', async () => {
      const data = {
        title: 'Test Config',
        author: 'Test Author',
        description: 'Test Description',
        keywords: 'test,keywords',
        links: { home: 'https://example.com' },
        permissions: { read: ['public'] },
      };

      const config = await repository.create(data);

      expect(config.id).toBeDefined();
      expect(config.title).toBe(data.title);
      expect(config.author).toBe(data.author);
    });

    it('should throw DatabaseError on failure', async () => {
      // 模拟数据库错误
      jest.spyOn(Config, 'create').mockRejectedValue(new Error('DB Error'));

      await expect(repository.create({})).rejects.toThrow('创建配置失败');
    });
  });

  describe('findById', () => {
    it('should return config when found', async () => {
      const created = await Config.create({
        title: 'Test',
        author: 'Author',
      });

      const found = await repository.findById(created.id);

      expect(found).toBeDefined();
      expect(found!.id).toBe(created.id);
    });

    it('should return null when not found', async () => {
      const found = await repository.findById(999);

      expect(found).toBeNull();
    });
  });
});
```

### Service 测试示例

**文件**: `src/services/ConfigService.test.ts`

```typescript
import { ConfigService } from './ConfigService';
import { ConfigRepository } from '../repositories/ConfigRepository';
import { DomainRepository } from '../repositories/DomainRepository';
import { NotFoundError } from '../errors/NotFoundError';

// Mock repositories
jest.mock('../repositories/ConfigRepository');
jest.mock('../repositories/DomainRepository');

describe('ConfigService', () => {
  let service: ConfigService;
  let configRepository: jest.Mocked<ConfigRepository>;
  let domainRepository: jest.Mocked<DomainRepository>;

  beforeEach(() => {
    configRepository = new ConfigRepository() as jest.Mocked<ConfigRepository>;
    domainRepository = new DomainRepository() as jest.Mocked<DomainRepository>;
    service = new ConfigService(configRepository, domainRepository);
  });

  describe('create', () => {
    it('should create a config', async () => {
      const input = {
        title: 'Test',
        author: 'Author',
      };

      const mockConfig = {
        id: 1,
        ...input,
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      configRepository.create.mockResolvedValue(mockConfig as any);

      const result = await service.create(input);

      expect(result.id).toBe(1);
      expect(result.title).toBe(input.title);
      expect(configRepository.create).toHaveBeenCalledWith(
        expect.objectContaining(input)
      );
    });
  });

  describe('delete', () => {
    it('should throw ConflictError when config is in use', async () => {
      domainRepository.countByConfigId.mockResolvedValue(2);

      await expect(service.delete(1)).rejects.toThrow('无法删除配置');
      expect(configRepository.delete).not.toHaveBeenCalled();
    });

    it('should delete config when not in use', async () => {
      domainRepository.countByConfigId.mockResolvedValue(0);
      configRepository.delete.mockResolvedValue(true);

      const result = await service.delete(1);

      expect(result).toBe(true);
      expect(configRepository.delete).toHaveBeenCalledWith(1);
    });
  });
});
```

### Middleware 测试示例

**文件**: `src/middleware/AuthMiddleware.test.ts`

```typescript
import { Request, Response, NextFunction } from 'express';
import { authMiddleware, generateToken, verifyToken } from './AuthMiddleware';

describe('AuthMiddleware', () => {
  let req: Partial<Request>;
  let res: Partial<Response>;
  let next: NextFunction;

  beforeEach(() => {
    req = {
      method: 'GET',
      headers: {},
    };
    res = {
      status: jest.fn().mockReturnThis(),
      json: jest.fn(),
    };
    next = jest.fn();
  });

  describe('authMiddleware', () => {
    it('should allow GET requests without token', () => {
      req.method = 'GET';

      authMiddleware(req as Request, res as Response, next);

      expect(next).toHaveBeenCalled();
      expect(res.status).not.toHaveBeenCalled();
    });

    it('should reject POST requests without token', () => {
      req.method = 'POST';

      authMiddleware(req as Request, res as Response, next);

      expect(res.status).toHaveBeenCalledWith(401);
      expect(res.json).toHaveBeenCalledWith(
        expect.objectContaining({
          error: expect.objectContaining({
            code: 'UNAUTHORIZED',
          }),
        })
      );
      expect(next).not.toHaveBeenCalled();
    });

    it('should allow POST requests with valid token', () => {
      req.method = 'POST';
      const token = generateToken();
      req.headers = {
        authorization: `Bearer ${token}`,
      };

      authMiddleware(req as Request, res as Response, next);

      expect(next).toHaveBeenCalled();
      expect(res.status).not.toHaveBeenCalled();
    });

    it('should reject POST requests with invalid token', () => {
      req.method = 'POST';
      req.headers = {
        authorization: 'Bearer invalid-token',
      };

      authMiddleware(req as Request, res as Response, next);

      expect(res.status).toHaveBeenCalledWith(403);
      expect(next).not.toHaveBeenCalled();
    });
  });

  describe('generateToken', () => {
    it('should generate a valid JWT token', () => {
      const token = generateToken();

      expect(token).toBeDefined();
      expect(typeof token).toBe('string');

      const payload = verifyToken(token);
      expect(payload).toBeDefined();
      expect(payload!.role).toBe('admin');
    });
  });
});
```

---

## 集成测试

### API 集成测试

**文件**: `src/routes/ConfigRoutes.integration.test.ts`

```typescript
import request from 'supertest';
import { createApp } from '../app';
import { setupTestDatabase, teardownTestDatabase } from '../test-utils/setupTestDatabase';
import { generateToken } from '../middleware/AuthMiddleware';
import { Config } from '../models/Config';

describe('Config Routes Integration', () => {
  let app: Express.Application;
  let token: string;

  beforeAll(async () => {
    await setupTestDatabase();
    app = createApp();
    token = generateToken();
  });

  afterAll(async () => {
    await teardownTestDatabase();
  });

  afterEach(async () => {
    await Config.destroy({ where: {}, truncate: true });
  });

  describe('POST /api/v1/configs', () => {
    it('should create a new config', async () => {
      const data = {
        title: 'Test Config',
        author: 'Test Author',
        description: 'Test Description',
      };

      const response = await request(app)
        .post('/api/v1/configs')
        .set('Authorization', `Bearer ${token}`)
        .send(data)
        .expect(201);

      expect(response.body.data).toMatchObject({
        id: expect.any(Number),
        title: data.title,
        author: data.author,
      });
    });

    it('should return 401 without token', async () => {
      const response = await request(app)
        .post('/api/v1/configs')
        .send({})
        .expect(401);

      expect(response.body.error.code).toBe('UNAUTHORIZED');
    });
  });

  describe('GET /api/v1/configs/:id', () => {
    it('should return config by id', async () => {
      const config = await Config.create({
        title: 'Test',
        author: 'Author',
      });

      const response = await request(app)
        .get(`/api/v1/configs/${config.id}`)
        .expect(200);

      expect(response.body.data.id).toBe(config.id);
    });

    it('should return 404 for non-existent config', async () => {
      const response = await request(app)
        .get('/api/v1/configs/999')
        .expect(404);

      expect(response.body.error.code).toBe('CONFIG_NOT_FOUND');
    });
  });

  describe('PUT /api/v1/configs/:id', () => {
    it('should update config', async () => {
      const config = await Config.create({
        title: 'Original',
        author: 'Author',
      });

      const response = await request(app)
        .put(`/api/v1/configs/${config.id}`)
        .set('Authorization', `Bearer ${token}`)
        .send({ title: 'Updated' })
        .expect(200);

      expect(response.body.data.title).toBe('Updated');
    });
  });

  describe('DELETE /api/v1/configs/:id', () => {
    it('should delete config', async () => {
      const config = await Config.create({
        title: 'Test',
        author: 'Author',
      });

      await request(app)
        .delete(`/api/v1/configs/${config.id}`)
        .set('Authorization', `Bearer ${token}`)
        .expect(204);

      const found = await Config.findByPk(config.id);
      expect(found).toBeNull();
    });
  });
});
```

---

## 属性测试

### 属性测试概念

属性测试（Property-Based Testing）通过生成大量随机输入来验证代码的通用属性。

### 使用 fast-check

**文件**: `src/services/LanguageResolver.property.test.ts`

```typescript
import * as fc from 'fast-check';
import { LanguageResolver } from './LanguageResolver';

describe('LanguageResolver Property Tests', () => {
  const resolver = new LanguageResolver({
    defaultLanguage: 'zh-cn',
    supportedLanguages: ['zh-cn', 'en-us', 'ja-jp'],
  });

  describe('normalizeLanguageCode', () => {
    it('should always return lowercase with hyphens', () => {
      fc.assert(
        fc.property(
          fc.string({ minLength: 2, maxLength: 10 }),
          (code) => {
            const normalized = resolver.normalizeLanguageCode(code);
            
            // Property 1: Result is lowercase
            expect(normalized).toBe(normalized.toLowerCase());
            
            // Property 2: No underscores
            expect(normalized).not.toContain('_');
            
            // Property 3: Idempotent (normalizing twice gives same result)
            expect(resolver.normalizeLanguageCode(normalized)).toBe(normalized);
          }
        )
      );
    });

    it('should preserve length', () => {
      fc.assert(
        fc.property(
          fc.string({ minLength: 1, maxLength: 20 }),
          (code) => {
            const normalized = resolver.normalizeLanguageCode(code);
            expect(normalized.length).toBe(code.length);
          }
        )
      );
    });
  });

  describe('isSupported', () => {
    it('should return boolean for any input', () => {
      fc.assert(
        fc.property(
          fc.string(),
          (code) => {
            const result = resolver.isSupported(code);
            expect(typeof result).toBe('boolean');
          }
        )
      );
    });

    it('should be case-insensitive', () => {
      fc.assert(
        fc.property(
          fc.constantFrom('zh-cn', 'en-us', 'ja-jp'),
          fc.boolean(),
          fc.boolean(),
          (lang, upperFirst, upperSecond) => {
            const [first, second] = lang.split('-');
            const modified = 
              (upperFirst ? first.toUpperCase() : first) + '-' +
              (upperSecond ? second.toUpperCase() : second);
            
            expect(resolver.isSupported(modified)).toBe(true);
          }
        )
      );
    });
  });
});
```

### 翻译服务属性测试

**文件**: `src/services/TranslationService.property.test.ts`

```typescript
import * as fc from 'fast-check';
import { TranslationService } from './TranslationService';

describe('TranslationService Property Tests', () => {
  describe('validateFieldLength', () => {
    it('should reject strings longer than maxLength', () => {
      fc.assert(
        fc.property(
          fc.integer({ min: 1, max: 100 }),
          fc.string({ minLength: 101 }),
          (maxLength, longString) => {
            expect(() => {
              service['validateFieldLength']('test', longString, maxLength);
            }).toThrow();
          }
        )
      );
    });

    it('should accept strings within maxLength', () => {
      fc.assert(
        fc.property(
          fc.integer({ min: 10, max: 100 }),
          (maxLength) => {
            const validString = 'a'.repeat(maxLength);
            
            expect(() => {
              service['validateFieldLength']('test', validString, maxLength);
            }).not.toThrow();
          }
        )
      );
    });
  });

  describe('validateKeywordsFormat', () => {
    it('should accept array of strings', () => {
      fc.assert(
        fc.property(
          fc.array(fc.string()),
          (keywords) => {
            expect(() => {
              service['validateKeywordsFormat'](keywords);
            }).not.toThrow();
          }
        )
      );
    });

    it('should reject non-array inputs', () => {
      fc.assert(
        fc.property(
          fc.oneof(
            fc.string(),
            fc.integer(),
            fc.boolean(),
            fc.object()
          ),
          (notArray) => {
            expect(() => {
              service['validateKeywordsFormat'](notArray);
            }).toThrow('Keywords must be an array');
          }
        )
      );
    });
  });
});
```

---

## 测试覆盖率

### 运行覆盖率测试

```bash
# 运行测试并生成覆盖率报告
npm run test:coverage

# 查看 HTML 报告
open coverage/lcov-report/index.html
```

### 覆盖率目标

```
Statements   : 85%
Branches     : 80%
Functions    : 85%
Lines        : 85%
```

### 覆盖率配置

**文件**: `jest.config.js`

```javascript
module.exports = {
  // ... 其他配置
  collectCoverageFrom: [
    'src/**/*.ts',
    '!src/**/*.d.ts',
    '!src/**/*.test.ts',
    '!src/**/*.spec.ts',
    '!src/index.ts',
  ],
  coverageThreshold: {
    global: {
      statements: 85,
      branches: 80,
      functions: 85,
      lines: 85,
    },
  },
};
```

### 当前覆盖率

根据项目测试报告，当前覆盖率为：

```
File                  | % Stmts | % Branch | % Funcs | % Lines
----------------------|---------|----------|---------|--------
All files             |   87.5  |   82.3   |   89.1  |   87.8
 config/              |   92.1  |   85.7   |   94.2  |   92.5
 errors/              |   100   |   100    |   100   |   100
 middleware/          |   88.3  |   81.5   |   90.2  |   88.7
 models/              |   95.2  |   90.1   |   96.3  |   95.5
 repositories/        |   91.7  |   87.2   |   93.4  |   92.1
 routes/              |   85.4  |   78.9   |   87.6  |   85.9
 services/            |   89.2  |   84.3   |   91.5  |   89.7
 validation/          |   93.8  |   88.6   |   95.1  |   94.2
```

---

## 测试最佳实践

### 1. 测试命名

使用描述性的测试名称：

```typescript
// ❌ 不好
it('test 1', () => {});

// ✅ 好
it('should return 404 when config not found', () => {});
```

### 2. AAA 模式

使用 Arrange-Act-Assert 模式：

```typescript
it('should create a config', async () => {
  // Arrange
  const data = { title: 'Test' };
  
  // Act
  const result = await service.create(data);
  
  // Assert
  expect(result.title).toBe('Test');
});
```

### 3. 测试隔离

每个测试应该独立运行：

```typescript
afterEach(async () => {
  // 清理测试数据
  await Config.destroy({ where: {}, truncate: true });
});
```

### 4. Mock 外部依赖

```typescript
jest.mock('../repositories/ConfigRepository');
```

### 5. 测试边界条件

```typescript
it('should handle empty input', () => {});
it('should handle null input', () => {});
it('should handle very long input', () => {});
```

### 6. 使用测试工具函数

```typescript
// test-utils/setupTestDatabase.ts
export async function setupTestDatabase() {
  await sequelize.sync({ force: true });
}

export async function teardownTestDatabase() {
  await sequelize.close();
}
```

---

## 相关文档

- [AI_REBUILD_05_MODULES.md](./AI_REBUILD_05_MODULES.md) - 核心模块
- [AI_REBUILD_06_MIDDLEWARE.md](./AI_REBUILD_06_MIDDLEWARE.md) - 中间件系统
- [AI_REBUILD_10_DEPLOYMENT.md](./AI_REBUILD_10_DEPLOYMENT.md) - 部署指南
