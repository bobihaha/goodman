# 阿里云部署说明

本项目当前推荐采用单机 Docker 部署：

- 前端：独立构建静态资源，由 Nginx 提供服务
- 后端：FastAPI 容器单独运行
- 数据库：ECS 本机 Docker 自建 MySQL
- 缓存：ECS 本机 Docker 自建 Redis

## 推荐拓扑

### 当前推荐方案

- 1 台 ECS
  - `nginx`
  - `frontend`
  - `backend`
  - `mysql`
  - `redis`

优点：

- 成本最低
- 结构简单，适合项目早期
- 部署和回滚都比较直接

## 服务器建议

- ECS: 8C16G 推荐，系统盘 SSD 80GB+
- 操作系统：Alibaba Cloud Linux 3 / Ubuntu 22.04 LTS
- 安全组：
  - `80/tcp`
  - `443/tcp`
  - `22/tcp` 仅办公网开放
  - `3306/tcp` 不对公网开放
  - `6379/tcp` 不对公网开放

## 资源建议

针对你现在的 `8核16G / 80GB` ECS，建议这样控制资源：

- `mysql`
  - CPU 上限：`4`
  - 内存上限：`8G`
  - `innodb_buffer_pool_size=4G`
- `backend`
  - CPU 上限：`2`
  - 内存上限：`3G`
  - `BACKEND_WORKERS=1`
- `redis`
  - CPU 上限：`1`
  - 内存上限：`1G`
  - `maxmemory=768MB`
- `nginx`
  - CPU 上限：`0.5`
  - 内存上限：`256MB`
- `frontend`
  - CPU 上限：`0.5`
  - 内存上限：`256MB`

这样总共给业务容器预留大约 `12.5G` 内存和 `8` 核上限，仍然给系统、Docker、自身缓存和临时构建保留余量，能明显降低 MySQL 抢内存和整机 OOM 的风险。

## 首次部署

### 1. 准备环境变量

复制模板：

```bash
cp .env.production.example .env.production
```

重点修改：

- `SECRET_KEY`
- `ALLOW_ORIGINS`

默认模板已经是单机 ECS 自建 MySQL/Redis，并带了 8C16G 的默认资源参数：

- `DB_HOST=mysql`
- `REDIS_URL=redis://redis:6379/0`
- `BACKEND_WORKERS=1`
- `MYSQL_INNODB_BUFFER_POOL_SIZE=4G`
- `REDIS_MAXMEMORY=768mb`

### 2. 构建并启动

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

### 3. 健康检查

```bash
curl http://127.0.0.1/health
```

返回 `{"status":"ok",...}` 代表后端启动成功。

## 发布顺序

1. 备份数据库
2. 执行数据库迁移
3. 发布后端
4. 验证 `/health`
5. 发布前端
6. 验证登录、卡片查询、库存、流量池、同步任务

## 备份命令

MySQL 备份：

```bash
bash deploy/scripts/backup_mysql.sh
```

Redis 备份：

```bash
bash deploy/scripts/backup_redis.sh
```

生产恢复：

```bash
bash deploy/scripts/restore_mysql.sh ./backups/mysql/xxx.sql.gz
```

发布前检查：

```bash
bash deploy/scripts/predeploy_check.sh
```

## 当前项目的特殊注意事项

### 1. 不要只配置 `DB_URL`

当前后端配置实际依赖以下字段：

- `DB_HOST`
- `DB_PORT`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`

请不要只写 `DB_URL`，否则可能连接到错误数据库。

### 2. 后端先保持单实例

项目在应用启动时会自动加载 APScheduler 定时任务。如果同时启动多个应用实例或多个 worker，可能重复执行同步任务。

正式扩容前，建议把调度器拆成独立 worker。

### 3. MySQL 迁移必须先在预发库演练

仓库内存在多份手写 SQL 脚本，且不是所有脚本都具备幂等性。生产库禁止直接“挑脚本现跑”。

请配合 [docs/DEPLOYMENT_MIGRATION_SOP.md](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/docs/DEPLOYMENT_MIGRATION_SOP.md) 执行。

### 4. MySQL 和 Redis 不要暴露公网

这两个服务应该只在 Docker 内部网络中被应用访问。即使 ECS 开了公网 IP，也不要开放 `3306` 和 `6379` 安全组。

### 5. 单机方案的升级路径

等项目进入稳定增长阶段后，建议按顺序迁移：

1. 先把 MySQL 迁到 RDS
2. 再把 Redis 迁到云 Redis
3. 最后考虑把调度器拆为独立 worker
