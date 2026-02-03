# 数据库设计

## 1. 数据库概述

### 1.1 数据库信息
- **数据库类型**: MySQL 8.0+
- **字符集**: utf8mb3
- **排序规则**: utf8mb3_unicode_ci
- **存储引擎**: InnoDB

### 1.2 表结构概览

项目使用三表架构：

1. **domains** - 域名表
2. **configs** - 配置表
3. **translations** - 翻译表

## 2. 表结构详解

### 2.1 domains 表

存储域名信息及其与配置的关联关系。

```sql
CREATE TABLE `domains` (
  `id` int NOT NULL AUTO_INCREMENT,
  `domain` varchar(255) NOT NULL,
  `config_id` int NOT NULL,
  `homepage` varchar(500) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `domain` (`domain`),
  KEY `config_id` (`config_id`),
  CONSTRAINT `domains_ibfk_1` FOREIGN KEY (`config_id`) REFERENCES `configs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_unicode_ci;
```

**字段说明:**

| 字段 | 类型 | 说明 | 约束 |
|------|------|------|------|
| id | int | 主键 | AUTO_INCREMENT, NOT NULL |
| domain | varchar(255) | 域名 | UNIQUE, NOT NULL |
| config_id | int | 关联的配置 ID | NOT NULL, FOREIGN KEY |
| homepage | varchar(500) | 主页 URL | NULL |
| created_at | timestamp | 创建时间 | DEFAULT CURRENT_TIMESTAMP |
| updated_at | timestamp | 更新时间 | ON UPDATE CURRENT_TIMESTAMP |

**索引:**
- PRIMARY KEY: `id`
- UNIQUE KEY: `domain`
- FOREIGN KEY: `config_id` → `configs(id)` ON DELETE CASCADE

**业务规则:**
- 域名必须唯一
- 必须关联一个有效的配置
- 删除配置时，关联的域名也会被删除（CASCADE）
- homepage 字段可选，用于存储域名的主页 URL

---

### 2.2 configs 表

存储配置的基本信息（默认语言内容）。

```sql
CREATE TABLE `configs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(200) DEFAULT NULL,
  `author` varchar(100) DEFAULT NULL,
  `description` text,
  `keywords` text,
  `links` json DEFAULT NULL,
  `permissions` json DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_unicode_ci;
```

**字段说明:**

| 字段 | 类型 | 说明 | 约束 |
|------|------|------|------|
| id | int | 主键 | AUTO_INCREMENT, NOT NULL |
| title | varchar(200) | 标题（默认语言） | NULL |
| author | varchar(100) | 作者（默认语言） | NULL |
| description | text | 描述（默认语言） | NULL |
| keywords | text | 关键词（默认语言） | NULL |
| links | json | 链接配置 | NULL |
| permissions | json | 权限配置 | NULL |
| created_at | timestamp | 创建时间 | DEFAULT CURRENT_TIMESTAMP |
| updated_at | timestamp | 更新时间 | ON UPDATE CURRENT_TIMESTAMP |

**索引:**
- PRIMARY KEY: `id`

**JSON 字段格式:**

**links 字段示例:**
```json
{
  "home": "https://example.com",
  "about": "https://example.com/about",
  "contact": "https://example.com/contact",
  "api": "https://api.example.com"
}
```

**permissions 字段示例:**
```json
{
  "read": true,
  "write": true,
  "admin": false,
  "features": {
    "comments": true,
    "upload": false,
    "api_access": true
  },
  "roles": ["user", "editor"],
  "limits": {
    "max_uploads": 100,
    "max_api_calls": 1000
  }
}
```

**业务规则:**
- 所有字段都是可选的
- title, author, description, keywords 存储默认语言（zh-cn）的内容
- links 和 permissions 使用 JSON 格式存储复杂配置
- 一个配置可以被多个域名共享

---

### 2.3 translations 表

存储配置的多语言翻译内容。

```sql
CREATE TABLE `translations` (
  `id` int NOT NULL AUTO_INCREMENT,
  `config_id` int NOT NULL,
  `language_code` varchar(10) NOT NULL,
  `title` varchar(200) NOT NULL,
  `author` varchar(100) NOT NULL,
  `description` text NOT NULL,
  `keywords` json NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `config_language_unique` (`config_id`,`language_code`),
  KEY `idx_config_id` (`config_id`),
  KEY `idx_language_code` (`language_code`),
  CONSTRAINT `translations_ibfk_1` FOREIGN KEY (`config_id`) REFERENCES `configs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_unicode_ci;
```

**字段说明:**

| 字段 | 类型 | 说明 | 约束 |
|------|------|------|------|
| id | int | 主键 | AUTO_INCREMENT, NOT NULL |
| config_id | int | 关联的配置 ID | NOT NULL, FOREIGN KEY |
| language_code | varchar(10) | 语言代码 | NOT NULL |
| title | varchar(200) | 翻译的标题 | NOT NULL |
| author | varchar(100) | 翻译的作者 | NOT NULL |
| description | text | 翻译的描述 | NOT NULL |
| keywords | json | 翻译的关键词数组 | NOT NULL |
| created_at | timestamp | 创建时间 | DEFAULT CURRENT_TIMESTAMP |
| updated_at | timestamp | 更新时间 | ON UPDATE CURRENT_TIMESTAMP |

**索引:**
- PRIMARY KEY: `id`
- UNIQUE KEY: `(config_id, language_code)` - 确保每个配置的每种语言只有一个翻译
- INDEX: `config_id` - 加速按配置查询
- INDEX: `language_code` - 加速按语言查询
- FOREIGN KEY: `config_id` → `configs(id)` ON DELETE CASCADE

**支持的语言代码:**
- `zh-cn`: 简体中文
- `zh-tw`: 繁体中文
- `en-us`: 美式英语
- `ja-jp`: 日语
- `th-th`: 泰语

**keywords 字段示例:**
```json
["关键词1", "关键词2", "关键词3"]
```

**业务规则:**
- 每个配置的每种语言只能有一个翻译（UNIQUE 约束）
- 所有字段都是必填的（NOT NULL）
- keywords 使用 JSON 数组格式存储
- 删除配置时，所有关联的翻译也会被删除（CASCADE）



## 3. 表关系图

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  ┌──────────────┐         ┌──────────────┐                │
│  │   domains    │         │   configs    │                │
│  ├──────────────┤         ├──────────────┤                │
│  │ id (PK)      │         │ id (PK)      │                │
│  │ domain       │         │ title        │                │
│  │ config_id(FK)├────────►│ author       │                │
│  │ homepage     │         │ description  │                │
│  │ created_at   │         │ keywords     │                │
│  │ updated_at   │         │ links        │                │
│  └──────────────┘         │ permissions  │                │
│                           │ created_at   │                │
│                           │ updated_at   │                │
│                           └──────┬───────┘                │
│                                  │                         │
│                                  │ 1:N                     │
│                                  │                         │
│                           ┌──────▼───────┐                │
│                           │ translations │                │
│                           ├──────────────┤                │
│                           │ id (PK)      │                │
│                           │ config_id(FK)│                │
│                           │ language_code│                │
│                           │ title        │                │
│                           │ author       │                │
│                           │ description  │                │
│                           │ keywords     │                │
│                           │ created_at   │                │
│                           │ updated_at   │                │
│                           └──────────────┘                │
│                                                             │
└─────────────────────────────────────────────────────────────┘

关系说明:
- domains.config_id → configs.id (N:1, CASCADE DELETE)
- translations.config_id → configs.id (N:1, CASCADE DELETE)
- 一个 config 可以被多个 domains 使用
- 一个 config 可以有多个 translations（不同语言）
```

## 4. 数据库初始化

### 4.1 完整初始化脚本

使用 `migrations/init_with_translations.sql` 创建完整的数据库结构：

```bash
mysql -u root -p bujiaban < migrations/init_with_translations.sql
```

### 4.2 分步迁移

如果从旧版本升级，按顺序执行以下迁移：

```bash
# 1. 添加 permissions 字段
./scripts/migrate.sh migrations/001_add_permissions_field.sql

# 2. 拆分为双表架构
./scripts/migrate.sh migrations/002_split_to_two_tables.sql

# 3. 添加 homepage 字段
./scripts/migrate.sh migrations/003_add_homepage_to_domains.sql

# 4. 创建 translations 表
./scripts/migrate.sh migrations/004_create_translations_table.sql

# 5. 迁移数据到 translations 表
./scripts/migrate.sh migrations/005_migrate_config_data_to_translations.sql
```

## 5. 示例数据

### 5.1 插入配置

```sql
INSERT INTO configs (title, author, description, keywords, links, permissions)
VALUES (
  '示例网站',
  '张三',
  '这是一个示例网站的描述',
  '示例,网站,测试',
  '{"home": "https://example.com", "about": "https://example.com/about"}',
  '{"read": true, "write": true, "admin": false}'
);
```

### 5.2 插入域名

```sql
INSERT INTO domains (domain, config_id, homepage)
VALUES (
  'example.com',
  1,
  'https://www.example.com'
);
```

### 5.3 插入翻译

```sql
-- 中文翻译
INSERT INTO translations (config_id, language_code, title, author, description, keywords)
VALUES (
  1,
  'zh-cn',
  '示例网站',
  '张三',
  '这是一个示例网站的描述',
  '["示例", "网站", "测试"]'
);

-- 英文翻译
INSERT INTO translations (config_id, language_code, title, author, description, keywords)
VALUES (
  1,
  'en-us',
  'Example Website',
  'John Doe',
  'This is an example website description',
  '["example", "website", "test"]'
);

-- 日文翻译
INSERT INTO translations (config_id, language_code, title, author, description, keywords)
VALUES (
  1,
  'ja-jp',
  'サンプルウェブサイト',
  '山田太郎',
  'これはサンプルウェブサイトの説明です',
  '["サンプル", "ウェブサイト", "テスト"]'
);
```

## 6. 查询示例

### 6.1 查询域名及其配置

```sql
SELECT 
  d.id,
  d.domain,
  d.homepage,
  c.id as config_id,
  c.title,
  c.author,
  c.description,
  c.keywords,
  c.links,
  c.permissions
FROM domains d
JOIN configs c ON d.config_id = c.id
WHERE d.domain = 'example.com';
```

### 6.2 查询配置的所有翻译

```sql
SELECT 
  t.id,
  t.language_code,
  t.title,
  t.author,
  t.description,
  t.keywords
FROM translations t
WHERE t.config_id = 1
ORDER BY t.language_code;
```

### 6.3 查询特定语言的配置

```sql
SELECT 
  c.id,
  COALESCE(t.title, c.title) as title,
  COALESCE(t.author, c.author) as author,
  COALESCE(t.description, c.description) as description,
  COALESCE(t.keywords, c.keywords) as keywords,
  c.links,
  c.permissions
FROM configs c
LEFT JOIN translations t ON c.id = t.config_id AND t.language_code = 'en-us'
WHERE c.id = 1;
```

### 6.4 查询使用同一配置的所有域名

```sql
SELECT 
  d.domain,
  d.homepage
FROM domains d
WHERE d.config_id = 1;
```

## 7. 性能优化

### 7.1 索引策略

**已创建的索引:**
- `domains.domain` (UNIQUE) - 加速域名查询
- `domains.config_id` - 加速配置关联查询
- `translations.config_id` - 加速按配置查询翻译
- `translations.language_code` - 加速按语言查询
- `translations.(config_id, language_code)` (UNIQUE) - 确保唯一性并加速组合查询

### 7.2 查询优化建议

1. **使用索引**: 所有查询都应该利用已有索引
2. **避免全表扫描**: 始终在 WHERE 子句中使用索引字段
3. **使用 JOIN 而非子查询**: JOIN 通常比子查询更高效
4. **限制返回行数**: 使用 LIMIT 分页查询

### 7.3 连接池配置

```typescript
{
  pool: {
    min: 2,        // 最小连接数
    max: 10,       // 最大连接数
    acquire: 30000, // 获取连接超时时间（毫秒）
    idle: 10000     // 连接空闲超时时间（毫秒）
  }
}
```

## 8. 数据完整性

### 8.1 外键约束

- `domains.config_id` → `configs.id` (ON DELETE CASCADE)
  - 删除配置时，自动删除所有关联的域名
  
- `translations.config_id` → `configs.id` (ON DELETE CASCADE)
  - 删除配置时，自动删除所有关联的翻译

### 8.2 唯一性约束

- `domains.domain` - 确保域名唯一
- `translations.(config_id, language_code)` - 确保每个配置的每种语言只有一个翻译

### 8.3 非空约束

**domains 表:**
- `domain` NOT NULL
- `config_id` NOT NULL

**translations 表:**
- `config_id` NOT NULL
- `language_code` NOT NULL
- `title` NOT NULL
- `author` NOT NULL
- `description` NOT NULL
- `keywords` NOT NULL

## 9. 备份和恢复

### 9.1 备份数据库

```bash
# 备份整个数据库
mysqldump -u root -p bujiaban > backup_$(date +%Y%m%d_%H%M%S).sql

# 仅备份结构
mysqldump -u root -p --no-data bujiaban > schema_backup.sql

# 仅备份数据
mysqldump -u root -p --no-create-info bujiaban > data_backup.sql
```

### 9.2 恢复数据库

```bash
# 恢复完整备份
mysql -u root -p bujiaban < backup_20260203_120000.sql

# 恢复结构
mysql -u root -p bujiaban < schema_backup.sql

# 恢复数据
mysql -u root -p bujiaban < data_backup.sql
```

## 10. 数据迁移注意事项

### 10.1 从单表到三表的迁移

如果从旧的单表结构迁移，需要：

1. 创建 configs 表
2. 将原表数据迁移到 configs 表
3. 创建 domains 表
4. 创建域名到配置的映射关系
5. 创建 translations 表
6. 将 configs 表的默认语言数据迁移到 translations 表

### 10.2 数据一致性检查

```sql
-- 检查孤立的域名（config_id 不存在）
SELECT d.* 
FROM domains d 
LEFT JOIN configs c ON d.config_id = c.id 
WHERE c.id IS NULL;

-- 检查孤立的翻译（config_id 不存在）
SELECT t.* 
FROM translations t 
LEFT JOIN configs c ON t.config_id = c.id 
WHERE c.id IS NULL;

-- 检查重复的翻译
SELECT config_id, language_code, COUNT(*) as count
FROM translations
GROUP BY config_id, language_code
HAVING count > 1;
```

## 11. 下一步

阅读完本文档后，请继续阅读：

1. [API 规范](./AI_REBUILD_04_API.md)
2. [核心模块](./AI_REBUILD_05_MODULES.md)

