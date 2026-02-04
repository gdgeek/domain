---
inclusion: fileMatch
fileMatchPattern: ".github/workflows/**/*.yml"
---

# CI/CD 工作流规范

GitHub Actions 三阶段流水线，部署到腾讯云容器服务。

---

## 三阶段流水线：测试 → 构建 → 发布

### 第一阶段：测试

#### Python
```yaml
test:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    - name: Install
      run: pip install flake8 pytest pytest-cov -r requirements.txt
    - name: Lint
      run: flake8 app/ tests/ --max-line-length=120 --ignore=E501,W503
    - name: Test
      env:
        FLASK_ENV: testing
      run: pytest tests/ -v --cov=app --cov-report=xml
```

#### Node.js
```yaml
test:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-node@v4
      with:
        node-version: '20'
        cache: 'npm'
    - run: npm ci
    - run: npm run lint
    - run: npm test -- --coverage
```

#### PHP
```yaml
test:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: shivammathur/setup-php@v2
      with:
        php-version: '8.2'
        extensions: mbstring, xml, ctype, json
        coverage: xdebug
    - run: composer install --no-interaction
    - run: vendor/bin/phpcs --standard=PSR12 app/
    - run: vendor/bin/phpunit --coverage-text
```

---

### 第二阶段：构建

```yaml
build:
  name: 构建
  needs: test
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    
    - uses: docker/setup-buildx-action@v3
    
    - uses: docker/login-action@v3
      with:
        registry: ${{ env.TCR_REGISTRY }}
        username: ${{ secrets.TENCENT_DOCKER_USERNAME }}
        password: ${{ secrets.TENCENT_DOCKER_PASSWORD }}
    
    - name: Extract version
      id: version
      run: |
        if [[ "${{ github.ref }}" == refs/tags/v* ]]; then
          echo "version=${GITHUB_REF#refs/tags/v}" >> $GITHUB_OUTPUT
        else
          echo "version=${{ github.event.inputs.tag || 'latest' }}" >> $GITHUB_OUTPUT
        fi
    
    - uses: docker/build-push-action@v5
      with:
        context: .
        push: true
        tags: |
          ${{ env.TCR_REGISTRY }}/${{ env.TCR_NAMESPACE }}/${{ env.IMAGE_NAME }}:${{ steps.version.outputs.version }}
          ${{ env.TCR_REGISTRY }}/${{ env.TCR_NAMESPACE }}/${{ env.IMAGE_NAME }}:latest
        cache-from: type=gha
        cache-to: type=gha,mode=max
```

---

### 第三阶段：发布

```yaml
deploy:
  name: 部署
  needs: build
  runs-on: ubuntu-latest
  steps:
    - name: Trigger Portainer Webhook
      run: curl -X POST "${{ secrets.PORTAINER_WEBHOOK_URL }}"
    
    - name: Summary
      run: |
        echo "## 🚀 部署完成" >> $GITHUB_STEP_SUMMARY
        echo "镜像: \`${{ env.TCR_REGISTRY }}/${{ env.TCR_NAMESPACE }}/${{ env.IMAGE_NAME }}:latest\`" >> $GITHUB_STEP_SUMMARY
```

---

## 腾讯云 TCR 配置

```yaml
env:
  TCR_REGISTRY: hkccr.ccs.tencentyun.com  # 香港
  TCR_NAMESPACE: your-namespace
  IMAGE_NAME: your-image
```

区域 Registry：
| 区域 | Registry |
|------|----------|
| 香港 | `hkccr.ccs.tencentyun.com` |
| 广州 | `ccr.ccs.tencentyun.com` |
| 上海 | `shccr.ccs.tencentyun.com` |
| 北京 | `bjccr.ccs.tencentyun.com` |

---

## 必需 GitHub Secrets

| Secret | 说明 |
|--------|------|
| `TENCENT_DOCKER_USERNAME` | 腾讯云容器服务用户名 |
| `TENCENT_DOCKER_PASSWORD` | 腾讯云容器服务密码 |
| `PORTAINER_WEBHOOK_URL` | Portainer 部署 Webhook |

---

## 触发条件

```yaml
# CI 测试
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

# 正式发布
on:
  push:
    tags: ['v*']
  workflow_dispatch:
    inputs:
      tag:
        description: '镜像标签'
        default: 'latest'
```

---

## 完整模板

```yaml
name: Deploy

on:
  push:
    tags: ['v*']
  workflow_dispatch:
    inputs:
      tag:
        description: '镜像标签'
        default: 'latest'

env:
  TCR_REGISTRY: hkccr.ccs.tencentyun.com
  TCR_NAMESPACE: your-namespace
  IMAGE_NAME: your-image

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      # 根据语言选择测试步骤

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: ${{ env.TCR_REGISTRY }}
          username: ${{ secrets.TENCENT_DOCKER_USERNAME }}
          password: ${{ secrets.TENCENT_DOCKER_PASSWORD }}
      - uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ env.TCR_REGISTRY }}/${{ env.TCR_NAMESPACE }}/${{ env.IMAGE_NAME }}:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - run: curl -X POST "${{ secrets.PORTAINER_WEBHOOK_URL }}"
```
