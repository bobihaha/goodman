# 停卡管理模块开发完成

## 📋 开发内容

### 1. 前端文件

#### API接口文件
- **文件**: `frontend/src/api/modules/suspend.ts`
- **功能**: 
  - 停卡策略管理（增删改查）
  - 批量停卡/复机
  - 批量强制激活（超级管理员）
  - 停卡记录查询
  - 停卡记录导出

#### 停卡策略页面
- **文件**: `frontend/src/views/suspend/policy/index.vue`
- **路由**: `/suspend/policy`
- **功能**:
  - 策略列表展示
  - 创建/编辑/删除策略
  - 启用/禁用策略
  - 支持三种策略类型：
    - 到期自动停卡
    - 流量池超限停卡
    - 单卡超量停卡
  - 配置告警阈值、紧急阈值、停卡阈值

#### 停卡记录页面
- **文件**: `frontend/src/views/suspend/logs/index.vue`
- **路由**: `/suspend/logs`
- **功能**:
  - 停卡记录列表
  - 按操作类型、停卡类型、时间范围筛选
  - 批量复机功能
  - 单个卡片复机
  - 导出停卡记录

#### 路由配置
- **文件**: `frontend/src/router/routes.ts`
- **新增路由**:
  - `/suspend/policy` - 停卡策略
  - `/suspend/logs` - 停卡记录

### 2. 后端API（已存在）

后端API已经完整实现，位于：
- **文件**: `app/api/v1/suspend.py`
- **服务层**: `app/services/suspend_service.py`

#### API端点

**停卡策略管理**:
- `GET /api/v1/suspend/policies` - 获取策略列表
- `POST /api/v1/suspend/policies` - 创建策略
- `GET /api/v1/suspend/policies/{id}` - 获取策略详情
- `PUT /api/v1/suspend/policies/{id}` - 更新策略
- `DELETE /api/v1/suspend/policies/{id}` - 删除策略

**手动停卡/复机**:
- `POST /api/v1/suspend/cards/suspend` - 手动停卡
- `POST /api/v1/suspend/cards/resume` - 手动复机
- `POST /api/v1/suspend/cards/force-activate` - 强制激活（超级管理员）

**自动任务**:
- `POST /api/v1/suspend/tasks/expired` - 执行到期停卡任务
- `POST /api/v1/suspend/tasks/card-exceed` - 执行单卡超量检查任务

**停卡记录**:
- `GET /api/v1/suspend/logs` - 获取停卡记录
- `POST /api/v1/suspend/logs/export` - 导出停卡记录

**告警管理**:
- `GET /api/v1/suspend/alerts` - 获取告警列表
- `GET /api/v1/suspend/alerts/stats` - 获取未处理告警统计
- `POST /api/v1/suspend/alerts/{id}/handle` - 处理告警

### 3. 数据库菜单配置

需要执行SQL脚本添加菜单：

```sql
-- 添加停卡管理菜单

-- 1. 添加停卡管理父菜单
INSERT INTO sys_menus (code, name, path, parent_id, sort, icon, status, created_at, updated_at)
VALUES ('suspend', '停卡管理', '/suspend', NULL, 8, 'warning', 'enable', NOW(), NOW());

-- 获取刚插入的父菜单ID
SET @parent_id = LAST_INSERT_ID();

-- 2. 添加停卡策略子菜单
INSERT INTO sys_menus (code, name, path, parent_id, sort, icon, status, created_at, updated_at)
VALUES ('suspend_policy', '停卡策略', '/suspend/policy', @parent_id, 1, 'setting', 'enable', NOW(), NOW());

-- 3. 添加停卡记录子菜单
INSERT INTO sys_menus (code, name, path, parent_id, sort, icon, status, created_at, updated_at)
VALUES ('suspend_logs', '停卡记录', '/suspend/logs', @parent_id, 2, 'document', 'enable', NOW(), NOW());

-- 4. 为超级管理员（user_id=1）分配菜单权限
INSERT INTO sys_user_menus (user_id, menu_id, created_at)
SELECT 1, id, NOW() FROM sys_menus WHERE code IN ('suspend', 'suspend_policy', 'suspend_logs') AND is_deleted = 0;
```

**SQL脚本文件**: `add_suspend_menus.sql`

## 🎯 功能特性

### 停卡策略管理

1. **到期自动停卡**
   - 自动检测到期卡片
   - 自动执行停卡操作
   - 记录停卡日志

2. **流量池超限停卡**
   - 设置告警阈值（如80%）
   - 设置紧急阈值（如90%）
   - 设置停卡阈值（如100%）
   - 达到阈值自动停卡

3. **单卡超量停卡**
   - 监控单卡流量使用率
   - 多级告警机制
   - 超限自动停卡

### 停卡记录管理

1. **记录查询**
   - 按操作类型筛选（停卡/复机）
   - 按停卡类型筛选
   - 按时间范围筛选
   - 分页展示

2. **批量复机**
   - 支持批量选择
   - 填写复机原因
   - 二次确认
   - 操作日志记录

3. **数据导出**
   - 导出Excel格式
   - 包含所有筛选条件
   - 文件名带时间戳

## 📝 使用说明

### 1. 执行数据库脚本

```bash
cd /Users/huiren/Documents/goodman/iot_card_platform
mysql -uroot -p数据库密码 iot_card_platform < add_suspend_menus.sql
```

### 2. 刷新前端页面

刷新浏览器，左侧菜单栏应该会显示"停卡管理"菜单，包含两个子菜单：
- 停卡策略
- 停卡记录

### 3. 创建停卡策略

1. 进入"停卡策略"页面
2. 点击"新增策略"按钮
3. 填写策略信息：
   - 策略名称
   - 策略类型
   - 策略描述
   - 阈值配置（流量池/单卡超量）
   - 是否自动停卡
4. 保存策略

### 4. 查看停卡记录

1. 进入"停卡记录"页面
2. 使用筛选条件查询
3. 查看停卡详情
4. 对已停卡的卡片执行复机操作

## ✅ 测试检查清单

- [ ] 停卡策略页面正常显示
- [ ] 可以创建停卡策略
- [ ] 可以编辑停卡策略
- [ ] 可以删除停卡策略
- [ ] 可以启用/禁用策略
- [ ] 停卡记录页面正常显示
- [ ] 可以筛选停卡记录
- [ ] 可以单个复机
- [ ] 可以批量复机
- [ ] 可以导出停卡记录

## 🔧 技术细节

### 前端技术栈
- Vue 3 Composition API
- TypeScript
- Element Plus
- Day.js（日期处理）

### 数据结构

**停卡策略**:
```typescript
interface SuspendPolicy {
  id: number
  name: string
  policy_type: 'expired' | 'pool_exceed' | 'card_exceed'
  description: string
  warning_threshold?: number
  critical_threshold?: number
  stop_threshold?: number
  auto_suspend: boolean
  auto_resume: boolean
  is_enabled: boolean
}
```

**停卡记录**:
```typescript
interface SuspendLog {
  id: number
  card_id: number
  iccid: string
  action: 'suspend' | 'resume'
  suspend_type: 'expired' | 'pool_exceed' | 'card_exceed' | 'manual' | 'force'
  reason: string
  operator_id: number
  created_at: string
}
```

## 📊 PRD文档更新

停卡管理模块已完成，对应PRD文档中的"8. 停卡管理"章节：

### 8.1 停卡策略 ✅
- 策略列表 ✅
- 创建策略 ✅
- 编辑策略 ✅
- 启用/禁用策略 ✅

### 8.2 停卡记录 ✅
- 停卡记录列表 ✅
- 按类型/时间筛选 ✅
- 查看停卡原因 ✅
- 手动批量复机 ✅

## 🎉 开发完成

停卡管理模块已全部开发完成，包括：
- ✅ 前端页面（停卡策略、停卡记录）
- ✅ API接口封装
- ✅ 路由配置
- ✅ 数据库菜单脚本

下一步：执行数据库脚本，然后刷新浏览器测试功能。


