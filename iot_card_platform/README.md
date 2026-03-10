# 物联网卡管理平台

## 项目概述

基于 **Vue 3 + FastAPI + MySQL** 的物联网卡管理平台，支持三级多租户 SaaS 架构。

**核心功能**：
- 卡片管理（查询、划拨、备注、续费、停复机）
- 流量池管理（组池共享、用量统计、加油包充值）
- 出入库管理（批量导入、Excel模板、回收）
- 停复机管理（策略、记录、告警）
- 用户权限管理（三级用户、超级登录、动态菜单）

**技术栈**：
- 前端：Vue 3.4 + TypeScript 5 + Element Plus 2.5 + Pinia 2.1
- 后端：FastAPI + SQLAlchemy 2.x + MySQL 8.4 + Redis
- 部署：Docker + Docker Compose

---

## 快速开始

### 前端
```bash
cd frontend
npm install
npm run dev
```

### 后端
```bash
cd app
pip install -r requirements.txt
uvicorn main:app --reload
```

### Docker部署
```bash
docker-compose up -d
```

---

## 文档导航

### 核心文档
- [前端需求文档](FRONTEND_PRD.md) - 功能需求、字段定义、开发规范
- [后端模块规划](MODULE_PLAN.md) - 模块职责、API端点、技术架构
- [API接口文档](API_DOCUMENTATION.md) - 完整的API接口说明

### 设计文档
- [系统架构](docs/ARCHITECTURE.md) - 系统架构设计
- [数据库设计](docs/DATABASE_SCHEMA.md) - 数据库表结构
- [开发指南](docs/DEVELOPMENT_GUIDE.md) - 开发规范和最佳实践

### 历史文档
- [变更日志](docs/archive/CHANGELOG.md) - 功能修复和更新记录
- [已完成功能](docs/archive/COMPLETED_FEATURES.md) - 功能开发完成清单

---

## 项目状态

**当前版本**：v2.0

**开发进度**：
- ✅ 核心模块已完成（17/17）
- ✅ 前端页面已完成（24个路由）
- 🔄 联调测试中
- 📋 待优化：性能优化、体验完善

**最近更新**（2026-03-10）：
- 修复仪表盘运营商筛选功能
- 优化到期卡和超量卡列表筛选逻辑

---

## 目录结构

```
iot_card_platform/
├── frontend/              # 前端项目（Vue3）
├── app/                   # 后端项目（FastAPI）
├── docs/                  # 文档目录
│   ├── archive/          # 历史文档归档
│   ├── ARCHITECTURE.md
│   ├── DATABASE_SCHEMA.md
│   └── DEVELOPMENT_GUIDE.md
├── FRONTEND_PRD.md       # 前端需求文档
├── MODULE_PLAN.md        # 后端模块规划
├── API_DOCUMENTATION.md  # API文档
└── README.md             # 本文件
```
