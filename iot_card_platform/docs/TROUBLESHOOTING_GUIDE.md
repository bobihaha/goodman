# 常见故障定位路径

这份文档面向日常维护和线上排障，目标不是罗列所有问题，而是给出一套“先看哪里、再看哪里、常见根因是什么”的定位路径。

如果你已经知道故障属于某个业务域，请同时配合 [模块责任边界](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/docs/MODULE_BOUNDARIES_GUIDE.md) 一起看。

## 1. 通用排查顺序

不确定问题在哪时，建议按这个顺序缩小范围：

1. 先判断是前端问题、后端问题，还是数据问题
2. 再确认是单个接口异常，还是整条业务链路异常
3. 先看浏览器 Network 和控制台
4. 再看后端接口日志和 `logs/app.log`
5. 如涉及定时任务、供应商或回调，再看调度和回调入口
6. 如接口正常但页面异常，再回到前端类型、字段映射和权限控制

## 2. 先看哪些位置

### 前端优先看

- `frontend/src/utils/request.ts`
  - 请求头、Token、统一错误处理、401 跳转
- `frontend/src/router/guards.ts`
  - 登录态判断、菜单权限、页面跳转
- 对应页面 `frontend/src/views/...`
  - 表单、列表、按钮、弹窗
- 对应 API 模块 `frontend/src/api/modules/...`
  - 接口路径、参数、响应字段

### 后端优先看

- `app/api/v1/...`
  - 路由路径、依赖注入、响应结构
- `app/services/...`
  - 核心业务逻辑
- `app/crud/...`
  - 实际查询和写库逻辑
- `app/schemas/...`
  - 请求参数和响应结构
- `app/db/models/...`
  - 数据库存储字段

### 调度 / 供应商 / 回调额外看

- `app/main.py`
  - 应用启动时是否加载调度器
- `app/scheduler.py`
  - 定时任务是否注册、执行
- `app/api/v1/callback.py`
  - 回调入口是否收到数据
- `app/clients/`
  - 供应商 API 调用细节

## 3. 日志和观察点

### 后端日志

默认日志文件：

- `logs/app.log`

重点关注：

- 认证失败
- 参数校验失败
- 定时同步失败
- 供应商调用异常
- 回调处理失败

### 前端观察点

- 浏览器 Console
- 浏览器 Network
- 请求状态码
- 请求体 / 响应体
- 是否被 401 自动重定向

### 数据层观察点

- 关键字段是否已落库
- 当前用户是否有数据可见范围
- 字段新增后是否已经迁移到数据库
- 同一条记录是否被多个流程重复更新

## 4. 常见故障场景

### 4.1 登录失败 / 自动跳回登录页

#### 常见症状

- 登录接口 422 / 400 / 401
- 登录成功后立刻跳回登录页
- 页面刷新后丢失登录态

#### 先看哪里

1. `frontend/src/utils/request.ts`
2. `frontend/src/stores/modules/auth.ts`
3. `frontend/src/router/guards.ts`
4. `app/api/v1/auth.py`
5. `app/schemas/auth.py`
6. `app/services/auth_service.py`

#### 重点检查

- 前端提交字段名是否与后端 schema 一致
- 返回是否是前端拦截器能识别的格式
- Token 是否成功写入本地存储
- 401 时是否被统一拦截并重定向
- `/api/v1/auth/profile` 是否正常返回当前用户

#### 常见根因

- 登录请求字段名不一致
- 响应格式变化，前端未兼容
- Token 未保存或读取失败
- 路由守卫在菜单未加载时误判无权限
- 后端 `SECRET_KEY` 或认证逻辑异常

### 4.2 页面提示“没有权限访问”

#### 常见症状

- 登录正常，但进入某个页面被拦回
- 明明菜单里有页面，打开详情页却没权限
- 不同账号菜单不一致

#### 先看哪里

1. `frontend/src/router/guards.ts`
2. `frontend/src/directives/permission.ts`
3. `frontend/src/stores/modules/auth.ts`
4. `app/api/v1/sys_menu.py`
5. `app/api/v1/permission.py`
6. 用户菜单和权限相关 service / crud

#### 重点检查

- 登录后菜单是否加载成功
- 路由 path 和菜单 path 是否一致
- 详情页是否已做父路径映射
- 后端是否返回了当前账号正确的菜单树
- 新增菜单后数据库菜单数据是否已补齐

#### 常见根因

- 路由路径和菜单路径不一致
- 菜单未配置到当前账号
- 新增页面只有前端路由，没有后端菜单数据
- 权限码变更后前端按钮判断未同步

### 4.3 接口 422 / 参数校验失败

#### 常见症状

- 页面请求发出后直接 422
- 后端接口在 Swagger 可调通，前端不通
- 同一个接口新增字段后开始报错

#### 先看哪里

1. 浏览器 Network 请求体
2. `app/schemas/...`
3. 对应前端类型 `frontend/src/types/...`
4. 对应 API 模块 `frontend/src/api/modules/...`
5. 页面表单提交逻辑

#### 重点检查

- 前端字段名和后端 schema 是否一致
- 必填字段是否漏传
- 日期、枚举、布尔值格式是否符合 schema
- 前端把 camelCase 直接发给了后端 snake_case 字段没有

#### 常见根因

- 字段名不一致
- 前端类型已改，页面表单没改
- 后端 schema 新增必填字段但前端未补
- 前端传了空字符串，后端实际要求 `null` 或数字

### 4.4 页面空白 / 路由 500 / 组件加载失败

#### 常见症状

- 打开页面白屏
- Vite 报 import 失败
- 某个页面路由一进就炸

#### 先看哪里

1. 浏览器 Console
2. `frontend/src/router/routes.ts`
3. 对应页面文件路径
4. `frontend/src/types/...`
5. `frontend/src/utils/formatter.ts` 等通用依赖文件

#### 重点检查

- 路由引用的页面文件是否存在
- 引入路径大小写是否正确
- 页面依赖的函数是否真的导出
- 懒加载路径是否写错

#### 常见根因

- 路由先配了，页面文件还没创建
- 导入路径或文件名大小写不一致
- 通用工具函数导出名被改动

### 4.5 卡片列表数据不对 / 详情与列表不一致

#### 常见症状

- 列表查不到卡
- 列表状态和详情状态不一致
- 批量操作后页面未反映

#### 先看哪里

1. `app/api/v1/iot_card.py`
2. `app/services/iot_card_service.py`
3. `app/crud/iot_card_crud.py`
4. `app/db/models/iot_card.py`
5. `frontend/src/api/modules/card.ts`
6. `frontend/src/views/cards/`

#### 重点检查

- 当前账号是否有可见范围
- 列表查询条件是否被改动
- 状态字段是否由其他流程异步更新
- 详情接口和列表接口是否用了不同字段口径

#### 常见根因

- 用户数据隔离条件生效
- 字段新增后列表查询没补
- 停复机 / 回调 / 同步任务修改了状态，但前端未刷新
- 列表和详情读的是不同聚合逻辑

### 4.6 出入库后数据不一致

#### 常见症状

- 出库成功但卡片归属没变
- 库存数量不对
- 回收后卡片仍在用户列表里

#### 先看哪里

1. `app/api/v1/stock.py`
2. `app/services/stock_service.py`
3. `app/crud/stock_crud.py`
4. `app/db/models/stock.py`
5. `app/db/models/iot_card.py`
6. `frontend/src/views/stock/`

#### 重点检查

- 事务是否完整提交
- 卡片归属用户字段是否更新
- 销售套餐、项目归属是否同步更新
- 库存记录和卡片主表是否口径一致

#### 常见根因

- 只写了记录表，没写卡主表
- 批量处理部分失败但前端当作全成功
- 出库逻辑调整后漏了项目或套餐字段

### 4.7 流量池统计异常 / 池内卡片不对

#### 常见症状

- 池用量不刷新
- 池卡数不对
- 加卡成功但池详情没变
- 超阈值停卡没触发

#### 先看哪里

1. `app/api/v1/pool.py`
2. `app/services/pool_service.py`
3. `app/crud/pool_crud.py`
4. `app/db/models/pool.py`
5. `app/db/models/iot_card.py`
6. `frontend/src/views/pools/`

#### 重点检查

- 卡片规格是否匹配组池规则
- 卡片 `pool_id` / `is_pool_member` 是否更新
- 池统计更新逻辑是否执行
- 阈值配置是否存在
- 停卡联动是否被供应商调用异常中断

#### 常见根因

- 规格不匹配导致未真正入池
- 统计刷新方法未被调用
- 池附加流量月份逻辑造成口径偏差
- 超阈值后供应商 API 调用失败

### 4.8 停复机按钮异常 / 卡状态改了又回滚

#### 常见症状

- 点击停卡或复机失败
- 前端提示成功但状态没变
- 状态短暂变化后又变回去

#### 先看哪里

1. `app/api/v1/suspend.py`
2. `app/services/suspend_service.py`
3. `app/db/models/suspend.py`
4. `app/db/models/iot_card.py`
5. `app/clients/`
6. `app/api/v1/callback.py`

#### 重点检查

- 供应商接口是否调用成功
- 日志记录和卡状态是否同时更新
- 是否有回调把状态再次纠正
- 是否被同步任务刷新覆盖

#### 常见根因

- 供应商接口成功/失败口径与本地处理不一致
- 本地已更新状态，但供应商回调又修正回原值
- 定时同步重新覆盖了手动操作结果

### 4.9 同步任务没执行 / 重复执行

#### 常见症状

- 流量长期不更新
- 某供应商一直没同步
- 同一时间段出现重复同步

#### 先看哪里

1. `app/main.py`
2. `app/scheduler.py`
3. `app/services/sync_service.py`
4. `app/crud/supplier_crud.py`
5. `logs/app.log`

#### 重点检查

- 应用启动时是否执行了 `start_scheduler()` 和 `load_sync_tasks()`
- 供应商是否启用且 `sync_interval` 合法
- 任务 ID 是否重复注册
- 当前部署是否启动了多个后端实例

#### 常见根因

- 供应商同步间隔配置异常
- 应用没有完整启动，任务未加载
- 多实例部署导致重复执行
- 同步异常被日志记录但页面没有暴露

### 4.10 供应商回调到了，但状态没更新

#### 常见症状

- 回调接口返回 success
- 但页面状态、日志、卡片信息没有变化

#### 先看哪里

1. `app/api/v1/callback.py`
2. `app/services/suspend_service.py` 中的回调处理逻辑
3. `app/services/card_status_service.py`
4. `app/db/models/iot_card.py`
5. `logs/app.log`

#### 重点检查

- 回调 payload 字段是否真的匹配处理逻辑
- 回调内容是否能定位到具体卡片
- 回调异常是否被吞掉只记录日志
- 回调是否只是成功接收，但业务未命中更新条件

#### 常见根因

- 回调字段结构与预期不一致
- ICCID / callback_no 等关联键不匹配
- 回调异常被捕获后仅写日志，接口仍返回 success

### 4.11 数据库字段已加，但代码报字段不存在

#### 常见症状

- 本地能跑，测试/生产报 Unknown column
- 接口一到某个查询就炸
- 前端新字段始终为空

#### 先看哪里

1. `app/db/models/...`
2. `app/schemas/...`
3. `app/db/migrations/...`
4. 实际数据库表结构
5. 对应 service / crud 查询

#### 重点检查

- 迁移脚本是否已执行到目标环境
- ORM 模型和数据库表结构是否一致
- 前后端是否都已经接入新字段

#### 常见根因

- 只改了代码没跑 SQL
- 只跑了部分环境
- 字段名改动后旧查询仍在使用旧字段

## 5. 快速判断是哪里的问题

### 更像前端问题

- Console 直接报 import / 渲染错误
- Network 根本没发请求
- 接口成功但页面没显示
- 某个按钮点了没反应

### 更像后端问题

- 接口 4xx/5xx
- 日志明确报异常
- 同一请求在 Swagger 也失败
- 数据未落库或状态未更新

### 更像数据 / 配置问题

- 某些账号正常，某些账号异常
- 某个供应商异常，其他正常
- 新环境才有问题
- SQL 跑过后才恢复

## 6. 排障时的注意事项

- 先保留现场，不要一上来改代码和改库
- 先确认当前环境指向的数据库和 Redis
- 涉及卡状态、停复机、同步时，不要只看一个接口结果
- 涉及权限问题时，至少用两个不同级别账号交叉验证
- 涉及 SQL 修复时，先参考 [数据库迁移规范](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/docs/DATABASE_MIGRATION_GUIDE.md)

## 7. 后续可继续沉淀的方向

- 每类故障补一条真实案例
- 给关键业务链路补“日志关键词索引”
- 给调度 / 回调 / 停复机补一份时序图
