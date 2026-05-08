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

## 当前生产连接信息

当前项目生产环境的 SSH 连接方式如下：

```bash
ssh -i /Users/renhui/Desktop/aliyun.pem -p 22222 deploy@47.100.81.73
```

说明：

- 发布、排障、健康检查前，默认先通过以上命令登录生产机
- 若后续服务器地址、用户名或密钥位置变更，需要同步更新本文档

## 当前生产环境实际落地信息

当前线上项目不是按 `docker-compose.prod.yml` 运行，而是按以下方式落地：

- 服务器：`47.100.81.73`
- SSH 用户：`deploy`
- SSH 端口：`22222`（密钥登录，密码登录禁用）
- 项目目录：`/home/deploy/iot_card_platform`
- Compose 文件：`docker-compose.yml`
- 环境文件：`.env`
- 健康检查脚本：`./check_system.sh`
- HTTPS 域名：`zerodaai.com` / `www.zerodaai.com`
- HTTPS 证书目录：`/home/deploy/iot_card_platform/certs`

登录后建议先执行：

```bash
cd /home/deploy/iot_card_platform
./check_system.sh
```

补充说明：

- `./check_system.sh` 比单看容器状态更可靠，适合作为发布后的首选验收命令
- 前端重建时可能会连带触发后端容器重建，发布后务必再次执行健康检查
- 当前线上 HTTP `/` 会 301 跳转 HTTPS，前端健康检查应使用 `http://127.0.0.1/healthz`
- 发布前备份文件会包含敏感数据，`release_backups` 目录建议权限为 `700`，备份文件建议权限为 `600`

## 服务器建议

- ECS: 8C16G 推荐，系统盘 SSD 80GB+
- 操作系统：Alibaba Cloud Linux 3 / Ubuntu 22.04 LTS
- 安全组：
  - `80/tcp`
  - `443/tcp`
  - `22222/tcp` 仅办公网开放，迁移完成后关闭公网 `22/tcp`
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

## 当前线上实际发布流程

以下流程是目前已经在线上验证过的实际做法，后续发版默认按此执行。

### 1. 登录并进入项目目录

```bash
ssh -i /Users/renhui/Desktop/aliyun.pem -p 22222 deploy@47.100.81.73
cd /home/deploy/iot_card_platform
```

### 2. 发布前备份

建议在项目目录下新建一次带时间戳的备份目录，至少保留：

- 数据库备份
- Redis 备份
- 本次发布涉及文件的代码快照

线上备份目录约定：

```bash
/home/deploy/iot_card_platform/release_backups/<timestamp>_<release_name>
```

如果生产机缺少仓库里的 `deploy/scripts/backup_mysql.sh` / `backup_redis.sh`，可以直接用容器备份：

```bash
TS=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="release_backups/${TS}_<release_name>"
mkdir -p "$BACKUP_DIR/mysql" "$BACKUP_DIR/redis"

docker exec iot_mysql sh -lc 'exec mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" --single-transaction --routines --triggers --events "$MYSQL_DATABASE"' \
  | gzip > "$BACKUP_DIR/mysql/iot_card_platform_${TS}.sql.gz"

docker exec iot_redis redis-cli BGSAVE >/dev/null
sleep 3
docker cp iot_redis:/data/dump.rdb "$BACKUP_DIR/redis/dump_${TS}.rdb"

chmod 700 release_backups "$BACKUP_DIR" "$BACKUP_DIR/mysql" "$BACKUP_DIR/redis"
chmod 600 "$BACKUP_DIR"/mysql/* "$BACKUP_DIR"/redis/*
```

### 3. 同步代码

推荐从本地将本次改动文件打包后同步到生产机，避免把无关文件一并覆盖：

```bash
tar czf - <changed_files...> | \
ssh -i /Users/renhui/Desktop/aliyun.pem -p 22222 deploy@47.100.81.73 \
  'bash -lc "cd /home/deploy/iot_card_platform && tar xzf -"'
```

### 4. 按改动范围重建容器

只发布后端：

```bash
docker compose -f docker-compose.yml up -d --build app
```

只发布前端：

```bash
docker compose -f docker-compose.yml up -d --build frontend
```

前后端一起发布：

```bash
docker compose -f docker-compose.yml up -d --build app frontend
```

后端镜像构建说明：

- 后端 `Dockerfile` 使用阿里云 PyPI 镜像源，并设置较长超时和重试，避免生产机直连 PyPI 导致构建失败。
- 如构建仍失败，不要默认把热补丁作为最终发布结果；应先确认旧容器是否仍健康，再修复构建问题并补一次标准 `docker compose ... --build`。
- 如确需临时热补丁，必须先备份容器内原文件，并在热补丁后尽快补标准镜像构建。

### 5. 发布后检查

```bash
./check_system.sh
curl http://127.0.0.1/health
curl -I http://127.0.0.1
curl -I http://zerodaai.com/
curl -I https://zerodaai.com/
docker compose -f docker-compose.yml ps
```

验收重点：

- `iot_card_app`、`iot_card_frontend`、`iot_mysql`、`iot_redis` 状态正常
- 后端 `/health` 返回 `{"status":"ok",...}`
- `http://zerodaai.com/` 返回 `301` 并跳转到 HTTPS
- `https://zerodaai.com/` 和 `https://www.zerodaai.com/` 返回 `HTTP 200`
- 证书 SAN 覆盖 `zerodaai.com` 和 `www.zerodaai.com`
- 如本次涉及导出、停复机、同步任务，需要补做对应业务验收

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

## 最近线上变更的运维注意点

### 1. 卡片列表导出现在由后端直接生成真实 XLSX

- 接口：`/api/v1/cards/export`
- 如果导出的 Excel 无法打开，优先检查后端返回的是否还是标准二进制文件，而不是 JSON
- 前端现在按 Blob 下载，后端负责产出真正的 `.xlsx`

### 2. 历史用量导出按月份展开列

- 例如选择 `2026-02` 到 `2026-04`，导出表头应分别出现 `2026-02用量(GB)`、`2026-03用量(GB)`、`2026-04用量(GB)`
- 若某月用量异常为 `0`，优先检查该月快照是否存在，以及月范围是否按自然月起止处理

### 3. 超级管理员手动停卡后，普通用户不可复机

- 该规则已在后端生效
- 前端卡片列表、卡片详情、流量池详情、批量复机弹窗均已补提示
- 排障时如果普通用户反馈“明明是停机卡但不能复机”，先看最近一次手动停卡日志的操作人是否为超级管理员
