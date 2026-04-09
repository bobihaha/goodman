# 系统巡检脚本说明

这份文档说明当前项目的日常巡检脚本怎么用、看什么、什么情况下需要继续排查。

适用场景：

- 日常巡检
- 发布后核验
- 线上性能观察
- 容器异常后的第一轮排查

建议配合以下内容一起使用：

- [运维命令速查与日志关键词索引](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/docs/OPS_COMMANDS_AND_LOG_INDEX.md)
- [常见故障定位路径](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/docs/TROUBLESHOOTING_GUIDE.md)

## 1. 脚本位置

仓库脚本：

- [check_system.sh](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/deploy/scripts/check_system.sh)

当前生产服务器脚本：

- `/home/deploy/iot_card_platform/check_system.sh`

## 2. 使用方式

### 2.1 在仓库环境执行

```bash
bash deploy/scripts/check_system.sh
```

### 2.2 在当前生产服务器执行

```bash
cd /home/deploy/iot_card_platform
bash ./check_system.sh
```

说明：

- 当前服务器目录存在 `noexec` 限制，建议固定使用 `bash ./check_system.sh`
- 不要依赖 `./check_system.sh`

## 3. 脚本会检查什么

当前脚本会依次输出：

1. 容器状态
2. 容器实时 CPU / 内存 / 网络
3. 后端 `/health`
4. 前端首页响应与响应耗时
5. MySQL 连接数、慢查询、关键参数
6. Redis `maxmemory`
7. 最近 50 行后端日志

脚本会自动识别：

- `docker-compose.prod.yml`
- 或 `docker-compose.yml`

同时也会自动识别不同部署下的服务名差异：

- `backend` 或 `app`
- `nginx` 或 `frontend`

## 4. 当前生产环境对应关系

截至 2026-04-09，当前生产服务器实际使用的是：

- Compose 文件：`/home/deploy/iot_card_platform/docker-compose.yml`
- 后端服务名：`app`
- 前端服务名：`frontend`
- MySQL 服务名：`mysql`
- Redis 服务名：`redis`

当前线上没有单独 `nginx` 服务，前端容器本身就是 Nginx 静态服务。

## 5. 当前资源目标值

当前生产机器为 `8C / 16G`，目标资源配额如下：

- MySQL：`4C / 8G`
- Backend：`2C / 3G`
- Redis：`1C / 1G`
- Frontend：`0.5C / 256M`

当前关键运行参数：

- `BACKEND_WORKERS=1`
- `MYSQL_MAX_CONNECTIONS=300`
- `MYSQL_INNODB_BUFFER_POOL_SIZE=4G`
- `REDIS_MAXMEMORY=768mb`

## 6. 正常结果怎么看

### 6.1 容器状态

正常标准：

- `mysql`、`redis`、`backend/app`、`frontend/nginx` 都是 `Up`
- 最好都带 `healthy`

如果出现：

- `Restarting`
- `Exited`
- `unhealthy`

优先去看最后一段后端日志和对应容器日志。

### 6.2 容器资源

重点看：

- `MEM USAGE / LIMIT`
- `CPU %`

当前这套配置下，日常低压状态通常应明显低于上限。

建议关注阈值：

- MySQL 内存长期超过 `6G`
- Backend 内存长期超过 `2G`
- Redis 内存长期逼近 `1G`
- 任一核心容器 CPU 长时间高于 `70%`

### 6.3 后端健康

正常返回示例：

```json
{"status":"ok","service":"IoT Card Platform"}
```

如果这里失败：

- 先看后端容器状态
- 再看后端日志
- 再看数据库和 Redis 是否 healthy

### 6.4 前端健康

脚本会输出：

- 首页返回码
- 首页响应耗时
- 首页 HTML 片段

正常标准：

- `code=200`
- 耗时通常很低
- 返回 HTML 头部内容

### 6.5 MySQL 状态

脚本当前会打印：

- `Threads_connected`
- `Threads_running`
- `Max_used_connections`
- `Slow_queries`
- `max_connections`
- `innodb_buffer_pool_size`

建议判断方式：

- `Max_used_connections` 明显低于 `300`，说明连接余量还大
- `Slow_queries` 如果持续增加，要排查慢 SQL
- `Threads_running` 长期偏高，说明当前并发压力上来了

### 6.6 Redis 状态

脚本会打印：

- `maxmemory`

当前目标值应为：

```text
maxmemory:805306368
```

这就是 `768mb`。

### 6.7 最近后端日志

这部分主要用来快速扫以下问题：

- Traceback
- timeout
- 数据库连接异常
- 供应商接口异常
- 回调异常
- 调度任务异常

## 7. 建议的日常使用方式

### 7.1 日常巡检

每天或每次发版后执行一次：

```bash
cd /home/deploy/iot_card_platform
bash ./check_system.sh
```

### 7.2 用户反馈系统慢

先执行脚本，看三件事：

1. 容器是否 healthy
2. MySQL 连接数和慢查询是否异常
3. 哪个容器的 CPU / 内存明显升高

### 7.3 发布后验证

建议顺序：

1. 发布完成
2. 跑 `bash ./check_system.sh`
3. 再人工验证登录、卡列表、核心业务页面

## 8. 常见异常与下一步动作

### 8.1 后端不 healthy

下一步先看：

```bash
docker compose logs --tail 100 app
```

### 8.2 MySQL 连接数明显升高

下一步先看：

```bash
docker exec iot_mysql sh -lc 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" -e "SHOW PROCESSLIST;"'
```

### 8.3 Slow_queries 持续增长

下一步优先排查：

- 卡列表分页查询
- 批量操作
- 导出接口
- 同步任务

### 8.4 前端正常、后端正常，但用户说页面慢

优先排查：

- 具体哪个接口慢
- 是否是卡列表筛选条件导致 SQL 变慢
- 是否是供应商接口等待时间长

## 9. 维护建议

后续如果线上结构再变，优先同步更新这两处：

- [check_system.sh](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/deploy/scripts/check_system.sh)
- [SYSTEM_CHECK_RUNBOOK.md](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/docs/SYSTEM_CHECK_RUNBOOK.md)

如果服务名、容器名、Compose 文件位置或 Redis/MySQL 口令管理方式变化，这份文档和脚本都要一起更新。
