# 轻量级域名配置服务

一个简单的域名配置管理服务，支持多语言配置和语言回退。

## 特性

- 🌐 域名管理（CRUD）
- 🌍 多语言配置支持（zh-CN, en-US, ja-JP, zh-TW, th-TH）
- 🔄 双重回退机制（语言回退 + 域名回退）
- 💾 三表架构设计（Domains, Configs, Translations）
- 🔐 API 密码认证
- 📦 Redis 缓存（可选）
- 📖 Swagger API 文档
- 🖥️ Web 管理界面
- 🏥 健康检查端点

## 详细文档

- [数据库设计](AI_REBUILD_03_DATABASE.md)
- [API 接口文档](AI_REBUILD_04_API.md)
- [国际化实现](AI_REBUILD_07_I18N.md)
- [部署指南](AI_REBUILD_10_DEPLOYMENT.md)
- [外部系统调用指南](API_INTEGRATION_GUIDE.md)

## 快速开始

### 使用 Docker（生产环境）

生产环境推荐使用 `docker-compose.yml`，默认配置为 PostgreSQL 数据库。

```bash
# 启动服务（包含 PostgreSQL 和 Redis）
docker compose up -d
```

或者直接运行镜像：

```bash
docker run -d \
  -p 5000:5000 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/dbname \
  -e ADMIN_PASSWORD=your-password \
  hkccr.ccs.tencentyun.com/gdgeek/domain:latest
```

### 本地开发（Development）

开发环境推荐使用 `docker-compose.dev.yml`，默认配置为 MySQL 数据库，且挂载本地代码以便热重载。

```bash
# 启动开发环境
docker compose -f docker-compose.dev.yml up -d
```

或者本地 Python 运行：

```bash
# 1. 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env

# 4. 初始化数据库
flask db upgrade

# 5. 启动服务
python run.py
```

## 访问地址

| 地址                             | 说明             |
| -------------------------------- | ---------------- |
| http://localhost:5000/admin/     | Web 管理界面     |
| http://localhost:5000/api/docs   | Swagger API 文档 |
| http://localhost:5000/api/health | 健康检查         |
| http://localhost:5000/api/query  | 公开查询接口     |

## 外部集成接口

本服务提供公开的查询接口供外部系统使用。详细说明请参考 [外部系统调用指南](API_INTEGRATION_GUIDE.md)。

### 简单示例

```bash
# 查询域名配置（自动处理语言回退）
curl "http://localhost:5000/api/query?domain=example.com&lang=en-US"
```

## API 认证

管理 API 需要密码认证，支持两种方式：

```bash
# 方式一：X-Admin-Password 请求头
curl -H "X-Admin-Password: your-password" http://localhost:5000/api/domains

# 方式二：Basic Auth（密码作为 password）
curl -u :your-password http://localhost:5000/api/domains
```

## 环境变量

| 变量             | 说明                             | 默认值         |
| ---------------- | -------------------------------- | -------------- |
| **Database**     |                                  |                |
| `DATABASE_URL`   | 完整数据库连接 URL (优先级最高)  | -              |
| `DB_HOST`        | 数据库主机                       | -              |
| `DB_PORT`        | 数据库端口                       | 3306           |
| `DB_USER`        | 数据库用户                       | root           |
| `DB_PASSWORD`    | 数据库密码                       | -              |
| `DB_NAME`        | 数据库名                         | domain_config  |
| **Redis**        |                                  |                |
| `REDIS_URL`      | 完整 Redis 连接 URL (优先级最高) | -              |
| `REDIS_ENABLED`  | 是否启用 Redis                   | false          |
| `REDIS_HOST`     | Redis 主机                       | localhost      |
| `REDIS_PORT`     | Redis 端口                       | 6379           |
| `REDIS_PASSWORD` | Redis 密码                       | -              |
| `REDIS_TTL`      | 缓存过期时间（秒）               | 3600           |
| **Security**     |                                  |                |
| `ADMIN_PASSWORD` | API/管理密码                     | admin123       |
| `SECRET_KEY`     | Flask 密钥                       | dev-secret-key |

## 项目结构

```
├── app/
│   ├── api/           # REST API
│   ├── admin/         # Web 管理界面
│   ├── models/        # 数据模型 (SQLAlchemy)
│   ├── repositories/  # 数据访问层
│   └── services/      # 业务逻辑层
├── migrations/        # 数据库迁移
├── tests/             # 测试
├── config.py          # 配置
└── run.py             # 启动脚本
```

## CI/CD

推送到 main 分支自动触发：

1. 测试（lint + pytest）
2. 构建 Docker 镜像（latest / 分支名 / commit hash）
3. 部署（通过 Portainer Webhook）

## License

MIT
