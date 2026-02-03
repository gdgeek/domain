# 轻量级域名配置服务

一个简单的域名配置管理服务，支持多语言配置和语言回退。

## 特性

- 🌐 域名管理（CRUD）
- 🌍 多语言配置支持（zh-CN, en, ja, zh-TW, th）
- 🔄 语言回退机制
- 📦 Redis 缓存（可选）
- 📖 Swagger API 文档
- 🖥️ Web 管理界面

## 快速开始

### 使用 Docker Compose（推荐）

```bash
# 开发环境（支持热重载）
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# 生产环境
docker-compose up -d
```

### 本地开发

```bash
# 1. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 4. 初始化数据库
flask db upgrade

# 5. 启动服务
python run.py
```

## 访问地址

- Web 管理界面: http://localhost:5000/admin/
- API 文档: http://localhost:5000/api/docs
- API 端点: http://localhost:5000/api/

## API 示例

### 创建域名
```bash
curl -X POST http://localhost:5000/api/domains \
  -H "Content-Type: application/json" \
  -d '{"name": "example.com", "description": "示例域名"}'
```

### 创建配置
```bash
curl -X POST http://localhost:5000/api/domains/1/configs \
  -H "Content-Type: application/json" \
  -d '{"language": "zh-CN", "data": {"title": "网站标题", "description": "网站描述"}}'
```

### 查询配置（支持语言回退）
```bash
# 查询中文配置
curl "http://localhost:5000/api/query?domain=example.com&lang=zh-CN"

# 查询英文配置（如果不存在会回退到中文）
curl "http://localhost:5000/api/query?domain=example.com&lang=en"
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| FLASK_ENV | 运行环境 | development |
| SECRET_KEY | 密钥 | dev-secret-key |
| DATABASE_URL | 数据库连接 | sqlite:///dev.db |
| REDIS_URL | Redis 连接（可选） | - |
| REDIS_TTL | 缓存过期时间（秒） | 3600 |

## 项目结构

```
.
├── app/
│   ├── api/           # REST API
│   ├── admin/         # Web 管理界面
│   ├── models/        # 数据模型
│   ├── repositories/  # 数据访问层
│   ├── services/      # 业务逻辑层
│   └── static/        # 静态文件
├── migrations/        # 数据库迁移
├── tests/             # 测试
├── config.py          # 配置
├── run.py             # 启动脚本
├── Dockerfile
└── docker-compose.yml
```

## License

MIT
