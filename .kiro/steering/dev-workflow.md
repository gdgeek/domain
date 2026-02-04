---
inclusion: always
---

# 开发基础工作流规范

适用于 Python、Node.js、PHP 项目的通用开发规范。

---

## 1. 项目结构

### 标准目录结构
```
project/
├── .github/workflows/     # CI/CD 配置
├── .kiro/                 # Kiro 配置
│   ├── steering/          # Steering 规则
│   └── specs/             # 功能规格
├── app/                   # 应用代码 (或 src/)
├── tests/                 # 测试代码
├── docs/                  # 文档
├── docker-compose.yml     # Docker 编排
├── Dockerfile             # 容器构建
├── README.md              # 项目说明
└── .env.example           # 环境变量模板
```

---

## 2. Git 工作流

### 分支策略
| 分支 | 用途 | 保护规则 |
|------|------|----------|
| `main` | 生产环境 | 需要 PR + 审核 |
| `develop` | 开发集成 | 需要 CI 通过 |
| `feature/*` | 功能开发 | 无 |
| `hotfix/*` | 紧急修复 | 无 |

### Commit 规范
```
<type>(<scope>): <subject>

type: feat|fix|docs|style|refactor|test|chore
scope: 可选，影响范围
subject: 简短描述，不超过50字符
```

示例：
- `feat(auth): 添加 JWT 认证`
- `fix(api): 修复分页参数验证`
- `docs: 更新 API 文档`

---

## 3. 代码规范

### Python
- 遵循 PEP 8
- 使用 type hints
- Lint: `flake8 --max-line-length=120`
- Format: `black`

### Node.js
- 使用 ESLint + Prettier
- 优先使用 TypeScript
- Lint: `npm run lint`

### PHP
- 遵循 PSR-12
- Lint: `phpcs --standard=PSR12`
- Format: `php-cs-fixer`

---

## 4. 测试规范

### 测试类型
| 类型 | 覆盖率目标 | 工具 |
|------|-----------|------|
| 单元测试 | ≥80% | pytest / jest / phpunit |
| 集成测试 | 关键路径 | 同上 |
| E2E 测试 | 核心流程 | playwright / cypress |

### 命令
```bash
# Python
pytest tests/ -v --cov=app --cov-report=term-missing

# Node.js
npm test -- --coverage

# PHP
vendor/bin/phpunit --coverage-text
```

---

## 5. Docker 开发环境

### docker-compose.dev.yml 模板
```yaml
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.dev
    volumes:
      - .:/app
    ports:
      - "5000:5000"
    environment:
      - DEBUG=true
    depends_on:
      - db
      - redis

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: dev
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: dev
    volumes:
      - db_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

volumes:
  db_data:
```

### 常用命令
```bash
docker compose -f docker-compose.dev.yml up -d    # 启动
docker compose -f docker-compose.dev.yml logs -f  # 日志
docker compose -f docker-compose.dev.yml down     # 停止
```

---

## 6. CI/CD 工作流

详细配置参见：#[[file:.kiro/steering/cicd-workflow.md]]

概要：
- 三阶段流水线：测试 → 构建 → 发布
- 部署目标：腾讯云容器服务 (TCR)
- 部署触发：Portainer Webhook
- 支持语言：Python / Node.js / PHP

---

## 7. 环境管理

### 环境变量
```bash
# .env.example - 提交到 Git
DATABASE_URL=postgresql://user:pass@localhost/db
REDIS_URL=redis://localhost:6379
SECRET_KEY=change-me-in-production
DEBUG=false

# .env - 不提交，本地使用
```

### 配置分层
| 环境 | 配置来源 |
|------|----------|
| 开发 | `.env` + 默认值 |
| 测试 | 环境变量 |
| 生产 | Secrets / 配置中心 |

---

## 8. 文档规范

### README 必备内容
1. 项目简介
2. 快速开始
3. 环境要求
4. 安装步骤
5. 配置说明
6. API 文档链接

### API 文档
- REST: OpenAPI/Swagger
- GraphQL: GraphQL Playground
- 自动生成优先

---

## 9. 安全规范

### 基本原则
- 不提交敏感信息到 Git
- 使用环境变量管理密钥
- 依赖定期更新
- 启用 Dependabot

### .gitignore 必备
```
.env
*.log
node_modules/
__pycache__/
vendor/
.idea/
.vscode/
*.db
```

---

## 10. Dockerfile 模板

### Python
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-b", "0.0.0.0:5000", "run:app"]
```

### Node.js
```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 3000
CMD ["node", "server.js"]
```

### PHP
```dockerfile
FROM php:8.2-fpm-alpine
WORKDIR /var/www
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer
COPY . .
RUN composer install --no-dev --optimize-autoloader
EXPOSE 9000
CMD ["php-fpm"]
```
