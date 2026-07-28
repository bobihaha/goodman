# 账号专属 H5 自助服务方案（优化版）

## 1. 需求目标

在现有物联网卡平台基础上，为每个二级用户自动生成一个专属 H5 访问地址，终端客户打开后可完成以下操作：

- 输入卡号 / ICCID 查询卡信息
- 支持输入后 6 位数字模糊查询
- 查看套餐、状态、用量、最近使用情况
- 查看激活时间、到期时间
- 查看智能诊断结果
- 执行停机 / 复机
- 查看账号品牌信息、客服信息、公告文案
- 填写备注，且备注同步回 Web 端

本方案按当前项目现状设计，尽量复用现有能力：

- 账号体系使用 `sys_users`
- 卡数据、套餐、用量、激活时间、到期时间、备注字段已存在
- 卡诊断、停机、复机已有后端基础能力
- 后台前端为 Vue 3，后端为 FastAPI

## 2. 核心设计结论

不建议为每个账号单独部署一套 H5 前端。

最优方案是：

- 全平台共用一套 H5 页面
- 每个二级用户生成一个随机专属地址
- 通过地址中的 `slug` 识别所属账号
- H5 页面动态加载该账号的品牌配置
- 查询和操作仅作用于该账号名下的卡

推荐地址格式：

- `https://card.xxx.com/h5/8F2kLmQx`

这样做的好处：

- 开发快
- 维护成本低
- 用户管理里可以直接生成、重置、停用
- 后续加品牌模板、二维码、验证码也方便

## 3. 适用账号范围

首版建议只给 `user_level = 2` 的二级用户生成专属 H5。

原因：

- 二级用户通常是客户主体或代理主体
- 卡资源归属更稳定
- 权限边界更清晰
- 后续如有需要，再扩展支持三级子用户

## 4. 优化后的业务范围

### 4.1 查询规则

H5 查询支持 3 种方式：

- 输入完整 ICCID
- 输入完整卡号
- 输入后 6 位数字模糊查询

其中“后 6 位查询”要特别处理：

- 若只匹配 1 张卡，直接进入详情结果
- 若匹配多张卡，先展示候选卡列表，供用户二次选择
- 候选列表要隐藏部分敏感信息，例如只显示 `ICCID后4位`、状态、套餐、激活时间

不建议“输入 6 位后直接展示全部完整卡信息”，这样容易造成误查和信息外泄。

### 4.2 H5 展示内容

查询成功后建议展示以下信息：

- ICCID
- 卡号
- 当前状态
- 套餐名称 / 套餐规格
- 套餐总量
- 本月已用
- 剩余流量
- 使用率
- 最近使用时间
- 激活时间
- 到期时间
- 当前备注
- 智能诊断结果
- 是否允许停机 / 复机

### 4.3 H5 可操作内容

- 停机
- 复机
- 新增备注 / 修改备注

备注要求：

- 终端客户在 H5 填写或修改备注
- 备注直接写入现有卡片备注字段
- Web 端卡列表、卡详情页同步可见
- 需要记录备注修改日志

## 5. 查询与交互流程

### 5.1 单卡直达流程

1. 用户打开专属 H5 地址
2. 页面展示品牌信息、公告、客服信息
3. 用户输入卡号 / ICCID / 后 6 位
4. 系统查询该账号可见范围内的卡
5. 若唯一匹配，直接展示卡详情
6. 用户查看信息、诊断结果
7. 用户可执行停机、复机、备注

### 5.2 多卡候选流程

1. 用户输入后 6 位数字
2. 系统匹配出多张卡
3. 页面展示候选列表
4. 用户点击具体卡片
5. 进入单卡详情页

### 5.3 停复机流程

1. 用户在详情页点击停机或复机
2. 系统校验该账号 H5 是否允许该操作
3. 如启用了验证码，先完成校验
4. 调用停机 / 复机接口
5. 成功后刷新卡状态与诊断结果

### 5.4 备注流程

1. 用户在详情页点击“备注”
2. 填写备注内容
3. 提交后更新卡片 `remark`
4. H5 端即时展示新备注
5. Web 端卡片列表和详情同步展示

## 6. 数据库设计

### 6.1 账号 H5 配置

首版建议直接在 `sys_users` 上扩字段。

建议新增字段：

- `h5_enabled` `TINYINT(1)` 是否启用
- `h5_slug` `VARCHAR(32)` 专属地址标识，唯一索引
- `h5_title` `VARCHAR(100)` H5 标题
- `h5_logo` `VARCHAR(255)` Logo 地址
- `h5_banner` `VARCHAR(255)` 顶部横幅图
- `h5_notice` `VARCHAR(1000)` 公告文案
- `h5_contact_phone` `VARCHAR(30)` 客服电话
- `h5_contact_wechat` `VARCHAR(50)` 客服微信
- `h5_theme` `JSON` 主题配置
- `h5_allow_suspend` `TINYINT(1)` 是否允许停机
- `h5_allow_resume` `TINYINT(1)` 是否允许复机
- `h5_allow_remark` `TINYINT(1)` 是否允许备注
- `h5_require_verify` `TINYINT(1)` 是否要求验证码
- `h5_status` `VARCHAR(20)` `enabled/disabled/expired`
- `h5_last_reset_at` `DATETIME` 最近重置时间

### 6.2 备注日志表

因为备注需要从 H5 同步回 Web，建议增加专门日志表，便于审计。

建议新增表：`card_h5_remark_logs`

建议字段：

- `id`
- `user_id` 二级用户 ID
- `card_id`
- `iccid`
- `old_remark`
- `new_remark`
- `source` 固定值 `h5`
- `operator_name` H5 端填写人，可选
- `operator_phone` 可选
- `client_ip`
- `created_at`

如果首版想快一点，也可以先复用现有操作日志体系，但建议至少保留“来源是 H5”的标识。

## 7. 用户管理页面改造

位置：
[frontend/src/views/users/index.vue](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/frontend/src/views/users/index.vue)

建议在“操作”列增加 H5 相关能力：

- `生成H5`
- `复制链接`
- `查看二维码`
- `H5配置`
- `重置链接`
- `停用链接`

### 7.1 H5 配置弹窗字段

- H5 标题
- Logo
- 顶部横幅图
- 公告文案
- 客服电话
- 客服微信
- 是否允许停机
- 是否允许复机
- 是否允许备注
- 是否需要验证码
- 页面主题色
- 页面状态

### 7.2 用户管理页展示字段

建议在用户列表增加一列或悬浮信息：

- H5 状态
- H5 地址
- 最近重置时间

## 8. H5 页面结构

建议新增公开路由：

- `/h5/:slug`

建议页面结构：

- 顶部品牌区
- 公告区
- 查询输入区
- 候选卡列表区
- 卡片详情区
- 智能诊断区
- 操作区
- 客服信息区

建议前端目录：

- `frontend/src/views/h5/index.vue`
- `frontend/src/views/h5/components/H5Header.vue`
- `frontend/src/views/h5/components/H5Notice.vue`
- `frontend/src/views/h5/components/CardSearchForm.vue`
- `frontend/src/views/h5/components/CardCandidateList.vue`
- `frontend/src/views/h5/components/CardInfoPanel.vue`
- `frontend/src/views/h5/components/CardDiagnosisPanel.vue`
- `frontend/src/views/h5/components/CardActionPanel.vue`
- `frontend/src/views/h5/components/CardRemarkDialog.vue`

### 8.1 H5 加载性能约束

- H5 公开路由使用独立轻量启动链路，不预加载后台主布局、登录态恢复、完整 Element Plus 和全量图标。
- H5 只注册首屏实际使用的组件与样式，后台完整依赖在非 H5 路由按需加载。
- `index.html` 保持不缓存，带内容哈希的 `/assets/` 静态资源缓存一年并标记为 `immutable`。
- 生产构建验收目标：公共入口不超过 60 KB gzip，H5 首屏本地静态资源总量不超过 180 KB gzip（不含接口数据和业务图片）。

## 9. H5 页面信息结构建议

### 9.1 顶部品牌区

展示：

- Logo
- 账号品牌名称
- 一句品牌说明

### 9.2 公告区

展示：

- 平台公告文案
- 特殊服务时间说明
- 客服提示

### 9.3 卡片详情区

展示：

- ICCID
- 卡号
- 套餐规格
- 当前状态
- 本月已用
- 套餐总量
- 剩余流量
- 使用率
- 最近使用时间
- 激活时间
- 到期时间
- 当前备注

### 9.4 操作区

根据配置动态展示：

- 停机按钮
- 复机按钮
- 备注按钮

## 10. 智能诊断建议

首版不需要大模型，建议规则诊断即可。

建议输出结构：

- `level`: `success / warn / error`
- `title`
- `description`
- `suggestion`
- `can_suspend`
- `can_resume`

建议诊断项：

- 卡片正常使用
- 卡片已停机
- 卡片未激活
- 卡片已到期
- 当月流量耗尽
- 使用率过高
- 长时间未使用
- 设备疑似离线
- 运营商状态异常
- 建议检查 APN / 设备配置

## 11. 后端接口设计

现有后台接口偏登录态管理，不适合直接暴露给 H5。建议单独增加一组 H5 专用接口。

建议前缀：

- `/api/v1/h5`

### 11.1 获取 H5 配置

`GET /api/v1/h5/{slug}/config`

返回：

- 标题
- Logo
- 横幅图
- 公告文案
- 客服电话
- 客服微信
- 是否允许停机
- 是否允许复机
- 是否允许备注
- 是否需要验证码

### 11.2 查询卡

`POST /api/v1/h5/{slug}/card/query`

请求参数：

- `keyword`

返回结构建议：

- `match_type`: `exact / fuzzy_single / fuzzy_multiple / none`
- `items`

其中：

- 完整匹配时，`items` 返回 1 条完整卡详情
- 后 6 位多条匹配时，`items` 返回候选卡简要信息列表

### 11.3 查询单卡详情

`GET /api/v1/h5/{slug}/card/{card_id}`

返回：

- 卡基础信息
- 套餐信息
- 用量信息
- 最近使用时间
- 激活时间
- 到期时间
- 当前备注
- 诊断结果
- 可执行动作

### 11.4 停机

`POST /api/v1/h5/{slug}/card/{card_id}/suspend`

请求参数：

- `reason`
- `verify_code` 可选

### 11.5 复机

`POST /api/v1/h5/{slug}/card/{card_id}/resume`

请求参数：

- `verify_code` 可选

### 11.6 修改备注

`PUT /api/v1/h5/{slug}/card/{card_id}/remark`

请求参数：

- `remark`
- `operator_name` 可选
- `operator_phone` 可选

说明：

- 更新卡片备注字段
- 记录 H5 备注日志
- Web 端卡列表和详情页同步可见

### 11.7 用户管理侧 H5 接口

- `POST /api/v1/users/{user_id}/h5/generate`
- `GET /api/v1/users/{user_id}/h5/detail`
- `PUT /api/v1/users/{user_id}/h5/config`
- `POST /api/v1/users/{user_id}/h5/reset`
- `PUT /api/v1/users/{user_id}/h5/status`

## 12. 查询匹配规则

建议采用以下逻辑：

### 12.1 输入完整 ICCID

- 精确匹配该账号名下卡片

### 12.2 输入完整卡号

- 精确匹配该账号名下卡片

### 12.3 输入纯数字且长度为 6

- 先按 ICCID 后 6 位匹配
- 再按卡号后 6 位匹配
- 合并去重
- 若多条命中，返回候选列表

### 12.4 非法输入

- 长度不足
- 含非法字符
- 超出可接受长度

直接返回友好错误提示。

## 13. 安全与权限控制

这是该需求最关键的部分。

### 13.1 卡范围限制

H5 查询和操作必须满足：

- `slug` 对应一个二级用户
- 卡片必须属于该二级用户可见范围

严禁出现“知道卡号就能跨账号查询”的情况。

### 13.2 停复机权限

是否允许停机 / 复机，由账号 H5 配置决定。

### 13.3 备注权限

是否允许修改备注，也由账号 H5 配置决定。

### 13.4 风控建议

建议至少做：

- 图片验证码或行为验证码
- 单 IP 频率限制
- 单卡每日操作次数限制
- 停复机操作日志
- 备注修改日志

H5 停机、复机和重启必须写入用户侧系统操作日志，并满足：

- 日志来源标记为 `h5`，记录卡片、H5 所属账号、供应商操作单号和当前处理状态。
- 重启按一个逻辑操作展示，同时保留停机、复机两个供应商阶段。
- 供应商确认成功或失败后回写最终结果；不能只记录“请求已提交”。
- 同一卡片存在同类处理中请求时返回原操作，不重复向供应商提交。
- 前端等待时间必须覆盖后端自动对账窗口，超时后明确提示仍在处理中，不能误报成功。

建议策略：

- 查询可以先尽量简化
- 停机 / 复机 / 备注建议做频控

## 14. 与 Web 端同步要求

备注同步是这次优化需求的重点。

同步目标：

- H5 修改备注后，Web 端卡列表备注字段同步更新
- H5 修改备注后，Web 端卡详情备注字段同步更新
- Web 端修改备注后，H5 再次查询时也能看到最新值

即：

- 不是单独存一份“H5备注”
- 而是直接共用现有卡片 `remark` 字段

这样最清晰，也最不容易产生双份数据冲突。

## 15. 域名与上线建议

正式上线建议配置域名和 HTTPS。

推荐方式：

- 后台：`https://admin.xxx.com`
- H5：`https://card.xxx.com/h5/{slug}`

不建议首版做每个用户一个独立二级域名，先用统一主域名加路径最稳妥。

## 16. 开发拆分建议

### 第一阶段：最小可用版本

- 生成用户专属 H5 地址
- H5 配置管理
- 输入卡号 / ICCID / 后 6 位查询
- 多候选卡选择
- 展示套餐、状态、用量、最近使用
- 展示激活时间、到期时间
- 展示公告、品牌、客服信息
- 停机 / 复机
- 备注写回 Web

### 第二阶段：增强版本

- 二维码
- 验证码
- 频控
- 操作日志查询
- 主题模板

### 第三阶段：SaaS 化

- 多模板品牌化
- 独立二级域名
- 访问统计
- 自助配置更多展示字段

## 17. 预估工期

基于当前项目已有能力，预估如下：

- 最小可用版：6 到 10 个工作日
- 加验证码、二维码、频控：10 到 14 个工作日
- 做强品牌化和 SaaS 化：2 到 3 周

## 18. 推荐实施顺序

建议按以下顺序落地：

1. 给 `sys_users` 增加 H5 配置字段
2. 增加 H5 后端接口
3. 增加 H5 查询匹配规则，支持后 6 位模糊查询
4. 增加备注写回与备注日志
5. 改用户管理页，支持生成 / 配置 / 重置 H5
6. 增加前端公开 H5 页面

## 19. 与当前项目的对应关系

可复用位置：

- 用户管理页：[frontend/src/views/users/index.vue](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/frontend/src/views/users/index.vue)
- 用户接口：[app/api/v1/sys_user.py](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/app/api/v1/sys_user.py)
- 用户模型：[app/db/models/sys_user.py](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/app/db/models/sys_user.py)
- 卡接口：[app/api/v1/iot_card.py](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/app/api/v1/iot_card.py)
- 卡字段定义：[app/schemas/iot_card.py](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/app/schemas/iot_card.py)
- 卡类型定义：[frontend/src/types/card.d.ts](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/frontend/src/types/card.d.ts)
- 卡列表页：[frontend/src/views/cards/list/index.vue](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/frontend/src/views/cards/list/index.vue)
- 卡详情页：[frontend/src/views/cards/detail/index.vue](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/frontend/src/views/cards/detail/index.vue)

## 20. 最终结论

这次优化后的需求依然很适合做，而且和当前系统的匹配度更高了。

最推荐的落地方式是：

- 一套统一 H5
- 每个二级用户一个随机专属地址
- 支持完整卡号 / ICCID / 后 6 位模糊查询
- 查询结果支持候选卡选择
- 展示套餐、状态、用量、最近使用、激活时间、到期时间
- 展示品牌、客服、公告
- 支持停机、复机、备注
- 备注直接同步到现有 Web 端卡片备注字段

这是开发成本、上线速度、后期维护之间最平衡的方案。
