# ECS 首次上线命令清单

这份清单适合你当前的单机低成本部署方案。

适用前提：

- 阿里云 ECS 已创建
- 系统为 Alibaba Cloud Linux 3 或 Ubuntu 22.04
- 已能通过 SSH 登录
- 项目将部署为 `nginx + frontend + backend + mysql + redis`

## 预计时长

- 纯新环境：2 到 3 小时
- 带数据库迁移：4 到 8 小时

## 1. 服务器初始化

```bash
mkdir -p /data/iot_card_platform
cd /data/iot_card_platform
```

如果机器还没装 Git：

```bash
sudo yum install -y git || sudo apt-get update && sudo apt-get install -y git
```

## 2. 安装 Docker

如果系统还没装 Docker，可以参考官方方式安装。安装完成后确认：

```bash
docker --version
docker compose version
```

## 3. 拉取代码

```bash
cd /data/iot_card_platform
git clone <你的仓库地址> project
cd project
```

如果代码已经在服务器上：

```bash
cd /data/iot_card_platform/project
git pull
```

## 4. 准备生产环境变量

```bash
cp .env.production.example .env.production
```

建议至少修改这些值：

```bash
sed -n '1,200p' .env.production
```

重点修改：

- `SECRET_KEY`
- `DB_PASSWORD`
- `MYSQL_ROOT_PASSWORD`
- `MYSQL_PASSWORD`
- `ALLOW_ORIGINS`

## 5. 执行发布前检查

```bash
bash deploy/scripts/predeploy_check.sh
```

## 6. 首次部署

```bash
bash deploy/scripts/first_deploy.sh
```

如果你想手动执行，也可以：

```bash
mkdir -p logs backups/mysql backups/redis
docker compose -f docker-compose.prod.yml up -d --build
```

## 7. 检查服务状态

```bash
bash deploy/scripts/health_check.sh
```

或者手动检查：

```bash
docker compose -f docker-compose.prod.yml ps
docker logs iot_backend --tail 200
docker logs iot_mysql --tail 100
docker logs iot_nginx --tail 100
curl http://127.0.0.1/health
```

## 8. 首次备份

```bash
bash deploy/scripts/backup_mysql.sh
bash deploy/scripts/backup_redis.sh
```

## 9. 后续发布

```bash
cd /data/iot_card_platform/project
git pull
bash deploy/scripts/backup_mysql.sh
docker compose -f docker-compose.prod.yml up -d --build backend frontend nginx
bash deploy/scripts/health_check.sh
```

## 10. 常用运维命令

查看容器：

```bash
docker compose -f docker-compose.prod.yml ps
```

查看资源：

```bash
docker stats
free -h
df -h
```

查看日志：

```bash
docker logs -f iot_backend
docker logs -f iot_mysql
docker logs -f iot_nginx
```

重启服务：

```bash
docker compose -f docker-compose.prod.yml restart
```

停止服务：

```bash
docker compose -f docker-compose.prod.yml down
```
