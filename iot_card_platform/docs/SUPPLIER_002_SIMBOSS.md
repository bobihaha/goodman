# 供应商 002：SIMBOSS 对接说明

## 接入原则

- 供应商编码 `002` 固定走 SIMBOSS 独立客户端。
- 已有 LX/UPIOT 客户端不改协议实现，避免影响线上客户。
- 客户端分发优先按 `suppliers.code` 判断，其次才按 `api_url` 兜底识别。

## 环境变量

生产环境通过 `.env.production` 或部署平台环境变量配置：

```env
SIMBOSS_API_URL=https://api.simboss.com
SIMBOSS_APPID=...
SIMBOSS_APP_SECRET=...
SIMBOSS_TEST_ICCID=...
```

供应商表也可以配置 `api_url`、`api_key`、`api_secret`，其中 `api_key` 对应 SIMBOSS `appid`，`api_secret` 对应 `AppSecret`。如果供应商编码为 `002` 且数据库字段为空，会回退读取环境变量。

## 已适配接口

| 系统能力 | SIMBOSS 接口 | 说明 |
| --- | --- | --- |
| 单卡用量 | `/2.0/device/detail` | `dataUsage` 映射本月用量，`usedDataVolume` 映射套餐用量 |
| 批量用量 | `/2.0/device/detail/batch` | 单批最多 100 张，客户端自动分片 |
| 单卡生命周期 | `/2.0/device/detail` | 映射测试期、激活日、到期日、状态 |
| 批量生命周期 | `/2.0/device/detail/batch` | 与批量用量共用详情接口 |
| 流量池卡开关网络 | `/2.0/device/modifyDeviceStatus` | 仅对系统 `card_type=pool` 的 SIMBOSS 卡调用；开：`ACTIVATED_NAME`，关：`DEACTIVATED_NAME` |
| 强制激活 | `/2.0/device/activate` | 文档说明需要联系客服开放权限 |
| IMEI 查询 | `/2.0/device/queryNum` | 配合详情中的 `imeiStatus` 判断机卡分离 |
| 流量池列表/用量 | `/2.0/card/pool/list` | 返回供应商侧流量池总量、用量、剩余量、卡数 |
| 流量池详情 | `/2.0/card/pool/detail` | 通过 `iccid`/`imsi`/`msisdn` 查询该卡所在流量池 |

## 状态映射

| SIMBOSS 状态 | 系统状态 |
| --- | --- |
| `testing` | `testing` |
| `inventory` | `silent` |
| `activation` | `activated` |
| `deactivation` | `suspended` |
| `retired` | `cancelled` |

## 停复机说明

SIMBOSS 文档中 `/2.0/device/modifyDeviceStatus` 标题为“流量池卡开关网络”。系统侧已限制：供应商编码为 `002` 时，只有流量池卡会向 SIMBOSS 发起网络关停/恢复请求；单卡不会调用该接口，避免把“流量池卡网络开关”误当成通用停复机能力。

## 验证记录

- 单元测试：`tests/test_services/test_simboss_client.py`
- 回归测试：`tests/test_services/test_upiot_client.py`
- 只读联调：测试 ICCID 可查询用量与生命周期，未执行停复机写操作。
