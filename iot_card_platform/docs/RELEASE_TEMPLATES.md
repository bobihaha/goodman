# 发版模板

## 1. 标准发布流程

结合当前项目，推荐你后续固定按下面流程做：

1. 本地开发代码
2. 本地自测功能
3. 本地跑后端测试和前端构建
4. 如有 SQL，先写成独立 `.sql` 文件
5. 本地或测试环境用 Docker 构建生产镜像验证
6. 上线前备份生产数据库
7. 先执行兼容型 SQL
8. 再用当前生产编排文件发布线上
9. 执行健康检查
10. 做业务验收
11. 观察日志 30 到 60 分钟

一句话版本：

> 本地写好代码 -> 本地测通 -> 本地按生产方式构建 -> 备份线上数据库 -> 先上兼容 SQL -> 再发容器 -> 健康检查和业务验证 -> 观察日志。

## 2. 发布前 Checklist

每次发版前直接复制这段：

```md
# 发布前 Checklist

- [ ] 本次发布范围已冻结
- [ ] 已明确影响模块
- [ ] 已确认是否涉及前端 / 后端 / SQL / 配置
- [ ] 本地功能自测通过
- [ ] 后端测试通过：`pytest tests`
- [ ] 前端构建通过：`cd frontend && npm run build`
- [ ] Docker 生产构建通过
- [ ] SQL 已单独成文件
- [ ] SQL 已评审，且有回滚方案
- [ ] 已确认 `.env.production` 是否需要变更
- [ ] 已确认上线负责人和验证负责人
- [ ] 已确认低峰发布窗口
```

## 3. 发布执行单模板

每次正式上线前，建议建一个简单发布单。

```md
# 发布单

## 基本信息

- 发布时间：
- 发布人：
- 验证人：
- 版本号：
- Git commit：

## 发布内容

- 功能 1：
- 功能 2：
- Bugfix：

## 影响范围

- 前端页面：
- 后端接口：
- 数据库：
- 配置项：
- 定时任务：

## SQL 变更

- 是否有 SQL：有 / 无
- SQL 文件：
- 是否已在测试环境执行：是 / 否
- 回滚方式：

## 发布命令

~~~bash
bash deploy/scripts/backup_mysql.sh
python scripts/run_migration.py app/db/migrations/xxx.sql
docker compose build
docker compose up -d
bash deploy/scripts/health_check.sh
~~~

## 验证结果

- 登录：
- 首页：
- 新功能主流程：
- 旧功能回归：
- 权限验证：

## 观察结果

- backend 日志：
- nginx 日志：
- 是否报错：

## 最终结果

- 发布成功 / 回滚
- 备注：
```

## 4. 无 SQL 发布命令模板

```bash
# 1. 上线前备份
bash deploy/scripts/backup_mysql.sh

# 2. 构建镜像
docker compose build

# 3. 启动新版本
docker compose up -d

# 4. 健康检查
bash deploy/scripts/health_check.sh
```

## 5. 有 SQL 发布命令模板

```bash
# 1. 上线前备份
bash deploy/scripts/backup_mysql.sh

# 2. 执行 SQL
python scripts/run_migration.py app/db/migrations/xxx.sql

# 3. 构建镜像
docker compose build

# 4. 启动新版本
docker compose up -d

# 5. 健康检查
bash deploy/scripts/health_check.sh
```

## 6. 回滚模板

如果发布后发现严重问题，优先按下面顺序处理：

1. 判断是代码问题还是 SQL/数据问题
2. 纯代码问题先回滚应用，不急着回滚数据库
3. SQL 或数据问题，再考虑恢复备份
4. 恢复后重新做健康检查和业务验收

数据库恢复命令：

```bash
bash deploy/scripts/restore_mysql.sh ./backups/mysql/xxx.sql.gz
```
