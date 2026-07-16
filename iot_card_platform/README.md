# 物联网卡管理平台

基于 Vue 3 + FastAPI + MySQL + Redis 的物联网卡管理平台，面向三级多租户 SaaS 场景，覆盖卡片管理、流量池、出入库、停复机、权限控制、项目管理与 H5 自助服务。

这份 README 的目标不是介绍功能亮点，而是作为后续维护的统一入口：帮助开发、排障、发布和接手同学快速找到正确位置。

## 1. 项目概览

### 核心能力

- 卡片管理：查询、备注、续费、加油包、停复机、批量操作
- 流量池管理：组池、用量统计、充值、池详情
- 出入库管理：入库、出库、库存、回收、记录
- 用户与权限：三级用户、菜单权限、超级登录、项目归属
- 供应商对接：流量同步、状态刷新、供应商回调
- 运维辅助：仪表盘、系统配置、调度任务、H5 用户门户
- 渠道推广：独立渠道账号、客户报备 H5、出库/续费推广积分和结算确认

### 当前技术栈

- 前端：Vue 3、TypeScript、Vite、Element Plus、Pinia
- 后端：FastAPI、SQLAlchemy Async、Pydantic Settings、APScheduler
- 数据：MySQL 8、Redis
- 部署：Docker、Docker Compose、Nginx

## 2. 仓库结构

```text
iot_card_platform/
├── app/                        # FastAPI 后端
│   ├── api/v1/                 # 路由层
│   ├── services/               # 业务服务层
│   ├── crud/                   # 数据访问层
│   ├── db/models/              # ORM 模型
│   ├── schemas/                # Pydantic 模型
│   ├── clients/                # 外部供应商接口
│   ├── utils/                  # 通用工具
│   └── scheduler.py            # 定时任务入口
├── frontend/                   # Vue 前端
│   ├── src/views/              # 页面
│   ├── src/api/modules/        # 前端 API 模块
│   ├── src/components/         # 通用/业务组件
│   ├── src/router/             # 路由与守卫
│   └── src/stores/             # Pinia 状态
├── docs/                       # 正式文档与运维 SOP
├── deploy/                     # 部署配置与脚本
├── scripts/                    # 初始化/修复脚本
├── sql/                        # 历史 SQL 脚本
├── tests/                      # pytest 测试
├── Dockerfile                  # 后端镜像
├── docker-compose.yml          # 简化后端启动
├── docker-compose.prod.yml     # 完整生产编排
└── README.md                   # 仓库维护入口
```

## 3. 关键模块对应位置

### 后端 API

- 认证：`app/api/v1/auth.py`
- 用户/权限/菜单：`app/api/v1/user.py`、`app/api/v1/sys_user.py`、`app/api/v1/permission.py`、`app/api/v1/sys_menu.py`
- 卡片：`app/api/v1/iot_card.py`
- 套餐：`app/api/v1/package.py`
- 供应商：`app/api/v1/supplier.py`
- 流量池：`app/api/v1/pool.py`
- 出入库：`app/api/v1/stock.py`
- 停复机：`app/api/v1/suspend.py`
- 同步任务：`app/api/v1/sync.py`
- 项目管理：`app/api/v1/project.py`
- H5 门户：`app/api/v1/h5.py`
- 渠道推广积分：`app/api/v1/channel.py`
- 回调：`app/api/v1/callback.py`

### 后端服务层

- `app/services/` 基本按照业务域拆分，日常排查优先看这里
- 外部接口封装在 `app/clients/`
- 数据模型在 `app/db/models/`
- 定时任务加载与调度在 `app/main.py`、`app/scheduler.py`

### 前端页面

- 登录：`frontend/src/views/login/`
- 仪表盘：`frontend/src/views/dashboard/`
- 用户管理：`frontend/src/views/users/`
- 卡片管理：`frontend/src/views/cards/`
- 流量池：`frontend/src/views/pools/`
- 出入库：`frontend/src/views/stock/`
- 停复机：`frontend/src/views/suspend/`
- 套餐：`frontend/src/views/packages/`
- 系统设置：`frontend/src/views/system/`
- H5 页面：`frontend/src/views/h5/`

## 4. 本地开发

### 4.1 后端

建议使用 Python 3.9。

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

启动后可访问：

- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- 健康检查: `http://localhost:8000/health`

### 4.2 前端

建议使用 Node.js 20。

```bash
cd frontend
npm install
npm run dev
```

默认访问地址：

- 前端：`http://localhost:3000`
- 开发代理：`/api` -> `http://localhost:8000`

### 4.3 使用 Docker

仅启动后端容器时可使用：

```bash
docker compose up -d --build
```

完整生产编排请使用：

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

## 5. 环境变量与配置约定

### 后端配置入口

- 配置类：`app/config.py`
- 默认读取文件名：`.env`
- 生产模板：`.env.production.example`

### 重要说明

- 当前后端配置实际依赖 `DB_HOST / DB_PORT / DB_USER / DB_PASSWORD / DB_NAME`
- 不建议只写 `DB_URL`，因为 `app/config.py` 会优先按分字段拼接连接串
- 生产环境必须设置 `SECRET_KEY`
- CORS 的 `ALLOW_ORIGINS` 需要使用 JSON 数组格式

### 推荐做法

开发环境建议从生产模板复制一份本地 `.env`，再按本机环境调整：

```bash
cp .env.production.example .env
```

至少确认以下变量：

```env
APP_ENV=development
DEBUG=True
PORT=8000
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=iot_card_platform
REDIS_URL=redis://127.0.0.1:6379/0
SECRET_KEY=replace_with_local_secret
ALLOW_ORIGINS=["http://localhost:3000","http://localhost:5173"]
```

### 前端环境变量

- 开发文件：`frontend/.env.development`
- 关键变量：`VITE_API_BASE_URL`

## 6. 数据库与迁移

当前仓库存在多种 SQL 来源，维护时要先辨认脚本用途：

- `app/db/migrations/`：当前更接近正式增量迁移目录
- `scripts/`：初始化、修复、一次性辅助脚本
- `sql/`：历史 SQL 与临时修复脚本

### 维护建议

- 优先把新增结构变更放到 `app/db/migrations/`
- 发布前先在测试库演练，不要直接在生产库挑历史 SQL 执行
- 涉及库存、停复机、同步、H5 字段时，先全文检索同名字段，避免漏改前后端

详细流程见：

- [数据库迁移规范](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/docs/DATABASE_MIGRATION_GUIDE.md)
- [部署迁移 SOP](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/docs/DEPLOYMENT_MIGRATION_SOP.md)
- [数据库结构文档](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/docs/DATABASE_SCHEMA.md)

## 7. 测试与验证

当前仓库以 Python 测试和若干验证脚本为主。

### 后端测试

```bash
pytest
```

如需按模块执行：

```bash
pytest tests/test_services
pytest tests/test_api
```

### 常见手工验证点

- 登录与权限菜单是否正常
- 卡片列表筛选、批量操作、详情页是否正常
- 出入库流程是否能闭环
- 流量池充值、明细和用量统计是否一致
- 停复机策略、记录、告警是否能联动
- 调度任务加载后是否出现重复执行

## 8. 部署与运维

### 推荐生产编排

`docker-compose.prod.yml` 会启动以下服务：

- `nginx`
- `frontend`
- `backend`
- `mysql`
- `redis`

### 运维脚本

- 预检查：`deploy/scripts/predeploy_check.sh`
- MySQL 备份：`deploy/scripts/backup_mysql.sh`
- Redis 备份：`deploy/scripts/backup_redis.sh`
- MySQL 恢复：`deploy/scripts/restore_mysql.sh`
- 健康检查：`deploy/scripts/health_check.sh`

### 当前部署注意事项

- `app/main.py` 启动时会自动加载 APScheduler 任务，生产环境不建议同时启动多个后端副本
- `docker-compose.yml` 仅适合简单后端容器启动，不等于完整生产环境
- 生产发布优先参考阿里云部署文档和稳定发布 Runbook

详细文档：

- [阿里云部署说明](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/deploy/README_DEPLOY_ALIYUN.md)
- [稳定发布 Runbook](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/docs/STABLE_RELEASE_RUNBOOK.md)
- [回滚 SOP](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/deploy/ROLLBACK_SOP.md)

## 9. 文档导航

### 架构与设计

- [系统架构](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/docs/ARCHITECTURE.md)
- [数据库结构](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/docs/DATABASE_SCHEMA.md)
- [数据库迁移规范](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/docs/DATABASE_MIGRATION_GUIDE.md)
- [模块责任边界](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/docs/MODULE_BOUNDARIES_GUIDE.md)
- [核心字段清单](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/docs/CORE_FIELDS_GUIDE.md)
- [关键链路时序图](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/docs/KEY_WORKFLOWS_SEQUENCE.md)
- [开发指南](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/docs/DEVELOPMENT_GUIDE.md)

### 需求与接口

- [前端需求文档](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/FRONTEND_PRD.md)
- [模块规划](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/MODULE_PLAN.md)
- [API 文档说明](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/API_DOCUMENTATION.md)

### 部署与协作

- [AI 协作指南](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/docs/AI_COLLABORATION_GUIDE.md)
- [发布模板](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/docs/RELEASE_TEMPLATES.md)
- [运维命令速查与日志关键词索引](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/docs/OPS_COMMANDS_AND_LOG_INDEX.md)
- [常见故障定位路径](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/docs/TROUBLESHOOTING_GUIDE.md)
- [快速修复指南](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/docs/QUICK_FIX_GUIDE.md)

### 历史归档

- [历史 README](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/docs/archive/README_OLD.md)
- [归档变更记录](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/docs/archive/CHANGELOG.md)
- [已完成功能清单](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/docs/archive/COMPLETED_FEATURES.md)

## 10. 维护时优先注意的几个点

- 环境变量以 `app/config.py` 为准，不要只参考旧 `.env` 文件
- 数据库变更脚本较分散，发布前一定先确认执行顺序和幂等性
- 调度器当前与应用进程耦合，扩容前先评估重复任务风险
- 仓库中有较多历史总结文档，改动功能后要同步更新对应 SOP 或模块说明
- Docker 运行依赖 `requirements.txt`，而不是 `pyproject.toml`，维护依赖版本时要同时关注两者是否一致

## 11. 建议的接手顺序

新同学首次接手时，建议按这个顺序熟悉：

1. 先读本 README，明确目录和运行方式
2. 再看 [系统架构](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/docs/ARCHITECTURE.md) 和 [数据库结构](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/docs/DATABASE_SCHEMA.md)
3. 再看 [模块责任边界](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/docs/MODULE_BOUNDARIES_GUIDE.md)，先建立改动影响面的认知
4. 再看 [核心字段清单](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/docs/CORE_FIELDS_GUIDE.md)，建立字段来源和影响面的认知
5. 再看 [关键链路时序图](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/docs/KEY_WORKFLOWS_SEQUENCE.md)，建立前后端与调度回调的链路认知
6. 本地启动前后端，确认 `/health`、登录、核心页面可访问
7. 按业务域进入 `app/api/v1`、`app/services`、`frontend/src/views`
8. 遇到线上或联调异常时，优先查 [常见故障定位路径](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/docs/TROUBLESHOOTING_GUIDE.md)
9. 发布前严格走部署与迁移 SOP

---

当前 README、数据库迁移规范、模块责任边界、常见故障定位路径、核心字段清单、关键链路时序图、运维命令速查已经补齐；后续如果继续完善，最值得补的是“真实故障案例库”。
