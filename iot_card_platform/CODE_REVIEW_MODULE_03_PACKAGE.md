# 模块3: 套餐管理模块 - 代码审查报告

**审查时间**: 2026-03-06
**优先级**: 🟡 MEDIUM
**审查状态**: ✅ 已完成

---

## 📋 审查范围

### 后端文件
- `app/api/v1/package.py` - 套餐管理API路由
- `app/services/package_service.py` - 套餐服务层
- `app/crud/package_crud.py` - 数据库操作层
- `app/db/models/package.py` - 套餐数据模型

---

## 🔴 CRITICAL 问题

### 1. 删除套餐未检查关联数据
**文件**: `app/services/package_service.py:92-100, 211-224`
**问题**: 删除底层套餐和销售套餐时，仅有TODO注释，未实际检查关联的卡片
**风险**:
- 删除正在使用的套餐导致卡片数据孤岛
- 外键约束错误
- 业务数据不一致

**代码片段**:
```python
async def delete_package(self, db: AsyncSession, package_id: int) -> bool:
    package = await supplier_package_crud.get_by_id(db, package_id)
    if not package:
        raise BusinessException(code=404, msg="套餐不存在")

    # TODO: 检查是否有关联的销售套餐或卡片

    return await supplier_package_crud.delete(db, package_id)
```

**建议**: 实现关联检查
```python
# 检查是否有销售套餐关联
from app.crud.package_crud import sale_package_crud
sale_count = await sale_package_crud.count_by_base_package(db, package_id)
if sale_count > 0:
    raise BusinessException(msg=f"该套餐被{sale_count}个销售套餐使用，无法删除")

# 检查是否有卡片使用
from app.crud.iot_card_crud import iot_card_crud
card_count = await iot_card_crud.count_by_package(db, package_id)
if card_count > 0:
    raise BusinessException(msg=f"该套餐被{card_count}张卡片使用，无法删除")
```

---

## 🟠 HIGH 问题

### 2. N+1查询问题严重
**文件**: `app/services/package_service.py:49-72, 149-175`
**问题**: 循环中查询供应商名称和底层套餐名称
**风险**: 性能问题，列表查询缓慢

**代码片段**:
```python
# 获取供应商名称映射
supplier_ids = list(set([p.supplier_id for p in packages]))
supplier_map = {}
for sid in supplier_ids:
    supplier = await supplier_crud.get_by_id(db, sid)  # N+1查询
    if supplier:
        supplier_map[sid] = supplier.name
```

**建议**: 使用批量查询或JOIN
```python
from sqlalchemy import select
from app.db.models.supplier import SupplierModel

# 批量查询供应商
stmt = select(SupplierModel).where(SupplierModel.id.in_(supplier_ids))
suppliers = (await db.execute(stmt)).scalars().all()
supplier_map = {s.id: s.name for s in suppliers}
```

---

### 3. 价格验证缺失
**文件**: `app/services/package_service.py:106-129`
**问题**: 创建销售套餐时未验证价格合理性
**风险**: 销售价低于成本价导致亏损

**建议**:
```python
if data.price_sale < data.price_cost:
    raise BusinessException(msg="销售价不能低于成本价")

if data.price_sale <= 0 or data.price_cost <= 0:
    raise BusinessException(msg="价格必须大于0")
```

---

### 4. 规格三要素未强制唯一
**文件**: `app/services/package_service.py:20-35`
**问题**: 未验证运营商+流量+周期的组合唯一性
**风险**: 创建重复规格的套餐，导致混淆

**建议**:
```python
# 检查规格是否已存在
existing = await supplier_package_crud.get_by_spec(
    db, data.supplier_id, data.carrier, data.flow_size, data.period_type
)
if existing:
    raise BusinessException(msg=f"该规格套餐已存在: {existing.get_spec_name()}")
```

---

## 🟡 MEDIUM 问题

### 5. 流量大小未验证范围
**文件**: `app/services/package_service.py:20-35`
**问题**: 未限制flow_size的合理范围
**建议**: 限制流量范围（如10MB-100GB）

---

### 6. 套餐编码格式未验证
**文件**: `app/services/package_service.py:20-35, 106-129`
**问题**: 未验证套餐编码格式
**建议**: 使用正则验证编码格式（如：PKG_CMCC_1G_M）

---

### 7. 价格精度问题
**文件**: `app/db/models/package.py:66, 140-141`
**问题**: DECIMAL(10, 2)可能不足以存储大额价格
**建议**: 考虑使用DECIMAL(12, 2)或更高精度

---

## 🟢 LOW 问题

### 8. 代码重复
**文件**: `app/db/models/package.py:72-90, 151-167`
**问题**: `get_spec_name()` 和 `_format_flow_size()` 在两个模型中重复
**建议**: 提取到工具类

---

### 9. 缺少套餐使用统计
**问题**: 无法查看套餐被多少卡片使用
**建议**: 添加统计字段或接口

---

## ✅ 优点

1. ✅ 规格三要素设计清晰
2. ✅ 底层套餐与销售套餐分离
3. ✅ 支持专属客户套餐（user_id）
4. ✅ 权限控制严格
5. ✅ 流量显示格式化友好

---

## 📊 问题统计

| 级别 | 数量 | 必须修复 |
|------|------|----------|
| 🔴 CRITICAL | 1 | ✅ 是 |
| 🟠 HIGH | 3 | ✅ 建议 |
| 🟡 MEDIUM | 3 | ⚠️ 可选 |
| 🟢 LOW | 2 | ❌ 否 |

---

## 🔧 修复优先级

1. **立即修复**:
   - 删除套餐前检查关联数据

2. **本周修复**:
   - N+1查询优化
   - 价格验证
   - 规格唯一性验证

3. **下次迭代**:
   - 流量范围验证
   - 编码格式验证
   - 代码重复消除
