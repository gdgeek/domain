# Implementation Plan: Lightweight Domain Config Service

## Overview

本实现计划将轻量级域名配置服务分解为离散的编码步骤。系统使用 Python + Flask 构建，采用极简的两表架构（domains + configs），通过 `域名 + 语言` 映射到对应的配置。

## Tasks

- [x] 1. 项目初始化和数据库设置
  - [x] 1.1 创建项目目录结构
    - 创建 app/, tests/, migrations/ 目录
    - 创建 requirements.txt（Flask, Flask-SQLAlchemy, Flask-RESTX, psycopg2-binary, redis, hypothesis, pytest）
    - 创建 config.py 配置文件
    - _Requirements: 9.4, 9.5_
  - [x] 1.2 配置 Flask 应用和数据库
    - 创建 Flask 应用工厂
    - 配置 SQLAlchemy 连接
    - 创建数据库模型（Domain, Config）
    - _Requirements: 4.1, 4.2_
  - [x] 1.3 创建数据库迁移
    - 使用 Flask-Migrate 创建初始迁移
    - 添加索引
    - _Requirements: 4.3, 4.4, 4.5_

- [x] 2. 实现数据模型和 Repository 层
  - [x] 2.1 实现 Domain Repository
    - create, get_by_id, get_by_name, get_all, update, delete
    - _Requirements: 1.1, 1.3, 1.4, 1.5, 1.6, 1.7_
  - [x] 2.2 实现 Config Repository
    - create, get_by_id, get_by_domain_and_language, get_all_by_domain, update, delete
    - _Requirements: 2.1, 2.4, 2.5, 2.6, 2.7_
  - [ ]* 2.3 编写 Domain CRUD 属性测试
    - **Property 1: Domain CRUD Round-Trip Consistency**
    - **Validates: Requirements 1.1, 1.4, 1.5**
  - [ ]* 2.4 编写 Config 唯一性约束属性测试
    - **Property 5: Config Language Uniqueness**
    - **Validates: Requirements 2.2**

- [ ] 3. 实现 Redis 缓存层（可选）
  - [x] 3.1 创建 CacheService 类
    - 实现 Redis 连接管理（支持无 Redis 运行）
    - 实现 get, set, invalidate, invalidate_all 方法
    - 缓存键格式: `domain:{name}:lang:{language}`
    - TTL: 3600 秒
    - _Requirements: 5.1, 5.2, 5.3, 5.5_
  - [ ]* 3.2 编写缓存失效属性测试
    - **Property 9: Cache Invalidation on Update**
    - **Validates: Requirements 5.4**

- [ ] 4. 实现业务逻辑层（Service Layer）
  - [x] 4.1 创建 DomainService
    - create_domain, get_domain, get_domain_by_name, list_domains, update_domain, delete_domain
    - 域名验证逻辑
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7_
  - [x] 4.2 创建 ConfigService
    - create_config, get_config, get_config_with_fallback, list_configs_by_domain, update_config, delete_config
    - 语言回退逻辑
    - 缓存集成
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_
  - [ ]* 4.3 编写域名删除级联属性测试
    - **Property 3: Domain Deletion Cascade**
    - **Validates: Requirements 1.7**
  - [ ]* 4.4 编写语言回退属性测试
    - **Property 7: Language Fallback**
    - **Validates: Requirements 3.2, 3.3**

- [ ] 5. 实现 REST API 层
  - [x] 5.1 创建 Flask-RESTX API 结构和 Swagger 配置
    - 配置 Flask-RESTX
    - 设置 Swagger UI 路由（/api/docs）
    - 定义错误响应模型
    - _Requirements: 8.1, 8.2, 8.3_
  - [x] 5.2 实现 Domain API 端点
    - POST /api/domains - 创建域名
    - GET /api/domains - 获取所有域名
    - GET /api/domains/{id} - 获取指定域名
    - PUT /api/domains/{id} - 更新域名
    - DELETE /api/domains/{id} - 删除域名
    - _Requirements: 1.1, 1.3, 1.4, 1.5, 1.6_
  - [x] 5.3 实现 Config API 端点
    - POST /api/domains/{id}/configs - 创建配置
    - GET /api/domains/{id}/configs - 获取所有配置
    - GET /api/domains/{id}/configs/{language} - 获取指定语言配置
    - PUT /api/domains/{id}/configs/{language} - 更新配置
    - DELETE /api/domains/{id}/configs/{language} - 删除配置
    - _Requirements: 2.4, 2.5, 2.6, 2.7_
  - [x] 5.4 实现查询 API 端点
    - GET /api/query?domain={domain_name}&lang={language}
    - 支持语言回退
    - 返回实际语言标识
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_
  - [x] 5.5 实现统一错误处理
    - 400（验证错误）、404（未找到）、409（重复）、500（服务器错误）
    - 统一 JSON 错误格式
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
  - [ ]* 5.6 编写 API 错误处理属性测试
    - **Property 10: HTTP Error Status Codes**
    - **Validates: Requirements 7.1, 7.2, 7.3, 7.5**

- [ ] 6. 实现 Web 管理界面
  - [x] 6.1 创建基础模板和静态文件
    - base.html 模板（导航栏）
    - 简单 CSS 样式
    - _Requirements: 6.7_
  - [x] 6.2 实现域名管理页面
    - 域名列表页面（/admin/domains）
    - 创建/编辑域名表单
    - 删除确认
    - _Requirements: 6.1, 6.2_
  - [x] 6.3 实现配置管理页面
    - 配置列表页面（/admin/domains/{id}/configs）
    - 语言选择下拉框
    - 创建/编辑配置表单
    - 显示已有语言配置
    - _Requirements: 6.3, 6.4, 6.5, 6.6_

- [ ] 7. 配置和部署准备
  - [x] 7.1 创建配置文件
    - config.py（环境变量支持）
    - .env.example
    - _Requirements: 9.6_
  - [x] 7.2 创建启动脚本和文档
    - run.py 启动脚本
    - README.md（安装、配置、运行说明）
    - _Requirements: 9.4, 9.5_

- [ ] 8. Docker 容器化
  - [x] 8.1 创建 Dockerfile
    - 基于 Python 3.11 镜像
    - 多阶段构建优化镜像大小
    - 配置 gunicorn 生产服务器
  - [x] 8.2 创建 docker-compose.yml
    - 应用服务（Flask app）
    - PostgreSQL 数据库服务
    - Redis 缓存服务（可选）
    - 配置网络和数据卷
  - [x] 8.3 创建 docker-compose.override.yml
    - 开发环境配置
    - 热重载支持

- [ ] 9. GitHub CI/CD
  - [x] 9.1 创建 GitHub Actions 工作流
    - .github/workflows/ci.yml
    - 代码检查（lint）
    - 运行测试
    - 构建 Docker 镜像
  - [x] 9.2 创建部署工作流
    - .github/workflows/deploy.yml
    - 推送镜像到 Docker Hub / GitHub Container Registry
    - 可选：自动部署到服务器

- [x] 10. Final Checkpoint
  - 运行所有测试
  - 手动测试 Web 界面
  - 验证 Swagger 文档
  - 测试 Docker 构建和运行
  - 验证 CI/CD 流程

## Notes

- 标记 `*` 的任务为可选的属性测试任务
- 每个任务都引用了具体的需求编号以便追溯
- 属性测试使用 hypothesis 库
- Redis 缓存是可选的，系统可以在没有 Redis 的情况下正常运行
