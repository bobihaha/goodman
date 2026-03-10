# 变更日志

## 2026-03-10

### 修复
- 修复仪表盘运营商筛选功能
- 修复到期卡和超量卡列表未按运营商筛选的问题
- 后端API添加 `carrier` 参数验证（仅允许 cmcc/cucc/ctcc）
- 前端API添加 `carrier` 可选参数
- 到期卡/超量卡组件支持 `carrier` props 并监听变化
- 仪表盘添加"本月到期卡"和"超量卡"统计卡片，点击跳转并筛选
- 卡片列表页面支持URL参数筛选

### 修改文件
- `app/api/v1/dashboard.py`
- `app/services/dashboard_service.py`
- `app/schemas/dashboard.py`
- `frontend/src/api/modules/dashboard.ts`
- `frontend/src/views/dashboard/components/ExpiringCardList.vue`
- `frontend/src/views/dashboard/components/OverUsageCardList.vue`
- `frontend/src/views/dashboard/index.vue`
- `frontend/src/views/cards/list/index.vue`

---

## 2026-03-06

### 修复
- 修复生命周期同步时未调用状态检查逻辑，导致超沉默期卡片状态未及时更新为已激活
- 修复销售套餐编辑时专属客户字段显示为空的问题（异步加载客户信息时序问题）
- 修复销售套餐创建 500 错误（后端 schema 缺少 user_id 字段）
- 修复出库权限漏洞（超级管理员给用户 B 出库时可选用户 A 的专属套餐）
- 修复卡片划拨 422 错误（前后端字段名不一致：target_user_id vs to_user_id）

### 新增
- 新增销售套餐客户搜索功能（按客户名称/账户筛选套餐）
- 新增卡片划拨权限校验（验证目标用户存在且为直属子用户）
- 新增停复机供应商API集成（停机/复机接口）

### 优化
- 代码质量优化（类型安全、错误处理、重置逻辑完善）
- 性能优化：预加载供应商信息，消除N+1查询（50卡操作：51次→2次查询）
- 容错设计：API失败不阻塞数据库更新，记录详细错误日志

---

## 2026-03-04

### 新增
- 新增卡片状态自动更新机制
- 新增定时任务自动同步供应商流量数据
- 新增自动转换规则：testing → silent、testing/silent → activated、activated → suspended

### 修复
- 修复沉默期超期规则：当前日期 > silent_expire_date 且有流量使用 → 自动转为 activated

---

## 2026-02-27

### 优化
- 卡片列表UI优化：搜索框宽度调整、表格网格线、数据格式优化
- 流量显示简化：2G 代替 2.00GB、512M 代替 512MB
- 使用百分比：0位小数（Math.round）

### 新增
- 新增高级搜索功能（前后端联动）
- 新增批量查询优化（结果直接显示在主列表）
- 新增划拨对话框修复（自动加载客户列表）
- 新增卡片详情页优化（字段调整、百分比优化）

---

## 2026-02-13

### 完成
- 完成续费管理模块（批量查询续费价格、Excel导出）
- 完成项目管理模块（项目CRUD、卡片分组）
- 完成17个核心模块前端开发

---

## 2026-02-11

### 新增
- 新增出库功能增强：套餐周期选择、卡类型选择、Excel批量出库
- 新增仪表盘增强：账户余额、到期卡明细、超量卡明细、流量池用量百分比
- 新增库存管理增强：Excel模板上传、出入库记录导出、卡片回收功能
- 新增卡片管理增强：批量查询、批量续费、批量停复机
- 新增流量池管理增强：充值加油包

---

## 2026-02-05

### 新增
- 新增套餐管理增强：套餐ID字段、自动组流量池功能
