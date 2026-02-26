# 物联网卡管理平台 — Docker 本地测试环境搭建方案

> 目标：Docker Compose 一键启动 Nginx + API + MySQL + Redis，本地浏览器访问 `http://localhost` 即可使用。

---

## 一、现状问题

| # | 问题 | 影响 |
|---|------|------|
| 1 | `.env.production` 设置 `DB_URL`，但 `config.py` 的 `@computed_field` 会覆盖它 | 数据库连接参数被忽略 |
| 2 | `init_database.sql` 使用 `iot_card_platform`，`docker-compose` 创建 `iot_card_db` | 表建在错误的库 / 建库失败 |
| 3 | `poetry.lock` 在 `.gitignore` 中，Dockerfile `COPY poetry.lock` 会失败 | 后端镜像构建失败 |
| 4 | 权限表、出入库表、超级登录表等 SQL 未自动加载 | 容器启动后缺表，API 报错 |
| 5 | 前端缺少 Dockerfile 和 Nginx 配置 | 无法容器化部署前端 |

---

## 二、文件变更清单

| 操作 | 文件 |
|------|------|
| 新建 | `frontend/Dockerfile` |
| 新建 | `frontend/nginx.conf` |
| 新建 | `frontend/.dockerignore` |
| 新建 | `.dockerignore` |
| 新建 | `scripts/docker-init/01_init_database.sql` |
| 新建 | `scripts/docker-init/02_create_permission_tables.sql` |
| 新建 | `scripts/docker-init/03_create_stock_tables.sql` |
| 新建 | `scripts/docker-init/04_create_super_login_tables.sql` |
| 修改 | `Dockerfile` |
| 修改 | `docker-compose.yml` |
| 修改 | `.env.production` |
| 修改 | `.gitignore`（移除 `poetry.lock`） |

---

## 三、实施步骤

### Step 1: 生成 poetry.lock + 修改 .gitignore

**操作：**

```bash
# 生成 lock 文件（Poetry 2.x 语法）
poetry lock
```

**修改 `.gitignore`：** 删除 `poetry.lock` 这一行，确保 lock 文件可以提交到仓库。

```diff
- poetry.lock
```

---

### Step 2: 修改 Dockerfile（后端）

**问题：** 当前 Dockerfile 假设 `poetry.lock` 已存在，且在容器内安装 poetry 全局包不够干净。

**修改后内容：**

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装 poetry
RUN pip install --no-cache-dir poetry \
    && poetry config virtualenvs.create false

# 先复制依赖声明，利用 Docker 缓存
COPY pyproject.toml poetry.lock ./

# 仅安装生产依赖
RUN poetry install --only main --no-root --no-interaction

# 复制项目代码
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**改动说明：**
- `poetry config virtualenvs.create false`：直接装到系统 Python，避免容器内多余虚拟环境
- CMD 不再通过 `poetry run` 启动，减少一层开销
- 如果 `poetry.lock` 不存在，构建前需先在本地执行 `poetry lock`

---

### Step 3: 创建 frontend/Dockerfile

多阶段构建：Node 编译 + Nginx 运行。

```dockerfile
# ---- 构建阶段 ----
FROM node:18-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
RUN npm run build

# ---- 运行阶段 ----
FROM nginx:1.25-alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

---

### Step 4: 创建 frontend/nginx.conf

```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Vue Router history 模式
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 反向代理
    location /api/ {
        proxy_pass http://iot_card_api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Swagger 文档代理
    location /docs {
        proxy_pass http://iot_card_api:8000;
        proxy_set_header Host $host;
    }

    location /openapi.json {
        proxy_pass http://iot_card_api:8000;
        proxy_set_header Host $host;
    }

    # 健康检查代理
    location /health {
        proxy_pass http://iot_card_api:8000;
        proxy_set_header Host $host;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff2?)$ {
        expires 7d;
        add_header Cache-Control "public, immutable";
    }
}
```

---

### Step 5: 创建 scripts/docker-init/ SQL 脚本

MySQL 官方镜像会在首次启动时自动执行 `/docker-entrypoint-initdb.d/` 目录下的 `.sql` 文件，按文件名字母序排列。

**目录结构：**

```
scripts/docker-init/
├── 01_init_database.sql
├── 02_create_permission_tables.sql
├── 03_create_stock_tables.sql
└── 04_create_super_login_tables.sql
```

**处理规则：**

| 源文件 | 目标文件 | 修改内容 |
|--------|----------|----------|
| `scripts/init_database.sql` | `01_init_database.sql` | 删除 `CREATE DATABASE` 和 `USE` 语句 |
| `scripts/create_permission_tables.sql` | `02_create_permission_tables.sql` | 删除 `USE iot_card_platform;` |
| `scripts/create_stock_tables.sql` | `03_create_stock_tables.sql` | 原文件无 `USE` 语句，直接复制 |
| `scripts/create_super_login_tables.sql` | `04_create_super_login_tables.sql` | 删除 `USE iot_card_platform;` |

**为什么要删除 `CREATE DATABASE` 和 `USE`？**
- Docker Compose 中 `MYSQL_DATABASE=iot_card_db` 会自动创建数据库
- `docker-entrypoint-initdb.d` 中的脚本默认在 `MYSQL_DATABASE` 指定的库中执行
- 保留 `USE iot_card_platform` 会导致表建到错误的数据库

---

### Step 6: 修改 .env.production

**核心改动：** 用独立字段替代 `DB_URL`，让 `config.py` 的 `@computed_field` 正确拼接连接串。

```env
# 应用配置
APP_NAME=IoT_Card_Platform_Prod
APP_ENV=production
DEBUG=False
PORT=8000

# 数据库配置（独立字段，由 config.py @computed_field 拼接为 DB_URL）
DB_HOST=mysql
DB_PORT=3306
DB_USER=iot_user
DB_PASSWORD=iot123456
DB_NAME=iot_card_db

# JWT 配置（请替换为真实随机密钥）
SECRET_KEY=<用 openssl rand -hex 32 生成>
ACCESS_TOKEN_EXPIRE_MINUTES=120
REFRESH_TOKEN_EXPIRE_DAYS=7

# Redis 配置
REDIS_URL=redis://redis:6379/0

# 跨域配置
ALLOW_ORIGINS=["http://localhost","http://localhost:80","http://localhost:3000"]
```

**生成 SECRET_KEY：**

```bash
openssl rand -hex 32
```

---

### Step 7: 修改 docker-compose.yml

```yaml
version: "3.8"

services:
  # ---- Nginx（前端 + 反向代理）----
  nginx:
    build: ./frontend
    restart: always
    ports:
      - "80:80"
    depends_on:
      iot_card_api:
        condition: service_healthy
    networks:
      - iot_network

  # ---- FastAPI 后端 ----
  iot_card_api:
    build: .
    restart: always
    env_file:
      - .env.production
    depends_on:
      mysql:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 15s
    networks:
      - iot_network

  # ---- MySQL ----
  mysql:
    image: mysql:8.0
    restart: always
    environment:
      MYSQL_ROOT_PASSWORD: root123456
      MYSQL_DATABASE: iot_card_db
      MYSQL_USER: iot_user
      MYSQL_PASSWORD: iot123456
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
      - ./scripts/docker-init:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    networks:
      - iot_network

  # ---- Redis ----
  redis:
    image: redis:7.0
    restart: always
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - iot_network

networks:
  iot_network:
    driver: bridge

volumes:
  mysql_data:
  redis_data:
```

**改动说明：**
- 新增 `nginx` 服务，构建自 `./frontend`，映射端口 80
- MySQL 挂载 `./scripts/docker-init` 到 `/docker-entrypoint-initdb.d`，首次启动自动建表
- 后端不再暴露 `8000` 端口到宿主机（通过 Nginx 代理访问）
- 所有服务加 `healthcheck`，`depends_on` 使用 `condition: service_healthy` 确保启动顺序

---

### Step 8: 创建 .dockerignore 文件

**根目录 `.dockerignore`（后端构建用）：**

```
__pycache__/
*.py[cod]
.venv/
venv/
.git/
.gitignore
frontend/
node_modules/
*.md
.env
.env.development
.env.local
logs/
.pytest_cache/
.coverage
htmlcov/
tests/
.idea/
.vscode/
```

**`frontend/.dockerignore`（前端构建用）：**

```
node_modules/
dist/
.git/
.gitignore
*.md
.env*
.vscode/
.idea/
```

---

## 四、验证流程

### 1. 构建前准备

```bash
# 生成 poetry.lock（如果不存在）
poetry lock

# 生成 SECRET_KEY
openssl rand -hex 32
# 将输出填入 .env.production 的 SECRET_KEY 字段
```

### 2. 构建并启动

```bash
# 清理旧容器和数据卷（首次可跳过）
docker-compose down -v

# 构建并启动所有服务
docker-compose up --build -d
```

### 3. 检查服务状态

```bash
# 查看所有容器状态，确认均为 healthy
docker-compose ps

# 查看日志（排查问题时使用）
docker-compose logs -f iot_card_api   # 后端日志
docker-compose logs -f mysql          # 数据库日志
docker-compose logs -f nginx          # Nginx 日志
```

### 4. 功能验证

| 验证项 | URL | 预期结果 |
|--------|-----|----------|
| 前端页面 | http://localhost | 显示登录页 |
| API 文档 | http://localhost/docs | Swagger UI |
| 健康检查 | http://localhost/health | `{"status": "ok"}` |
| API 接口 | http://localhost/api/... | 正常返回数据 |

### 5. 常见问题排查

```bash
# MySQL 初始化失败 → 清除数据卷重建
docker-compose down -v && docker-compose up --build -d

# 后端连不上 MySQL → 检查 healthcheck 是否通过
docker-compose ps

# 前端白屏 → 检查 Nginx 日志
docker-compose logs nginx
```

---

## 五、架构示意

```
                    ┌──────────────┐
  浏览器 ──:80──▶  │    Nginx     │
                    │  (前端静态)   │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │ /api/      │ /docs      │ /health
              ▼            ▼            ▼
        ┌─────────────────────────────────┐
        │        iot_card_api (FastAPI)    │
        │            :8000                │
        └──────┬──────────────┬───────────┘
               │              │
               ▼              ▼
        ┌────────────┐  ┌──────────┐
        │  MySQL 8.0 │  │ Redis 7.0│
        │   :3306    │  │  :6379   │
        └────────────┘  └──────────┘
```

---

## 六、注意事项

1. **首次启动**：MySQL 初始化 SQL 仅在数据卷为空时执行。如需重新初始化，必须 `docker-compose down -v` 清除数据卷。
2. **数据库名统一**：Docker 环境统一使用 `iot_card_db`，本地开发环境保持 `iot_card_platform` 不变。
3. **SECRET_KEY**：`.env.production` 中的密钥必须替换为真实随机值，不要使用示例值。
4. **端口冲突**：确保本机 80、3306、6379 端口未被占用，否则修改 `docker-compose.yml` 中的端口映射。
5. **前端 API 地址**：前端 Vite 构建时的 `VITE_API_BASE_URL` 应设为 `/api`（相对路径），由 Nginx 代理到后端。
