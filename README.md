# 轻量级域名配置服务

一个简单的域名配置管理服务，支持多语言配置和语言回退。

## 特性

- 🌐 域名管理（CRUD）
- 🌍 多语言配置支持（zh-CN, en-US, ja-JP, zh-TW, th-TH）
- 🔄 语言回退机制
- 🔐 API 密码认证
- 📦 Redis 缓存（可选）
- 📖 Swagger API 文档
- 🖥️ Web 管理界面
- 🏥 健康检查端点

## 快速开始

### 使用 Docker（推荐）

```bash
docker run -d \
  -p 5000:5000 \
  -e DATABASE_URL=sqlite:///data/app.db \
  -e ADMIN_PASSWORD=your-password \
  -v domain-data:/app/data \
  hkccr.ccs.tencentyun.com/gdgeek/domain:latest
```

### 使用 Docker Compose

```bash
# 开发环境
docker compose -f docker-compose.dev.yml up -d

# 生产环境
docker compose up -d
```

### 本地开发

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

| 地址 | 说明 |
|------|------|
| http://localhost:5000/admin/ | Web 管理界面 |
| http://localhost:5000/api/docs | Swagger API 文档 |
| http://localhost:5000/api/health | 健康检查 |

## API 认证

API 需要密码认证，支持两种方式：

```bash
# 方式一：X-Admin-Password 请求头
curl -H "X-Admin-Password: your-password" http://localhost:5000/api/domains

# 方式二：Basic Auth（密码作为 password）
curl -u :your-password http://localhost:5000/api/domains
```

## API 示例

### 创建域名
```bash
curl -X POST http://localhost:5000/api/domains \
  -H "Content-Type: application/json" \
  -H "X-Admin-Password: your-password" \
  -d '{"name": "example.com", "description": "示例域名"}'
```

### 创建配置
```bash
curl -X POST http://localhost:5000/api/domains/1/configs \
  -H "Content-Type: application/json" \
  -H "X-Admin-Password: your-password" \
  -d '{"language": "zh-CN", "data": {"title": "网站标题"}}'
```

### 查询配置（公开接口，无需认证）
```bash
curl "http://localhost:5000/api/query?domain=example.com&lang=zh-CN"
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| DATABASE_URL | 数据库连接 | sqlite:///dev.db |
| ADMIN_PASSWORD | API/管理密码 | admin123 |
| SECRET_KEY | Flask 密钥 | dev-secret-key |
| REDIS_URL | Redis 连接（可选） | - |
| REDIS_TTL | 缓存过期时间（秒） | 3600 |

## 项目结构

```
├── app/
│   ├── api/           # REST API
│   ├── admin/         # Web 管理界面
│   ├── models/        # 数据模型
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
