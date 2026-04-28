# 关键链路时序图

这份文档用于帮助维护者快速理解项目里的关键业务链路，适合用于：

- 新同学接手
- 改需求前评估影响面
- 联调时快速对齐前后端边界
- 排查“某一步成功了，但下一步没生效”的问题

建议结合以下文档一起看：

- [模块责任边界](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/docs/MODULE_BOUNDARIES_GUIDE.md)
- [核心字段清单](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/docs/CORE_FIELDS_GUIDE.md)
- [常见故障定位路径](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/docs/TROUBLESHOOTING_GUIDE.md)

## 1. 登录与鉴权链路

适用场景：

- 登录失败
- 登录成功后立刻跳回登录页
- 页面提示无权限
- 超级登录异常

```mermaid
sequenceDiagram
    participant U as "用户"
    participant FE as "前端登录页"
    participant API as "auth API"
    participant SVC as "AuthService"
    participant DB as "MySQL"
    participant STORE as "前端 Auth Store"
    participant GUARD as "Router Guard"

    U->>FE: 输入 account/password
    FE->>API: POST /api/v1/auth/login
    API->>SVC: login(request, ip, user_agent)
    SVC->>DB: 查询 sys_users / 校验密码 / 记录登录日志
    DB-->>SVC: 用户数据 + 菜单权限来源
    SVC-->>API: access_token + refresh_token + current_user
    API-->>FE: ResponseModel(data=LoginResponse)
    FE->>STORE: 保存 token / user
    STORE->>API: 获取 profile / menus / permissions
    FE->>GUARD: 进入目标页面
    GUARD->>STORE: 检查 isLoggedIn / menus
    STORE-->>GUARD: 登录态 + 菜单树
    GUARD-->>U: 放行页面或跳回 /dashboard /login
```

### 关键节点

- 登录入参字段以 `app/schemas/auth.py` 为准
- token 生成和登录日志记录在 `app/services/auth_service.py`
- 前端统一拦截和 401 跳转在 `frontend/src/utils/request.ts`
- 登录后菜单加载与权限校验在 `frontend/src/router/guards.ts`

### 容易出问题的点

- 登录字段名不一致
- 返回格式和前端响应拦截器不兼容
- token 保存成功，但菜单未加载
- 菜单 path 与前端 route path 不一致

## 2. 批量出库分配链路

适用场景：

- 出库成功但卡归属没变
- 出库记录有了，但卡片列表不对
- 用户看不到刚出库的卡

```mermaid
sequenceDiagram
    participant U as "运营人员"
    participant FE as "出库页面"
    participant API as "stock API"
    participant SVC as "StockService"
    participant CRUD as "stock_out_crud"
    participant DB as "MySQL"
    participant CARD as "卡片列表/详情"

    U->>FE: 选择库存卡 + 目标用户 + 销售套餐
    FE->>API: POST /api/v1/stock/out
    API->>SVC: stock_out(...)
    SVC->>DB: 校验目标用户状态
    SVC->>DB: 校验销售套餐权限
    SVC->>CRUD: 创建出库记录并更新卡片归属
    CRUD->>DB: 写 stock_out_records / stock_out_record_cards
    CRUD->>DB: 更新 iot_cards.user_id / sale_package_id / 生命周期字段
    DB-->>CRUD: 提交事务
    CRUD-->>SVC: 出库结果
    SVC-->>API: record_no / success / failed
    API-->>FE: 出库成功
    FE->>CARD: 刷新库存和卡片列表
    CARD->>DB: 按 user_id 查询卡片
    DB-->>CARD: 新归属数据
```

### 关键节点

- 出库前校验目标用户与销售套餐关系在 `app/services/stock_service.py`
- 卡片主表更新和记录表写入在 `stock_out_crud`
- 卡归属最终以 `iot_cards.user_id`、`sale_package_id` 为准

### 容易出问题的点

- 只写记录表，没有同步写卡片主表
- 目标用户被禁用
- 专属套餐误出给其他用户
- 页面刷新的是旧筛选条件

## 3. 供应商同步刷新链路

适用场景：

- 流量长期不更新
- 卡状态与供应商侧不一致
- 仪表盘数据不准
- 同步执行一次后池统计没更新

```mermaid
sequenceDiagram
    participant APP as "FastAPI 启动"
    participant SCH as "Scheduler"
    participant SYNC as "SyncService"
    participant CLIENT as "Supplier Client"
    participant DB as "MySQL"
    participant POOL as "Pool CRUD"
    participant UI as "卡片/仪表盘/流量池页面"

    APP->>SCH: start_scheduler()
    APP->>SCH: load_sync_tasks()
    SCH->>DB: 读取 enabled suppliers + sync_interval
    DB-->>SCH: 供应商配置
    SCH->>SCH: 注册定时任务

    SCH->>SYNC: 定时触发 sync_usage(supplier_id)
    SYNC->>DB: 查询待同步卡片
    DB-->>SYNC: 卡片列表
    SYNC->>CLIENT: get_batch_usage(iccids)
    CLIENT-->>SYNC: data_used / data_total / lifecycle
    SYNC->>DB: 更新 iot_cards.data_used/data_total/data_sync_at
    SYNC->>DB: 调用卡状态检查逻辑
    SYNC->>DB: 记录用量快照
    SYNC->>POOL: 更新流量池统计
    POOL->>DB: 更新 traffic_pools.card_count/data_used/data_total
    DB-->>SYNC: 提交成功
    UI->>DB: 刷新卡片/池/仪表盘查询
    DB-->>UI: 最新统计结果
```

### 关键节点

- 调度器启动和任务装载在 `app/main.py`、`app/scheduler.py`
- 同步核心在 `app/services/sync_service.py`
- 供应商调用在 `app/clients/supplier_api.py`
- 池统计刷新会进一步影响告警和停卡逻辑

### 容易出问题的点

- `sync_interval` 配置异常，任务没注册
- 多实例部署，导致重复同步
- 同步成功更新卡片后，流量池统计没有刷新
- 状态被同步更新后，前端页面仍显示旧数据

## 4. 单卡 / 批量续费链路

适用场景：

- 续费成功但到期日没变
- 续费记录页没有对应记录
- 点“续费 1 个月”却被延长 3 个月

```mermaid
sequenceDiagram
    participant U as "运营人员/客户"
    participant FE as "卡片列表续费弹窗"
    participant API as "iot_card API"
    participant SVC as "IotCardService"
    participant PKG as "sale_package_crud"
    participant DB as "MySQL"
    participant LOG as "sys_operation_logs"
    participant RPT as "续费记录页"

    U->>FE: 选择续费月数(1/3/6/12)
    FE->>API: POST /api/v1/cards/{id}/renew 或 /batch/renew-by-iccids
    API->>SVC: purchase_card_renew(...) / batch_renew_by_iccids(...)
    SVC->>DB: 查询卡片当前 expired_at / sale_package_id / period_type
    SVC->>PKG: 查询销售套餐基础周期
    PKG-->>SVC: period_type + 基础周期字段
    SVC->>SVC: 以“本次选择的续费月数/年数”为准计算新到期日
    SVC->>DB: 更新 iot_cards.expired_at
    SVC->>LOG: 写 cards/renew 操作日志
    DB-->>SVC: 提交成功
    SVC-->>API: 续费结果
    API-->>FE: 续费成功
    RPT->>LOG: 聚合 renew 操作日志
    LOG-->>RPT: 操作时间 + 卡号 + 具体续费周期
```

### 关键节点

- 续费接口参数语义是“续费月数”，不是“续几个出库周期”
- 到期日更新在 `app/services/iot_card_service.py`
- 续费记录页当前基于 `sys_operation_logs` 聚合
- 如果日志漏写，页面会显示“续费成功但续费记录为空”
- 当前实现默认只更新本地 `iot_cards.expired_at`，未对接供应商续费接口

### 容易出问题的点

- 错把 `iot_cards.period_count` 当成本次续费时长，导致“续费 1 个月”被放大
- 历史销售套餐 `period_months / period_days` 缺失，导致旧逻辑算不出新到期日
- 批量续费路径漏写操作日志，导致记录页查不到

## 5. 手动停复机与供应商回调链路

适用场景：

- 点击停卡/复机成功但状态没变
- 状态短暂变了又被改回去
- 回调已经收到但页面无变化

```mermaid
sequenceDiagram
    participant U as "运营人员/H5 用户"
    participant FE as "前端或 H5"
    participant API as "suspend API"
    participant SVC as "SuspendActionService"
    participant CLIENT as "Supplier Client"
    participant DB as "MySQL"
    participant CB as "callback API"
    participant REC as "回调补偿逻辑"

    U->>FE: 发起停卡或复机
    FE->>API: POST /api/v1/suspend/cards/suspend|resume
    API->>SVC: 校验当前卡状态和可操作性
    SVC->>DB: 写 suspend_logs
    SVC->>DB: 创建 supplier_suspend_operations(callback_no)
    SVC->>CLIENT: 调供应商停复机接口
    CLIENT-->>SVC: 请求结果
    SVC->>DB: 记录 request_result / 本地状态
    SVC-->>FE: 返回操作结果

    CLIENT-->>CB: POST /api/v1/callbacks/upiot/sor
    CB->>DB: 读取 payload
    CB->>SVC: handle_upiot_sor_callback(...)
    SVC->>DB: 通过 callback_no / iccid 匹配 supplier_suspend_operations
    SVC->>DB: 更新 callback_status / callback_payload / card status
    SVC->>DB: 必要时纠正 suspend_type / suspend_reason
    DB-->>CB: 更新完成
    CB-->>CLIENT: success

    SVC->>REC: 若回调未到，延迟执行 reconcile
    REC->>CLIENT: 主动查询 lifecycle
    CLIENT-->>REC: 当前状态
    REC->>DB: 补偿更新 operation 与 card
```

### 关键节点

- 手动停复机主逻辑在 `app/services/suspend_service.py`
- 回调入口在 `app/api/v1/callback.py`
- 回调匹配核心键是 `callback_no`
- 即使回调没到，也可能触发延迟补偿查询

### 容易出问题的点

- 本地状态更新了，但供应商侧失败
- 供应商侧成功了，但回调没落到正确记录
- 回调异常被吞掉，接口仍返回 `success`
- 同步任务或回调把手工状态再次覆盖

## 6. 模块联动总览

### 登录与鉴权链路会影响

- 登录页
- token 存储
- 菜单加载
- 路由守卫
- 超级登录

### 出库分配链路会影响

- 库存页面
- 卡片列表
- 用户归属
- 套餐关联
- 项目归属
- 出库记录

### 同步刷新链路会影响

- 卡片用量
- 卡片状态
- 流量池统计
- 仪表盘
- 停复机判断

### 停复机回调链路会影响

- 卡片状态
- 停复机日志
- 回调记录
- H5 操作结果
- 后续同步纠偏

## 7. 使用建议

当你准备修改某条链路时，建议做这三件事：

1. 先看对应时序图，确认上下游模块
2. 再对照 [核心字段清单](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/docs/CORE_FIELDS_GUIDE.md) 检查关键字段
3. 最后按 [常见故障定位路径](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/docs/TROUBLESHOOTING_GUIDE.md) 设计回归验证点
