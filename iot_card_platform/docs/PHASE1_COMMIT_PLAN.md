# 一期建议提交拆分

## 提交 1：后端规则收口

建议包含：

- [suspend_service.py](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/app/services/suspend_service.py)
- [suspend.py](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/app/api/v1/suspend.py)
- [suspend_crud.py](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/app/crud/suspend_crud.py)
- [iot_card.py](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/app/api/v1/iot_card.py)
- [iot_card_service.py](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/app/services/iot_card_service.py)

建议说明：

- 收口复机入口
- 增加普通复机资格校验
- 增加强制复机能力
- 增加单卡后台补量与自动复机

## 提交 2：流量池补量与日志

建议包含：

- [pool.py](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/app/api/v1/pool.py)
- [pool_service.py](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/app/services/pool_service.py)
- [pool_crud.py](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/app/crud/pool_crud.py)
- [system.py](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/app/api/v1/system.py)
- [system_service.py](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/app/services/system_service.py)
- [system_crud.py](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/app/crud/system_crud.py)
- [pool.py](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/app/schemas/pool.py)
- [iot_card.py](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/app/schemas/iot_card.py)

建议说明：

- 增加流量池后台补量
- 修正池总量统计
- 增加按目标对象过滤操作日志

## 提交 3：前端业务入口

建议包含：

- [card.ts](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/frontend/src/api/modules/card.ts)
- [pool.ts](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/frontend/src/api/modules/pool.ts)
- [BatchAddFlowDialog.vue](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/frontend/src/views/cards/list/components/BatchAddFlowDialog.vue)
- [BatchResumeDialog.vue](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/frontend/src/views/cards/list/components/BatchResumeDialog.vue)
- [cards/list/index.vue](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/frontend/src/views/cards/list/index.vue)
- [cards/detail/index.vue](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/frontend/src/views/cards/detail/index.vue)
- [pools/list/components/RechargeDialog.vue](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/frontend/src/views/pools/list/components/RechargeDialog.vue)
- [pools/list/index.vue](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/frontend/src/views/pools/list/index.vue)
- [pools/detail/index.vue](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/frontend/src/views/pools/detail/index.vue)

建议说明：

- 接入补量、复机、强制复机前端入口
- 接入补量日志展示

## 提交 4：测试与文档

建议包含：

- [test_flow_adjustment_services.py](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/tests/test_services/test_flow_adjustment_services.py)
- [test_flow_adjustment_api.py](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/tests/test_api/test_flow_adjustment_api.py)
- [PHASE1_FLOW_ADJUSTMENT_PLAN.md](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/docs/PHASE1_FLOW_ADJUSTMENT_PLAN.md)
- [PHASE1_DELIVERY_CHECKLIST.md](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/docs/PHASE1_DELIVERY_CHECKLIST.md)
- [PHASE1_RELEASE_NOTE.md](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/docs/PHASE1_RELEASE_NOTE.md)

建议说明：

- 补充一期方案、测试与上线文档

## 提交 5：前端类型治理

建议包含：

- [request.ts](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/frontend/src/utils/request.ts)
- [api/index.ts](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/frontend/src/api/index.ts)
- [types/user.d.ts](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/frontend/src/types/user.d.ts)
- [types/package.d.ts](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/frontend/src/types/package.d.ts)
- [types/supplier.d.ts](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/frontend/src/types/supplier.d.ts)
- 以及本次为通过构建而同步修复的 `views/stock`、`views/packages`、`views/suppliers`、`views/users`、`views/system`、`views/dashboard`、`views/pools` 等类型问题文件

建议说明：

- 清理历史 TypeScript 报错
- 恢复前端生产构建

## 备注

- 如果你希望提交历史更干净，建议至少拆成“业务功能”和“前端类型治理”两大类
- 如果你希望合并提交，也建议保留文档单独一提交，后续回溯会更方便
