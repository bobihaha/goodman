# 物联网卡管理平台 (IoT SIM Card Management Platform)

基于 FastAPI 构建的物联网卡管理后端系统，支持卡片管理、套餐管理、流量监控、设备绑定等核心功能。

## 项目结构

```
app/
├── api/v1/          # 接口路由层
│   ├── common.py    # 公共接口
│   ├── user.py      # 用户模块
│   ├── iot_card.py  # 物联网卡模块
│   ├── package.py   # 套餐模块
│   └── device.py    # 设备模块
├── schemas/         # 数据校验模型
├── services/        # 业务逻辑层
├── crud/            # 数据操作层
├── db/models/       # ORM 模型
├── utils/           # 工具类
├── clients/         # 第三方服务
├── middleware/      # 中间件
├── tasks/           # 定时任务
├── config.py        # 配置管理
└── main.py          # 应用入口
```

## 核心功能

- ✅ 物联网卡管理（ICCID/IMSI/MSISDN）
- ✅ 套餐管理与订购
- ✅ 流量用量统计
- ✅ 设备绑定管理
- ✅ 卡片状态监控
- ✅ 批量导入导出
- ✅ JWT 认证 + 权限控制
- ✅ Docker 容器化部署

## 快速启动

### 1. 安装依赖
```bash
pip install poetry
poetry install
```

### 2. 配置环境
```bash
cp .env.development .env
```

### 3. 启动服务
```bash
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 访问文档
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- 健康检查: http://localhost:8000/api/v1/health

### 5. 生产部署
```bash
docker-compose up -d --build
```
