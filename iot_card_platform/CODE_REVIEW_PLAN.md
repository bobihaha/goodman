# 物联网卡管理平台 - 代码审查规划

## 📋 审查目标

- 代码质量：可读性、可维护性、规范性
- 安全性：SQL注入、XSS、认证授权漏洞
- 性能：N+1查询、内存泄漏、并发问题
- 业务逻辑：数据一致性、边界条件处理
- 错误处理：异常捕获、用户友好提示

---

## 🎯 审查范围

### 后端 (Python + FastAPI)
- API路由层 (`app/api/v1/`)
- 数据模型层 (`app/db/models/`)
- 数据操作层 (`app/crud/`)
- Schema验证层 (`app/schemas/`)
- 工具函数 (`app/utils/`)
- 外部客户端 (`app/clients/`)

### 前端 (Vue 3 + TypeScript)
- 页面组件 (`frontend/src/views/`)
- API接口 (`frontend/src/api/`)
- 类型定义 (`frontend/src/types/`)
- 工具函数 (`frontend/src/utils/`)

---

## 📦 模块审查清单

### 模块 1: 认证授权模块 ✅
**优先级**: 🔴 CRITICAL

**审查重点**:
- [ ] JWT token生成和验证逻辑
- [ ] 密码加密强度 (bcrypt)
- [ ] 超级登录权限校验
- [ ] 会话管理和token刷新
- [ ] 权限中间件实现

**文件清单**:
- 后端: `app/api/v1/auth.py`, `app/utils/auth.py`, `app/crud/sys_user_crud.py`
- 前端: `views/login/`, `api/modules/auth.ts`, `utils/auth.ts`

---

### 模块 2: 用户管理模块 ✅
**优先级**: 🟠 HIGH

**审查重点**:
- [ ] 三级用户体系数据隔离
- [ ] 用户CRUD权限控制
- [ ] parent_id关系维护
- [ ] 用户删除级联处理
- [ ] 输入验证 (用户名、邮箱格式)

**文件清单**:
- 后端: `app/api/v1/sys_user.py`, `app/crud/sys_user_crud.py`, `app/db/models/sys_user.py`
- 前端: `views/users/`, `api/modules/user.ts`

---

### 模块 3: 套餐管理模块 ✅
**优先级**: 🟡 MEDIUM

**审查重点**:
- [ ] 底层套餐与销售套餐关联逻辑
- [ ] 规格三要素验证 (运营商+流量+周期)
- [ ] 专属客户权限过滤
- [ ] 套餐删除前依赖检查
- [ ] 价格计算精度

**文件清单**:
- 后端: `app/api/v1/package.py`, `app/crud/package_crud.py`, `app/db/models/package.py`
- 前端: `views/packages/`, `api/modules/package.ts`

---

### 模块 4: 出入库管理模块 ✅
**优先级**: 🔴 CRITICAL

**审查重点**:
- [ ] Excel导入数据验证 (ICCID格式、重复检查)
- [ ] 批量操作事务处理
- [ ] 库存数量一致性
- [ ] 出库权限校验
- [ ] 卡片状态转换逻辑
- [ ] 回收操作可逆性

**文件清单**:
- 后端: `app/api/v1/stock.py`, `app/crud/stock_crud.py`, `app/db/models/stock.py`
- 前端: `views/stock/`, `api/modules/stock.ts`

---

### 模块 5: 卡片管理模块 ✅
**优先级**: 🟠 HIGH

**审查重点**:
- [ ] 卡片列表查询性能 (索引优化)
- [ ] 划拨操作权限验证
- [ ] 批量操作性能
- [ ] 备注字段XSS防护
- [ ] 导出功能内存控制

**文件清单**:
- 后端: `app/api/v1/iot_card.py`, `app/crud/iot_card_crud.py`, `app/db/models/iot_card.py`
- 前端: `views/cards/`, `api/modules/card.ts`

---

### 模块 6: 流量池管理模块 ✅
**优先级**: 🟡 MEDIUM

**审查重点**:
- [ ] 组池规则验证 (规格匹配)
- [ ] 流量统计计算准确性
- [ ] 池卡关联维护
- [ ] 告警阈值触发逻辑
- [ ] 并发加卡/移卡处理

**文件清单**:
- 后端: `app/api/v1/pool.py`, `app/crud/pool_crud.py`, `app/db/models/pool.py`
- 前端: `views/pools/`, `api/modules/pool.ts`

---

### 模块 7: 停卡策略模块 ✅
**优先级**: 🔴 CRITICAL

**审查重点**:
- [ ] 供应商API调用错误处理
- [ ] 停机/复机幂等性
- [ ] 批量操作性能优化 (N+1查询)
- [ ] 停卡记录完整性
- [ ] 定时任务异常恢复

**文件清单**:
- 后端: `app/api/v1/suspend.py`, `app/crud/suspend_crud.py`, `app/clients/supplier_api.py`
- 前端: `views/suspend/`, `api/modules/suspend.ts`

---

### 模块 8: 供应商对接模块 ✅
**优先级**: 🔴 CRITICAL

**审查重点**:
- [ ] API密钥安全存储
- [ ] 请求签名验证
- [ ] 超时和重试机制
- [ ] 响应数据验证
- [ ] 同步任务调度器稳定性

**文件清单**:
- 后端: `app/api/v1/supplier.py`, `app/clients/upiot_client.py`, `app/tasks/`
- 前端: `views/suppliers/`, `api/modules/supplier.ts`

---

### 模块 9: 数据同步模块 ✅
**优先级**: 🟠 HIGH

**审查重点**:
- [ ] 流量数据同步准确性
- [ ] 卡片状态自动转换逻辑
- [ ] 生命周期日期计算
- [ ] 同步失败重试策略
- [ ] 日志记录完整性

**文件清单**:
- 后端: `app/api/v1/sync.py`, `app/crud/sync_crud.py`

---

### 模块 10: 仪表盘模块 ✅
**优先级**: 🟢 LOW

**审查重点**:
- [ ] 统计查询性能
- [ ] 数据聚合准确性
- [ ] 缓存策略
- [ ] 图表数据格式

**文件清单**:
- 后端: `app/api/v1/dashboard.py`, `app/crud/dashboard_crud.py`
- 前端: `views/dashboard/`, `api/modules/dashboard.ts`

---

### 模块 11: 项目管理模块 ✅
**优先级**: 🟢 LOW

**审查重点**:
- [ ] 项目权限隔离
- [ ] 卡片数量统计准确性
- [ ] 项目删除级联处理

**文件清单**:
- 后端: `app/api/v1/project.py`, `app/crud/project_crud.py`
- 前端: `views/projects/`, `api/modules/project.ts`

---

## 🔍 审查方法

### 1. 静态代码分析
- 使用 `pylint` / `flake8` 检查Python代码
- 使用 `eslint` / `vue-tsc` 检查TypeScript代码
- 检查代码规范和潜在bug

### 2. 安全审查
- SQL注入风险扫描
- XSS漏洞检查
- 认证授权漏洞
- 敏感信息泄露

### 3. 性能审查
- 数据库查询优化
- N+1查询检测
- 内存泄漏排查
- 并发安全性

### 4. 业务逻辑审查
- 边界条件测试
- 异常场景处理
- 数据一致性验证
- 用户体验优化

---

## 📊 审查进度

| 模块 | 优先级 | 状态 | 发现问题 | 修复状态 |
|------|--------|------|----------|----------|
| 认证授权 | 🔴 CRITICAL | ⏳ 待审查 | - | - |
| 用户管理 | 🟠 HIGH | ⏳ 待审查 | - | - |
| 套餐管理 | 🟡 MEDIUM | ⏳ 待审查 | - | - |
| 出入库管理 | 🔴 CRITICAL | ⏳ 待审查 | - | - |
| 卡片管理 | 🟠 HIGH | ⏳ 待审查 | - | - |
| 流量池管理 | 🟡 MEDIUM | ⏳ 待审查 | - | - |
| 停卡策略 | 🔴 CRITICAL | ⏳ 待审查 | - | - |
| 供应商对接 | 🔴 CRITICAL | ⏳ 待审查 | - | - |
| 数据同步 | 🟠 HIGH | ⏳ 待审查 | - | - |
| 仪表盘 | 🟢 LOW | ⏳ 待审查 | - | - |
| 项目管理 | 🟢 LOW | ⏳ 待审查 | - | - |

---

## 📝 问题分级

- **🔴 CRITICAL**: 安全漏洞、数据丢失风险，必须立即修复
- **🟠 HIGH**: 功能缺陷、性能问题，应尽快修复
- **🟡 MEDIUM**: 代码质量、可维护性问题，建议修复
- **🟢 LOW**: 优化建议、代码风格，可选修复

---

## 🚀 审查流程

1. **准备阶段**: 创建审查文档，列出审查清单
2. **执行阶段**: 按模块逐个审查，记录问题
3. **汇总阶段**: 整理问题清单，按优先级排序
4. **修复阶段**: 按优先级修复问题
5. **验证阶段**: 验证修复效果，回归测试

---

**创建时间**: 2026-03-06
**审查人**: Claude Code
**预计完成**: 2026-03-08
