# 线上回撤 SOP

适用当前项目的生产环境快速回撤流程。

适用前提：

- 服务器：`47.100.81.73`
- 项目目录：`/home/deploy/iot_card_platform`
- 发布方式：覆盖代码文件后执行 `docker compose up -d --build ...`
- 主要容器：
  - `iot_card_app`
  - `iot_card_frontend`
  - `iot_mysql`
  - `iot_redis`


## 1. 回撤分级

按风险分两类处理：

### A 类：仅代码问题，无 SQL 变更

特征：

- 页面报错
- 接口逻辑异常
- 业务行为不符合预期
- 数据库结构没有变化

处理原则：

- 优先回撤代码
- 不恢复数据库
- 通过恢复备份文件并重建容器完成回撤


### B 类：代码 + SQL 变更

特征：

- 发布同时执行过 SQL
- 数据库字段、索引、表结构发生变化
- 回代码后问题仍未恢复

处理原则：

- 先回代码
- 再判断是否需要数据库恢复
- 除非明确确认，否则不要直接整库回滚


## 2. 发布前必须准备

每次正式发布前，至少保留下面三类信息：

1. 文件备份目录
2. 数据库备份文件
3. 本次变更清单

建议记录模板：

```text
发布时间：
发布内容：
影响范围：后端 / 前端 / SQL
文件备份目录：
数据库备份文件：
新增文件：
回撤命令：
验证命令：
```


## 3. A 类回撤：仅代码问题

### Step 1：登录服务器

```bash
ssh -i /Users/renhui/Desktop/aliyun.pem -p 22222 deploy@47.100.81.73
```


### Step 2：进入项目目录

```bash
cd /home/deploy/iot_card_platform
```


### Step 3：确认本次备份目录

示例：

```bash
ls -la /home/deploy/release_backups/diagnostics_20260324_192356
```


### Step 4：恢复被改动的文件

按本次发布实际改动恢复。

示例：

```bash
cp /home/deploy/release_backups/diagnostics_20260324_192356/iot_card.py.bak app/api/v1/iot_card.py
cp /home/deploy/release_backups/diagnostics_20260324_192356/supplier_api.py.bak app/clients/supplier_api.py
cp /home/deploy/release_backups/diagnostics_20260324_192356/upiot_client.py.bak app/clients/upiot_client.py
cp /home/deploy/release_backups/diagnostics_20260324_192356/iot_card_service.py.bak app/services/iot_card_service.py
cp /home/deploy/release_backups/diagnostics_20260324_192356/card.ts.bak frontend/src/api/modules/card.ts
cp /home/deploy/release_backups/diagnostics_20260324_192356/card.d.ts.bak frontend/src/types/card.d.ts
cp /home/deploy/release_backups/diagnostics_20260324_192356/index.vue.bak frontend/src/views/cards/list/index.vue
```


### Step 5：删除本次新增文件

如果本次发布新增了文件，回撤时需要手工删除。

示例：

```bash
rm -f frontend/src/views/cards/list/components/CardDiagnosticsDialog.vue
```


### Step 6：按影响范围重建容器

只回后端：

```bash
docker compose up -d --build app
```

只回前端：

```bash
docker compose up -d --build frontend
```

前后端都回：

```bash
docker compose up -d --build app frontend
```


### Step 7：检查容器状态

```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
```

预期：

- `iot_card_app` 为 `healthy`
- `iot_card_frontend` 为 `healthy`


### Step 8：检查日志

```bash
docker logs --tail 100 iot_card_app
docker logs --tail 100 iot_card_frontend
```


### Step 9：做最小业务验收

至少确认：

- 登录正常
- 卡片列表可打开
- 本次变更涉及的功能恢复正常


## 4. B 类回撤：包含 SQL 变更

### 处理原则

如果本次发布包含 SQL，不要默认执行整库恢复。

优先顺序：

1. 先回代码
2. 观察问题是否消失
3. 只有在确认无法通过回代码恢复时，才考虑恢复数据库


### 什么时候才考虑恢复数据库

只有满足下面任一情况时再考虑：

- SQL 已破坏主流程，系统无法正常运行
- 回代码后问题依旧存在
- 可以接受备份时点之后的数据丢失


### 数据库恢复前必须确认

- 是否会覆盖发布后产生的新数据
- 是否会影响其他已正常使用的功能
- 是否已通知业务方或操作方


### 恢复数据库的基本思路

备份文件示例：

```bash
/home/deploy/db_backups/xxx.sql.gz
```

恢复前建议先停止应用写入：

```bash
docker compose stop app
```

恢复命令示例：

```bash
gunzip -c /home/deploy/db_backups/xxx.sql.gz | docker exec -i iot_mysql mysql -uroot -p数据库密码 数据库名
```

恢复后再启动应用：

```bash
docker compose up -d --build app
```

注意：

- 数据库恢复风险高
- 生产恢复前必须人工确认


## 5. 这次诊断功能发布的回撤示例

本次相关备份：

- 文件备份目录：`/home/deploy/release_backups/diagnostics_20260324_192356`
- 数据库备份文件：`/home/deploy/db_backups/iot_card_diag_20260324_192356.sql.gz`


### 回撤整次诊断功能发布

```bash
cd /home/deploy/iot_card_platform

cp /home/deploy/release_backups/diagnostics_20260324_192356/iot_card.py.bak app/api/v1/iot_card.py
cp /home/deploy/release_backups/diagnostics_20260324_192356/supplier_api.py.bak app/clients/supplier_api.py
cp /home/deploy/release_backups/diagnostics_20260324_192356/upiot_client.py.bak app/clients/upiot_client.py
cp /home/deploy/release_backups/diagnostics_20260324_192356/iot_card_service.py.bak app/services/iot_card_service.py
cp /home/deploy/release_backups/diagnostics_20260324_192356/card.ts.bak frontend/src/api/modules/card.ts
cp /home/deploy/release_backups/diagnostics_20260324_192356/card.d.ts.bak frontend/src/types/card.d.ts
cp /home/deploy/release_backups/diagnostics_20260324_192356/index.vue.bak frontend/src/views/cards/list/index.vue

rm -f frontend/src/views/cards/list/components/CardDiagnosticsDialog.vue

docker compose up -d --build app frontend
docker ps --format "table {{.Names}}\t{{.Status}}"
```


### 只回撤后续的 status 接口修正

如果只是回掉后面那次“诊断状态接口改为 `/status`”的小补丁：

```bash
cd /home/deploy/iot_card_platform

cp /home/deploy/release_backups/diagnostics_20260324_192356/upiot_client.py.pre_status_fix.bak app/clients/upiot_client.py

docker compose up -d --build app
docker ps --format "table {{.Names}}\t{{.Status}}"
```


## 6. 发布后建议保留时间

建议：

- 文件备份至少保留 7 天
- 数据库备份至少保留到观察期结束
- 高风险发布可保留更久


## 7. 最稳的实践

以后每次发布都建议固定执行：

1. 备份本次会修改的文件
2. 备份数据库
3. 记录新增文件
4. 记录回撤命令
5. 发布后立刻验证

一句话原则：

> 无 SQL 变更，优先通过“恢复文件 + 重建容器”快速回撤；有 SQL 变更，先回代码，再谨慎评估数据库是否需要恢复。
