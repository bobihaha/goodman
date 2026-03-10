# 模块4: 出入库管理模块 - 代码审查报告

**审查时间**: 2026-03-06
**优先级**: 🔴 CRITICAL
**审查状态**: ✅ 已完成

---

## 📋 审查范围

### 后端文件
- `app/api/v1/stock.py` - 出入库API路由
- `app/services/stock_service.py` - 出入库服务层
- `app/crud/stock_crud.py` - 数据库操作层 (1203行)
- `app/db/models/stock.py` - 数据模型

---

## 🔴 CRITICAL 问题

### 1. 批量操作缺少事务回滚机制
**文件**: `app/crud/stock_crud.py:200-243`
**问题**: 入库操作中，部分卡片失败后继续提交成功的卡片，但未正确处理事务
**风险**:
- 数据不一致：部分卡片入库成功，部分失败
- 库存统计错误
- 无法完整回滚失败操作

**代码片段**:
```python
# 当前实现：部分成功部分失败
for card in cards:
    try:
        # 创建卡片
        success_count += 1
    except:
        fail_details.append(...)

await db.commit()  # 提交所有成功的
```

**建议**: 使用savepoint或全部成功/全部失败策略
```python
try:
    async with db.begin_nested():  # savepoint
        for card in cards:
            # 创建卡片，任何失败都回滚
    await db.commit()
except Exception:
    await db.rollback()
    raise BusinessException("入库失败，已回滚")
```

---

### 2. ICCID格式验证不足
**文件**: `app/crud/stock_crud.py` (入库逻辑)
**问题**: 未严格验证ICCID格式（应为19-20位数字）
**风险**:
- 无效ICCID入库
- 后续同步失败
- 供应商API调用失败

**建议**:
```python
import re
def validate_iccid(iccid: str):
    if not re.match(r'^\d{19,20}$', iccid):
        raise ValueError(f"ICCID格式错误: {iccid}")
```

---

### 3. 出库权限校验不完整
**文件**: `app/api/v1/stock.py:109`
**问题**: 仅检查`require_super_admin`，未验证目标用户是否存在
**风险**:
- 出库给不存在的用户
- 数据孤岛

**建议**:
```python
# 在service层添加
target_user = await sys_user_crud.get_by_id(db, to_user_id)
if not target_user:
    raise BusinessException(msg="目标用户不存在")
if target_user.status != UserStatus.enable:
    raise BusinessException(msg="目标用户已禁用")
```

---

### 4. 库存数量统计可能不准确
**文件**: `app/crud/stock_crud.py:241`
**问题**: 批次计数更新与卡片创建不在同一事务
**风险**: 并发操作导致计数错误

**建议**: 使用数据库触发器或在同一事务内更新

---

## 🟠 HIGH 问题

### 5. Excel导入缺少文件大小限制
**文件**: `app/api/v1/stock.py:406` (batch_stock_out_import)
**问题**: 未限制上传文件大小
**风险**:
- 内存溢出
- DoS攻击

**建议**:
```python
from fastapi import UploadFile, File
@router.post("/batch-import")
async def batch_import(
    file: UploadFile = File(..., max_length=10*1024*1024)  # 10MB
):
    ...
```

---

### 6. 批量查询无数量限制
**文件**: `app/api/v1/stock.py` (batch_query)
**问题**: 允许查询任意数量ICCID
**风险**:
- 数据库压力过大
- 响应超时

**建议**:
```python
if len(iccid_list) > 10000:
    raise BusinessException(msg="单次最多查询10000条")
```

---

### 7. 回收操作不可逆
**文件**: `app/crud/stock_crud.py:997` (recycle_cards)
**问题**: 卡片回收后无法恢复
**建议**: 添加软删除标记，保留30天恢复期

---

## 🟡 MEDIUM 问题

### 8. 单号生成可能重复
**文件**: `app/crud/stock_crud.py:18-30`
**问题**: 使用时间戳+4位随机，高并发下可能重复
```python
def generate_batch_no() -> str:
    return f"B{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:4].upper()}"
```

**建议**: 使用数据库自增ID或UUID全量
```python
def generate_batch_no() -> str:
    return f"B{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"
```

---

### 9. N+1查询问题
**文件**: `app/services/stock_service.py:77-88`
**问题**: 循环中查询supplier_name和package_name
```python
for item in items:
    supplier_query = select(SupplierModel.name).where(...)
    supplier_result = await db.execute(supplier_query)
```

**建议**: 使用JOIN或预加载
```python
query = select(PurchaseBatchModel).join(SupplierModel).join(SupplierPackageModel)
```

---

### 10. 日期格式不统一
**问题**: 部分使用date，部分使用datetime
**建议**: 统一使用datetime，前端格式化

---

## 🟢 LOW 问题

### 11. 错误信息不够友好
**示例**: `raise ValueError("批次不存在")`
**建议**: 使用BusinessException并提供错误码

---

### 12. 缺少操作日志
**问题**: 出入库操作未记录详细日志
**建议**: 添加操作日志表，记录操作人、时间、详情

---

## ✅ 优点

1. ✅ 权限控制严格（仅超级管理员）
2. ✅ 记录详细（入库单、出库单、回收单）
3. ✅ 支持批量操作
4. ✅ 失败详情记录（fail_details）
5. ✅ 状态管理清晰（BatchStatus, StockInStatus）

---

## 📊 问题统计

| 级别 | 数量 | 必须修复 |
|------|------|----------|
| 🔴 CRITICAL | 4 | ✅ 是 |
| 🟠 HIGH | 3 | ✅ 建议 |
| 🟡 MEDIUM | 3 | ⚠️ 可选 |
| 🟢 LOW | 2 | ❌ 否 |

---

## 🔧 修复优先级

1. **立即修复**:
   - 添加事务回滚机制
   - ICCID格式验证
   - 出库用户存在性验证
   - 库存统计事务一致性

2. **本周修复**:
   - 文件大小限制
   - 批量查询数量限制
   - 回收软删除

3. **下次迭代**:
   - 优化N+1查询
   - 统一日期格式
   - 完善日志
