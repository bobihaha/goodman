# 一期交付清单

## 范围

本期已完成以下能力：

- 统一复机规则，禁止绕过停卡原因直接复机
- 支持超级管理员强制复机
- 支持上级用户给下级用户后台补单卡流量
- 支持上级用户给下级用户后台补流量池流量
- 补量后自动重检并按规则自动复机
- 卡片详情、卡片列表、流量池详情、流量池列表均已接入补量/复机入口
- 卡片详情、流量池详情支持查看补量日志
- 前端 TypeScript 存量错误已清理完成，生产构建可通过

## 关键规则

- `manual` 人工停卡：普通复机不允许，需强制复机
- `expired` 到期停卡：普通复机不允许，需续费
- `card_exceed` 单卡超量：补量后才允许复机
- `pool_exceed` 流量池超量：池补量后才允许复机
- 单卡补量仅允许非流量池卡
- 流量池卡必须在流量池维度补量
- 二级用户只能给直属下级用户补量
- 三级用户无后台补量权限

## 核心接口

- `POST /api/v1/cards/batch/add-flow-by-iccids`
- `POST /api/v1/cards/batch/resume-by-iccids`
- `POST /api/v1/cards/batch/force-resume-by-iccids`
- `POST /api/v1/pools/{pool_id}/recharge`
- `GET /api/v1/system/logs/operation?module=cards&action=add_flow&target_type=card&target_id=xxx`
- `GET /api/v1/system/logs/operation?module=pools&action=add_flow&target_type=pool&target_id=xxx`

## 重点回归

### 停复机

- 人工停卡卡片点击普通复机，前端应提示不可复机
- 到期停卡卡片点击普通复机，前端应提示先续费
- 单卡超量卡片未补量前点击复机，应失败
- 单卡超量卡片补量后点击复机，应成功
- 流量池超量卡片在池未补量前点击复机，应失败
- 流量池补量后，池内 `pool_exceed` 卡片应自动恢复
- 超级管理员可见并可用“强制复机”

### 补量

- 单卡列表批量补量成功后，返回成功/失败/自动复机数量
- 单卡详情补量成功后，详情页状态和日志应刷新
- 流量池列表补量成功后，返回自动复机数量
- 流量池详情补量成功后，池内停卡卡片状态应刷新
- 流量池卡走单卡补量，应被拦截

### 日志

- 单卡补量后，卡片详情页补量日志可按当前卡片查到记录
- 流量池补量后，流量池详情页补量日志可按当前流量池查到记录
- 日志中应包含补量备注和自动复机数量信息

### 权限

- 超管可给任意可见用户补量
- 二级用户只能给直属下级用户补量
- 三级用户无补量入口且接口调用应失败
- 强制复机仅超级管理员可用

## 已补测试

- 服务层测试：
  - [test_flow_adjustment_services.py](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/tests/test_services/test_flow_adjustment_services.py)
- 接口层测试：
  - [test_flow_adjustment_api.py](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/tests/test_api/test_flow_adjustment_api.py)

说明：

- 当前仓库已声明 `pytest` 和 `pytest-asyncio`
- 本机执行环境未安装 pytest，因此本次无法直接跑测试
- 语法校验已通过，前端全量 `npm run build` 已通过

## 构建验证

- 后端：关键改动文件已通过 `py_compile`
- 前端：`npm run build` 成功

## 上线注意

- 当前前端构建仍会提示 Sass `@import` 废弃告警，不影响发布
- 当前前端构建仍会提示部分 chunk 体积较大，不影响发布
- 建议上线后重点抽查：
  - 人工停卡不能普通复机
  - 池超量补量后自动复机
  - 卡片详情/流量池详情补量日志展示
  - 二级用户给非直属客户补量时被正确拦截

## 二期边界

本期不包含：

- 下级用户自助购买单卡流量
- 下级用户自助购买流量池加油包
- 下级用户到期续费支付
- 商品、订单、支付回调链路

二期建议在本期能力基础上继续扩展商品化购买流程。
