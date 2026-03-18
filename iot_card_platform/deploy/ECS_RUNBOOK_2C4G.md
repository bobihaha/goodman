# ECS 单机部署执行清单

适用机器：

- 阿里云 ECS
- 2 核 4G
- 80GB 系统盘

目标：

- 单机部署 `nginx + frontend + backend + mysql + redis`
- 前后端分离打包
- 具备基础备份能力

## 预计时长

- 纯新环境：2 到 3 小时
- 带数据库迁移：4 到 8 小时

## 上线前准备

### 安全组

放行：

- `22`
- `80`
- `443`

不要放行：

- `3306`
- `6379`

### 系统准备

建议目录：

```bash
/data/iot_card_platform
```

建议结构：

```text
/data/iot_card_platform/
├── project
├── backups
└── logs
```

## 执行步骤

### 1. 上传代码

把项目放到 ECS，例如：

```bash
mkdir -p /data/iot_card_platform
cd /data/iot_card_platform
git clone <your_repo_url> project
cd project
```

### 2. 准备环境变量

```bash
cp .env.production.example .env.production
```

修改：

- `SECRET_KEY`
- `ALLOW_ORIGINS`
- MySQL 密码

### 3. 做上线前检查

```bash
bash deploy/scripts/predeploy_check.sh
```

### 4. 首次启动

```bash
bash deploy/scripts/first_deploy.sh
```

### 5. 检查容器

```bash
bash deploy/scripts/health_check.sh
```

### 6. 健康检查

```bash
curl http://127.0.0.1/health
```

### 7. 首次备份

```bash
bash deploy/scripts/backup_mysql.sh
bash deploy/scripts/backup_redis.sh
```

## 发布流程

每次发布建议：

1. 拉最新代码
2. 备份 MySQL
3. 执行迁移
4. 重建后端和前端
5. 验证核心功能

命令示例：

```bash
git pull
bash deploy/scripts/backup_mysql.sh
docker compose -f docker-compose.prod.yml up -d --build backend frontend nginx
bash deploy/scripts/health_check.sh
```

## 常规运维

查看资源：

```bash
docker stats
free -h
df -h
```

查看后端日志：

```bash
docker logs -f iot_backend
```

查看 MySQL 日志：

```bash
docker logs -f iot_mysql
```

## 风险提示

- 当前方案适合前期，不适合高并发
- MySQL 和应用同机，发版前必须备份
- 数据库迁移一定要先演练
- 当前后端带 APScheduler，保持单实例运行
