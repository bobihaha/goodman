# 套餐管理模块 - 完整使用指南

## ✅ 已完成的工作

### 1. 前后端字段对齐
已将前端字段名称完全对齐到后端API：

| 功能 | 前端字段（旧） | 后端字段 | 状态 |
|------|--------------|---------|------|
| 套餐标识 | `package_id` | `code` | ✅ 已修复 |
| 有效天数 | `valid_days` | `effective_days` | ✅ 已修复 |
| 成本价 | `cost_price` | `price_cost` | ✅ 已修复 |
| 销售价 | `sale_price` | `price_sale` | ✅ 已修复 |
| 关联套餐 | `supplier_package_id` | `base_package_id` | ✅ 已修复 |

### 2. 修复的问题

#### 问题1: 菜单图标报错
**错误信息**：
```
Slot "default" invoked outside of the render function
```

**原因**：`<el-icon>` 和 `<component :is="...">` 在同一行导致 Vue 响应式系统问题

**解决方案**：
```vue
<!-- 修复前 -->
<el-icon><component :is="item.icon" /></el-icon>

<!-- 修复后 -->
<el-icon>
  <component :is="item.icon" />
</el-icon>
```

#### 问题2: API路径不匹配
**解决方案**：
- 底层套餐：`/api/v1/packages/supplier` ✅
- 销售套餐：`/api/v1/packages/sale` ✅
- 供应商：`/api/v1/suppliers` ✅

#### 问题3: 获取启用列表的API
**问题**：后端没有 `/enabled` 端点

**解决方案**：使用列表接口 + 过滤参数
```typescript
getEnabled(): Promise<SupplierPackage[]> {
  return get<SupplierPackage[]>('/packages/supplier', { 
    params: { status: 'enable', page: 1, page_size: 1000 } 
  }).then(res => res.list || [])
}
```

## 🚀 如何使用

### 步骤1: 确保后端运行
```bash
# 检查后端是否运行
ps aux | grep uvicorn

# 如果没有运行，启动后端
cd /Users/huiren/Documents/goodman/iot_card_platform
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 步骤2: 确保前端运行
```bash
# 检查前端是否运行
lsof -i :3000

# 如果没有运行，启动前端
cd /Users/huiren/Documents/goodman/iot_card_platform/frontend
npm run dev
```

### 步骤3: 访问套餐管理
1. 打开浏览器：`http://localhost:3000`
2. 登录系统
3. 点击侧边栏"套餐管理"
4. 选择"底层套餐"或"销售套餐"

### 步骤4: 创建供应商（如果没有）
**注意**：创建底层套餐前，必须先有供应商数据！

如果数据库中没有供应商，需要先创建：
```sql
-- 在MySQL中执行
INSERT INTO suppliers (name, contact, phone, status, created_at, updated_at) 
VALUES ('测试供应商', '张三', '13800138000', 'enable', NOW(), NOW());
```

或者通过API创建（需要供应商管理模块）。

### 步骤5: 创建底层套餐
1. 点击"新增套餐"按钮
2. 填写表单：
   - **套餐编码**：如 `CMCC-1G-M`（必填，唯一）
   - **套餐名称**：如 `中国移动1GB月包`（必填）
   - **运营商**：选择运营商（必填）
   - **周期类型**：月包/年包（必填）
   - **流量规格**：输入数值，选择单位MB/GB（必填）
   - **有效天数**：默认月包30天，年包360天（可选）
   - **成本价**：采购成本（必填）
   - **供应商**：选择供应商（必填）
   - **状态**：启用/禁用（必填）
   - **备注**：可选
3. 点击"确定"保存

### 步骤6: 创建销售套餐
1. 切换到"销售套餐"标签
2. 点击"新增销售套餐"按钮
3. 填写表单：
   - **底层套餐**：选择关联的底层套餐（可选，选择后会自动填充信息）
   - **套餐编码**：如 `CMCC-1G-M-SALE`（必填，唯一）
   - **销售套餐名称**：如 `移动1GB月包（销售）`（必填）
   - **运营商**：选择运营商（必填）
   - **周期类型**：月包/年包（必填）
   - **流量规格**：输入流量大小（必填）
   - **成本价**：成本价格（必填）
   - **有效天数**：有效天数（可选）
   - **销售价格**：销售价格（必填，不能低于成本价）
   - **状态**：启用/禁用（必填）
   - **备注**：可选
4. 系统会自动计算利润率并显示颜色标识：
   - 🔴 红色：亏损（利润率 < 0%）
   - 🟠 橙色：低利润（0% ≤ 利润率 < 10%）
   - 🟢 绿色：正常（利润率 ≥ 10%）
5. 点击"确定"保存

## 📊 功能特性

### 底层套餐管理
- ✅ 列表展示（分页、排序）
- ✅ 多条件搜索（关键词、运营商、周期、供应商、状态）
- ✅ 新增套餐
- ✅ 编辑套餐
- ✅ 删除套餐
- ✅ 启用/禁用套餐
- ✅ 流量单位自动转换（MB/GB）
- ✅ 供应商关联显示

### 销售套餐管理
- ✅ 列表展示（分页、排序）
- ✅ 多条件搜索（关键词、底层套餐、状态）
- ✅ 新增套餐
- ✅ 编辑套餐
- ✅ 删除套餐
- ✅ 启用/禁用套餐
- ✅ 底层套餐关联
- ✅ 利润率自动计算
- ✅ 利润率颜色标识
- ✅ 智能表单填充

## 🐛 常见问题

### 问题1: 页面显示空白
**原因**：数据库中没有数据

**解决方案**：
1. 打开浏览器控制台（F12）
2. 查看 Console 标签页的日志
3. 如果显示"暂无供应商数据"，需要先创建供应商
4. 如果显示"暂无套餐数据"，需要先创建套餐

### 问题2: 创建套餐时提示"供应商不存在"
**原因**：数据库中没有供应商数据

**解决方案**：
```sql
-- 在MySQL中创建测试供应商
INSERT INTO suppliers (name, contact, phone, status, created_at, updated_at) 
VALUES 
  ('中国移动供应商', '李四', '13900139000', 'enable', NOW(), NOW()),
  ('中国联通供应商', '王五', '13700137000', 'enable', NOW(), NOW()),
  ('中国电信供应商', '赵六', '13600136000', 'enable', NOW(), NOW());
```

### 问题3: 创建套餐时提示"套餐编码已存在"
**原因**：套餐编码必须唯一

**解决方案**：
- 修改套餐编码，使用不同的名称
- 建议格式：`{运营商}-{流量}-{周期}-{序号}`
- 例如：`CMCC-1G-M-001`, `CMCC-1G-M-002`

### 问题4: 销售价格不能低于成本价
**原因**：前端验证规则，防止亏本销售

**解决方案**：
- 确保销售价格 ≥ 成本价
- 如果确实需要低价销售，需要修改验证规则

### 问题5: API返回401错误
**原因**：未登录或Token过期

**解决方案**：
1. 重新登录系统
2. 检查浏览器 localStorage 中是否有 `access_token`
3. 如果Token过期，系统会自动跳转到登录页

## 📝 数据库表结构

### supplier_packages（底层套餐表）
```sql
CREATE TABLE supplier_packages (
  id INT PRIMARY KEY AUTO_INCREMENT,
  code VARCHAR(50) UNIQUE NOT NULL COMMENT '套餐编码',
  name VARCHAR(100) NOT NULL COMMENT '套餐名称',
  carrier ENUM('cmcc','cucc','ctcc') NOT NULL COMMENT '运营商',
  flow_size INT NOT NULL COMMENT '流量大小(MB)',
  period_type ENUM('monthly','yearly') NOT NULL COMMENT '周期类型',
  effective_days INT NOT NULL COMMENT '有效天数',
  price_cost DECIMAL(10,2) NOT NULL COMMENT '成本价',
  supplier_id INT NOT NULL COMMENT '供应商ID',
  status ENUM('enable','disable') DEFAULT 'enable',
  remark TEXT,
  created_at DATETIME,
  updated_at DATETIME,
  is_deleted TINYINT DEFAULT 0
);
```

### sale_packages（销售套餐表）
```sql
CREATE TABLE sale_packages (
  id INT PRIMARY KEY AUTO_INCREMENT,
  code VARCHAR(50) UNIQUE NOT NULL COMMENT '套餐编码',
  name VARCHAR(100) NOT NULL COMMENT '套餐名称',
  base_package_id INT COMMENT '关联的底层套餐ID',
  carrier ENUM('cmcc','cucc','ctcc') NOT NULL COMMENT '运营商',
  flow_size INT NOT NULL COMMENT '流量大小(MB)',
  period_type ENUM('monthly','yearly') NOT NULL COMMENT '周期类型',
  effective_days INT NOT NULL COMMENT '有效天数',
  price_cost DECIMAL(10,2) NOT NULL COMMENT '成本价',
  price_sale DECIMAL(10,2) NOT NULL COMMENT '销售价',
  is_public TINYINT DEFAULT 0 COMMENT '是否公开',
  sort_order INT DEFAULT 0 COMMENT '排序',
  user_id INT COMMENT '所属用户ID',
  status ENUM('enable','disable') DEFAULT 'enable',
  remark TEXT,
  created_at DATETIME,
  updated_at DATETIME,
  is_deleted TINYINT DEFAULT 0
);
```

## 🎯 下一步计划

1. **供应商管理模块**：创建供应商管理页面，方便添加供应商
2. **批量导入**：支持Excel批量导入套餐
3. **套餐统计**：显示套餐使用情况统计
4. **套餐复制**：快速复制现有套餐创建新套餐
5. **套餐历史**：记录套餐价格变更历史

## 📞 技术支持

如有问题，请查看：
- 浏览器控制台（F12 → Console）
- 前端日志：已添加详细的 `console.log`
- 后端日志：`/Users/huiren/Documents/goodman/iot_card_platform/logs/app.log`

---

**最后更新**：2026-02-09  
**状态**：✅ 已完成，可以正常使用





