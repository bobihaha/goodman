# 账号专属 H5 自助服务方案

## 1. 目标

在现有物联网卡平台基础上，为每个二级用户自动生成一个专属 H5 访问地址，终端客户可通过该地址完成以下操作：

- 输入卡号/ICCID 查询卡信息
- 查看套餐、状态、用量、最近使用情况
- 查看智能诊断结果
- 执行停机/复机
- 查看账号品牌信息、客服信息、公告文案

本方案基于当前项目已有能力设计：

- 后端已存在 `sys_user` 多级账号体系
- 后端已存在卡片列表、卡诊断、批量停机/复机等接口
- 前端为 Vue 3 + Vite 单页应用
- 生产部署已有 `Nginx + frontend + backend` 拓扑

## 2. 实现思路

不要为每个账号单独部署一套 H5 前端。

推荐方案：

- 全平台共用一套 H5 页面
- 每个账号生成一个唯一访问地址
- H5 页面通过地址中的 `slug` 或 `token` 识别所属账号
- 页面加载该账号的专属配置
- 终端用户只能查询该账号名下的卡

示例地址：

- `https://card.xxx.com/h5/u8k3p9x2`
- `https://card.xxx.com/h5/tenant/u8k3p9x2`
- `https://abc.card.xxx.com`

优点：

- 前后端只维护一套代码
- 生成链接快，用户管理里即可启用
- 后续改样式、加功能，一次发布全生效
- 可以逐步扩展到品牌定制、二级域名、短信验证

## 3. 账号与链接关系

建议一条账号只对应一条当前生效的主 H5 地址，同时允许重置。

### 3.1 适用对象

首期建议只给 `user_level = 2` 的二级用户生成 H5。

原因：

- 二级用户通常代表外部客户/代理主体
- 卡资源归属更稳定
- 权限边界更清晰

如果后续要给三级子用户独立生成 H5，可在二期扩展。

### 3.2 地址标识规则

建议使用不可枚举的随机 `slug`，长度 8 到 16 位。

示例：

- `4gK8mP2x`
- `u_7d9Qa3Lm`

生成规则建议：

- 使用随机字符串，不使用自增 ID
- 重置地址时生成新 `slug`
- 原地址立即失效
- 后台保留重置时间和操作人

## 4. 数据库设计

当前账号主体是 `sys_users`，建议不要新建独立账号表，直接在现有用户体系上扩展。

### 4.1 方案 A：直接给 `sys_users` 扩字段

适合首版快速上线。

建议新增字段：

- `h5_enabled` `TINYINT(1)` 是否启用 H5，默认 `0`
- `h5_slug` `VARCHAR(32)` H5 专属地址标识，唯一索引
- `h5_title` `VARCHAR(100)` H5 标题
- `h5_logo` `VARCHAR(255)` Logo 地址
- `h5_banner` `VARCHAR(255)` 顶部横幅图
- `h5_notice` `VARCHAR(500)` 公告文案
- `h5_contact_phone` `VARCHAR(30)` 客服电话
- `h5_contact_wechat` `VARCHAR(50)` 客服微信
- `h5_theme` `JSON` 主题配置
- `h5_allow_stop` `TINYINT(1)` 是否允许停机
- `h5_allow_resume` `TINYINT(1)` 是否允许复机
- `h5_require_sms_verify` `TINYINT(1)` 是否要求短信验证
- `h5_query_limit_per_day` `INT` 每日查询限额
- `h5_status` `VARCHAR(20)` 链接状态，建议值：`enabled/disabled/expired`
- `h5_last_reset_at` `DATETIME` 最近重置时间

### 4.2 方案 B：新增 `user_h5_configs` 表

适合后续做品牌模板、多域名、多链接管理。

建议字段：

- `id`
- `user_id`
- `slug`
- `domain`
- `title`
- `logo`
- `banner`
- `notice`
- `contact_phone`
- `contact_wechat`
- `theme_config`
- `allow_stop`
- `allow_resume`
- `require_sms_verify`
- `query_limit_per_day`
- `status`
- `last_reset_at`
- `created_by`
- `updated_by`
- `created_at`
- `updated_at`

首版建议用方案 A，开发最快。

## 5. 用户管理页面改造

位置：现有 [frontend/src/views/users/index.vue](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/frontend/src/views/users/index.vue)

建议在“操作”列增加 H5 相关按钮：

- `生成H5`
- `复制链接`
- `查看二维码`
- `H5配置`
- `停用链接`
- `重置链接`

建议交互：

### 5.1 未生成时

- 显示 `生成H5`
- 点击后自动生成 `slug` 和默认配置

### 5.2 已生成时

- 显示当前状态：启用/停用
- 可直接复制链接
- 可打开配置弹窗修改标题、Logo、公告、联系方式
- 可重置链接
- 可停用/启用

### 5.3 弹窗字段

- H5标题
- Logo
- 公告文案
- 客服电话
- 客服微信
- 是否允许停机
- 是否允许复机
- 是否需要短信验证
- 页面主题色
- 页面状态

## 6. H5 前端页面结构

建议单独新增一个公开访问路由，不复用后台登录页布局。

建议路由：

- `/h5/:slug`

建议前端目录：

- `frontend/src/views/h5/index.vue`
- `frontend/src/views/h5/components/CardQueryForm.vue`
- `frontend/src/views/h5/components/CardOverview.vue`
- `frontend/src/views/h5/components/CardUsagePanel.vue`
- `frontend/src/views/h5/components/CardDiagnosisPanel.vue`
- `frontend/src/views/h5/components/CardActionPanel.vue`

页面流程：

1. 访问 `/h5/:slug`
2. 根据 `slug` 拉取 H5 配置
3. 展示品牌头图、标题、公告
4. 用户输入卡号/ICCID
5. 后端返回卡信息、用量、诊断结果、可执行操作
6. 用户点击停机/复机
7. 如开启验证，则先短信验证码校验
8. 操作成功后刷新卡状态

页面模块建议：

- 顶部品牌区
- 公告区
- 卡号查询区
- 卡片基础信息区
- 本月用量区
- 智能诊断区
- 停机/复机操作区
- 客服联系方式区

## 7. 智能诊断建议

当前项目已存在卡诊断接口基础，可在 H5 层做“翻译”和“组合判断”。

建议首版诊断输出：

- `正常使用`
- `卡片已停机`
- `卡片未激活`
- `卡片已到期`
- `当月套餐流量已耗尽`
- `近24小时无使用记录`
- `设备疑似离线`
- `运营商状态异常`
- `请检查 APN/设备配置`

建议返回结构：

- `level`: `success/warn/error`
- `title`
- `description`
- `suggestion`
- `can_resume`
- `can_suspend`

首版不需要 AI 模型，规则引擎即可。

## 8. 后端接口设计

现有后台接口多依赖登录态，不适合直接给 H5 使用。建议增加一组公开 H5 接口，并单独做限流和鉴权。

建议前缀：

- `/api/v1/h5`

### 8.1 获取 H5 配置

`GET /api/v1/h5/{slug}/config`

返回：

- 标题
- Logo
- 公告
- 联系方式
- 是否允许停机/复机
- 是否需要验证码

### 8.2 查询卡信息

`POST /api/v1/h5/{slug}/card/query`

请求参数：

- `card_no`
- `captcha_token` 可选

返回：

- 卡片基础信息
- 套餐信息
- 本月用量
- 最近使用时间
- 当前状态
- 诊断结果
- 可执行操作

### 8.3 发送短信验证码

`POST /api/v1/h5/{slug}/sms/send`

请求参数：

- `card_no`
- `phone`
- `biz_type` `suspend/resume`

### 8.4 停机

`POST /api/v1/h5/{slug}/card/suspend`

请求参数：

- `card_no`
- `sms_code` 可选
- `reason`

### 8.5 复机

`POST /api/v1/h5/{slug}/card/resume`

请求参数：

- `card_no`
- `sms_code` 可选

### 8.6 生成/重置 H5 地址

后台管理接口：

- `POST /api/v1/users/{user_id}/h5/generate`
- `PUT /api/v1/users/{user_id}/h5/config`
- `POST /api/v1/users/{user_id}/h5/reset`
- `PUT /api/v1/users/{user_id}/h5/status`
- `GET /api/v1/users/{user_id}/h5/detail`

## 9. 卡查询范围控制

这是最关键的安全点。

H5 查询出的卡必须满足：

- 卡片归属 `user_id` 为当前 `slug` 对应账号
- 或卡片处于该账号可访问范围内

严禁只按卡号查询、不校验归属。

建议复用现有卡服务里的用户范围控制逻辑，不要在 H5 接口里重新写一套松散判断。

## 10. 停机/复机风控建议

如果“只输入卡号就能停机/复机”，风险较高。

建议至少做以下其中两项：

- 图片验证码
- 单 IP 频率限制
- 单卡每日操作次数限制
- 短信验证码
- 最近一次实名手机号校验
- 操作日志审计

建议策略：

- 查询可先放开为“输入卡号即可查”
- 停机/复机必须加验证码

## 11. 域名与部署建议

正式上线建议一定配置域名和 HTTPS。

推荐方式：

- 主后台：`https://admin.xxx.com`
- 客户 H5：`https://card.xxx.com/h5/{slug}`

首版不建议给每个用户分配独立子域名，原因是：

- Nginx 配置更简单
- 证书更简单
- 生成链接即可使用
- 不影响后续升级到二级域名

当前项目已有 Nginx 反代结构，可直接复用，只需保证：

- 前端路由支持 `/h5/:slug`
- `/api/v1/h5/*` 走后端
- 开启 HTTPS

## 12. 页面原型流程

### 12.1 后台操作流程

1. 管理员进入客户管理
2. 选择某个二级用户
3. 点击 `生成H5`
4. 系统创建 `slug` 和默认配置
5. 后台展示完整链接和二维码
6. 管理员复制给客户

### 12.2 终端用户流程

1. 打开专属 H5 地址
2. 输入卡号/ICCID
3. 查看卡信息、套餐、用量、诊断
4. 如需要停机/复机，点击对应按钮
5. 完成验证码校验
6. 操作成功并刷新状态

## 13. 开发拆分建议

### 第一阶段：最小可用版本

- 账号生成专属 H5 地址
- H5 品牌配置
- 卡号查询
- 用量展示
- 规则诊断
- 停机/复机
- 操作日志

### 第二阶段：增强版本

- 短信验证码
- 二维码
- 自定义主题
- 查询频控
- 操作频控
- 链接失效时间
- 多公告配置

### 第三阶段：SaaS 化

- 独立二级域名
- 多套模板主题
- 自定义备案域名
- 多链接管理
- 访问统计和转化统计

## 14. 开发工期预估

基于当前项目已有卡管理能力，预估如下：

- 最小可用版：5 到 8 个工作日
- 含短信验证和二维码：8 到 12 个工作日
- 含品牌定制和多域名：2 到 3 周

前提：

- 现有卡查询、卡状态、停复机接口可直接复用
- 供应商侧调用链稳定
- 不新增复杂审批流

## 15. 推荐落地方案

建议按下面方式开工：

1. 后端先给 `sys_users` 增加 H5 配置字段
2. 用户管理页新增 `生成H5/复制链接/H5配置/重置链接`
3. 新增公开 H5 路由 `/h5/:slug`
4. 新增 `/api/v1/h5/*` 接口
5. 查询先不强制短信验证
6. 停机/复机必须预留验证码能力

这样改动最小，最贴合你当前项目结构，也最容易尽快上线。

## 16. 与现有项目对应关系

现有可复用模块：

- 用户管理页：[frontend/src/views/users/index.vue](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/frontend/src/views/users/index.vue)
- 用户接口：[app/api/v1/sys_user.py](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/app/api/v1/sys_user.py)
- 用户模型：[app/db/models/sys_user.py](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/app/db/models/sys_user.py)
- 卡接口：[app/api/v1/iot_card.py](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/app/api/v1/iot_card.py)
- 诊断弹窗：[frontend/src/views/cards/list/components/CardDiagnosticsDialog.vue](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/frontend/src/views/cards/list/components/CardDiagnosticsDialog.vue)
- 部署说明：[deploy/README_DEPLOY_ALIYUN.md](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/deploy/README_DEPLOY_ALIYUN.md)

## 17. 结论

这个需求适合做，而且和你现在系统的匹配度很高。

最推荐的落地方式不是“每个账号一套独立 H5 程序”，而是：

- 一套统一 H5
- 每个账号一个专属随机地址
- 后台用户管理里生成、配置、复制、重置
- H5 只展示和操作该账号名下的卡

这样开发快、维护轻、后续扩展也顺。
