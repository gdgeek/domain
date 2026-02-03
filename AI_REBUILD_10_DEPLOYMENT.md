# AI 重建指南 10 - 部署指南

## 概述

本文档详细说明项目的部署方案，包括 Docker 部署、环境配置、数据库初始化和运维管理。

## 目录

- [部署架构](#部署架构)
- [Docker 部署](#docker-部署)
- [环境配置](#环境配置)
- [数据库初始化](#数据库初始化)
- [运维管理](#运维管理)
- [故障排查](#故障排查)

---

## 部署架构

### 服务架构

```
┌─────────────────────────────────────┐
│         Nginx (反向代理)             │
│  HTTPS, 负载均衡, 静态文件           │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Node.js Application             │
│  Express, TypeScript                 │
│  Port: 3000                          │
└──────────────┬──────────────────────┘
               │
       ┌───────┴───────┐
       │               │
┌──────▼──────┐ ┌─────▼──────┐
│   MySQL     │ │   Redis    │
│  Port: 3306 │ │ Port: 6379 │
└─────────────┘ └────────────┘
```

### Docker Compose 架构

```yaml
services:
  app:        # Node.js 应用
  mysql:      # MySQL 数据库
  redis:      # Redis 缓存
```

---

## Docker 部署

### Dockerfile

**文件**: `Dockerfile`

```dockerfile
# Multi-stage build for domain-config-service
# Stage 1: Build stage
FROM node:24-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies (including devDependencies for build)
RUN npm ci

# Copy source code
COPY . .

# Build TypeScript to JavaScript
RUN npm run build

# Remove devDependencies
RUN npm prune --production

# Stage 2: Production stage
FROM node:24-alpine AS production

# Install dumb-init for proper signal handling
RUN apk add --no-cache dumb-init

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Copy built application from builder stage
COPY --from=builder --chown=nodejs:nodejs /app/dist ./dist
COPY --from=builder --chown=nodejs:nodejs /app/node_modules ./node_modules

# Copy migration files
COPY --chown=nodejs:nodejs src/models/migrations ./src/models/migrations

# Copy public files for admin interface
COPY --chown=nodejs:nodejs public ./public

# Create logs directory with proper permissions
RUN mkdir -p logs && \
    chown -R nodejs:nodejs logs && \
    chmod -R 755 logs

# Switch to non-root user
USER nodejs

# Expose application port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000/health', (res) => { process.exit(res.statusCode === 200 ? 0 : 1) })"

# Use dumb-init to handle signals properly
ENTRYPOINT ["dumb-init", "--"]

# Start the application
CMD ["node", "dist/index.js"]
```

### Docker Compose

**文件**: `docker-compose.yml`

```yaml
version: '3.8'

services:
  # Node.js 应用
  app:
    build:
      context: .
      dockerfile: Dockerfile
    image: domain-config-app:latest
    container_name: domain-config-app
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - PORT=3000
      - DB_HOST=mysql
      - DB_PORT=3306
      - DB_USER=root
      - DB_PASSWORD=${DB_PASSWORD:-admin123}
      - DB_NAME=domain_config
      - REDIS_ENABLED=true
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_TTL=3600
      - ADMIN_PASSWORD=${ADMIN_PASSWORD:-admin123}
      - JWT_SECRET=${JWT_SECRET:-your-secret-key}
      - JWT_EXPIRES_IN=24h
    depends_on:
      mysql:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - app-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "node", "-e", "require('http').get('http://localhost:3000/health', (res) => { process.exit(res.statusCode === 200 ? 0 : 1) })"]
      interval: 30s
      timeout: 3s
      retries: 3
      start_period: 10s

  # MySQL 数据库
  mysql:
    image: mysql:8.0
    container_name: domain-config-mysql
    environment:
      - MYSQL_ROOT_PASSWORD=${DB_PASSWORD:-admin123}
      - MYSQL_DATABASE=domain_config
      - MYSQL_CHARACTER_SET_SERVER=utf8mb4
      - MYSQL_COLLATION_SERVER=utf8mb4_unicode_ci
    ports:
      - "3306:3306"
    volumes:
      - mysql-data:/var/lib/mysql
      - ./migrations:/docker-entrypoint-initdb.d
    networks:
      - app-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-p${DB_PASSWORD:-admin123}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis 缓存
  redis:
    image: redis:7-alpine
    container_name: domain-config-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    networks:
      - app-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

networks:
  app-network:
    driver: bridge

volumes:
  mysql-data:
  redis-data:
```

### 构建和启动

```bash
# 1. 构建镜像
docker-compose build

# 2. 启动所有服务
docker-compose up -d

# 3. 查看日志
docker-compose logs -f

# 4. 查看服务状态
docker-compose ps

# 5. 停止服务
docker-compose down

# 6. 停止并删除数据卷
docker-compose down -v
```

---

## 环境配置

### 环境变量文件

**文件**: `.env`

```bash
# ============================================================
# 应用配置
# ============================================================
NODE_ENV=production
PORT=3000
API_PREFIX=/api/v1

# ============================================================
# 数据库配置
# ============================================================
DB_HOST=mysql
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your-strong-password-here
DB_NAME=domain_config

# ============================================================
# Redis 配置
# ============================================================
REDIS_ENABLED=true
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
REDIS_TTL=3600

# ============================================================
# 安全配置
# ============================================================
# 管理员密码（必须修改）
ADMIN_PASSWORD=your-admin-password-here

# JWT 密钥（必须修改，使用强随机密钥）
JWT_SECRET=your-jwt-secret-key-here
JWT_EXPIRES_IN=24h

# ============================================================
# 限流配置
# ============================================================
RATE_LIMIT_WINDOW_MS=60000
RATE_LIMIT_MAX=100

# ============================================================
# 多语言配置
# ============================================================
DEFAULT_LANGUAGE=zh-cn
SUPPORTED_LANGUAGES=zh-cn,zh-tw,en-us,ja-jp,th-th

# ============================================================
# 日志配置
# ============================================================
LOG_LEVEL=info
LOG_FILE=logs/app.log
LOG_ERROR_FILE=logs/app.error.log
```

### 生产环境配置

**重要**: 在生产环境中必须修改以下配置：

```bash
# 1. 生成强 JWT 密钥
openssl rand -base64 32

# 2. 设置强管理员密码
ADMIN_PASSWORD=MyStr0ng!P@ssw0rd2024

# 3. 设置强数据库密码
DB_PASSWORD=MyStr0ng!DB!P@ssw0rd2024

# 4. 设置 JWT 密钥
JWT_SECRET=generated-random-key-from-step-1
```

---

## 数据库初始化

### 初始化脚本

**文件**: `migrations/init_with_translations.sql`

```sql
-- 创建数据库
CREATE DATABASE IF NOT EXISTS domain_config 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci;

USE domain_config;

-- 创建 configs 表
CREATE TABLE IF NOT EXISTS configs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(255),
  author VARCHAR(255),
  description VARCHAR(255),
  keywords VARCHAR(255),
  links JSON,
  permissions JSON,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建 domains 表
CREATE TABLE IF NOT EXISTS domains (
  id INT AUTO_INCREMENT PRIMARY KEY,
  domain VARCHAR(255) NOT NULL UNIQUE,
  config_id INT NOT NULL,
  homepage VARCHAR(500),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (config_id) REFERENCES configs(id) ON DELETE CASCADE,
  INDEX idx_domain (domain),
  INDEX idx_config_id (config_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建 translations 表
CREATE TABLE IF NOT EXISTS translations (
  id INT AUTO_INCREMENT PRIMARY KEY,
  config_id INT NOT NULL,
  language_code VARCHAR(10) NOT NULL,
  title VARCHAR(200) NOT NULL,
  author VARCHAR(100) NOT NULL,
  description VARCHAR(1000) NOT NULL,
  keywords TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY unique_config_language (config_id, language_code),
  FOREIGN KEY (config_id) REFERENCES configs(id) ON DELETE CASCADE,
  INDEX idx_config_id (config_id),
  INDEX idx_language_code (language_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 插入示例数据
INSERT INTO configs (title, author, description, keywords, links, permissions) VALUES
('示例网站', '作者', '这是一个示例网站', '关键词1,关键词2', '{}', '{}');

INSERT INTO domains (domain, config_id, homepage) VALUES
('example.com', 1, 'https://example.com');

INSERT INTO translations (config_id, language_code, title, author, description, keywords) VALUES
(1, 'zh-cn', '示例网站', '作者', '这是一个示例网站', '关键词1,关键词2'),
(1, 'en-us', 'Example Website', 'Author', 'This is an example website', 'keyword1,keyword2');
```

### 手动初始化

```bash
# 1. 连接到 MySQL 容器
docker exec -it domain-config-mysql mysql -uroot -p

# 2. 执行初始化脚本
source /docker-entrypoint-initdb.d/init_with_translations.sql

# 3. 验证表结构
USE domain_config;
SHOW TABLES;
DESCRIBE configs;
DESCRIBE domains;
DESCRIBE translations;

# 4. 查看数据
SELECT * FROM configs;
SELECT * FROM domains;
SELECT * FROM translations;
```

---

## 运维管理

### 日志管理

#### 查看应用日志

```bash
# 查看实时日志
docker-compose logs -f app

# 查看最近 100 行日志
docker-compose logs --tail=100 app

# 查看特定时间的日志
docker-compose logs --since="2024-01-01T00:00:00" app
```

#### 日志文件位置

```
logs/
├── app.log          # 应用日志
└── app.error.log    # 错误日志
```

#### 日志轮转配置

**文件**: `logrotate.conf`

```
/app/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 nodejs nodejs
}
```

### 数据库备份

#### 自动备份脚本

```bash
#!/bin/bash
# backup-db.sh

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/domain_config_$DATE.sql"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
docker exec domain-config-mysql mysqldump \
  -uroot -p${DB_PASSWORD} \
  domain_config > $BACKUP_FILE

# 压缩备份文件
gzip $BACKUP_FILE

# 删除 7 天前的备份
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_FILE.gz"
```

#### 设置定时备份

```bash
# 添加到 crontab
crontab -e

# 每天凌晨 2 点备份
0 2 * * * /path/to/backup-db.sh
```

#### 恢复数据库

```bash
# 解压备份文件
gunzip domain_config_20240101_020000.sql.gz

# 恢复数据库
docker exec -i domain-config-mysql mysql \
  -uroot -p${DB_PASSWORD} \
  domain_config < domain_config_20240101_020000.sql
```

### 监控和告警

#### 健康检查

```bash
# 检查应用健康状态
curl http://localhost:3000/health

# 响应示例
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00.000Z",
  "services": {
    "database": "healthy",
    "redis": "healthy"
  }
}
```

#### 监控指标

```bash
# 查看 Prometheus 指标
curl http://localhost:3000/metrics
```

#### 性能监控

```bash
# 查看容器资源使用
docker stats

# 查看容器详细信息
docker inspect domain-config-app
```

### 扩容和负载均衡

#### 水平扩容

```yaml
# docker-compose.yml
services:
  app:
    deploy:
      replicas: 3  # 运行 3 个实例
```

#### Nginx 负载均衡

```nginx
upstream backend {
    least_conn;
    server app1:3000;
    server app2:3000;
    server app3:3000;
}

server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 故障排查

### 常见问题

#### 1. 应用无法启动

**症状**: 容器启动后立即退出

**排查步骤**:

```bash
# 查看容器日志
docker-compose logs app

# 检查环境变量
docker-compose config

# 检查端口占用
netstat -tulpn | grep 3000
```

**常见原因**:
- 数据库连接失败
- 端口被占用
- 环境变量配置错误

#### 2. 数据库连接失败

**症状**: 应用日志显示 "ECONNREFUSED" 或 "Access denied"

**排查步骤**:

```bash
# 检查 MySQL 容器状态
docker-compose ps mysql

# 测试数据库连接
docker exec -it domain-config-mysql mysql -uroot -p

# 检查数据库配置
docker exec domain-config-mysql mysql -uroot -p -e "SHOW VARIABLES LIKE 'character%';"
```

**解决方案**:
- 检查数据库密码
- 确认数据库已初始化
- 检查网络连接

#### 3. Redis 连接失败

**症状**: 应用日志显示 Redis 连接错误

**排查步骤**:

```bash
# 检查 Redis 容器状态
docker-compose ps redis

# 测试 Redis 连接
docker exec -it domain-config-redis redis-cli ping

# 查看 Redis 日志
docker-compose logs redis
```

**解决方案**:
- 检查 Redis 配置
- 确认 Redis 容器运行正常
- 检查网络连接

#### 4. 内存不足

**症状**: 容器被 OOM Killer 杀死

**排查步骤**:

```bash
# 查看容器资源使用
docker stats

# 查看系统内存
free -h

# 查看 Docker 日志
journalctl -u docker
```

**解决方案**:
- 增加容器内存限制
- 优化应用内存使用
- 增加服务器内存

#### 5. 磁盘空间不足

**症状**: 无法写入日志或数据

**排查步骤**:

```bash
# 查看磁盘使用
df -h

# 查看 Docker 磁盘使用
docker system df

# 清理未使用的资源
docker system prune -a
```

### 调试技巧

#### 进入容器调试

```bash
# 进入应用容器
docker exec -it domain-config-app sh

# 查看文件
ls -la /app

# 查看进程
ps aux

# 查看网络
netstat -tulpn
```

#### 查看详细日志

```bash
# 设置日志级别为 debug
docker-compose up -d --env LOG_LEVEL=debug

# 查看详细日志
docker-compose logs -f app
```

---

## 部署检查清单

### 部署前检查

- [ ] 修改所有默认密码
- [ ] 配置 HTTPS
- [ ] 设置防火墙规则
- [ ] 配置备份策略
- [ ] 设置监控告警
- [ ] 测试健康检查
- [ ] 测试数据库连接
- [ ] 测试 Redis 连接
- [ ] 验证环境变量
- [ ] 运行安全扫描

### 部署后检查

- [ ] 验证应用可访问
- [ ] 测试 API 端点
- [ ] 检查日志输出
- [ ] 验证数据库数据
- [ ] 测试缓存功能
- [ ] 验证备份正常
- [ ] 检查监控指标
- [ ] 测试故障恢复
- [ ] 验证性能指标
- [ ] 文档更新

---

## 相关文档

- [AI_REBUILD_02_TECH_STACK.md](./AI_REBUILD_02_TECH_STACK.md) - 技术栈
- [AI_REBUILD_03_DATABASE.md](./AI_REBUILD_03_DATABASE.md) - 数据库设计
- [AI_REBUILD_09_SECURITY.md](./AI_REBUILD_09_SECURITY.md) - 安全机制
- [AI_REBUILD_11_TESTING.md](./AI_REBUILD_11_TESTING.md) - 测试指南
