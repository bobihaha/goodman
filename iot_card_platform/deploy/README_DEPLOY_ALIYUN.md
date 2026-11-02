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

### 2026-11-02 子账号关联流量池只读修复

#### 当日 15:00 追加：补量展示与首页告警入口

- 使用生产基线隔离包发布 `deploy/release_manifests/sub_user_pool_addon_alert_20261102.txt` 中 6 个文件，未包含本地首页其他未发布功能。无 SQL、环境或依赖变更。
- 子账号流量池列表和详情移除所属客户及统计口径说明；池级有效补量每池一次计入总额度，过期补量排除，沿用历史无月份补量的兼容逻辑。
- 首页告警卡和“查看全部”改为只读弹窗，默认查询未处理告警，无需停卡管理菜单；后端原有账号范围不变。
- 备份：`/home/deploy/iot_card_platform/release_backups/20261102_145908_sub_user_pool_addon_alert_20261102`，MySQL 12,861,002 字节、Redis 88 字节、原文件归档 14,477 字节。回滚恢复该归档的 6 个文件并重建 app/frontend，不恢复数据库；旧镜像保留为 `iot_card_platform:rollback-subpool-addon-20261102` 与 `iot_card_frontend:rollback-subpool-addon-20261102`。
- 验证：18 项相关测试、本地类型检查/构建、生产镜像构建及系统健康检查通过。实际账号 API 核验：浦东融媒体 3 池 27 卡，总额度 138,240 MB（135G），当前有效池级补量 0；上海翕禾 4 条未处理告警与首页统计一致，返回记录均在账号范围内。
- 公网生产静态资源配合模拟 API 的浏览器验证通过：没有停卡菜单时点击首页告警可打开列表，停留首页、不提示无权限、不显示处理按钮。该验证不是使用真实账号密码的浏览器登录验收。发布后的完整 30–60 分钟观察尚未完成。

- 北京时间 10:16 完成前后端切换。清单：`deploy/release_manifests/sub_user_pool_scope_20261102.txt`，共 8 个运行文件；发布前确认生产原文件与本次补丁基线一致，无 SQL、环境变量或依赖变更，未覆盖其他未发布模块。
- 子账号可查看本人有效卡片对应流量池；列表、详情、用量、统计及仪表盘只汇总本人卡片，不含共享池补量，保持池级写入和全池日志权限边界。前端显示统计范围并隐藏池级操作。
- 备份：`/home/deploy/iot_card_platform/release_backups/20261102_101516_sub_user_pool_scope_20261102`。MySQL 压缩备份 12,851,822 字节、Redis 88 字节、原源码归档 22,198 字节，目录 700、文件 600；MySQL/源码 gzip 完整性检查通过，Redis RDB 校验通过。
- 生产镜像构建、`check_system.sh` 通过，四个容器健康，前后端重启次数 0；MySQL/Redis 未重启。8 个源文件 SHA-256 与本地发布文件一致，两个 HTTPS 域名返回 200，HTTP 返回 301。
- 实际账号 API 验收：上海翕禾传媒科技有限公司下“浦东融媒体”返回 3 个流量池、27 张本人有效池卡；列表、详情、卡片、用量、统计、仪表盘、告警筛选和分页通过；无关池及全池日志返回业务 404，未认证返回业务 401。验证只发送 GET，短期验证凭据仅保留在容器进程内存，不写文件或输出。
- 本地相关测试 15 项、前端类型检查及构建通过。刚发布后的健康与接口验证通过；30–60 分钟完整观察及真实浏览器登录交互尚未完成，不将其记作已验收。
- 回滚：恢复此次 `files/source_files_20261102_101516.tar.gz` 的原文件，移走新增的 `app/services/sub_user_pool_service.py` 后仅重建 app/frontend；旧镜像另保留为 `iot_card_platform:rollback-subpool-20261102` 与 `iot_card_frontend:rollback-subpool-20261102`。无数据库结构变更，不恢复整库，回滚后重做健康及权限检查。


### 2026-10-30 卡片列表统计卡点击修复

- 仅发布 `frontend/src/views/cards/list/index.vue` 中“沉默期”“已停机”点击筛选修复；使用生产原文件对比后的隔离发布包，排除本地未发布的 `over_usage` 重置修改。无 SQL、环境变量或后端变更。
- 使用文件清单发布脚本的临时副本执行备份及发布，前端启动命令增加 `--no-deps`，仅重建前端，后端保持运行。
- 备份：`/home/deploy/iot_card_platform/release_backups/20261030_112116_card_status_click_20261030`，包含 MySQL、Redis 和原页面文件。
- 验证：生产 Vite 镜像构建通过，四个容器健康，`check_system.sh` 通过；两个 HTTPS 域名返回 200，HTTP 返回 301，公网页面 JS/CSS 已包含修复。筛选逻辑及 Vue 编译在本地通过；本地全量类型检查未完成，验收浏览器无登录会话，登录后的点击验收及 30–60 分钟观察尚未完成。
- 回滚：从上述备份的 `files/source_files_20261030_112116.tar.gz` 恢复原页面文件，执行 `docker compose up -d --no-deps --build frontend`，随后执行健康检查；本次无需恢复数据库。

#### 同日追加：已激活统计卡

- 追加发布“已激活”统计卡，复用相同的状态筛选、分页重置及批量查询退出逻辑；发布范围仍仅为上述页面，未包含本地其他修改。
- 备份：`/home/deploy/iot_card_platform/release_backups/20261030_112858_card_activated_click_20261030`，包含 MySQL、Redis 和追加发布前的页面。
- 验证：三个状态入口的针对性逻辑验证及 Vue 脚本/模板编译通过；生产镜像构建、`check_system.sh` 和公网 HTTPS 检查通过，四个容器健康，公网 JS 确认包含三个状态点击绑定。验收浏览器无登录会话，实际登录点击及长时间观察尚未完成；本地完整 Vite 构建被 esbuild 依赖异常阻塞。
- 追加发布回滚：从此次备份的 `files/source_files_20261030_112858.tar.gz` 恢复页面并仅重建前端，可保留首次发布的沉默期、已停机修复；完全回滚两次修改则使用首次备份。

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

发布范围隔离规则：

- 未定稿或未确认上线的模块不得随生产修复一起发布，例如官网内容、官网图片、官网路由、运营中心等仍在开发中的页面。
- 本地工作区存在大量未提交改动时，必须先冻结本次发布文件清单，只同步本次目标相关文件，禁止整包覆盖生产目录。
- 生产机不是完整 Git 工作树，可能存在已热发布但本地当前分支未包含的文件；覆盖任何线上文件前，先备份并对比生产原文件，确认不会回退线上已有功能。
- 小修复优先使用“干净基线 + 本次补丁”的临时发布目录或最小文件包验证，确认构建通过后再同步到生产。
- 发布官网相关内容前，必须得到“官网已定稿并允许上线”的明确确认。

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

脚本会自动识别当前生产的 `.env/docker-compose.yml` 与标准部署的
`.env.production/docker-compose.prod.yml`，并在可用空间不足 10GB 时阻止构建。
如确有不同容量要求，可显式设置 `MIN_DEPLOY_FREE_GB`；该检查只拦截发布，
不会自动清理 Docker 镜像、数据卷或发布备份。

文件清单发布脚本会在服务重建后等待容器进入 `healthy`，再运行系统检查和日志扫描，
避免容器仍处于启动阶段时产生误报。

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
