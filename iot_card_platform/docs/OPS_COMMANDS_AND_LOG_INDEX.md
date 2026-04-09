# 运维命令速查与日志关键词索引

这份文档面向上线、巡检、回滚和排障实操，尽量使用当前仓库里已经存在的脚本、容器名和健康检查口径。

适合场景：

- 发布前检查
- 发布后健康验证
- 容器异常排查
- 后端日志排查
- MySQL / Redis 基础确认
- 同步、回调、停复机类问题快速定位

建议配合以下文档一起看：

- [稳定上线操作手册](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/docs/STABLE_RELEASE_RUNBOOK.md)
- [常见故障定位路径](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/docs/TROUBLESHOOTING_GUIDE.md)
- [数据库迁移规范](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/docs/DATABASE_MIGRATION_GUIDE.md)

## 1. 当前生产容器约定

基于 `docker-compose.prod.yml`，当前核心容器名如下：

- `iot_nginx`
- `iot_frontend`
- `iot_backend`
- `iot_mysql`
- `iot_redis`

排障时先确认容器名，不要混用 `service name` 和 `container_name`。

## 2. 发布前速查

### 2.1 发布前基础检查

```bash
bash deploy/scripts/predeploy_check.sh
```

用途：

- 检查 `.env.production`
- 检查 `docker-compose.prod.yml`
- 检查 Docker / Docker Compose
- 检查编排配置是否可解析
- 查看磁盘空间

### 2.2 本地后端测试

```bash
pytest tests
```

### 2.3 本地前端构建

```bash
cd frontend
npm run build
```

### 2.4 生产镜像构建

```bash
docker compose -f docker-compose.prod.yml build
```

## 3. 发布与回滚速查

### 3.1 启动或更新生产容器

```bash
docker compose -f docker-compose.prod.yml up -d
```

如果本次有代码改动，通常先执行：

```bash
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

### 3.2 数据库备份

```bash
bash deploy/scripts/backup_mysql.sh
```

### 3.3 数据库恢复

```bash
bash deploy/scripts/restore_mysql.sh ./backups/mysql/xxx.sql.gz
```

### 3.4 执行 SQL 迁移

```bash
python scripts/run_migration.py app/db/migrations/xxx.sql
```

注意：

- 执行前先确认 `.env` 指向的数据库环境
- 生产环境先备份
- 不要临场执行未评审 SQL

## 4. 健康检查速查

### 4.1 一键健康检查

```bash
bash deploy/scripts/health_check.sh
```

它会检查：

- 容器状态
- 后端 `/health`
- Nginx 首页
- MySQL ping
- Redis ping
- 最近 50 行后端日志

### 4.2 手工健康检查

```bash
docker compose -f docker-compose.prod.yml ps
curl -fsS http://127.0.0.1/health
curl -fsS http://127.0.0.1/
docker exec iot_mysql sh -lc 'exec mysqladmin -uroot -p"$MYSQL_ROOT_PASSWORD" ping'
docker exec iot_redis redis-cli ping
```

### 4.3 查看容器状态

```bash
docker compose -f docker-compose.prod.yml ps
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```

## 5. 日志查看速查

### 5.1 后端容器日志

```bash
docker logs iot_backend --tail 100
docker logs -f iot_backend
```

### 5.2 Nginx 日志

```bash
docker logs iot_nginx --tail 100
docker logs -f iot_nginx
```

### 5.3 MySQL / Redis 日志

```bash
docker logs iot_mysql --tail 100
docker logs iot_redis --tail 100
```

### 5.4 宿主机后端文件日志

项目将后端日志挂载到：

- `logs/app.log`

常用查看方式：

```bash
tail -n 100 logs/app.log
tail -f logs/app.log
```

## 6. 容器内排查速查

### 6.1 进入后端容器

```bash
docker exec -it iot_backend sh
```

### 6.2 进入 MySQL 容器

```bash
docker exec -it iot_mysql sh
```

### 6.3 进入 Redis 容器

```bash
docker exec -it iot_redis sh
```

### 6.4 检查后端环境变量是否加载

```bash
docker exec iot_backend sh -lc 'env | sort | grep -E "APP_|DB_|REDIS_|SECRET_|ALLOW_ORIGINS"'
```

### 6.5 检查 MySQL / Redis 连接

```bash
docker exec iot_mysql sh -lc 'exec mysqladmin -uroot -p"$MYSQL_ROOT_PASSWORD" ping'
docker exec iot_redis redis-cli ping
```

## 7. 数据库排查速查

### 7.1 连接 MySQL

```bash
docker exec -it iot_mysql sh -lc 'exec mysql -uroot -p"$MYSQL_ROOT_PASSWORD" "$MYSQL_DATABASE"'
```

### 7.2 看表是否存在

```sql
SHOW TABLES;
SHOW TABLES LIKE 'iot_cards';
SHOW TABLES LIKE 'supplier_suspend_operations';
```

### 7.3 看字段是否存在

```sql
SHOW COLUMNS FROM iot_cards;
SHOW COLUMNS FROM sys_users;
SHOW COLUMNS FROM traffic_pools;
```

### 7.4 看最近记录

```sql
SELECT id, iccid, status, suspend_type, data_sync_at
FROM iot_cards
ORDER BY id DESC
LIMIT 20;

SELECT id, callback_no, callback_status, account_status, completed_at
FROM supplier_suspend_operations
ORDER BY id DESC
LIMIT 20;

SELECT id, target_type, target_name, alert_level, handled
FROM alert_logs
ORDER BY id DESC
LIMIT 20;
```

## 8. 关键链路日志关键词索引

下面这些关键词适合用来快速筛日志。

### 8.1 登录 / 权限 / 菜单

建议关键词：

- `登录`
- `login`
- `认证`
- `Auth`
- `权限`
- `permission`
- `菜单`
- `menu`
- `401`
- `403`

示例：

```bash
grep -Ei "登录|login|认证|permission|菜单|401|403" logs/app.log | tail -n 50
docker logs iot_backend 2>&1 | grep -Ei "登录|login|permission|401|403" | tail -n 50
```

### 8.2 同步任务 / 调度器

建议关键词：

- `定时任务`
- `同步`
- `sync`
- `已加载同步任务`
- `定时同步完成`
- `定时同步失败`

示例：

```bash
grep -Ei "定时任务|同步|sync|已加载同步任务|定时同步完成|定时同步失败" logs/app.log | tail -n 100
docker logs iot_backend 2>&1 | grep -Ei "定时任务|同步|sync" | tail -n 100
```

### 8.3 停复机 / 回调

建议关键词：

- `停卡`
- `复机`
- `suspend`
- `resume`
- `callback`
- `回调`
- `callback_no`
- `UPIOT`

示例：

```bash
grep -Ei "停卡|复机|suspend|resume|callback|回调|UPIOT" logs/app.log | tail -n 100
docker logs iot_backend 2>&1 | grep -Ei "停卡|复机|callback|UPIOT" | tail -n 100
```

### 8.4 流量池 / 超限 / 告警

建议关键词：

- `流量池`
- `pool`
- `超限`
- `告警`
- `alert`
- `threshold`

示例：

```bash
grep -Ei "流量池|pool|超限|告警|alert|threshold" logs/app.log | tail -n 100
docker logs iot_backend 2>&1 | grep -Ei "流量池|pool|超限|告警|alert" | tail -n 100
```

### 8.5 出入库 / 回收

建议关键词：

- `入库`
- `出库`
- `库存`
- `回收`
- `stock`
- `recycle`

示例：

```bash
grep -Ei "入库|出库|库存|回收|stock|recycle" logs/app.log | tail -n 100
docker logs iot_backend 2>&1 | grep -Ei "入库|出库|库存|回收|stock|recycle" | tail -n 100
```

## 9. 常见排障命令组合

### 9.1 发布后快速确认服务全活着

```bash
docker compose -f docker-compose.prod.yml ps
bash deploy/scripts/health_check.sh
```

### 9.2 后端接口 500，但不确定原因

```bash
docker logs iot_backend --tail 200
tail -n 200 logs/app.log
```

### 9.3 怀疑是数据库字段没迁移

```bash
docker exec -it iot_mysql sh -lc 'exec mysql -uroot -p"$MYSQL_ROOT_PASSWORD" "$MYSQL_DATABASE" -e "SHOW COLUMNS FROM iot_cards"'
```

### 9.4 怀疑同步任务没跑

```bash
grep -Ei "已加载同步任务|定时同步完成|定时同步失败|sync" logs/app.log | tail -n 100
docker logs iot_backend 2>&1 | grep -Ei "已加载同步任务|定时同步完成|定时同步失败|sync" | tail -n 100
```

### 9.5 怀疑回调到了但状态没更新

```bash
grep -Ei "callback|回调|UPIOT|callback_no" logs/app.log | tail -n 100
docker exec -it iot_mysql sh -lc 'exec mysql -uroot -p"$MYSQL_ROOT_PASSWORD" "$MYSQL_DATABASE" -e "SELECT id, callback_no, callback_status, account_status, completed_at FROM supplier_suspend_operations ORDER BY id DESC LIMIT 20;"'
```

## 10. 使用建议

### 上线时建议固定顺序

1. 先跑 `predeploy_check.sh`
2. 再备份数据库
3. 如有 SQL，先执行迁移
4. 再构建和启动容器
5. 再跑 `health_check.sh`
6. 最后结合日志关键词做 30 到 60 分钟观察

### 排障时建议固定顺序

1. 先看容器状态
2. 再看健康检查
3. 再看后端日志
4. 再按业务关键词筛日志
5. 最后再进数据库核对记录
