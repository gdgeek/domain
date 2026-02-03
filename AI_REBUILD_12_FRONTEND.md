# AI 重建指南 12 - 前端管理界面

## 概述

本文档详细说明项目的前端管理界面实现，包括界面设计、功能模块、API 集成和使用指南。

## 目录

- [界面架构](#界面架构)
- [技术栈](#技术栈)
- [功能模块](#功能模块)
- [API 集成](#api-集成)
- [使用指南](#使用指南)

---

## 界面架构

### 页面结构

```
admin-bootstrap.html
├── 登录界面
│   └── 密码验证
├── 主界面
│   ├── 导航栏
│   ├── 标签页
│   │   ├── 配置管理
│   │   ├── 域名管理
│   │   └── 翻译管理
│   └── 模态框
│       ├── 创建/编辑配置
│       ├── 创建/编辑域名
│       └── 创建/编辑翻译
```

### 界面流程

```
1. 用户访问 /admin
2. 显示登录界面
3. 输入密码 → 调用登录 API
4. 获取 JWT 令牌 → 存储到 localStorage
5. 显示主界面
6. 加载数据 → 显示列表
7. 用户操作 → 调用 API → 刷新列表
```

---

## 技术栈

### 前端框架

- **Bootstrap 5.3.0**: UI 框架
- **Bootstrap Icons**: 图标库
- **原生 JavaScript**: 无需额外框架

### CDN 资源

```html
<!-- Bootstrap 5 CSS -->
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

<!-- Bootstrap Icons -->
<link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">

<!-- Bootstrap 5 JS -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
```

---

## 功能模块

### 1. 登录模块

#### 界面

```html
<div id="loginContainer" class="container">
    <div class="card login-card">
        <div class="card-body">
            <h3 class="card-title text-center mb-4">
                <i class="bi bi-shield-lock"></i> 管理员登录
            </h3>
            <div id="loginAlert"></div>
            <form id="loginForm">
                <div class="mb-3">
                    <label class="form-label">管理密码</label>
                    <input type="password" class="form-control" id="password" required>
                </div>
                <button type="submit" class="btn btn-primary w-100">登录</button>
            </form>
        </div>
    </div>
</div>
```

#### 登录逻辑

```javascript
document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const password = document.getElementById('password').value;
    
    try {
        const response = await fetch('/api/v1/sessions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password })
        });
        
        if (!response.ok) {
            throw new Error('密码错误');
        }
        
        const data = await response.json();
        
        // 存储令牌
        localStorage.setItem('token', data.data.token);
        
        // 显示主界面
        document.getElementById('loginContainer').style.display = 'none';
        document.getElementById('mainContainer').style.display = 'block';
        
        // 加载数据
        loadConfigs();
        loadDomains();
    } catch (error) {
        showAlert('loginAlert', 'danger', error.message);
    }
});
```

### 2. 配置管理模块

#### 配置列表

```html
<div class="card">
    <div class="card-header d-flex justify-content-between align-items-center">
        <h5 class="mb-0"><i class="bi bi-file-text"></i> 配置列表</h5>
        <button class="btn btn-success btn-sm" onclick="showCreateConfigModal()">
            <i class="bi bi-plus-circle"></i> 添加配置
        </button>
    </div>
    <div class="card-body">
        <div id="configAlert"></div>
        <div class="table-responsive">
            <table class="table table-hover">
                <thead class="table-light">
                    <tr>
                        <th>ID</th>
                        <th>标题</th>
                        <th>作者</th>
                        <th>描述</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody id="configTableBody">
                    <!-- 动态加载 -->
                </tbody>
            </table>
        </div>
    </div>
</div>
```

#### 加载配置列表

```javascript
async function loadConfigs() {
    try {
        const response = await fetch('/api/v1/configs');
        const data = await response.json();
        
        const tbody = document.getElementById('configTableBody');
        tbody.innerHTML = '';
        
        if (data.data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center">暂无数据</td></tr>';
            return;
        }
        
        data.data.forEach(config => {
            const row = `
                <tr>
                    <td>${config.id}</td>
                    <td>${config.title || '-'}</td>
                    <td>${config.author || '-'}</td>
                    <td>${config.description || '-'}</td>
                    <td class="table-actions">
                        <button class="btn btn-sm btn-primary" onclick="editConfig(${config.id})">
                            <i class="bi bi-pencil"></i> 编辑
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="deleteConfig(${config.id})">
                            <i class="bi bi-trash"></i> 删除
                        </button>
                    </td>
                </tr>
            `;
            tbody.innerHTML += row;
        });
    } catch (error) {
        showAlert('configAlert', 'danger', '加载配置列表失败');
    }
}
```

#### 创建配置

```javascript
async function createConfig() {
    const data = {
        title: document.getElementById('configTitle').value,
        author: document.getElementById('configAuthor').value,
        description: document.getElementById('configDescription').value,
        keywords: document.getElementById('configKeywords').value,
    };
    
    try {
        const token = localStorage.getItem('token');
        const response = await fetch('/api/v1/configs', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error('创建失败');
        }
        
        // 关闭模态框
        bootstrap.Modal.getInstance(document.getElementById('configModal')).hide();
        
        // 刷新列表
        loadConfigs();
        
        showAlert('configAlert', 'success', '配置创建成功');
    } catch (error) {
        showAlert('configModalAlert', 'danger', error.message);
    }
}
```

#### 更新配置

```javascript
async function updateConfig(id) {
    const data = {
        title: document.getElementById('configTitle').value,
        author: document.getElementById('configAuthor').value,
        description: document.getElementById('configDescription').value,
        keywords: document.getElementById('configKeywords').value,
    };
    
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`/api/v1/configs/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error('更新失败');
        }
        
        bootstrap.Modal.getInstance(document.getElementById('configModal')).hide();
        loadConfigs();
        showAlert('configAlert', 'success', '配置更新成功');
    } catch (error) {
        showAlert('configModalAlert', 'danger', error.message);
    }
}
```

#### 删除配置

```javascript
async function deleteConfig(id) {
    if (!confirm('确定要删除这个配置吗？')) {
        return;
    }
    
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`/api/v1/configs/${id}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error.message);
        }
        
        loadConfigs();
        showAlert('configAlert', 'success', '配置删除成功');
    } catch (error) {
        showAlert('configAlert', 'danger', error.message);
    }
}
```

### 3. 域名管理模块

#### 域名列表

```html
<div class="card">
    <div class="card-header d-flex justify-content-between align-items-center">
        <h5 class="mb-0"><i class="bi bi-globe"></i> 域名列表</h5>
        <button class="btn btn-success btn-sm" onclick="showCreateDomainModal()">
            <i class="bi bi-plus-circle"></i> 添加域名
        </button>
    </div>
    <div class="card-body">
        <div id="domainAlert"></div>
        <div class="table-responsive">
            <table class="table table-hover">
                <thead class="table-light">
                    <tr>
                        <th>ID</th>
                        <th>域名</th>
                        <th>配置 ID</th>
                        <th>首页</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody id="domainTableBody">
                    <!-- 动态加载 -->
                </tbody>
            </table>
        </div>
    </div>
</div>
```

#### 加载域名列表

```javascript
async function loadDomains() {
    try {
        const response = await fetch('/api/v1/domains');
        const data = await response.json();
        
        const tbody = document.getElementById('domainTableBody');
        tbody.innerHTML = '';
        
        if (data.data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center">暂无数据</td></tr>';
            return;
        }
        
        data.data.forEach(domain => {
            const row = `
                <tr>
                    <td>${domain.id}</td>
                    <td>${domain.domain}</td>
                    <td>${domain.configId}</td>
                    <td>${domain.homepage || '-'}</td>
                    <td class="table-actions">
                        <button class="btn btn-sm btn-primary" onclick="editDomain(${domain.id})">
                            <i class="bi bi-pencil"></i> 编辑
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="deleteDomain(${domain.id})">
                            <i class="bi bi-trash"></i> 删除
                        </button>
                    </td>
                </tr>
            `;
            tbody.innerHTML += row;
        });
    } catch (error) {
        showAlert('domainAlert', 'danger', '加载域名列表失败');
    }
}
```

#### 创建域名

```javascript
async function createDomain() {
    const data = {
        domain: document.getElementById('domainName').value,
        configId: parseInt(document.getElementById('domainConfigId').value),
        homepage: document.getElementById('domainHomepage').value || null,
    };
    
    try {
        const token = localStorage.getItem('token');
        const response = await fetch('/api/v1/domains', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error('创建失败');
        }
        
        bootstrap.Modal.getInstance(document.getElementById('domainModal')).hide();
        loadDomains();
        showAlert('domainAlert', 'success', '域名创建成功');
    } catch (error) {
        showAlert('domainModalAlert', 'danger', error.message);
    }
}
```

### 4. 翻译管理模块

#### 翻译列表

```html
<div class="card">
    <div class="card-header">
        <h5 class="mb-0"><i class="bi bi-translate"></i> 翻译管理</h5>
    </div>
    <div class="card-body">
        <div class="mb-3">
            <label class="form-label">选择配置</label>
            <select class="form-select" id="translationConfigSelect" onchange="loadTranslations()">
                <option value="">请选择配置</option>
            </select>
        </div>
        <div id="translationAlert"></div>
        <div id="translationContent" style="display: none;">
            <button class="btn btn-success btn-sm mb-3" onclick="showCreateTranslationModal()">
                <i class="bi bi-plus-circle"></i> 添加翻译
            </button>
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead class="table-light">
                        <tr>
                            <th>语言</th>
                            <th>标题</th>
                            <th>作者</th>
                            <th>描述</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody id="translationTableBody">
                        <!-- 动态加载 -->
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
```

#### 加载翻译列表

```javascript
async function loadTranslations() {
    const configId = document.getElementById('translationConfigSelect').value;
    
    if (!configId) {
        document.getElementById('translationContent').style.display = 'none';
        return;
    }
    
    try {
        const response = await fetch(`/api/v1/configs/${configId}/translations`);
        const data = await response.json();
        
        document.getElementById('translationContent').style.display = 'block';
        
        const tbody = document.getElementById('translationTableBody');
        tbody.innerHTML = '';
        
        if (data.data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center">暂无翻译</td></tr>';
            return;
        }
        
        data.data.forEach(translation => {
            const row = `
                <tr>
                    <td>${translation.languageCode}</td>
                    <td>${translation.title}</td>
                    <td>${translation.author}</td>
                    <td>${translation.description}</td>
                    <td class="table-actions">
                        <button class="btn btn-sm btn-primary" onclick="editTranslation('${translation.languageCode}')">
                            <i class="bi bi-pencil"></i> 编辑
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="deleteTranslation('${translation.languageCode}')">
                            <i class="bi bi-trash"></i> 删除
                        </button>
                    </td>
                </tr>
            `;
            tbody.innerHTML += row;
        });
    } catch (error) {
        showAlert('translationAlert', 'danger', '加载翻译列表失败');
    }
}
```

#### 创建翻译

```javascript
async function createTranslation() {
    const configId = document.getElementById('translationConfigSelect').value;
    const data = {
        languageCode: document.getElementById('translationLanguage').value,
        title: document.getElementById('translationTitle').value,
        author: document.getElementById('translationAuthor').value,
        description: document.getElementById('translationDescription').value,
        keywords: document.getElementById('translationKeywords').value.split(',').map(k => k.trim()),
    };
    
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`/api/v1/configs/${configId}/translations`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error('创建失败');
        }
        
        bootstrap.Modal.getInstance(document.getElementById('translationModal')).hide();
        loadTranslations();
        showAlert('translationAlert', 'success', '翻译创建成功');
    } catch (error) {
        showAlert('translationModalAlert', 'danger', error.message);
    }
}
```

---

## API 集成

### API 基础配置

```javascript
const API_BASE_URL = '/api/v1';

// 获取令牌
function getToken() {
    return localStorage.getItem('token');
}

// 通用请求函数
async function apiRequest(url, options = {}) {
    const token = getToken();
    
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
    };
    
    if (token && options.method !== 'GET') {
        defaultOptions.headers['Authorization'] = `Bearer ${token}`;
    }
    
    const response = await fetch(`${API_BASE_URL}${url}`, {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers,
        },
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error.message);
    }
    
    return response.json();
}
```

### API 调用示例

```javascript
// 获取配置列表
const configs = await apiRequest('/configs');

// 创建配置
const newConfig = await apiRequest('/configs', {
    method: 'POST',
    body: JSON.stringify(data),
});

// 更新配置
const updatedConfig = await apiRequest(`/configs/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
});

// 删除配置
await apiRequest(`/configs/${id}`, {
    method: 'DELETE',
});
```

---

## 使用指南

### 访问管理界面

1. 打开浏览器访问: `http://localhost:3000/admin`
2. 输入管理员密码（默认: `admin123`）
3. 点击"登录"按钮

### 管理配置

1. 点击"配置管理"标签
2. 点击"添加配置"按钮
3. 填写配置信息
4. 点击"保存"按钮

### 管理域名

1. 点击"域名管理"标签
2. 点击"添加域名"按钮
3. 填写域名信息
4. 选择关联的配置
5. 点击"保存"按钮

### 管理翻译

1. 点击"翻译管理"标签
2. 选择要管理的配置
3. 点击"添加翻译"按钮
4. 选择语言并填写翻译内容
5. 点击"保存"按钮

### 退出登录

点击右上角的"退出"按钮

---

## 界面优化

### 响应式设计

使用 Bootstrap 的响应式类：

```html
<div class="container-fluid">
    <div class="row">
        <div class="col-12 col-md-6 col-lg-4">
            <!-- 内容 -->
        </div>
    </div>
</div>
```

### 加载状态

显示加载指示器：

```javascript
function showLoading(elementId) {
    document.getElementById(elementId).innerHTML = `
        <div class="text-center">
            <div class="spinner-border" role="status">
                <span class="visually-hidden">加载中...</span>
            </div>
        </div>
    `;
}
```

### 错误处理

统一的错误提示：

```javascript
function showAlert(containerId, type, message) {
    const alert = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    document.getElementById(containerId).innerHTML = alert;
    
    // 3 秒后自动关闭
    setTimeout(() => {
        const alertElement = document.querySelector(`#${containerId} .alert`);
        if (alertElement) {
            bootstrap.Alert.getInstance(alertElement).close();
        }
    }, 3000);
}
```

---

## 相关文档

- [AI_REBUILD_04_API.md](./AI_REBUILD_04_API.md) - API 设计
- [AI_REBUILD_09_SECURITY.md](./AI_REBUILD_09_SECURITY.md) - 安全机制
- [AI_REBUILD_10_DEPLOYMENT.md](./AI_REBUILD_10_DEPLOYMENT.md) - 部署指南
