# 供应商模块开发文档

## 📋 模块概述

供应商模块用于管理物联网卡供应商信息，包括供应商基本信息、联系方式、API对接配置等。

**开发时间**: 2026-02-09  
**开发状态**: ✅ 已完成

---

## 🎯 功能特性

### 1. 供应商管理
- ✅ 供应商列表查询（分页、筛选）
- ✅ 新增供应商
- ✅ 编辑供应商信息
- ✅ 删除供应商
- ✅ 启用/禁用供应商
- ✅ API连接测试

### 2. 查询筛选
- ✅ 关键词搜索（名称/编码）
- ✅ 按供应商类型筛选
- ✅ 按状态筛选

### 3. 供应商类型
- 中国移动 (cmcc)
- 中国联通 (cucc)
- 中国电信 (ctcc)
- 虚拟运营商 (mvno)
- 其他 (other)

---

## 📁 文件结构

```
frontend/src/
├── api/modules/
│   └── supplier.ts                    # 供应商API接口
├── types/
│   └── supplier.d.ts                  # 供应商类型定义
├── constants/
│   └── supplier.ts                    # 供应商常量
└── views/suppliers/
    ├── index.vue                      # 供应商列表页
    └── components/
        └── SupplierFormDialog.vue     # 供应商表单弹窗

backend/app/
├── api/v1/
│   └── supplier.py                    # 供应商API路由
├── db/models/
│   └── supplier.py                    # 供应商数据模型
├── schemas/
│   └── supplier.py                    # 供应商Schema
├── crud/
│   └── supplier_crud.py               # 供应商CRUD操作
└── services/
    └── supplier_service.py            # 供应商业务逻辑
```

---

## 🔌 API 接口

### 1. 获取供应商列表
```typescript
GET /api/v1/suppliers

// 请求参数
{
  keyword?: string      // 关键词搜索
  type?: string        // 供应商类型
  status?: string      // 状态
  page?: number        // 页码
  page_size?: number   // 每页数量
}

// 响应
{
  code: 200,
  data: {
    list: Supplier[],
    total: number,
    page: number,
    page_size: number
  }
}
```

### 2. 获取供应商选项
```typescript
GET /api/v1/suppliers/options

// 响应
{
  code: 200,
  data: Supplier[]  // 所有启用的供应商
}
```

### 3. 创建供应商
```typescript
POST /api/v1/suppliers

// 请求体
{
  name: string           // 供应商名称 *
  code: string          // 供应商编码 *
  type: string          // 供应商类型 *
  contact_name?: string // 联系人
  contact_phone?: string // 联系电话
  contact_email?: string // 联系邮箱
  api_url?: string      // API地址
  api_key?: string      // API Key
  api_secret?: string   // API Secret
  api_config?: object   // API配置
  remark?: string       // 备注
}

// 响应
{
  code: 200,
  msg: "创建成功",
  data: Supplier
}
```

### 4. 更新供应商
```typescript
PUT /api/v1/suppliers/{id}

// 请求体（所有字段可选）
{
  name?: string
  type?: string
  contact_name?: string
  contact_phone?: string
  contact_email?: string
  api_url?: string
  api_key?: string
  api_secret?: string
  api_config?: object
  remark?: string
  status?: string
}

// 响应
{
  code: 200,
  msg: "更新成功",
  data: Supplier
}
```

### 5. 删除供应商
```typescript
DELETE /api/v1/suppliers/{id}

// 响应
{
  code: 200,
  msg: "删除成功"
}
```

### 6. 测试API连接
```typescript
POST /api/v1/suppliers/{id}/test

// 响应
{
  code: 200,
  data: {
    success: boolean,
    message: string,
    response_time?: number
  }
}
```

---

## 💾 数据模型

### 供应商表 (suppliers)

```sql
CREATE TABLE `suppliers` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(100) NOT NULL COMMENT '供应商名称',
    `code` VARCHAR(50) NOT NULL COMMENT '供应商编码',
    `type` ENUM('cmcc', 'cucc', 'ctcc', 'mvno', 'other') DEFAULT 'other' COMMENT '供应商类型',
    `contact_name` VARCHAR(50) DEFAULT NULL COMMENT '联系人',
    `contact_phone` VARCHAR(20) DEFAULT NULL COMMENT '联系电话',
    `contact_email` VARCHAR(100) DEFAULT NULL COMMENT '联系邮箱',
    `api_url` VARCHAR(255) DEFAULT NULL COMMENT 'API地址',
    `api_key` VARCHAR(255) DEFAULT NULL COMMENT 'API Key',
    `api_secret` VARCHAR(255) DEFAULT NULL COMMENT 'API Secret',
    `api_config` JSON DEFAULT NULL COMMENT 'API配置',
    `remark` VARCHAR(500) DEFAULT NULL COMMENT '备注',
    `status` ENUM('enable', 'disable') DEFAULT 'enable' COMMENT '状态',
    `created_by` BIGINT UNSIGNED DEFAULT NULL COMMENT '创建人ID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_deleted` TINYINT DEFAULT 0,
    
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_code` (`code`),
    KEY `idx_type` (`type`),
    KEY `idx_status` (`status`)
) COMMENT='供应商表';
```

---

## 🎨 界面设计

### 1. 列表页面

**功能区域**：
- 页面标题和描述
- 搜索筛选区（关键词、类型、状态）
- 操作按钮（新增供应商）
- 数据表格
- 分页组件

**表格列**：
- 供应商编码
- 供应商名称
- 类型（标签显示）
- 联系人
- 联系电话
- 联系邮箱
- API配置状态
- 状态（启用/禁用）
- 备注
- 创建时间
- 操作（编辑、测试API、启用/禁用、删除）

### 2. 表单弹窗

**基本信息**：
- 供应商编码（新增时必填，编辑时禁用）
- 供应商名称（必填）
- 供应商类型（必填）

**联系信息**：
- 联系人
- 联系电话（手机号格式验证）
- 联系邮箱（邮箱格式验证）

**API配置**：
- API地址（URL格式验证）
- API Key（密码框）
- API Secret（密码框）
- API配置（JSON格式）

**其他**：
- 状态（启用/禁用）
- 备注

---

## 🔐 权限控制

**访问权限**: 仅超级管理员可访问

所有供应商管理接口都需要超级管理员权限：
```python
current_user: CurrentUser = Depends(require_super_admin)
```

---

## ✅ 表单验证

### 前端验证规则

```typescript
{
  code: [
    { required: true, message: '请输入供应商编码' },
    { min: 1, max: 50, message: '长度在 1 到 50 个字符' },
    { pattern: /^[A-Za-z0-9_-]+$/, message: '只能包含字母、数字、下划线和横线' }
  ],
  name: [
    { required: true, message: '请输入供应商名称' },
    { min: 1, max: 100, message: '长度在 1 到 100 个字符' }
  ],
  type: [
    { required: true, message: '请选择供应商类型' }
  ],
  contact_phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码' }
  ],
  contact_email: [
    { type: 'email', message: '请输入正确的邮箱地址' }
  ],
  api_url: [
    { type: 'url', message: '请输入正确的URL地址' }
  ]
}
```

### 后端验证

使用 Pydantic 进行数据验证：
```python
class SupplierCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=50)
    type: SupplierType = Field(default=SupplierType.OTHER)
    # ... 其他字段
```

---

## 🎯 使用场景

### 场景1：添加新供应商

1. 点击"新增供应商"按钮
2. 填写供应商基本信息（编码、名称、类型）
3. 填写联系信息（可选）
4. 配置API信息（可选）
5. 点击"确定"提交

### 场景2：配置API对接

1. 编辑供应商
2. 填写API地址、Key、Secret
3. 配置额外参数（JSON格式）
4. 保存后点击"测试API"验证连接

### 场景3：管理供应商状态

1. 在列表中找到目标供应商
2. 点击"启用"或"禁用"按钮
3. 确认操作

---

## 🔧 技术实现

### 1. API配置JSON编辑

支持在表单中编辑JSON格式的API配置：

```typescript
// 编辑时格式化显示
if (data.api_config) {
  apiConfigText.value = JSON.stringify(data.api_config, null, 2)
}

// 提交时解析JSON
if (apiConfigText.value.trim()) {
  try {
    formData.api_config = JSON.parse(apiConfigText.value)
  } catch (e) {
    ElMessage.error('API配置JSON格式不正确')
    return
  }
}
```

### 2. 密钥安全处理

- 编辑时不回显API Key和Secret
- 如果编辑时密钥字段为空，则不更新该字段
- 使用密码框显示密钥输入

```typescript
// 编辑时不回显
api_key: '',  // 不回显密钥
api_secret: '',  // 不回显密钥

// 提交时处理
if (!updateData.api_key) delete updateData.api_key
if (!updateData.api_secret) delete updateData.api_secret
```

### 3. 类型标签颜色

根据供应商类型显示不同颜色的标签：

```typescript
const getTypeTagType = (type: string) => {
  const typeMap: Record<string, string> = {
    cmcc: '',          // 默认蓝色
    cucc: 'success',   // 绿色
    ctcc: 'warning',   // 橙色
    mvno: 'info',      // 灰色
    other: 'info'      // 灰色
  }
  return typeMap[type] || ''
}
```

---

## 🧪 测试要点

### 功能测试

- [ ] 创建供应商（各种类型）
- [ ] 编辑供应商信息
- [ ] 删除供应商
- [ ] 启用/禁用供应商
- [ ] 搜索筛选功能
- [ ] 分页功能
- [ ] API连接测试

### 验证测试

- [ ] 必填字段验证
- [ ] 编码唯一性验证
- [ ] 手机号格式验证
- [ ] 邮箱格式验证
- [ ] URL格式验证
- [ ] JSON格式验证

### 边界测试

- [ ] 超长文本输入
- [ ] 特殊字符输入
- [ ] 空值处理
- [ ] 并发操作

---

## 📝 注意事项

### 1. 编码唯一性

供应商编码必须唯一，数据库有唯一索引约束。创建时需要检查编码是否已存在。

### 2. 删除限制

删除供应商前应检查是否有关联的底层套餐或卡片。如果有关联数据，应提示用户无法删除。

### 3. API配置安全

- API Key和Secret应加密存储
- 不在日志中记录敏感信息
- 编辑时不回显密钥

### 4. 权限控制

所有供应商管理功能仅限超级管理员访问，前端和后端都需要进行权限验证。

---

## 🚀 后续优化

### 功能增强

- [ ] 供应商API对接实现
- [ ] 批量导入供应商
- [ ] 供应商数据统计
- [ ] 供应商评分系统
- [ ] API调用日志记录

### 性能优化

- [ ] 列表数据缓存
- [ ] 搜索防抖优化
- [ ] 虚拟滚动（大数据量）

### 用户体验

- [ ] 表单自动保存草稿
- [ ] 操作历史记录
- [ ] 批量操作功能

---

## 📚 相关文档

- [套餐管理模块](./PACKAGE_MODULE.md)
- [出入库管理模块](./STOCK_MODULE.md)
- [API文档](../API_DOCUMENTATION.md)
- [故障排查](../TROUBLESHOOTING.md)

---

## 📊 开发统计

- **开发时间**: 约2小时
- **代码行数**: 
  - 前端: ~800行
  - 后端: ~300行（已有）
- **文件数量**: 7个
- **API接口**: 6个

---

## ✅ 完成清单

- [x] 数据模型设计
- [x] 后端API实现
- [x] 前端类型定义
- [x] 前端常量定义
- [x] API接口封装
- [x] 列表页面开发
- [x] 表单弹窗开发
- [x] 路由配置
- [x] 权限控制
- [x] 表单验证
- [x] 文档编写

---

**文档维护**: 2026-02-09  
**维护者**: 开发团队




