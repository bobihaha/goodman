# 数据库迁移规范

这份文档用于约束本项目的数据库变更方式，覆盖开发期、测试期和发布期。目标是减少“脚本分散、命名不统一、上线临时写 SQL、回滚不可控”这几类常见风险。

如果你要上线生产变更，除了看本规范，也必须同时看 [数据库迁移 SOP](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/docs/DEPLOYMENT_MIGRATION_SOP.md)。

## 1. 适用范围

本规范适用于以下变更：

- 新表、新字段、新索引
- 默认值调整
- 历史数据修复
- 唯一约束补充
- 与业务功能配套的数据初始化

以下操作默认视为高风险，不能按普通变更直接执行：

- 删除字段
- 修改字段类型
- 修改唯一约束
- 大表全量回填
- 大量历史数据清洗

## 2. 当前项目现状

仓库里与数据库相关的脚本主要分成三类：

- `app/db/migrations/`
  - 推荐作为后续正式增量迁移目录
  - 新功能发布优先放这里
- `scripts/`
  - 初始化、修复、辅助执行脚本
  - 例如 `scripts/run_migration.py`
- `sql/`
  - 历史 SQL、一次性脚本、临时修复脚本
  - 不应默认视为“可直接上线”

结论：

- 新增迁移文件统一放 `app/db/migrations/`
- 历史 `sql/` 和 `scripts/*.sql` 只作为参考，不直接复用到新发布

## 3. 目录与命名规范

### 推荐命名

统一采用：

```text
app/db/migrations/YYYYMMDD_<action>_<target>.sql
```

示例：

```text
app/db/migrations/20260403_add_project_owner_fields.sql
app/db/migrations/20260403_fix_stock_record_indexes.sql
app/db/migrations/20260403_backfill_card_usage_history.sql
```

### 命名要求

- 日期使用 `YYYYMMDD`
- 动作用英文动词开头，如 `add`、`fix`、`backfill`、`create`
- 目标名称简短明确，不要写成 `update_some_fields_final_v2.sql`
- 一个文件只做一个发布目标，不要把多件不相关的事情塞进同一个脚本

## 4. 迁移脚本分类建议

### 结构变更脚本

用于：

- 建表
- 加字段
- 加索引
- 加约束

建议命名：

```text
YYYYMMDD_add_xxx.sql
YYYYMMDD_create_xxx.sql
```

### 数据修复脚本

用于：

- 历史数据回填
- 脏数据修复
- 状态纠正

建议命名：

```text
YYYYMMDD_backfill_xxx.sql
YYYYMMDD_fix_xxx_data.sql
```

### 校验脚本

用于：

- 发布前后核对数量
- 检查重复数据
- 检查空值、非法值

建议命名：

```text
YYYYMMDD_verify_xxx.sql
```

### 推荐拆分方式

同一批发布如果同时涉及结构和数据，建议最少拆成：

```text
app/db/migrations/20260403_add_xxx_schema.sql
app/db/migrations/20260403_backfill_xxx_data.sql
app/db/migrations/20260403_verify_xxx.sql
```

## 5. 编写原则

### 基本原则

- 先兼容，后切换，最后清理
- 先结构，后数据
- 先测试库，后生产库
- 先备份，后执行
- 优先让旧代码与新结构短期兼容

### 幂等性要求

尽量让脚本可重复执行，至少要做到“重复执行时能明确失败原因，而不是留下半成品”。

推荐做法：

- `ADD COLUMN` 前先确认字段是否已存在
- 新增索引前先确认索引是否已存在
- 回填数据时增加明确条件，避免重复覆盖
- 初始化数据时用唯一键或存在性判断保护

### 禁止事项

- 禁止把历史无关 SQL 拼进本次发布脚本
- 禁止在生产环境现场临时手写结构变更 SQL
- 禁止把删字段、改类型、回填大表混在一个脚本里
- 禁止在没有验证脚本的情况下上线高影响数据修复

## 6. 推荐变更模式

### 模式 1：新增字段

适合：

- 新功能字段
- 新状态字段
- 新配置字段

建议流程：

1. 先加可空字段或安全默认值字段
2. 应用代码兼容新旧状态
3. 如有需要再补历史回填
4. 观察稳定后再考虑收紧约束

### 模式 2：新增唯一约束

建议流程：

1. 先写重复数据检查 SQL
2. 清理冲突数据
3. 在测试库验证无冲突
4. 再加唯一索引

### 模式 3：字段替换

不要一步到位删旧字段，建议两次发布：

第一次发布：

- 新增新字段
- 回填新字段
- 应用读取切换到新字段

第二次发布：

- 观察确认无旧逻辑依赖
- 再删除旧字段

### 模式 4：大表回填

建议：

- 按主键或时间范围分批
- 每批有清晰范围
- 避免单条 SQL 更新整张表
- 上线前预估执行耗时

## 7. 脚本内容模板

### 7.1 结构变更模板

```sql
-- 变更目标：为 iot_cards 增加示例字段
-- 风险级别：低
-- 执行前提：确认字段不存在

ALTER TABLE iot_cards
ADD COLUMN example_flag TINYINT NOT NULL DEFAULT 0 COMMENT '示例字段';

CREATE INDEX idx_iot_cards_example_flag ON iot_cards(example_flag);
```

### 7.2 数据回填模板

```sql
-- 变更目标：回填 example_flag
-- 风险级别：中
-- 执行前提：字段已存在

UPDATE iot_cards
SET example_flag = 1
WHERE example_flag = 0
  AND status = 'activated';
```

### 7.3 校验模板

```sql
-- 校验字段是否存在
SHOW COLUMNS FROM iot_cards LIKE 'example_flag';

-- 校验索引是否存在
SHOW INDEX FROM iot_cards WHERE Key_name = 'idx_iot_cards_example_flag';

-- 校验回填结果
SELECT status, example_flag, COUNT(*) AS total
FROM iot_cards
GROUP BY status, example_flag
ORDER BY status, example_flag;
```

## 8. 开发流程

### Step 1：先确认变更类型

提交 SQL 前先回答这几个问题：

- 这是结构变更还是数据修复
- 是否影响已有代码兼容
- 是否需要前后端同时发版
- 是否需要历史数据回填
- 是否可能锁表或长时间执行

### Step 2：全文检索影响范围

尤其是新增或修改字段时，先检索：

- `app/db/models/`
- `app/schemas/`
- `app/crud/`
- `app/services/`
- `app/api/v1/`
- `frontend/src/api/modules/`
- `frontend/src/views/`

避免只改数据库不改模型，或只改后端不改前端。

### Step 3：补齐代码层对应修改

常见需要同步修改的位置：

- ORM 模型
- Schema
- CRUD 查询条件
- Service 业务逻辑
- API 请求/响应字段
- 前端类型定义与页面展示

## 9. 本地与测试环境执行

仓库内提供了执行脚本：

```bash
python scripts/run_migration.py app/db/migrations/xxx.sql
```

### 使用前注意

- 该脚本依赖当前应用数据库配置
- 默认连接的是应用 `.env` 指向的数据库
- 执行前必须确认自己连接的是正确环境

### 推荐顺序

1. 先备份测试库
2. 执行结构脚本
3. 执行数据脚本
4. 执行校验 SQL
5. 启动后端并做接口验证
6. 启动前端并做页面验证

## 10. 发布前检查

发布前至少确认：

- SQL 文件放在 `app/db/migrations/`
- 文件命名符合规范
- 已标记结构脚本、数据脚本、校验脚本
- 已在测试环境完整执行
- 已确认是否幂等
- 已确认高风险操作的回滚策略
- 已确认需要观察的核心表和关键接口

## 11. 生产执行约束

生产执行时，以 [数据库迁移 SOP](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/docs/DEPLOYMENT_MIGRATION_SOP.md) 为准，这里只补充项目内约束：

- 只能执行本次发布确认过的脚本
- 不要临时复用 `sql/` 目录里的旧脚本
- 高风险变更必须安排低峰窗口
- 后端上线后要重点关注定时任务是否异常或重复执行
- 如果数据库结构已变更但应用异常，优先考虑应用回滚而不是现场硬回滚 DDL

## 12. 推荐发布包结构

若某次发布涉及数据库，建议在发布说明中明确列出：

```text
release/
├── app/db/migrations/20260403_add_xxx_schema.sql
├── app/db/migrations/20260403_backfill_xxx_data.sql
├── app/db/migrations/20260403_verify_xxx.sql
└── docs/release_notes_xxx.md
```

发布说明里至少写清楚：

- 变更目标
- 影响表
- 执行顺序
- 回滚思路
- 验证方式

## 13. 与现有文档的关系

- 本文档：
  - 解决“平时应该怎么写迁移”
  - 面向开发与维护
- [数据库迁移 SOP](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/docs/DEPLOYMENT_MIGRATION_SOP.md)
  - 解决“生产发布当天怎么执行迁移”
  - 面向发布执行
- [稳定发布 Runbook](/Users/renhui/Documents/GitHub/goodman/iot_card_platform/docs/STABLE_RELEASE_RUNBOOK.md)
  - 解决“整次上线怎么走流程”
  - 面向整体发布

## 14. 维护建议

后续如果继续演进，建议把数据库迁移机制再往前推进一步：

- 引入统一迁移台账，记录每次已执行脚本
- 给高频核心表补一份“索引与热点 SQL”说明
- 对 `scripts/run_migration.py` 增加环境确认和执行日志能力
- 逐步减少 `sql/` 目录里不可追踪的一次性脚本
