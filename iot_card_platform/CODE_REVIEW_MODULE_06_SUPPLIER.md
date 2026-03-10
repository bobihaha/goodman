# 模块6: 供应商管理模块 - 代码审查报告

**审查时间**: 2026-03-06
**优先级**: 🟡 MEDIUM
**审查状态**: ✅ 已完成

---

## 📋 审查范围

### 后端文件
- `app/api/v1/supplier.py` - 供应商管理API路由
- `app/services/supplier_service.py` - 供应商服务层
- `app/crud/supplier_crud.py` - 数据库操作层

---

## 🔴 CRITICAL 问题

**无CRITICAL问题** ✅

---

## 🟠 HIGH 问题

### 1. API密钥明文存储
**文件**: `app/services/supplier_service.py:84-92`
**问题**: API Key和Secret直接存储在数据库，未加密
**风险**: 数据库泄露导致供应商API凭证泄露

**建议**:
```python
from cryptography.fernet import Fernet
import os

# 使用环境变量中的加密密钥
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
cipher = Fernet(ENCRYPTION_KEY)

def encrypt_secret(secret: str) -> str:
    return cipher.encrypt(secret.encode()).decode()

def decrypt_secret(encrypted: str) -> str:
    return cipher.decrypt(encrypted.encode()).decode()
```

---

### 2. API测试使用真实ICCID探测
**文件**: `app/services/supplier_service.py:95-106`
**问题**: 使用固定的假ICCID测试，可能被供应商识别为异常行为
**风险**: 被供应商封禁IP或账号

**建议**: 使用供应商提供的测试接口或健康检查接口

---

## 🟡 MEDIUM 问题

### 3. 删除检查完整但性能较差
**文件**: `app/services/supplier_service.py:65-71`
**问题**: 两次count查询，可以合并
**建议**:
```python
# 一次查询获取两个计数
from sqlalchemy import select, func, union_all
stmt = select(
    func.count(PackageModel.id).label('package_count'),
    func.count(IotCardModel.id).label('card_count')
).select_from(...)
```

---

### 4. 异常处理过于宽泛
**文件**: `app/services/supplier_service.py:100`
**问题**: `except Exception` 捕获所有异常
**建议**: 区分网络错误、认证错误、业务错误

---

## 🟢 LOW 问题

### 5. 缺少操作日志
**问题**: 供应商创建、更新、删除未记录审计日志
**建议**: 添加操作日志记录

---

## ✅ 优点

1. ✅ 删除前检查关联数据（套餐、卡片）
2. ✅ 供应商编码唯一性验证
3. ✅ 权限控制严格（仅超级管理员）
4. ✅ API连通性测试功能

---

## 📊 问题统计

| 级别 | 数量 | 必须修复 |
|------|------|----------|
| 🔴 CRITICAL | 0 | ❌ 否 |
| 🟠 HIGH | 2 | ✅ 建议 |
| 🟡 MEDIUM | 2 | ⚠️ 可选 |
| 🟢 LOW | 1 | ❌ 否 |

---

## 🔧 修复优先级

1. **本周修复**:
   - API密钥加密存储
   - API测试方法优化

2. **下次迭代**:
   - 删除检查性能优化
   - 异常处理精确化
   - 操作日志记录
