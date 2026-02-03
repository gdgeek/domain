# 技术栈详解

## 1. 核心技术栈

### 1.1 运行时环境
- **Node.js**: 16.x+
- **TypeScript**: 5.9.3
- **运行环境**: Node.js 24-alpine (Docker)

### 1.2 Web 框架
- **Express**: 4.18.2
  - 成熟稳定的 Node.js Web 框架
  - 中间件生态丰富
  - 性能优秀

### 1.3 数据库
- **MySQL**: 8.0
  - 关系型数据库
  - 支持事务和外键
  - 字符集: utf8mb3
  - 排序规则: utf8mb3_unicode_ci

- **Sequelize**: 6.35.2
  - TypeScript 友好的 ORM
  - 支持迁移管理
  - 连接池管理

### 1.4 缓存
- **Redis**: 7.x
  - 高性能内存数据库
  - 支持多种数据结构
  - 用于缓存和会话管理

- **ioredis**: 5.3.2
  - Redis 客户端
  - 支持 Promise
  - 连接池管理

## 2. 开发依赖

### 2.1 类型定义
```json
{
  "@types/express": "^4.17.21",
  "@types/node": "^20.10.6",
  "@types/jest": "^29.5.11",
  "@types/cors": "^2.8.17",
  "@types/jsonwebtoken": "^9.0.5"
}
```

### 2.2 测试框架
```json
{
  "jest": "^29.7.0",
  "ts-jest": "^29.1.1",
  "@types/jest": "^29.5.11"
}
```

### 2.3 代码质量
```json
{
  "eslint": "^8.56.0",
  "@typescript-eslint/eslint-plugin": "^6.17.0",
  "@typescript-eslint/parser": "^6.17.0",
  "prettier": "^3.1.1"
}
```

### 2.4 开发工具
```json
{
  "ts-node-dev": "^2.0.0",
  "nodemon": "^3.0.2"
}
```

## 3. 核心库

### 3.1 认证和安全
- **jsonwebtoken**: 9.0.2
  - JWT Token 生成和验证
  - 无状态认证

- **bcrypt**: 5.1.1
  - 密码加密
  - 安全哈希

### 3.2 数据验证
- **joi**: 17.11.0
  - 强大的数据验证库
  - Schema 定义
  - 错误消息自定义

### 3.3 日志
- **winston**: 3.11.0
  - 结构化日志
  - 多种传输方式
  - 日志级别管理

### 3.4 监控
- **prom-client**: 15.1.0
  - Prometheus 客户端
  - 指标收集
  - 性能监控

### 3.5 API 文档
- **swagger-ui-express**: 5.0.0
  - Swagger UI 集成
  - API 文档可视化

- **swagger-jsdoc**: 6.2.8
  - JSDoc 注释生成 Swagger 文档

### 3.6 其他工具
- **cors**: 2.8.5 - CORS 支持
- **dotenv**: 16.3.1 - 环境变量管理
- **express-rate-limit**: 7.1.5 - 请求限流

## 4. 完整的 package.json

```json
{
  "name": "domain-config-service",
  "version": "1.0.0",
  "description": "域名配置管理服务",
  "main": "dist/index.js",
  "scripts": {
    "dev": "ts-node-dev --respawn --transpile-only src/index.ts",
    "build": "tsc",
    "start": "node dist/index.js",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "lint": "eslint src --ext .ts",
    "lint:fix": "eslint src --ext .ts --fix",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "express": "^4.18.2",
    "typescript": "^5.9.3",
    "sequelize": "^6.35.2",
    "mysql2": "^3.7.0",
    "ioredis": "^5.3.2",
    "jsonwebtoken": "^9.0.2",
    "joi": "^17.11.0",
    "winston": "^3.11.0",
    "prom-client": "^15.1.0",
    "swagger-ui-express": "^5.0.0",
    "swagger-jsdoc": "^6.2.8",
    "cors": "^2.8.5",
    "dotenv": "^16.3.1",
    "express-rate-limit": "^7.1.5"
  },
  "devDependencies": {
    "@types/express": "^4.17.21",
    "@types/node": "^20.10.6",
    "@types/jest": "^29.5.11",
    "@types/cors": "^2.8.17",
    "@types/jsonwebtoken": "^9.0.5",
    "@types/swagger-ui-express": "^4.1.6",
    "@types/swagger-jsdoc": "^6.0.4",
    "jest": "^29.7.0",
    "ts-jest": "^29.1.1",
    "ts-node-dev": "^2.0.0",
    "eslint": "^8.56.0",
    "@typescript-eslint/eslint-plugin": "^6.17.0",
    "@typescript-eslint/parser": "^6.17.0",
    "prettier": "^3.1.1"
  }
}
```

## 5. TypeScript 配置

### 5.1 tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "lib": ["ES2020"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "moduleResolution": "node",
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "**/*.test.ts"]
}
```

## 6. Jest 配置

### 6.1 jest.config.js

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
    '!src/**/*.test.ts',
    '!src/**/*.spec.ts',
    '!src/types/**',
  ],
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'lcov', 'html'],
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
};
```

## 7. ESLint 配置

### 7.1 .eslintrc.json

```json
{
  "parser": "@typescript-eslint/parser",
  "extends": [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended"
  ],
  "parserOptions": {
    "ecmaVersion": 2020,
    "sourceType": "module"
  },
  "rules": {
    "@typescript-eslint/no-explicit-any": "warn",
    "@typescript-eslint/explicit-module-boundary-types": "off",
    "no-console": "warn"
  }
}
```

## 8. Docker 相关

### 8.1 基础镜像
- **node:24-alpine** - 轻量级 Node.js 镜像
- **mysql:8.0** - MySQL 数据库
- **redis:7-alpine** - Redis 缓存

### 8.2 Docker 工具
- **dumb-init** - 信号处理
- **wget** - 健康检查

## 9. 技术选型理由

### 9.1 为什么选择 TypeScript？
- ✅ 类型安全，减少运行时错误
- ✅ 更好的 IDE 支持和代码提示
- ✅ 代码可维护性更高
- ✅ 接口定义清晰

### 9.2 为什么选择 Express？
- ✅ 成熟稳定，社区活跃
- ✅ 中间件生态丰富
- ✅ 性能优秀
- ✅ 学习曲线平缓

### 9.3 为什么选择 Sequelize？
- ✅ TypeScript 支持好
- ✅ 自动处理连接池
- ✅ 支持事务
- ✅ 迁移管理方便

### 9.4 为什么选择 MySQL？
- ✅ 关系型数据库，支持外键
- ✅ 事务支持完善
- ✅ 性能优秀
- ✅ 生态成熟

### 9.5 为什么选择 Redis？
- ✅ 高性能内存数据库
- ✅ 支持多种数据结构
- ✅ 持久化支持
- ✅ 集群支持

### 9.6 为什么选择 JWT？
- ✅ 无状态认证
- ✅ 易于扩展
- ✅ 跨域支持好
- ✅ 标准化

### 9.7 为什么选择 Joi？
- ✅ 强大的验证功能
- ✅ 错误消息自定义
- ✅ TypeScript 支持
- ✅ 性能优秀

### 9.8 为什么选择 Winston？
- ✅ 结构化日志
- ✅ 多种传输方式
- ✅ 日志级别管理
- ✅ 性能优秀

### 9.9 为什么选择 Prometheus？
- ✅ 标准的监控格式
- ✅ 强大的查询语言
- ✅ 可视化支持（Grafana）
- ✅ 社区活跃

## 10. 版本要求

### 10.1 最低版本要求
- Node.js: >= 16.x
- MySQL: >= 5.7
- Redis: >= 6.x (可选)
- npm: >= 8.x

### 10.2 推荐版本
- Node.js: 20.x LTS
- MySQL: 8.0
- Redis: 7.x
- npm: 10.x

## 11. 开发工具推荐

### 11.1 IDE
- **VS Code** (推荐)
  - TypeScript 支持好
  - 插件丰富
  - 调试方便

### 11.2 VS Code 插件
- ESLint
- Prettier
- TypeScript
- Docker
- REST Client

### 11.3 数据库工具
- **MySQL Workbench** - MySQL 管理
- **Redis Commander** - Redis 管理
- **DBeaver** - 通用数据库工具

### 11.4 API 测试工具
- **Postman** - API 测试
- **Insomnia** - API 测试
- **curl** - 命令行测试

## 12. 性能优化

### 12.1 数据库优化
- 连接池配置
- 索引优化
- 查询优化

### 12.2 缓存优化
- Redis 缓存
- 缓存失效策略
- 缓存预热

### 12.3 应用优化
- 异步处理
- 请求限流
- 响应压缩

## 13. 下一步

阅读完本文档后，请继续阅读：

1. [数据库设计](./AI_REBUILD_03_DATABASE.md)
2. [API 规范](./AI_REBUILD_04_API.md)
3. [核心模块](./AI_REBUILD_05_MODULES.md)
